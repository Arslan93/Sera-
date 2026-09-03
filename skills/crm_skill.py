import os
import json
import uuid
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from skills.base_skill import BaseSkill
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

LEADS_FILE = Path(__file__).resolve().parent.parent / "data" / "leads.json"

def _load_leads() -> List[Dict[str, Any]]:
    if not LEADS_FILE.exists():
        return []
    try:
        with open(LEADS_FILE, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return []

def _save_leads(leads: List[Dict[str, Any]]) -> None:
    LEADS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LEADS_FILE, "w", encoding="utf-8") as f:
        json.dump(leads, f, indent=2, ensure_ascii=False)


class CreateLeadTool(BaseTool):
    name = "create_lead"
    description = "Adds a new business client or lead to the CRM database with contact details and deal notes."
    parameters = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Full name of the contact person."},
            "email": {"type": "string", "description": "Email address of the lead."},
            "phone": {"type": "string", "description": "Phone or WhatsApp number."},
            "company": {"type": "string", "description": "Company or business name."},
            "deal_value": {"type": "string", "description": "Estimated deal value or budget (e.g. '$2,500', '₹50,000')."},
            "status": {
                "type": "string",
                "enum": ["New", "Contacted", "Proposal Sent", "In Negotiation", "Won", "Lost"],
                "description": "Current pipeline status (default: 'New')."
            },
            "notes": {"type": "string", "description": "Initial notes or project requirements."}
        },
        "required": ["name"]
    }

    def execute(self, name: str, email: str = "", phone: str = "", company: str = "", deal_value: str = "", status: str = "New", notes: str = "") -> Dict[str, Any]:
        leads = _load_leads()
        lead_id = f"lead_{uuid.uuid4().hex[:6]}"
        now = datetime.now().isoformat()

        new_lead = {
            "id": lead_id,
            "name": name,
            "email": email,
            "phone": phone,
            "company": company,
            "deal_value": deal_value,
            "status": status,
            "notes": notes,
            "created_at": now,
            "updated_at": now
        }
        leads.append(new_lead)
        _save_leads(leads)

        logger.info(f"Created CRM lead: {name} (ID: {lead_id})")
        return {"status": "success", "message": f"Successfully created lead '{name}' with ID {lead_id}.", "lead": new_lead}


class ListLeadsTool(BaseTool):
    name = "list_leads"
    description = "Lists all business leads and clients in the CRM pipeline, optionally filtered by status."
    parameters = {
        "type": "object",
        "properties": {
            "filter_status": {
                "type": "string",
                "enum": ["All", "New", "Contacted", "Proposal Sent", "In Negotiation", "Won", "Lost"],
                "description": "Optional status filter."
            }
        }
    }

    def execute(self, filter_status: str = "All") -> Dict[str, Any]:
        leads = _load_leads()
        if filter_status and filter_status != "All":
            leads = [l for l in leads if l.get("status", "").lower() == filter_status.lower()]

        return {
            "status": "success",
            "total": len(leads),
            "filter": filter_status,
            "leads": leads
        }


class UpdateLeadStatusTool(BaseTool):
    name = "update_lead_status"
    description = "Updates the pipeline status or adds notes to an existing CRM lead."
    parameters = {
        "type": "object",
        "properties": {
            "lead_identifier": {
                "type": "string",
                "description": "The lead ID (e.g. 'lead_a1b2c3') or contact name to search."
            },
            "new_status": {
                "type": "string",
                "enum": ["New", "Contacted", "Proposal Sent", "In Negotiation", "Won", "Lost"],
                "description": "The new pipeline stage."
            },
            "new_notes": {
                "type": "string",
                "description": "Additional notes to append."
            }
        },
        "required": ["lead_identifier"]
    }

    def execute(self, lead_identifier: str, new_status: str = None, new_notes: str = None) -> Dict[str, Any]:
        leads = _load_leads()
        target_lead = None
        ident_clean = lead_identifier.strip().lower()

        for lead in leads:
            if lead.get("id", "").lower() == ident_clean or ident_clean in lead.get("name", "").lower():
                target_lead = lead
                break

        if not target_lead:
            return {"status": "error", "message": f"No lead found matching identifier '{lead_identifier}'."}

        if new_status:
            target_lead["status"] = new_status
        if new_notes:
            existing = target_lead.get("notes", "")
            target_lead["notes"] = f"{existing} | {new_notes}" if existing else new_notes
        target_lead["updated_at"] = datetime.now().isoformat()

        _save_leads(leads)
        logger.info(f"Updated CRM lead {target_lead['id']} -> status: {target_lead['status']}")
        return {"status": "success", "message": f"Updated lead '{target_lead['name']}' to status '{target_lead['status']}'.", "lead": target_lead}


class CRMSkill(BaseSkill):
    name = "crm_business"
    description = "Business CRM automation skill for managing client leads, deal pipeline, and contact updates."

    def get_tools(self) -> List[BaseTool]:
        return [CreateLeadTool(), ListLeadsTool(), UpdateLeadStatusTool()]
