import os
import io
import time
import wave
import tempfile
import logging
import threading
import numpy as np
import sounddevice as sd
from typing import Optional
from groq import Groq
from core.config import config

logger = logging.getLogger(__name__)

DEFAULT_SAMPLE_RATE = 16000  # 16 kHz sample rate (optimal for Whisper STT)
DEFAULT_CHANNELS = 1         # Mono audio

class SpeechToText:
    """
    Handles audio capture from the microphone and transcription using Groq-hosted Whisper API.
    """
    def __init__(self, api_key: Optional[str] = None, model: str = "whisper-large-v3-turbo"):
        self.api_key = api_key or config.groq_api_key
        self.model = model
        self.client = Groq(api_key=self.api_key)

    def record_audio(self, duration: float = 5.0, sample_rate: int = DEFAULT_SAMPLE_RATE) -> bytes:
        """
        Records audio from the default microphone for a fixed duration.
        Returns WAV audio bytes.
        """
        logger.info(f"Recording audio for {duration} seconds...")
        audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=DEFAULT_CHANNELS, dtype='int16')
        sd.wait()
        logger.info("Audio recording completed.")

        # Convert numpy array to WAV bytes
        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wf:
            wf.setnchannels(DEFAULT_CHANNELS)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sample_rate)
            wf.writeframes(audio_data.tobytes())
        
        return wav_io.getvalue()

    def record_until_stopped(self, stop_event: threading.Event, sample_rate: int = DEFAULT_SAMPLE_RATE) -> bytes:
        """
        Records audio in blocks continuously until stop_event is set.
        """
        logger.info("Recording audio continuously until stop event...")
        recorded_frames = []

        def callback(indata, frames, time_info, status):
            if status:
                logger.warning(f"Audio record status: {status}")
            recorded_frames.append(indata.copy())

        with sd.InputStream(samplerate=sample_rate, channels=DEFAULT_CHANNELS, dtype='int16', callback=callback):
            while not stop_event.is_set():
                time.sleep(0.05)

        logger.info("Recording stopped.")
        if not recorded_frames:
            return b""

        full_audio = np.concatenate(recorded_frames, axis=0)
        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wf:
            wf.setnchannels(DEFAULT_CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(full_audio.tobytes())

        return wav_io.getvalue()

    def transcribe(self, audio_bytes: bytes) -> str:
        """
        Transcribes WAV audio bytes into text using Groq's Whisper API.
        """
        if not audio_bytes or len(audio_bytes) < 10:
            return ""

        temp_wav = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_wav = f.name
                f.write(audio_bytes)

            with open(temp_wav, "rb") as audio_file:
                logger.info(f"Sending audio transcription request to Groq ({self.model})...")
                transcription = self.client.audio.transcriptions.create(
                    file=(os.path.basename(temp_wav), audio_file.read()),
                    model=self.model,
                    response_format="text"
                )

            transcribed_text = transcription if isinstance(transcription, str) else getattr(transcription, "text", str(transcription))
            cleaned = transcribed_text.strip()
            logger.info(f"Transcribed audio: '{cleaned}'")
            return cleaned
        except Exception as e:
            logger.error(f"Failed to transcribe audio with Groq Whisper: {e}", exc_info=True)
            return ""
        finally:
            if temp_wav and os.path.exists(temp_wav):
                try:
                    os.remove(temp_wav)
                except Exception:
                    pass

stt = SpeechToText()
