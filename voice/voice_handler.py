import logging
import threading
from typing import Optional, Callable
from voice.tts import TextToSpeech, tts
from voice.stt import SpeechToText, stt

logger = logging.getLogger(__name__)

class VoiceHandler:
    """
    Unified voice coordinator managing Speech-To-Text (Groq Whisper)
    and Text-To-Speech (edge-tts) for SERA.
    """
    def __init__(self, tts_instance: Optional[TextToSpeech] = None, stt_instance: Optional[SpeechToText] = None):
        self.tts = tts_instance or tts
        self.stt = stt_instance or stt
        self.voice_enabled = False

    def toggle_voice(self) -> bool:
        """Toggles voice responses on/off."""
        self.voice_enabled = not self.voice_enabled
        return self.voice_enabled

    def speak(self, text: str, blocking: bool = False):
        """Speaks text using TTS if voice mode is enabled."""
        if not self.voice_enabled or not text:
            return
        self.tts.speak(text, blocking=blocking)

    def speak_async(self, text: str):
        """Asynchronously speaks text without blocking the caller."""
        self.speak(text, blocking=False)

    def record_and_transcribe(self, duration: float = 5.0) -> str:
        """Records from microphone for a fixed duration and returns transcribed text."""
        audio_bytes = self.stt.record_audio(duration=duration)
        return self.stt.transcribe(audio_bytes)

    def record_interactive(self, on_start: Optional[Callable] = None, on_stop: Optional[Callable] = None) -> str:
        """
        Records microphone input interactively until the user presses Enter in terminal.
        """
        stop_event = threading.Event()

        if on_start:
            on_start()

        # Start recording in background thread
        audio_container = {}

        def _record_worker():
            audio_container["bytes"] = self.stt.record_until_stopped(stop_event)

        record_thread = threading.Thread(target=_record_worker)
        record_thread.start()

        try:
            # Wait for user input to stop
            input()
        finally:
            stop_event.set()
            record_thread.join()
            if on_stop:
                on_stop()

        raw_bytes = audio_container.get("bytes", b"")
        return self.stt.transcribe(raw_bytes)

voice_handler = VoiceHandler()
