import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from skills.base_skill import BaseSkill
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

NOTES_FILE = Path("data/notes.json")

class AddNoteTool(BaseTool):
    name = "add_note"
    description = "Saves a quick note or reminder with a title, content, and optional subject tag."
    parameters = {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "The title or subject of the note."},
            "content": {"type": "string", "description": "The body text of the note."},
            "tag": {"type": "string", "description": "Optional category or subject tag (e.g. 'DBMS', 'Computer Networks')."}
        },
        "required": ["title", "content"]
    }

    def execute(self, title: str, content: str, tag: Optional[str] = None) -> Dict[str, Any]:
        NOTES_FILE.parent.mkdir(parents=True, exist_ok=True)
        notes = []
        if NOTES_FILE.exists():
            try:
                with open(NOTES_FILE, "r", encoding="utf-8") as f:
                    notes = json.load(f)
            except Exception:
                notes = []

        # If tag is not provided, check for active study session to auto-tag
        if not tag:
            study_file = Path("data/study_sessions.json")
            if study_file.exists():
                try:
                    with open(study_file, "r", encoding="utf-8") as f:
                        s_data = json.load(f)
                        active_id = s_data.get("active_session_id")
                        if active_id:
                            for s in s_data.get("sessions", []):
                                if s.get("id") == active_id and s.get("status") == "active":
                                    tag = s.get("subject")
                                    break
                except Exception:
                    pass

        new_note = {"title": title, "content": content}
        if tag:
            new_note["tag"] = tag

        notes.append(new_note)

        with open(NOTES_FILE, "w", encoding="utf-8") as f:
            json.dump(notes, f, indent=2, ensure_ascii=False)

        tag_msg = f" with tag '{tag}'" if tag else ""
        return {"status": "success", "message": f"Saved note '{title}'{tag_msg}.", "total_notes": len(notes)}



class ListNotesTool(BaseTool):
    name = "list_notes"
    description = "Lists all saved personal notes and reminders."
    parameters = {"type": "object", "properties": {}}

    def execute(self) -> Dict[str, Any]:
        if not NOTES_FILE.exists():
            return {"status": "success", "notes": [], "message": "No notes saved yet."}

        try:
            with open(NOTES_FILE, "r", encoding="utf-8") as f:
                notes = json.load(f)
            return {"status": "success", "total": len(notes), "notes": notes}
        except Exception as e:
            return {"status": "error", "message": f"Failed to read notes: {str(e)}"}


class NotesSkill(BaseSkill):
    name = "quick_notes"
    description = "Allows SERA to save, view, and organize quick personal notes and reminders."

    def get_tools(self) -> List[BaseTool]:
        return [AddNoteTool(), ListNotesTool()]
