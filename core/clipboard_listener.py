import time
import logging
import threading
from typing import Callable, Optional

import pyperclip

logger = logging.getLogger(__name__)

DEFAULT_HOTKEY = "ctrl+shift+s"
DEFAULT_DEBOUNCE_SECONDS = 2.0


class ClipboardCaptureListener:
    """
    Background global hotkey listener for SERA.
    Listens for a global hotkey (e.g. Ctrl+Shift+S) to capture, classify,
    and auto-file clipboard contents into SERA notes, links, or code storage.
    """
    def __init__(
        self,
        on_capture: Optional[Callable[[str], None]] = None,
        hotkey: str = DEFAULT_HOTKEY,
        debounce_seconds: float = DEFAULT_DEBOUNCE_SECONDS
    ):
        self.on_capture = on_capture
        self.hotkey = hotkey
        self.debounce_seconds = debounce_seconds
        self.is_listening = False
        self.last_trigger_time = 0.0
        self._lock = threading.Lock()

    def start(self, on_capture: Optional[Callable[[str], None]] = None) -> bool:
        """Starts background hotkey listening."""
        if self.is_listening:
            logger.info("ClipboardCaptureListener is already listening.")
            return True

        if on_capture:
            self.on_capture = on_capture

        try:
            import keyboard

            def _on_hotkey():
                self._handle_trigger()

            keyboard.add_hotkey(self.hotkey, _on_hotkey)
            self.is_listening = True
            logger.info(f"ClipboardCaptureListener started with hotkey '{self.hotkey}'.")
            return True
        except Exception as e:
            logger.error(f"Failed to register global hotkey '{self.hotkey}': {e}")
            self.is_listening = False
            return False

    def stop(self) -> None:
        """Unregisters the hotkey and stops listening."""
        if not self.is_listening:
            return

        try:
            import keyboard
            try:
                keyboard.remove_hotkey(self.hotkey)
            except Exception:
                pass
        except Exception as e:
            logger.warning(f"Error unregistering hotkey: {e}")
        finally:
            self.is_listening = False
            logger.info("ClipboardCaptureListener stopped.")

    def _handle_trigger(self) -> None:
        """Internal trigger handler with debounce check and clipboard extraction."""
        with self._lock:
            now = time.time()
            if (now - self.last_trigger_time) < self.debounce_seconds:
                logger.debug("Clipboard trigger debounced (within cooldown window).")
                return
            self.last_trigger_time = now

        try:
            clipboard_text = pyperclip.paste()
            if not clipboard_text or not clipboard_text.strip():
                logger.debug("Clipboard is empty or whitespace only. Skipping capture.")
                return

            clean_text = clipboard_text.strip()
            logger.info(f"Captured {len(clean_text)} characters from clipboard via hotkey.")

            if self.on_capture:
                # Run callback in a daemon thread so keyboard hook thread is not blocked
                callback_thread = threading.Thread(
                    target=self.on_capture,
                    args=(clean_text,),
                    daemon=True
                )
                callback_thread.start()
            else:
                # Default fallback action: directly file into captures & notes
                from skills.clipboard_capture_skill import file_captured_content
                file_captured_content(clean_text)

        except Exception as e:
            logger.error(f"Error handling clipboard capture trigger: {e}", exc_info=True)


clipboard_listener = ClipboardCaptureListener()
