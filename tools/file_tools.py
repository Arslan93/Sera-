import os
import time
import shutil
import logging
import string
from pathlib import Path
from typing import Dict, Any, List
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

USER_HOME = Path.home()
STANDARD_FOLDERS = {
    "downloads": USER_HOME / "Downloads",
    "download": USER_HOME / "Downloads",
    "documents": USER_HOME / "Documents",
    "document": USER_HOME / "Documents",
    "desktop": USER_HOME / "Desktop",
    "pictures": USER_HOME / "Pictures",
    "photos": USER_HOME / "Pictures",
    "music": USER_HOME / "Music",
    "videos": USER_HOME / "Videos",
    "home": USER_HOME,
}

def resolve_folder_path(folder_input: str) -> Path:
    key = folder_input.strip().lower()
    if key in STANDARD_FOLDERS:
        return STANDARD_FOLDERS[key]
    path = Path(folder_input).expanduser().resolve()
    return path

def resolve_file_path(file_input: str) -> Path:
    """Resolves file paths, handling shortcuts like 'desktop/demo.html' or 'downloads/file.txt'."""
    clean = file_input.strip().replace("\\", "/")
    parts = clean.split("/")
    first = parts[0].lower()
    if first in STANDARD_FOLDERS:
        remaining = "/".join(parts[1:]) if len(parts) > 1 else ""
        return (STANDARD_FOLDERS[first] / remaining).resolve()
    return Path(file_input).expanduser().resolve()

class OpenFolderTool(BaseTool):
    name = "open_folder"
    description = "Opens a folder in File Explorer (e.g. 'downloads', 'documents', 'desktop', or a specific folder path)."
    parameters = {
        "type": "object",
        "properties": {
            "folder_path": {
                "type": "string",
                "description": "Folder name (e.g. 'downloads', 'documents', 'desktop') or custom directory path."
            }
        },
        "required": ["folder_path"]
    }

    def execute(self, folder_path: str) -> Dict[str, Any]:
        target = resolve_folder_path(folder_path)
        if not target.exists() or not target.is_dir():
            return {"status": "error", "message": f"Folder '{folder_path}' does not exist."}

        try:
            if os.name == 'nt':
                os.startfile(str(target))
            else:
                import subprocess
                subprocess.Popen(["xdg-open", str(target)])
            logger.info(f"Opened folder: {target}")
            return {"status": "success", "message": f"Opened folder: {target}"}
        except Exception as e:
            logger.error(f"Failed to open folder {target}: {e}")
            return {"status": "error", "message": f"Could not open folder: {str(e)}"}


class OpenFileTool(BaseTool):
    name = "open_file"
    description = "Opens a file with its default system associated application."
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to open."
            }
        },
        "required": ["file_path"]
    }

    def execute(self, file_path: str) -> Dict[str, Any]:
        target = Path(file_path).expanduser().resolve()
        if not target.exists() or not target.is_file():
            return {"status": "error", "message": f"File '{file_path}' does not exist."}

        try:
            if os.name == 'nt':
                os.startfile(str(target))
            else:
                import subprocess
                subprocess.Popen(["xdg-open", str(target)])
            logger.info(f"Opened file: {target}")
            return {"status": "success", "message": f"Opened file: {target.name}"}
        except Exception as e:
            logger.error(f"Failed to open file {target}: {e}")
            return {"status": "error", "message": f"Could not open file: {str(e)}"}


class ListFilesTool(BaseTool):
    name = "list_files"
    description = "Lists files and subdirectories in a directory (e.g. 'downloads', 'documents', 'desktop', or custom path)."
    parameters = {
        "type": "object",
        "properties": {
            "folder_path": {
                "type": "string",
                "description": "Directory name or path (e.g. 'downloads', 'desktop', 'documents', or a path). Defaults to current directory."
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of items to return (default: 25)."
            }
        }
    }

    def execute(self, folder_path: str = "downloads", limit: int = 25) -> Dict[str, Any]:
        target = resolve_folder_path(folder_path) if folder_path else Path.cwd()
        if not target.exists() or not target.is_dir():
            return {"status": "error", "message": f"Directory '{folder_path}' does not exist."}

        try:
            items = []
            for entry in list(target.iterdir())[:limit]:
                is_file = entry.is_file()
                size_str = f"{entry.stat().st_size / 1024:.1f} KB" if is_file else "<DIR>"
                items.append({
                    "name": entry.name,
                    "type": "file" if is_file else "directory",
                    "size": size_str
                })

            total_count = len(list(target.iterdir()))
            return {
                "status": "success",
                "folder": str(target),
                "total_items": total_count,
                "showing": len(items),
                "items": items
            }
        except Exception as e:
            logger.error(f"Failed to list directory {target}: {e}")
            return {"status": "error", "message": f"Could not list directory: {str(e)}"}


class SearchFileTool(BaseTool):
    name = "search_file"
    description = "Searches the computer across user directories and drives for files or game/app folders by name (e.g. 'naruto', 'steam', 'report.pdf')."
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The name or keyword of the file or folder to find (e.g. 'naruto', 'game', 'notes.txt')."
            },
            "search_root": {
                "type": "string",
                "description": "Optional directory to start searching in (e.g. 'desktop', 'downloads', 'C:\\', 'D:\\'). Defaults to checking common user folders and drives."
            },
            "auto_open": {
                "type": "boolean",
                "description": "If true, automatically opens the first found folder or file in File Explorer."
            }
        },
        "required": ["query"]
    }

    def execute(self, query: str, search_root: str = None, auto_open: bool = False) -> Dict[str, Any]:
        query_clean = query.strip().lower()
        results = []

        # Determine roots to search
        search_paths = []
        if search_root:
            search_paths = [resolve_folder_path(search_root)]
        else:
            # Common user paths first (fastest)
            search_paths = [
                USER_HOME / "Desktop",
                USER_HOME / "Downloads",
                USER_HOME / "Documents",
                Path("C:/Program Files"),
                Path("C:/Program Files (x86)"),
                Path("C:/Games"),
                Path("D:/Games"),
                Path("D:/"),
                Path("E:/"),
            ]

        # Scan directories with depth limit and strict time cutoff to keep response fast
        start_time = time.time()
        timeout_seconds = 8.0

        for root_path in search_paths:
            if time.time() - start_time > timeout_seconds:
                logger.info(f"Search timed out after {timeout_seconds}s; returning gathered matches.")
                break

            if not root_path.exists():
                continue
            
            try:
                for dirpath, dirnames, filenames in os.walk(str(root_path)):
                    if time.time() - start_time > timeout_seconds:
                        dirnames.clear()
                        break

                    # Check depth to prevent infinite slow crawl
                    rel_depth = len(Path(dirpath).relative_to(root_path).parts) if root_path != Path(dirpath) else 0
                    if rel_depth > 3:
                        dirnames.clear()
                        continue

                    # Check directories
                    for d in list(dirnames):
                        if query_clean in d.lower():
                            full_dir = os.path.join(dirpath, d)
                            results.append({"type": "directory", "name": d, "path": full_dir})
                            if len(results) >= 10:
                                break

                    # Check files
                    for f in filenames:
                        if query_clean in f.lower():
                            full_file = os.path.join(dirpath, f)
                            results.append({"type": "file", "name": f, "path": full_file})
                            if len(results) >= 10:
                                break

                    if len(results) >= 10:
                        break
            except Exception:
                continue

            if len(results) >= 10:
                break

        opened_path = None
        if auto_open and results:
            first_match = results[0]["path"]
            try:
                if os.path.isdir(first_match):
                    os.startfile(first_match)
                else:
                    os.startfile(os.path.dirname(first_match))
                opened_path = first_match
            except Exception as e:
                logger.error(f"Auto-open failed for {first_match}: {e}")

        if results:
            return {
                "status": "success",
                "message": f"Found {len(results)} match(es) for '{query}'.",
                "matches": results,
                "opened": opened_path
            }
        else:
            return {
                "status": "not_found",
                "message": f"No files or folders found matching '{query}' in common locations."
            }


class WriteFileTool(BaseTool):
    name = "write_file"
    description = "Creates or overwrites a file on disk with the specified content/code (e.g. 'desktop/demo.html', 'downloads/script.py', 'test.txt')."
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path or destination of the file to create (e.g. 'desktop/demo.html', 'downloads/index.html', 'C:/Users/HP/Desktop/demo.html')."
            },
            "content": {
                "type": "string",
                "description": "The exact content or code to write into the file."
            }
        },
        "required": ["file_path", "content"]
    }

    def execute(self, file_path: str, content: str) -> Dict[str, Any]:
        target = resolve_file_path(file_path)
        try:
            # Ensure parent directories exist
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"Successfully wrote file: {target} ({len(content)} chars)")
            return {
                "status": "success",
                "message": f"Successfully created file at {target}",
                "file_path": str(target),
                "size_bytes": len(content.encode('utf-8'))
            }
        except Exception as e:
            logger.error(f"Failed to write file {target}: {e}", exc_info=True)
            return {"status": "error", "message": f"Could not create file '{file_path}': {str(e)}"}


class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Reads the text content of a file on disk (e.g. 'desktop/demo.html', 'main.py')."
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to read."
            },
            "max_chars": {
                "type": "integer",
                "description": "Maximum number of characters to read (default: 10000)."
            }
        },
        "required": ["file_path"]
    }

    def execute(self, file_path: str, max_chars: int = 10000) -> Dict[str, Any]:
        target = resolve_file_path(file_path)
        if not target.exists() or not target.is_file():
            return {"status": "error", "message": f"File '{file_path}' does not exist."}

        try:
            with open(target, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(max_chars)

            return {
                "status": "success",
                "file_path": str(target),
                "content": content
            }
        except Exception as e:
            logger.error(f"Failed to read file {target}: {e}", exc_info=True)
            return {"status": "error", "message": f"Could not read file '{file_path}': {str(e)}"}


class DeleteFileTool(BaseTool):
    name = "delete_file"
    description = "Deletes a specific file on disk safely (e.g. 'desktop/temp.txt'). System directories cannot be deleted."
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to delete."
            }
        },
        "required": ["file_path"]
    }

    def execute(self, file_path: str) -> Dict[str, Any]:
        target = resolve_file_path(file_path)
        
        # Safety checks: ensure it is a file and not root or system directory
        if not target.exists():
            return {"status": "error", "message": f"File '{file_path}' does not exist."}
        if target.is_dir():
            return {"status": "error", "message": f"Path '{file_path}' is a directory. delete_file only deletes individual files."}
        if target in [USER_HOME, Path("C:/"), Path("C:/Windows"), Path("C:/Program Files")]:
            return {"status": "error", "message": "Deleting system root paths is blocked for safety."}

        try:
            target.unlink()
            logger.info(f"Deleted file: {target}")
            return {"status": "success", "message": f"Successfully deleted file: {target}"}
        except Exception as e:
            logger.error(f"Failed to delete file {target}: {e}", exc_info=True)
            return {"status": "error", "message": f"Could not delete file '{file_path}': {str(e)}"}


class MoveFileTool(BaseTool):
    name = "move_file"
    description = "Moves or renames a file from source_path to destination_path on disk."
    parameters = {
        "type": "object",
        "properties": {
            "source_path": {
                "type": "string",
                "description": "Current file path."
            },
            "destination_path": {
                "type": "string",
                "description": "New file path or destination folder."
            }
        },
        "required": ["source_path", "destination_path"]
    }

    def execute(self, source_path: str, destination_path: str) -> Dict[str, Any]:
        src = resolve_file_path(source_path)
        if not src.exists():
            return {"status": "error", "message": f"Source file '{source_path}' does not exist."}

        dst = resolve_file_path(destination_path)
        if dst.is_dir():
            dst = dst / src.name

        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            logger.info(f"Moved file from {src} to {dst}")
            return {
                "status": "success",
                "message": f"Successfully moved '{src.name}' to '{dst}'",
                "source": str(src),
                "destination": str(dst)
            }
        except Exception as e:
            logger.error(f"Failed to move file from {src} to {dst}: {e}", exc_info=True)
            return {"status": "error", "message": f"Could not move file: {str(e)}"}


