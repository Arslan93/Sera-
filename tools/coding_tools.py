import os
import sys
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from tools.base_tool import BaseTool
from tools.file_tools import resolve_file_path

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECONDS = 15

class ExecuteCodeTool(BaseTool):
    name = "execute_code"
    description = "Executes a snippet of code or a script file in Python, Node.js, or PowerShell in a sandboxed subprocess and returns stdout, stderr, and exit code."
    parameters = {
        "type": "object",
        "properties": {
            "language": {
                "type": "string",
                "enum": ["python", "javascript", "nodejs", "powershell", "cmd", "shell"],
                "description": "The programming language or shell to execute (default: 'python')."
            },
            "code": {
                "type": "string",
                "description": "The code string to execute directly (if not running an existing file)."
            },
            "file_path": {
                "type": "string",
                "description": "Optional path to an existing script file to execute."
            },
            "timeout": {
                "type": "integer",
                "description": "Execution timeout in seconds (default: 15)."
            }
        }
    }

    def execute(self, language: str = "python", code: Optional[str] = None, file_path: Optional[str] = None, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> Dict[str, Any]:
        lang = language.lower().strip()
        temp_file = None

        try:
            # 1. Determine execution target
            if file_path:
                target_path = resolve_file_path(file_path)
                if not target_path.exists():
                    return {"status": "error", "message": f"File '{file_path}' does not exist."}
                run_file = str(target_path)
            elif code:
                # Write to temp file for execution
                ext = ".py" if lang == "python" else ".js" if lang in ["javascript", "nodejs"] else ".ps1" if lang == "powershell" else ".bat"
                with tempfile.NamedTemporaryFile(suffix=ext, delete=False, mode="w", encoding="utf-8") as tf:
                    temp_file = tf.name
                    tf.write(code)
                run_file = temp_file
            else:
                return {"status": "error", "message": "Either 'code' or 'file_path' must be provided."}

            # 2. Build execution command
            if lang == "python":
                cmd = [sys.executable, run_file]
            elif lang in ["javascript", "nodejs"]:
                cmd = ["node", run_file]
            elif lang == "powershell":
                cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", run_file]
            else:
                cmd = ["cmd", "/c", run_file]

            logger.info(f"Executing sandboxed process: {' '.join(cmd)} (timeout: {timeout}s)")

            # 3. Run subprocess
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(Path(run_file).parent)
            )

            stdout = proc.stdout.strip()
            stderr = proc.stderr.strip()
            exit_code = proc.returncode

            logger.info(f"Execution finished with exit code {exit_code}")
            return {
                "status": "success" if exit_code == 0 else "error",
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr,
                "output": stdout if exit_code == 0 else f"Error (Exit Code {exit_code}):\n{stderr or stdout}"
            }

        except subprocess.TimeoutExpired:
            logger.warning(f"Process timed out after {timeout} seconds")
            return {
                "status": "error",
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Execution timed out after {timeout} seconds.",
                "output": f"TimeoutError: Process exceeded {timeout}s execution limit."
            }
        except Exception as e:
            logger.error(f"Error during code execution: {e}", exc_info=True)
            return {
                "status": "error",
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "output": f"Execution failed: {str(e)}"
            }
        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass


class EditFileTool(BaseTool):
    name = "edit_file"
    description = "Modifies an existing file by replacing a specific target text block with replacement content."
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to edit."
            },
            "target_text": {
                "type": "string",
                "description": "The exact substring/block of code to be replaced."
            },
            "replacement_text": {
                "type": "string",
                "description": "The new replacement content."
            }
        },
        "required": ["file_path", "target_text", "replacement_text"]
    }

    def execute(self, file_path: str, target_text: str, replacement_text: str) -> Dict[str, Any]:
        target = resolve_file_path(file_path)
        if not target.exists() or not target.is_file():
            return {"status": "error", "message": f"File '{file_path}' does not exist."}

        try:
            with open(target, "r", encoding="utf-8") as f:
                content = f.read()

            if target_text not in content:
                return {
                    "status": "error",
                    "message": f"Target text block not found in '{file_path}'. Make sure the target text matches exactly."
                }

            updated_content = content.replace(target_text, replacement_text, 1)
            with open(target, "w", encoding="utf-8") as f:
                f.write(updated_content)

            logger.info(f"Successfully edited file: {target}")
            return {
                "status": "success",
                "message": f"Successfully updated '{file_path}'.",
                "file_path": str(target)
            }
        except Exception as e:
            logger.error(f"Failed to edit file {target}: {e}", exc_info=True)
            return {"status": "error", "message": f"Could not edit file '{file_path}': {str(e)}"}
