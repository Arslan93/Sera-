import re
import os
import io
import asyncio
import tempfile
import logging
import threading
import soundfile as sf
import sounddevice as sd
import edge_tts
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_VOICE = "en-US-AriaNeural"  # Clear, natural female voice. Alternatively: en-US-GuyNeural

def clean_text_for_speech(text: str) -> str:
    """
    Cleans markdown, URLs, code blocks, and special formatting from text
    so speech synthesis sounds fluent and natural.
    """
    if not text:
        return ""
    # Remove code blocks ```code```
    text = re.sub(r'```[\s\S]*?```', 'code block omitted', text)
    # Remove inline code `code`
    text = re.sub(r'`([^`]+)`', r'\1', text)
    # Remove markdown links [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Remove raw URLs
    text = re.sub(r'https?://\S+', 'link', text)
    # Remove markdown headers (#, ##)
    text = re.sub(r'#+\s*', '', text)
    # Remove bold/italic markers (*, _)
    text = re.sub(r'[*_]{1,3}', '', text)
    # Remove bullet markers (- , * , • )
    text = re.sub(r'^\s*[-*•]\s+', '', text, flags=re.MULTILINE)
    # Clean multiple spaces/newlines
    text = re.sub(r'\s+', ' ', text).strip()
    return text

class TextToSpeech:
    """
    Handles Text-To-Speech generation using Microsoft edge-tts and playback via sounddevice.
    """
    def __init__(self, voice: str = DEFAULT_VOICE):
        self.voice = voice
        self._lock = threading.Lock()

    async def _synthesize_audio_bytes(self, text: str) -> bytes:
        """Asynchronously synthesizes text into MP3/audio bytes using edge-tts."""
        communicate = edge_tts.Communicate(text, self.voice)
        audio_data = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data.extend(chunk["data"])
        return bytes(audio_data)

    def speak(self, text: str, blocking: bool = True):
        """
        Synthesizes and plays back speech audio for the given text.
        """
        clean_text = clean_text_for_speech(text)
        if not clean_text or len(clean_text.strip()) == 0:
            return

        def _run_speech():
            with self._lock:
                try:
                    # Run async synthesis
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    audio_bytes = loop.run_until_complete(self._synthesize_audio_bytes(clean_text))
                    loop.close()

                    if not audio_bytes:
                        return

                    # Read into soundfile and play via sounddevice
                    with io.BytesIO(audio_bytes) as audio_file:
                        data, samplerate = sf.read(audio_file)
                        sd.play(data, samplerate)
                        sd.wait()
                    logger.debug("Finished TTS playback.")
                except Exception as e:
                    logger.error(f"Error during TTS playback: {e}", exc_info=True)

        if blocking:
            _run_speech()
        else:
            thread = threading.Thread(target=_run_speech, daemon=True)
            thread.start()

    def speak_async(self, text: str):
        """Non-blocking convenience wrapper."""
        self.speak(text, blocking=False)

tts = TextToSpeech()
