import unittest
from unittest.mock import MagicMock, patch
import os
import tempfile

from voice.tts import TextToSpeech, clean_text_for_speech
from voice.stt import SpeechToText
from voice.voice_handler import VoiceHandler
from interfaces.terminal import TerminalInterface
from memory.database import Database
from memory.memory_store import MemoryStore
from core.orchestrator import Orchestrator
from core.llm_client import LLMProvider

class TestPhase3Voice(unittest.TestCase):
    def test_clean_text_for_speech(self):
        raw_md = "### Hello **world**! Here is `code` and [a link](https://example.com).\n```python\nprint('secret')\n```\n- Item 1\n- Item 2"
        cleaned = clean_text_for_speech(raw_md)
        self.assertNotIn("###", cleaned)
        self.assertNotIn("**", cleaned)
        self.assertNotIn("`", cleaned)
        self.assertNotIn("https://", cleaned)
        self.assertNotIn("print('secret')", cleaned)
        self.assertIn("Hello world!", cleaned)
        self.assertIn("Item 1 Item 2", cleaned)

    @patch("sounddevice.play")
    @patch("sounddevice.wait")
    @patch("soundfile.read", return_value=(MagicMock(), 24000))
    @patch.object(TextToSpeech, "_synthesize_audio_bytes", return_value=b"fake_mp3_data")
    def test_tts_speak(self, mock_synth, mock_sf, mock_sd_wait, mock_sd_play):
        tts_engine = TextToSpeech()
        tts_engine.speak("Hello from SERA", blocking=True)
        mock_sd_play.assert_called_once()
        mock_sd_wait.assert_called_once()

    def test_stt_transcription_with_mock(self):
        stt_engine = SpeechToText()
        stt_engine.client = MagicMock()
        stt_engine.client.audio.transcriptions.create.return_value = "hello sera open notepad"

        result = stt_engine.transcribe(b"RIFF....WAVEfmt ....data....fake_audio_bytes_more_than_100_bytes_padding_long_enough_for_test")
        self.assertEqual(result, "hello sera open notepad")

    def test_voice_handler_toggle(self):
        handler = VoiceHandler(tts_instance=MagicMock(), stt_instance=MagicMock())
        self.assertFalse(handler.voice_enabled)
        is_on = handler.toggle_voice()
        self.assertTrue(is_on)
        self.assertTrue(handler.voice_enabled)
        is_off = handler.toggle_voice()
        self.assertFalse(is_off)
        self.assertFalse(handler.voice_enabled)

    @patch.object(VoiceHandler, "speak_async")
    def test_terminal_voice_commands(self, mock_speak):
        class MockLLM(LLMProvider):
            def generate_response(self, messages, tools=None, stream=False):
                class MockChoice:
                    message = MagicMock(role="assistant", content="Hello!", tool_calls=None)
                mock_res = MagicMock()
                mock_res.choices = [MockChoice()]
                return mock_res

        temp_db_fd, temp_db_path = tempfile.mkstemp(suffix='.db')
        try:
            db = Database(db_path=temp_db_path)
            memory = MemoryStore(database=db)
            orch = Orchestrator(llm_client=MockLLM(), memory=memory, system_prompt="You are SERA.")
            terminal = TerminalInterface(orch)

            self.assertTrue(terminal._handle_command('/voice'))
            self.assertTrue(terminal.voice_handler.voice_enabled)
            mock_speak.assert_called_once()
            self.assertTrue(terminal._handle_command('/voice'))
            self.assertFalse(terminal.voice_handler.voice_enabled)
        finally:
            os.close(temp_db_fd)
            if os.path.exists(temp_db_path):
                os.remove(temp_db_path)

if __name__ == '__main__':
    unittest.main()
