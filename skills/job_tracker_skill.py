import os
import json
import uuid
import difflib
import logging
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

from skills.base_skill import BaseSkill
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

JOB_APPLICATIONS_FILE = Path("data/job_applications.json")

VALID_STAGES = ["applied", "oa_test", "interview", "offer", "rejected", "ghosted"]

STAGE_NORMALIZATION = {
    "applied": "applied",
    "apply": "applied",
    "oa": "oa_test",
    "oa_test": "oa_test",
    "online_assessment": "oa_test",
    "assessment": "oa_test",
    "test": "oa_test",
    "interview": "interview",
    "interviewing": "interview",
    "round": "interview",
    "offer": "offer",
    "accepted": "offer",
    "hired": "offer",
    "rejected": "rejected",
    "reject": "rejected",
    "denied": "rejected",
    "ghosted": "ghosted",
    "ghost": "ghosted",
    "no_response": "ghosted"
}


def load_job_applications() -> Dict[str, Any]:
    """Loads job applications from storage or initializes empty schema."""
    if not JOB_APPLICATIONS_FILE.exists():
        return {"applications": []}
    try:
        with open(JOB_APPLICATIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {"applications": []}
            data.setdefault("applications", [])
            return data
    except Exception as e:
        logger.warning(f"Error reading job applications file: {e}")
        return {"applications": []}


def save_job_applications(data: Dict[str, Any]) -> None:
    """Saves job applications using atomic write (temp file + replace)."""
    try:
        JOB_APPLICATIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
        temp_file = JOB_APPLICATIONS_FILE.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(temp_file, JOB_APPLICATIONS_FILE)
    except Exception as e:
        logger.error(f"Failed to atomically save job applications: {e}")


def fuzzy_find_application(company: str, applications: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Finds an application matching company name using exact, substring, and difflib matching."""
    if not company or not applications:
        return None

    target = company.strip().lower()

    # 1. Exact case-insensitive match
    for app in applications:
        if app.get("company", "").strip().lower() == target:
            return app

    # 2. Substring match (either target inside company name, or company inside target)
    for app in applications:
        app_comp = app.get("company", "").strip().lower()
        if target in app_comp or app_comp in target:
            return app

    # 3. Difflib close matches
    comp_map = {app.get("company", "").strip().lower(): app for app in applications}
    matches = difflib.get_close_matches(target, list(comp_map.keys()), n=1, cutoff=0.55)
    if matches:
        return comp_map[matches[0]]

    return None


class LogApplicationTool(BaseTool):
    name = "log_application"
    description = "Logs a new job/internship application."
    parameters = {
        "type": "object",
        "properties": {
            "company": {
                "type": "string",
                "description": "Company name applied to (e.g. 'Google', 'Shippoz', 'Amazon')."
            },
            "role": {
                "type": "string",
                "description": "Role or position title (e.g. 'AI Engineer Intern', 'Full-Stack Developer')."
            },
            "platform": {
                "type": "string",
                "description": "Platform where applied (e.g. 'LinkedIn', 'Indeed', 'Referral', 'Company site')."
            },
            "applied_date": {
                "type": "string",
                "description": "Date applied in YYYY-MM-DD format. Defaults to today if omitted."
            },
            "notes": {
                "type": "string",
                "description": "Optional notes, link, or context about the application."
            }
        },
        "required": ["company", "role"]
    }

    def execute(
        self,
        company: str,
        role: str,
        platform: Optional[str] = "Unknown",
        applied_date: Optional[str] = None,
        notes: Optional[str] = ""
    ) -> Dict[str, Any]:
        data = load_job_applications()

        now = datetime.now()
        app_date = applied_date.strip() if (applied_date and applied_date.strip()) else now.strftime("%Y-%m-%d")

        app_id = str(uuid.uuid4())
        record = {
            "id": app_id,
            "company": company.strip(),
            "role": role.strip(),
            "platform": (platform or "Unknown").strip(),
            "applied_date": app_date,
            "stage": "applied",
            "last_contact_date": app_date,
            "next_followup_date": None,
            "notes": (notes or "").strip(),
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }

        data["applications"].append(record)
        save_job_applications(data)

        return {
            "status": "success",
            "message": f"Logged application for '{record['role']}' at '{record['company']}' on {record['applied_date']}.",
            "application": record
        }


class UpdateApplicationStageTool(BaseTool):
    name = "update_application_stage"
    description = "Updates an application's stage (e.g. moved to interview, rejected)."
    parameters = {
        "type": "object",
        "properties": {
            "company": {
                "type": "string",
                "description": "Name of the company to update (fuzzy matched)."
            },
            "stage": {
                "type": "string",
                "description": "New stage: 'applied', 'oa_test', 'interview', 'offer', 'rejected', or 'ghosted'."
            },
            "notes": {
                "type": "string",
                "description": "Optional new notes to append to existing application notes."
            },
            "next_followup_date": {
                "type": "string",
                "description": "Optional next follow-up date in YYYY-MM-DD format."
            }
        },
        "required": ["company", "stage"]
    }

    def execute(
        self,
        company: str,
        stage: str,
        notes: Optional[str] = None,
        next_followup_date: Optional[str] = None
    ) -> Dict[str, Any]:
        data = load_job_applications()
        matched_app = fuzzy_find_application(company, data.get("applications", []))

        if not matched_app:
            return {
                "status": "error",
                "message": f"No job application found matching company '{company}'."
            }

        # Normalize stage
        clean_stage = stage.strip().lower()
        normalized_stage = STAGE_NORMALIZATION.get(clean_stage)
        if not normalized_stage or normalized_stage not in VALID_STAGES:
            return {
                "status": "error",
                "message": f"Invalid stage '{stage}'. Must be one of: {', '.join(VALID_STAGES)}."
            }

        now = datetime.now()
        matched_app["stage"] = normalized_stage
        matched_app["updated_at"] = now.isoformat()
        matched_app["last_contact_date"] = now.strftime("%Y-%m-%d")

        if next_followup_date and next_followup_date.strip():
            matched_app["next_followup_date"] = next_followup_date.strip()

        # Append notes rather than overwriting
        if notes and notes.strip():
            new_note = notes.strip()
            existing_notes = matched_app.get("notes", "").strip()
            if existing_notes:
                matched_app["notes"] = f"{existing_notes} | {new_note}"
            else:
                matched_app["notes"] = new_note

        save_job_applications(data)

        return {
            "status": "success",
            "message": f"Updated '{matched_app['company']}' ({matched_app['role']}) to stage '{normalized_stage}'.",
            "application": matched_app
        }


class ListPendingFollowupsTool(BaseTool):
    name = "list_pending_followups"
    description = "Lists applications with a follow-up due soon or overdue."
    parameters = {
        "type": "object",
        "properties": {
            "within_days": {
                "type": "integer",
                "description": "Window in days to look ahead for follow-ups (default 7)."
            }
        },
        "required": []
    }

    def execute(self, within_days: int = 7) -> Dict[str, Any]:
        data = load_job_applications()
        apps = data.get("applications", [])

        window = max(1, within_days if within_days is not None else 7)
        today = datetime.now().date()
        target_cutoff = today + timedelta(days=window)

        followups: List[Dict[str, Any]] = []

        for app in apps:
            stage = app.get("stage", "applied")
            # Terminal states typically don't have followups unless explicitly set
            next_followup_str = app.get("next_followup_date")
            applied_str = app.get("applied_date")

            # Condition 1: Explicit next_followup_date set within window or overdue
            if next_followup_str:
                try:
                    f_date = datetime.strptime(next_followup_str.strip(), "%Y-%m-%d").date()
                    if f_date <= target_cutoff:
                        is_overdue = f_date < today
                        followups.append({
                            "id": app.get("id"),
                            "company": app.get("company"),
                            "role": app.get("role"),
                            "stage": stage,
                            "followup_date": str(f_date),
                            "is_overdue": is_overdue,
                            "type": "scheduled",
                            "days_diff": (today - f_date).days if is_overdue else (f_date - today).days,
                            "notes": app.get("notes", "")
                        })
                except ValueError:
                    pass

            # Condition 2: stage='applied' with applied_date >= 14 days ago and no next_followup_date set
            elif stage == "applied" and applied_str:
                try:
                    app_date = datetime.strptime(applied_str.strip(), "%Y-%m-%d").date()
                    days_since_applied = (today - app_date).days
                    if days_since_applied >= 14:
                        followups.append({
                            "id": app.get("id"),
                            "company": app.get("company"),
                            "role": app.get("role"),
                            "stage": stage,
                            "applied_date": str(app_date),
                            "is_overdue": True,
                            "type": "auto_suggested",
                            "days_since_applied": days_since_applied,
                            "notes": app.get("notes", "")
                        })
                except ValueError:
                    pass

        # Sort: Overdue items first (largest days_diff / days_since_applied), then scheduled upcoming
        def sort_key(item):
            if item.get("is_overdue"):
                return (0, -item.get("days_since_applied", item.get("days_diff", 0)))
            return (1, item.get("days_diff", 0))

        followups.sort(key=sort_key)

        overdue_count = sum(1 for f in followups if f.get("is_overdue"))
        scheduled_count = sum(1 for f in followups if not f.get("is_overdue"))

        if not followups:
            msg = f"No pending follow-ups due in the next {window} days."
        else:
            top_companies = [f["company"] for f in followups[:2]]
            if len(followups) == 1:
                msg = f"You have 1 follow-up due: {followups[0]['company']} ({followups[0]['role']})."
            else:
                msg = f"You have {len(followups)} follow-up(s) due: {', '.join(top_companies)}{' and others' if len(followups) > 2 else ''}."

        return {
            "status": "success",
            "within_days": window,
            "total_followups": len(followups),
            "overdue_count": overdue_count,
            "upcoming_count": scheduled_count,
            "followups": followups,
            "message": msg
        }


class GetApplicationStatsTool(BaseTool):
    name = "get_application_stats"
    description = "Summarizes application funnel — counts per stage."
    parameters = {
        "type": "object",
        "properties": {},
        "required": []
    }

    def execute(self) -> Dict[str, Any]:
        data = load_job_applications()
        apps = data.get("applications", [])

        counts = {s: 0 for s in VALID_STAGES}
        for app in apps:
            s = app.get("stage", "applied")
            if s in counts:
                counts[s] += 1
            else:
                counts[s] = counts.get(s, 0) + 1

        total = len(apps)

        parts = []
        if counts.get("applied", 0) > 0:
            parts.append(f"{counts['applied']} applied")
        if counts.get("oa_test", 0) > 0:
            parts.append(f"{counts['oa_test']} in OA test")
        if counts.get("interview", 0) > 0:
            parts.append(f"{counts['interview']} in interview")
        if counts.get("offer", 0) > 0:
            parts.append(f"{counts['offer']} offer")
        if counts.get("rejected", 0) > 0:
            parts.append(f"{counts['rejected']} rejected")
        if counts.get("ghosted", 0) > 0:
            parts.append(f"{counts['ghosted']} ghosted")

        if parts:
            summary = f"Application Funnel: {', '.join(parts)} ({total} total)."
        else:
            summary = "No job applications recorded yet."

        return {
            "status": "success",
            "total_applications": total,
            "stage_counts": counts,
            "summary": summary,
            "message": summary
        }


class JobTrackerSkill(BaseSkill):
    name = "job_tracker"
    description = "Tracks job and internship applications, stages, follow-up reminders, and search statistics."

    def get_tools(self) -> List[BaseTool]:
        return [
            LogApplicationTool(),
            UpdateApplicationStageTool(),
            ListPendingFollowupsTool(),
            GetApplicationStatsTool()
        ]
