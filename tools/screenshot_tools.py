import os
import datetime
import logging
from pathlib import Path
from typing import Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class TakeScreenshotTool(BaseTool):
    name = "take_screenshot"
    description = "Captures a screenshot of the current screen and saves it locally in the screenshots directory."
    parameters = {
        "type": "object",
        "properties": {
            "custom_name": {
                "type": "string",
                "description": "Optional custom filename prefix for the screenshot."
            }
        }
    }

    def execute(self, custom_name: str = "screenshot") -> Dict[str, Any]:
        try:
            import pyautogui
            screenshots_dir = Path("screenshots")
            screenshots_dir.mkdir(exist_ok=True)

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{custom_name}_{timestamp}.png"
            file_path = screenshots_dir / filename

            screenshot = pyautogui.screenshot()
            screenshot.save(str(file_path))

            abs_path = str(file_path.resolve())
            logger.info(f"Screenshot saved to: {abs_path}")
            return {
                "status": "success",
                "message": f"Screenshot taken and saved successfully.",
                "file_path": abs_path,
                "filename": filename
            }
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return {"status": "error", "message": f"Could not capture screenshot: {str(e)}"}
