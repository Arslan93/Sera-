import io
import time
import wave
import logging
import threading
import numpy as np
import sounddevice as sd
from typing import Callable, Optional, List
from voice.stt import SpeechToText, stt

logger = logging.getLogger(__name__)

DEFAULT_WAKE_WORDS = ["hey sera", "sera", "wake up sera"]
ENERGY_THRESHOLD = 500  # RMS energy threshold to trigger speech chunk check
CHUNK_DURATION = 2.0    # 2-second listening chunks

class WakeWordListener:
    """
    Background hands-free wake word listener for SERA.
    Monitors audio energy and verifies wake phrases using Whisper.
    """
    def __init__(self, stt_instance: Optional[SpeechToText] = None, wake_words: Optional[List[str]] = None):
        self.stt = stt_instance or stt
        self.wake_words = [w.lower() for w in (wake_words or DEFAULT_WAKE_WORDS)]
        self.is_listening = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self, on_wake: Callable[[], None]):
        """Starts background wake word listener thread."""
        if self.is_listening:
            return

        self.is_listening = True
        self._stop_event.clear()

        def _worker():
            logger.info("Wake word listener started.")
            sample_rate = 16000
            channels = 1
            chunk_samples = int(CHUNK_DURATION * sample_rate)

            while not self._stop_event.is_set():
                try:
                    # Record a short chunk
                    audio = sd.rec(chunk_samples, samplerate=sample_rate, channels=channels, dtype='int16')
                    sd.wait()

                    if self._stop_event.is_set():
                        break

                    # Calculate RMS energy
                    rms = np.sqrt(np.mean(audio.astype(float)**2))
                    if rms < ENERGY_THRESHOLD:
                        time.sleep(0.1)
                        continue

                    # Energy detected, transcribe chunk
                    wav_io = io.BytesIO()
                    with wave.open(wav_io, 'wb') as wf:
                        wf.setnchannels(channels)
                        wf.setsampwidth(2)
                        wf.setframerate(sample_rate)
                        wf.writeframes(audio.tobytes())

                    text = self.stt.transcribe(wav_io.getvalue()).lower().strip()
                    logger.debug(f"Wake word audio chunk: '{text}' (RMS: {rms:.1f})")

                    for wake_phrase in self.wake_words:
                        if wake_phrase in text:
                            logger.info(f"Wake word detected: '{wake_phrase}'!")
                            on_wake()
                            # Pause briefly after wake trigger
                            time.sleep(1.0)
                            break

                except Exception as e:
                    logger.error(f"Error in wake word listener: {e}")
                    time.sleep(0.5)

            logger.info("Wake word listener stopped.")

        self._thread = threading.Thread(target=_worker, daemon=True)
        self._thread.start()

    def stop(self):
        """Stops background wake word listener."""
        self.is_listening = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

wake_word_listener = WakeWordListener()
