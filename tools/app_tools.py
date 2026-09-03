import subprocess
import os
import shutil
import logging
import psutil
import glob
from pathlib import Path
from typing import Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# Known application names, executables, or URL schemes
KNOWN_APPS = {
    "notepad": ["notepad.exe"],
    "calculator": ["calc.exe"],
    "calc": ["calc.exe"],
    "paint": ["mspaint.exe"],
    "mspaint": ["mspaint.exe"],
    "cmd": ["cmd.exe"],
    "command prompt": ["cmd.exe"],
    "powershell": ["powershell.exe"],
    "terminal": ["wt.exe", "powershell.exe"],
    "explorer": ["explorer.exe"],
    "file explorer": ["explorer.exe"],
    "file manager": ["explorer.exe"],
    "task manager": ["taskmgr.exe"],
    "taskmgr": ["taskmgr.exe"],
    "chrome": ["chrome.exe", r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"],
    "google chrome": ["chrome.exe", r"C:\Program Files\Google\Chrome\Application\chrome.exe"],
    "edge": ["msedge.exe", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"],
    "microsoft edge": ["msedge.exe", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"],
    "code": ["code.cmd", "code.exe", os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe")],
    "vscode": ["code.cmd", "code.exe", os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe")],
    "vs code": ["code.cmd", "code.exe", os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe")],
    "steam": ["steam://open/main", r"C:\Program Files (x86)\Steam\steam.exe", r"C:\Program Files\Steam\steam.exe"],
    "spotify": ["spotify:", os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe")],
    "discord": ["discord:", os.path.expandvars(r"%LOCALAPPDATA%\Discord\Update.exe --processStart Discord.exe")],
    "vlc": [r"C:\Program Files\VideoLAN\VLC\vlc.exe", r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"],
    "brave": [r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"],
    "telegram": [os.path.expandvars(r"%APPDATA%\Telegram Desktop\Telegram.exe")],
    "epic": [r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win64\EpicGamesLauncher.exe"],
    "epic games": [r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win64\EpicGamesLauncher.exe"],
}

def find_application_target(app_name: str) -> Optional[str]:
    """
    Finds the executable path or launch protocol for an application on Windows.
    """
    key = app_name.strip().lower()

    # 1. Check Known Apps mappings
    if key in KNOWN_APPS:
        for candidate in KNOWN_APPS[key]:
            if candidate.endswith(":") or candidate.startswith("steam://") or candidate.startswith("discord://") or candidate.startswith("spotify:"):
                return candidate
            if os.path.exists(candidate) or shutil.which(candidate):
                return candidate

    # 2. Check system PATH
    which_path = shutil.which(app_name) or shutil.which(f"{app_name}.exe")
    if which_path:
        return which_path

    # 3. Check Windows Registry (App Paths)
    if os.name == 'nt':
        try:
            import winreg
            for root_key in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                for sub in (f"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\{app_name}.exe",
                            f"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\{app_name}"):
                    try:
                        with winreg.OpenKey(root_key, sub) as reg_k:
                            val, _ = winreg.QueryValueEx(reg_k, "")
                            if val and os.path.exists(val):
                                return val
                    except Exception:
                        pass
        except Exception:
            pass

    # 4. Check Common Directories
    search_dirs = [
        Path(r"C:\Program Files (x86)"),
        Path(r"C:\Program Files"),
        Path(os.path.expandvars(r"%LOCALAPPDATA%\Programs")),
        Path(os.path.expandvars(r"%APPDATA%")),
    ]

    for s_dir in search_dirs:
        if not s_dir.exists():
            continue
        try:
            # Check direct subfolder
            for sub in s_dir.iterdir():
                if key in sub.name.lower():
                    if sub.is_file() and sub.suffix.lower() == ".exe":
                        return str(sub)
                    if sub.is_dir():
                        for exe_candidate in sub.glob("*.exe"):
                            if key in exe_candidate.name.lower():
                                return str(exe_candidate)
        except Exception:
            continue

    # 5. Check Start Menu Shortcuts (.lnk)
    start_menu_dirs = [
        Path(os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs")),
        Path(r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs"),
    ]
    for sm in start_menu_dirs:
        if sm.exists():
            for lnk in sm.rglob("*.lnk"):
                if key in lnk.stem.lower():
                    return str(lnk)

    return None

class OpenAppTool(BaseTool):
    name = "open_app"
    description = "Opens a desktop application by name (e.g. steam, notepad, calculator, chrome, vs code, discord, spotify, file explorer, cmd, powershell)."
    parameters = {
        "type": "object",
        "properties": {
            "app_name": {
                "type": "string",
                "description": "The name of the application to open (e.g. 'steam', 'notepad', 'calculator', 'chrome', 'vscode', 'discord', 'spotify')."
            }
        },
        "required": ["app_name"]
    }

    def execute(self, app_name: str) -> Dict[str, Any]:
        target = find_application_target(app_name)
        if not target:
            logger.warning(f"Could not find executable for app: {app_name}")
            return {
                "status": "error",
                "message": f"Could not find application '{app_name}' on your system. Please make sure it is installed."
            }

        try:
            if os.name == 'nt':
                # os.startfile handles URLs, protocols, executables, and .lnk files without launching cmd stderr
                os.startfile(target)
            else:
                subprocess.Popen([target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            logger.info(f"Successfully launched application: {app_name} via target '{target}'")
            return {"status": "success", "message": f"Successfully launched {app_name}."}
        except Exception as e:
            logger.error(f"Failed to launch {target}: {e}", exc_info=True)
            return {"status": "error", "message": f"Failed to open '{app_name}': {str(e)}"}


PROTECTED_PROCESSES = {
    "system", "registry", "smss.exe", "csrss.exe", "wininit.exe", "services.exe",
    "lsass.exe", "svchost.exe", "explorer.exe", "taskmgr.exe", "python.exe",
    "powershell.exe", "cmd.exe", "dwm.exe", "fontdrvhost.exe", "spoolsv.exe"
}

class CloseAppTool(BaseTool):
    name = "close_app"
    description = "Closes a running user application or process by name (e.g. steam, notepad, chrome, calc, discord). System-critical processes are protected."
    parameters = {
        "type": "object",
        "properties": {
            "app_name": {
                "type": "string",
                "description": "The name of the application process to close (e.g. 'steam', 'notepad', 'chrome', 'calc', 'discord')."
            }
        },
        "required": ["app_name"]
    }

    def execute(self, app_name: str) -> Dict[str, Any]:
        target = app_name.strip().lower()
        
        # Check against protected system processes
        for protected in PROTECTED_PROCESSES:
            if target == protected or target == protected.replace(".exe", ""):
                msg = f"Operation blocked: Closing system-critical process '{app_name}' is not permitted for system stability and safety."
                logger.warning(msg)
                return {"status": "error", "message": msg}

        closed_count = 0

        # Look for running processes matching the name
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                pname = proc.info['name'].lower()
                # Skip protected processes even if substring matches
                if any(prot in pname for prot in PROTECTED_PROCESSES):
                    continue

                if target in pname or pname.startswith(target):
                    proc.terminate()
                    closed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        if closed_count > 0:
            logger.info(f"Closed {closed_count} process(es) matching: {app_name}")
            return {"status": "success", "message": f"Successfully closed {closed_count} instance(s) of '{app_name}'."}
        else:
            return {"status": "not_found", "message": f"No running application found matching '{app_name}'."}
