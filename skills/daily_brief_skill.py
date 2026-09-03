import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from skills.base_skill import BaseSkill
from skills.notes_skill import ListNotesTool
from tools.base_tool import BaseTool
from tools.system_tools import GetSystemInfoTool
from voice.tts import clean_text_for_speech

logger = logging.getLogger(__name__)

STATE_FILE = Path("data/state.json")
PROFILE_FILE = Path("data/user_profile.json")


def load_state() -> Dict[str, Any]:
    """Loads the application state file."""
    if not STATE_FILE.exists():
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to read state file {STATE_FILE}: {e}")
        return {}


def save_state(state: Dict[str, Any]) -> None:
    """Saves the application state file."""
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save state file {STATE_FILE}: {e}")


def should_trigger_daily_brief() -> bool:
    """Checks if the daily brief has already been delivered today."""
    state = load_state()
    today_str = datetime.now().strftime("%Y-%m-%d")
    return state.get("last_brief_date") != today_str


def mark_daily_brief_delivered() -> None:
    """Marks today's date as having delivered the daily brief."""
    state = load_state()
    state["last_brief_date"] = datetime.now().strftime("%Y-%m-%d")
    state["last_brief_timestamp"] = datetime.now().isoformat()
    save_state(state)


def get_user_preferred_name() -> str:
    """Retrieves the user's preferred name from profile if available."""
    if PROFILE_FILE.exists():
        try:
            with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("preferred_name") or data.get("name") or "Arslan"
        except Exception:
            pass
    return "Arslan"


class GetDailyBriefTool(BaseTool):
    name = "get_daily_brief"
    description = (
        "Generates a short daily orientation summary: pending tasks, "
        "recent coding context, and system status."
    )
    parameters = {
        "type": "object",
        "properties": {
            "verbose": {
                "type": "boolean",
                "description": "If true, includes full hardware system stats (CPU, RAM, battery) in the brief."
            }
        },
        "required": []
    }

    def execute(self, verbose: bool = False) -> Dict[str, Any]:
        """
        Gathers data from notes, clients/deliverables (if available),
        recent sessions, and hardware metrics to produce a short natural language brief.
        """
        now = datetime.now()
        hour = now.hour
        if hour < 12:
            greeting_period = "Good morning"
        elif hour < 17:
            greeting_period = "Good afternoon"
        else:
            greeting_period = "Good evening"

        user_name = get_user_preferred_name()
        greeting = f"{greeting_period}, {user_name}."
        date_str = now.strftime("%A, %B %d, %Y")

        # 1. Notes data
        notes_data = self._fetch_notes(now)

        # 2. Client deliverables & payments (if ClientTrackerSkill is present)
        deliverables_data, payments_data = self._fetch_client_data()

        # 3. Job application followups (if JobTrackerSkill is present)
        job_followups = self._fetch_job_followups()

        # 4. Recent coding/conversation sessions recap
        recent_sessions = self._fetch_recent_sessions_recap()

        # 5. System info
        system_info, system_summary = self._fetch_system_snapshot(verbose=verbose)

        # 6. Build natural-language TTS-friendly paragraph
        brief_text = self._compose_brief_text(
            greeting=greeting,
            notes_data=notes_data,
            deliverables_data=deliverables_data,
            payments_data=payments_data,
            job_followups=job_followups,
            recent_sessions=recent_sessions,
            system_summary=system_summary
        )

        return {
            "status": "success",
            "brief_text": brief_text,
            "raw_data": {
                "greeting": greeting,
                "date": date_str,
                "notes": notes_data,
                "client_deliverables": deliverables_data,
                "client_payments": payments_data,
                "job_followups": job_followups,
                "recent_sessions": recent_sessions,
                "system_info": system_info
            }
        }

    def _fetch_notes(self, now: datetime) -> List[Dict[str, Any]]:
        """Queries notes and filters for today or takes recent notes."""
        try:
            list_tool = ListNotesTool()
            res = list_tool.execute()
            all_notes = res.get("notes", []) if isinstance(res, dict) else []
            if not all_notes:
                return []

            today_iso = now.strftime("%Y-%m-%d")
            today_short = now.strftime("%b %d").lower()

            # Check if any notes match today's date or 'today' in title/content/due_date
            today_notes = [
                n for n in all_notes
                if today_iso in str(n.get("due_date", ""))
                or today_iso in str(n.get("date", ""))
                or today_short in str(n.get("title", "")).lower()
                or today_short in str(n.get("content", "")).lower()
                or "today" in str(n.get("title", "")).lower()
                or "today" in str(n.get("content", "")).lower()
            ]

            if today_notes:
                return today_notes
            return all_notes[-3:]
        except Exception as e:
            logger.warning(f"Error fetching notes for daily brief: {e}")
            return []

    def _fetch_client_data(self) -> Tuple[Optional[Any], Optional[Any]]:
        """Fetches pending deliverables and payments if ClientTrackerSkill is loaded."""
        deliverables_data = None
        payments_data = None

        try:
            from skills.skill_manager import skill_manager
            client_skill = None
            for skill in skill_manager.loaded_skills.values():
                if (
                    getattr(skill, "name", "") in ["client_tracker", "clients", "client_management"]
                    or hasattr(skill, "get_pending_deliverables")
                ):
                    if skill_manager.is_skill_enabled(skill.name):
                        client_skill = skill
                        break

            if client_skill:
                if hasattr(client_skill, "get_pending_deliverables"):
                    deliverables_data = client_skill.get_pending_deliverables(within_days=3)
                if hasattr(client_skill, "get_pending_payments"):
                    payments_data = client_skill.get_pending_payments()
            else:
                # Also check tool registry for standalone tool registration
                from tools.tool_registry import tool_registry
                if "get_pending_deliverables" in tool_registry._tools:
                    deliverables_data = tool_registry.execute_tool("get_pending_deliverables", within_days=3)
                if "get_pending_payments" in tool_registry._tools:
                    payments_data = tool_registry.execute_tool("get_pending_payments")
        except Exception as e:
            logger.warning(f"Error fetching client deliverables: {e}")

        return deliverables_data, payments_data

    def _fetch_job_followups(self) -> Optional[List[Dict[str, Any]]]:
        """Fetches pending job followups if JobTrackerSkill is loaded."""
        try:
            from skills.skill_manager import skill_manager
            from tools.tool_registry import tool_registry

            has_tool = "list_pending_followups" in tool_registry._tools
            is_enabled = skill_manager.is_skill_enabled("job_tracker") if "job_tracker" in skill_manager.loaded_skills else True

            if has_tool and is_enabled:
                res = tool_registry.execute_tool("list_pending_followups", within_days=7)
                if isinstance(res, dict) and res.get("status") == "success":
                    return res.get("followups", [])

            # Direct fallback if skill module is present and enabled
            if is_enabled:
                try:
                    from skills.job_tracker_skill import ListPendingFollowupsTool
                    res = ListPendingFollowupsTool().execute(within_days=7)
                    if isinstance(res, dict) and res.get("status") == "success":
                        return res.get("followups", [])
                except ImportError:
                    pass
        except Exception as e:
            logger.warning(f"Error fetching job followups for daily brief: {e}")
        return None

    def _fetch_recent_sessions_recap(self, limit: int = 3) -> List[str]:
        """Queries the SQLite database for the first user message of recent sessions."""
        recent_topics = []
        try:
            from memory.database import db
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT s.id, m.content 
                    FROM sessions s
                    JOIN messages m ON s.id = m.session_id
                    WHERE m.role = 'user' AND m.content IS NOT NULL AND TRIM(m.content) != ''
                    GROUP BY s.id
                    ORDER BY s.updated_at DESC, s.id DESC
                    LIMIT ?
                """, (limit,))
                rows = cursor.fetchall()
                for row in rows:
                    content = row["content"].strip()
                    if content.startswith("/"):
                        continue
                    # First line or up to 60 characters
                    topic = content.split("\n")[0][:60].strip()
                    if topic and topic not in recent_topics:
                        recent_topics.append(topic)
        except Exception as e:
            logger.warning(f"Error querying recent sessions for daily brief: {e}")
        return recent_topics

    def _fetch_system_snapshot(self, verbose: bool = False) -> Tuple[Optional[Dict[str, Any]], str]:
        """Fetches hardware status."""
        try:
            tool = GetSystemInfoTool()
            info = tool.execute()
            if info.get("status") != "success":
                return None, "System stats currently unavailable."

            cpu_usage = info.get("cpu", {}).get("usage_percent", "0%")
            ram_info = info.get("ram", {})
            ram_used = ram_info.get("used_gb", 0)
            ram_total = ram_info.get("total_gb", 0)
            ram_percent = ram_info.get("percent_used", 0)
            battery = info.get("battery")

            if verbose:
                summary = f"System is at {cpu_usage} CPU usage and {ram_percent}% RAM ({ram_used} of {ram_total} GB used)."
                if isinstance(battery, dict) and not battery.get("power_plugged"):
                    summary += f" Battery is at {battery.get('percent')}%."
                return info, summary
            else:
                if ram_percent > 85:
                    summary = f"Note that RAM usage is high at {ram_percent}%."
                else:
                    summary = "System is running smoothly."
                return info, summary
        except Exception as e:
            logger.warning(f"Error fetching system snapshot: {e}")
            return None, "System status is normal."

    def _compose_brief_text(
        self,
        greeting: str,
        notes_data: List[Dict[str, Any]],
        deliverables_data: Optional[Any] = None,
        payments_data: Optional[Any] = None,
        job_followups: Optional[Any] = None,
        recent_sessions: Optional[List[str]] = None,
        system_summary: str = ""
    ) -> str:
        """Composes a fluent, TTS-ready daily orientation paragraph."""
        sentences = [greeting]

        # 1. Deliverables section
        if deliverables_data:
            deliverable_sentence = self._format_deliverables_sentence(deliverables_data)
            if deliverable_sentence:
                sentences.append(deliverable_sentence)

        # 2. Payments section
        if payments_data:
            payment_sentence = self._format_payments_sentence(payments_data)
            if payment_sentence:
                sentences.append(payment_sentence)

        # 3. Job application follow-ups
        if job_followups:
            if len(job_followups) == 1:
                comp = job_followups[0].get("company", "a company")
                role = job_followups[0].get("role", "")
                role_txt = f" for {role}" if role else ""
                sentences.append(f"You have 1 job application follow-up due: {comp}{role_txt}.")
            else:
                top_comps = [f.get("company", "") for f in job_followups[:2] if f.get("company")]
                sentences.append(f"You have {len(job_followups)} job application follow-ups due, including {', '.join(top_comps)}.")

        # 4. Recent coding context
        if recent_sessions:
            if len(recent_sessions) == 1:
                sentences.append(f"You were last working on '{recent_sessions[0]}' in SERA.")
            else:
                topics_str = ", ".join([f"'{t}'" for t in recent_sessions[:2]])
                sentences.append(f"In your recent sessions, you worked on {topics_str}.")

        # 5. Notes section
        if notes_data:
            if len(notes_data) == 1:
                sentences.append(f"You have 1 active note: '{notes_data[0].get('title', 'Untitled')}'.")
            else:
                titles = ", ".join([f"'{n.get('title', 'Untitled')}'" for n in notes_data[:2]])
                sentences.append(f"You have {len(notes_data)} active notes, including {titles}.")
        else:
            sentences.append("No urgent notes.")

        # 6. System status
        if system_summary:
            sentences.append(system_summary)

        full_text = " ".join(sentences)
        return clean_text_for_speech(full_text)

    def _format_deliverables_sentence(self, deliverables_data: Any) -> Optional[str]:
        """Formats client deliverables into a natural-language sentence."""
        overdue = []
        upcoming = []

        now_str = datetime.now().strftime("%Y-%m-%d")

        items = []
        if isinstance(deliverables_data, dict):
            if "overdue" in deliverables_data or "upcoming" in deliverables_data:
                overdue = deliverables_data.get("overdue", [])
                upcoming = deliverables_data.get("upcoming", [])
            elif "deliverables" in deliverables_data:
                items = deliverables_data.get("deliverables", [])
        elif isinstance(deliverables_data, list):
            items = deliverables_data

        if items:
            for item in items:
                due = str(item.get("due_date") or item.get("due") or "")
                if due and due < now_str:
                    overdue.append(item)
                else:
                    upcoming.append(item)

        total = len(overdue) + len(upcoming)
        if total == 0:
            return None

        parts = []
        if overdue:
            first_overdue = overdue[0]
            title = first_overdue.get("title") or first_overdue.get("task") or "task"
            client = first_overdue.get("client") or first_overdue.get("client_name") or "client"
            parts.append(f"{len(overdue)} overdue deliverable: {title} for {client}")

        if upcoming:
            first_up = upcoming[0]
            title = first_up.get("title") or first_up.get("task") or "task"
            client = first_up.get("client") or first_up.get("client_name") or "client"
            due = first_up.get("due_date") or first_up.get("due") or "soon"
            parts.append(f"{len(upcoming)} deliverable due soon: {title} for {client} (due {due})")

        return f"You have {', and '.join(parts)}."

    def _format_payments_sentence(self, payments_data: Any) -> Optional[str]:
        """Formats pending payments into a natural-language sentence."""
        items = []
        if isinstance(payments_data, dict):
            items = payments_data.get("pending_payments") or payments_data.get("payments") or []
        elif isinstance(payments_data, list):
            items = payments_data

        if not items:
            return None

        total_amount = 0
        for item in items:
            amount = item.get("amount") or item.get("value") or 0
            try:
                total_amount += float(str(amount).replace("$", "").replace(",", ""))
            except (ValueError, TypeError):
                pass

        if total_amount > 0:
            return f"You have {len(items)} pending payment invoices totaling ${total_amount:,.2f}."
        return f"You have {len(items)} pending payment invoices."


class DailyBriefSkill(BaseSkill):
    name = "daily_brief"
    description = (
        "Generates a personalized daily briefing summarizing pending tasks, "
        "recent coding context, and system status."
    )

    def get_tools(self) -> List[BaseTool]:
        return [GetDailyBriefTool()]


def check_and_trigger_daily_brief(force: bool = False, verbose: bool = False) -> Optional[Dict[str, Any]]:
    """Convenience helper to check gating and trigger daily brief once per day."""
    if not force and not should_trigger_daily_brief():
        return None
    tool = GetDailyBriefTool()
    result = tool.execute(verbose=verbose)
    mark_daily_brief_delivered()
    return result
