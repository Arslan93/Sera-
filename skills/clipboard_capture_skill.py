import os
import re
import json
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from skills.base_skill import BaseSkill
from skills.notes_skill import AddNoteTool
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

CAPTURES_FILE = Path("data/captures.json")
READ_LATER_FILE = Path("data/read_later.json")

VALID_CLASSIFICATIONS = ["code", "task", "link", "note"]


def load_json_file(file_path: Path, default_key: str) -> Dict[str, Any]:
    """Safely loads a JSON storage file or returns empty structure."""
    if not file_path.exists():
        return {default_key: []}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {default_key: []}
            data.setdefault(default_key, [])
            return data
    except Exception as e:
        logger.warning(f"Error reading {file_path}: {e}")
        return {default_key: []}


def save_json_file(file_path: Path, data: Dict[str, Any]) -> None:
    """Saves data using atomic file replacement (temp file + os.replace)."""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        temp_file = file_path.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(temp_file, file_path)
    except Exception as e:
        logger.error(f"Failed to atomically save {file_path}: {e}")


def classify_content(content: str) -> str:
    """
    Lightweight heuristic pass to classify clipboard content as:
    - 'link': URLs and web addresses
    - 'code': programming constructs, functions, brackets, imports
    - 'task': actionable todo items and reminders
    - 'note': general prose, concepts, or thoughts
    """
    text = content.strip()
    if not text:
        return "note"

    # 1. URL / Link check
    url_pattern = re.compile(
        r'^(https?://|www\.)[^\s/$.?#].[^\s]*$',
        re.IGNORECASE
    )
    if url_pattern.match(text) or (text.startswith("http://") or text.startswith("https://")):
        return "link"

    # 2. Task check
    task_keywords = ["todo:", "fixme:", "[ ]", "task:", "action item:", "remember to", "need to", "must do"]
    lower_text = text.lower()
    for kw in task_keywords:
        if lower_text.startswith(kw) or f"\n{kw}" in lower_text:
            return "task"

    # 3. Code check
    code_indicators = [
        "def ", "class ", "import ", "from ", "return ", "function", "const ",
        "let ", "var ", "=>", "public class ", "SELECT ", "CREATE TABLE",
        "#!/bin/", "console.log", "print(", "<?php", "namespace ", "struct ",
        "impl ", "fn ", "async def "
    ]
    code_score = sum(1 for indicator in code_indicators if indicator in text)

    # Syntax structure check (braces, brackets, semicolons, indents)
    has_brackets = "{" in text and "}" in text
    has_semicolons = text.count(";") >= 2
    has_html_tags = bool(re.search(r'</?[a-zA-Z][a-zA-Z0-9]*[^<>]*>', text))

    if code_score >= 2 or (code_score >= 1 and (has_brackets or has_semicolons or has_html_tags)):
        return "code"
    if has_html_tags and ("<div" in text.lower() or "<script" in text.lower() or "<html" in text.lower()):
        return "code"

    # Default to general note
    return "note"


def file_captured_content(raw_content: str, classification: Optional[str] = None) -> Dict[str, Any]:
    """
    Classifies and files captured clipboard content into notes.json,
    read_later.json, or review queue, and records in captures.json.
    """
    clean_content = raw_content.strip()
    if not clean_content:
        return {
            "status": "error",
            "message": "Clipboard content is empty."
        }

    category = classification.strip().lower() if classification else classify_content(clean_content)
    if category not in VALID_CLASSIFICATIONS:
        category = classify_content(clean_content)

    filed_destination = "pending_review"
    now_iso = datetime.now().isoformat()
    capture_id = str(uuid.uuid4())

    try:
        if category == "link":
            tool = AddLinkToReadLaterTool()
            tool.execute(url=clean_content)
            filed_destination = "data/read_later.json"

        elif category == "task":
            notes_tool = AddNoteTool()
            first_line = clean_content.split("\n")[0][:40]
            title = f"Task: {first_line}" if not first_line.lower().startswith("task:") else first_line
            notes_tool.execute(title=title, content=clean_content, tag="task")
            filed_destination = "data/notes.json (task)"

        elif category == "code":
            notes_tool = AddNoteTool()
            first_line = clean_content.split("\n")[0][:40]
            title = f"Code Snippet: {first_line}"
            notes_tool.execute(title=title, content=clean_content, tag="code")
            filed_destination = "data/notes.json (code)"

        else:  # note
            notes_tool = AddNoteTool()
            first_line = clean_content.split("\n")[0][:40]
            title = first_line if first_line else "Quick Note"
            notes_tool.execute(title=title, content=clean_content, tag="clipboard")
            filed_destination = "data/notes.json (note)"

    except Exception as e:
        logger.error(f"Error filing captured content: {e}")
        filed_destination = "pending_review"

    # Record in captures.json for audit and undo
    captures_data = load_json_file(CAPTURES_FILE, "captures")
    capture_record = {
        "id": capture_id,
        "raw_content": clean_content,
        "classification": category,
        "filed_to": filed_destination,
        "captured_at": now_iso
    }
    captures_data["captures"].append(capture_record)
    save_json_file(CAPTURES_FILE, captures_data)

    return {
        "status": "success",
        "capture_id": capture_id,
        "classification": category,
        "filed_to": filed_destination,
        "message": f"Captured {category} → filed to {filed_destination}."
    }


class ProcessClipboardCaptureTool(BaseTool):
    name = "process_clipboard_capture"
    description = "Classifies and files a captured clipboard snippet into notes, read-later links, or review."
    parameters = {
        "type": "object",
        "properties": {
            "raw_content": {
                "type": "string",
                "description": "The raw clipboard content to classify and file."
            },
            "classification": {
                "type": "string",
                "description": "Optional explicit classification: 'code', 'task', 'link', or 'note'."
            }
        },
        "required": ["raw_content"]
    }

    def execute(self, raw_content: str, classification: Optional[str] = None) -> Dict[str, Any]:
        return file_captured_content(raw_content, classification)


class AddLinkToReadLaterTool(BaseTool):
    name = "add_link_to_read_later"
    description = "Saves a URL to a read-later list."
    parameters = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL to save for reading later."
            },
            "title": {
                "type": "string",
                "description": "Optional title or description for the link."
            }
        },
        "required": ["url"]
    }

    def execute(self, url: str, title: Optional[str] = "") -> Dict[str, Any]:
        clean_url = url.strip()
        if not clean_url:
            return {"status": "error", "message": "URL cannot be empty."}

        read_later_data = load_json_file(READ_LATER_FILE, "links")
        now_iso = datetime.now().isoformat()
        link_id = str(uuid.uuid4())

        record = {
            "id": link_id,
            "url": clean_url,
            "title": (title or clean_url).strip(),
            "added_at": now_iso
        }

        read_later_data["links"].append(record)
        save_json_file(READ_LATER_FILE, read_later_data)

        return {
            "status": "success",
            "message": f"Saved link to Read-Later list: {record['title']}",
            "link": record
        }


class ClipboardCaptureSkill(BaseSkill):
    name = "clipboard_capture"
    description = "Automatically captures, classifies, and files clipboard snippets into notes, links, or code."

    def get_tools(self) -> List[BaseTool]:
        return [
            ProcessClipboardCaptureTool(),
            AddLinkToReadLaterTool()
        ]
