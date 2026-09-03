import os
import json
import uuid
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

from skills.base_skill import BaseSkill
from skills.notes_skill import ListNotesTool
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

STUDY_SESSIONS_FILE = Path("data/study_sessions.json")


def load_study_sessions() -> Dict[str, Any]:
    """Loads study sessions from JSON storage or initializes default structure."""
    if not STUDY_SESSIONS_FILE.exists():
        return {"sessions": [], "active_session_id": None}
    try:
        with open(STUDY_SESSIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {"sessions": [], "active_session_id": None}
            data.setdefault("sessions", [])
            data.setdefault("active_session_id", None)
            return data
    except Exception as e:
        logger.warning(f"Failed to read study sessions file: {e}")
        return {"sessions": [], "active_session_id": None}


def save_study_sessions(data: Dict[str, Any]) -> None:
    """Saves study sessions data to JSON storage."""
    try:
        STUDY_SESSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STUDY_SESSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save study sessions file: {e}")


class StartStudyTool(BaseTool):
    name = "start_study"
    description = "Starts a timed study session for a given subject."
    parameters = {
        "type": "object",
        "properties": {
            "subject": {
                "type": "string",
                "description": "The subject or topic being studied (e.g. 'DBMS', 'Computer Networks', 'Operating Systems')."
            }
        },
        "required": ["subject"]
    }

    def execute(self, subject: str) -> Dict[str, Any]:
        data = load_study_sessions()
        active_id = data.get("active_session_id")

        if active_id:
            active_session = next((s for s in data.get("sessions", []) if s.get("id") == active_id), None)
            active_subj = active_session.get("subject", "another topic") if active_session else "another topic"
            return {
                "status": "error",
                "message": f"You have an active session on '{active_subj}' — end it first or it'll keep running.",
                "active_session_id": active_id,
                "active_subject": active_subj
            }

        session_id = str(uuid.uuid4())
        now_iso = datetime.now().isoformat()
        clean_subject = subject.strip()

        new_session = {
            "id": session_id,
            "subject": clean_subject,
            "started_at": now_iso,
            "ended_at": None,
            "duration_minutes": None,
            "topics_covered": "",
            "status": "active"
        }

        data["sessions"].append(new_session)
        data["active_session_id"] = session_id
        save_study_sessions(data)

        return {
            "status": "success",
            "message": f"Started study session for '{clean_subject}'. Timer is running.",
            "session_id": session_id,
            "subject": clean_subject,
            "started_at": now_iso
        }


class EndStudyTool(BaseTool):
    name = "end_study"
    description = "Ends the current active study session and logs a summary."
    parameters = {
        "type": "object",
        "properties": {
            "topics_covered": {
                "type": "string",
                "description": "Freeform summary of topics studied during this session."
            }
        },
        "required": []
    }

    def execute(self, topics_covered: Optional[str] = "") -> Dict[str, Any]:
        data = load_study_sessions()
        active_id = data.get("active_session_id")

        if not active_id:
            return {
                "status": "error",
                "message": "No active study session found to end."
            }

        session = next((s for s in data.get("sessions", []) if s.get("id") == active_id), None)
        if not session:
            data["active_session_id"] = None
            save_study_sessions(data)
            return {
                "status": "error",
                "message": "Active session record not found."
            }

        now = datetime.now()
        ended_at_iso = now.isoformat()
        try:
            started_at_dt = datetime.fromisoformat(session["started_at"])
            duration_minutes = round(max(0.0, (now - started_at_dt).total_seconds() / 60.0), 1)
        except Exception:
            duration_minutes = 0.0

        session["ended_at"] = ended_at_iso
        session["duration_minutes"] = duration_minutes
        session["status"] = "completed"

        if topics_covered:
            session["topics_covered"] = topics_covered.strip()

        data["active_session_id"] = None
        save_study_sessions(data)

        subject = session.get("subject", "Study")
        topics_msg = f" Topics: {session['topics_covered']}." if session.get("topics_covered") else ""

        return {
            "status": "success",
            "message": f"Nice, {duration_minutes} minutes on {subject} logged.{topics_msg}",
            "session": session,
            "subject": subject,
            "duration_minutes": duration_minutes,
            "topics_covered": session.get("topics_covered", ""),
            "started_at": session.get("started_at"),
            "ended_at": ended_at_iso
        }


class QuizMeTool(BaseTool):
    name = "quiz_me"
    description = "Retrieves study notes and materials for a subject to generate quick recall quiz questions."
    parameters = {
        "type": "object",
        "properties": {
            "subject": {
                "type": "string",
                "description": "The subject or topic to quiz on (e.g. 'DBMS', 'Computer Networks')."
            },
            "num_questions": {
                "type": "integer",
                "description": "Number of recall questions to generate (default 3)."
            }
        },
        "required": ["subject"]
    }

    def execute(self, subject: str, num_questions: int = 3) -> Dict[str, Any]:
        clean_subject = subject.strip().lower()
        num_q = max(1, min(10, num_questions or 3))

        material_chunks: List[Dict[str, Any]] = []

        # 1. Pull from notes.json via ListNotesTool
        try:
            notes_tool = ListNotesTool()
            notes_res = notes_tool.execute()
            all_notes = notes_res.get("notes", []) if isinstance(notes_res, dict) else []

            for n in all_notes:
                tag = str(n.get("tag", "")).lower()
                title = str(n.get("title", "")).lower()
                content = str(n.get("content", "")).lower()

                if clean_subject in tag or clean_subject in title or clean_subject in content:
                    material_chunks.append({
                        "source": "notes.json",
                        "title": n.get("title", "Note"),
                        "tag": n.get("tag", ""),
                        "content": n.get("content", "")
                    })
        except Exception as e:
            logger.warning(f"Error reading notes for quiz_me: {e}")

        # 2. Check for optional exam prep files in data/ or areas/
        exam_paths = [
            Path("data/rgpv-exam-prep.md"),
            Path("areas/rgpv-exam-prep.md"),
            Path(f"data/{clean_subject}.md"),
            Path(f"data/{clean_subject}.txt")
        ]
        for ep in exam_paths:
            if ep.exists():
                try:
                    text_content = ep.read_text(encoding="utf-8")
                    if clean_subject in ep.name.lower() or clean_subject in text_content.lower():
                        material_chunks.append({
                            "source": str(ep),
                            "title": ep.stem,
                            "content": text_content[:2000]
                        })
                except Exception as e:
                    logger.warning(f"Error reading exam prep file {ep}: {e}")

        # If no material found, return not_found to avoid LLM hallucination
        if not material_chunks:
            return {
                "status": "not_found",
                "message": (
                    f"No study notes or material found for subject '{subject}'. "
                    f"Please add notes for '{subject}' first using add_note."
                ),
                "material": []
            }

        return {
            "status": "success",
            "subject": subject,
            "num_questions": num_q,
            "material": material_chunks,
            "instruction_for_llm": (
                f"Generate {num_q} short recall questions strictly from this material. "
                "Do not include answers in the questions. Test key concepts, definitions, and mechanisms."
            )
        }


class GetStudyStatsTool(BaseTool):
    name = "get_study_stats"
    description = "Shows total study time per subject over a given period."
    parameters = {
        "type": "object",
        "properties": {
            "days": {
                "type": "integer",
                "description": "Number of days in the lookback window (default 7)."
            }
        },
        "required": []
    }

    def execute(self, days: int = 7) -> Dict[str, Any]:
        window_days = max(1, days if days is not None else 7)
        data = load_study_sessions()
        cutoff = datetime.now() - timedelta(days=window_days)

        subject_durations: Dict[str, float] = {}
        subject_counts: Dict[str, int] = {}
        total_minutes = 0.0

        for session in data.get("sessions", []):
            if session.get("status") == "completed" and session.get("ended_at"):
                try:
                    ended_at_dt = datetime.fromisoformat(session["ended_at"])
                    if ended_at_dt >= cutoff:
                        subj = session.get("subject", "Uncategorized")
                        dur = float(session.get("duration_minutes") or 0.0)
                        subject_durations[subj] = subject_durations.get(subj, 0.0) + dur
                        subject_counts[subj] = subject_counts.get(subj, 0) + 1
                        total_minutes += dur
                except Exception as e:
                    logger.warning(f"Error parsing session timestamp: {e}")

        # Sort subjects by total minutes descending
        sorted_stats = sorted(
            subject_durations.items(),
            key=lambda item: item[1],
            reverse=True
        )

        breakdown = [
            {
                "subject": subj,
                "total_minutes": round(minutes, 1),
                "session_count": subject_counts.get(subj, 0)
            }
            for subj, minutes in sorted_stats
        ]

        if not breakdown:
            summary_msg = f"No completed study sessions recorded in the last {window_days} days."
        else:
            top_parts = [f"{b['subject']}: {b['total_minutes']}m ({b['session_count']} sessions)" for b in breakdown[:3]]
            summary_msg = f"Study stats (last {window_days} days): {round(total_minutes, 1)} total minutes logged across {len(breakdown)} subject(s) — {', '.join(top_parts)}."

        return {
            "status": "success",
            "days": window_days,
            "total_minutes": round(total_minutes, 1),
            "breakdown": breakdown,
            "message": summary_msg
        }


class StudySessionSkill(BaseSkill):
    name = "study_session"
    description = "Manages focused study sessions, timers, study stats, and recall quiz retrieval for RGPV exam prep."

    def get_tools(self) -> List[BaseTool]:
        return [
            StartStudyTool(),
            EndStudyTool(),
            QuizMeTool(),
            GetStudyStatsTool()
        ]
