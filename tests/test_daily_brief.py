import unittest
import os
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from skills.base_skill import BaseSkill
from skills.skill_manager import SkillManager, skill_manager
from skills.daily_brief_skill import (
    GetDailyBriefTool,
    DailyBriefSkill,
    load_state,
    save_state,
    should_trigger_daily_brief,
    mark_daily_brief_delivered,
    check_and_trigger_daily_brief,
    STATE_FILE
)
from memory.database import Database
from memory.memory_store import MemoryStore
from models.message import Message


class MockClientTrackerSkill(BaseSkill):
    name = "client_tracker"
    description = "Mock client tracker skill for testing."

    def get_tools(self):
        return []

    def get_pending_deliverables(self, within_days: int = 3):
        today = datetime.now()
        yesterday_str = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        tomorrow_str = (today + timedelta(days=2)).strftime("%Y-%m-%d")
        return {
            "overdue": [
                {"title": "Backend API Spec", "client": "Apex Corp", "due_date": yesterday_str}
            ],
            "upcoming": [
                {"title": "React Dashboard MVP", "client": "Nexus Labs", "due_date": tomorrow_str}
            ]
        }

    def get_pending_payments(self):
        return {
            "pending_payments": [
                {"client": "Apex Corp", "amount": 2500.0, "invoice_id": "INV-101"}
            ]
        }


class TestDailyBriefSkill(unittest.TestCase):
    def setUp(self):
        self.original_state = None
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    self.original_state = json.load(f)
            except Exception:
                self.original_state = None

    def tearDown(self):
        if self.original_state is not None:
            save_state(self.original_state)
        elif STATE_FILE.exists():
            STATE_FILE.unlink(missing_ok=True)
        # Ensure mock client tracker is removed if present
        if "client_tracker" in skill_manager.loaded_skills:
            del skill_manager.loaded_skills["client_tracker"]
        if "client_tracker" in skill_manager.enabled_skills:
            del skill_manager.enabled_skills["client_tracker"]

    def test_daily_brief_skill_discovery(self):
        """Tests that DailyBriefSkill is discovered by SkillManager and its tool is registered."""
        manager = SkillManager()
        skills = manager.discover_and_load_skills()
        self.assertIn("daily_brief", skills)
        skill = skills["daily_brief"]
        self.assertIsInstance(skill, BaseSkill)
        tools = skill.get_tools()
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0].name, "get_daily_brief")

    def test_empty_data_sources(self):
        """Tests that brief generation with empty notes and sessions runs without crashing."""
        with patch("skills.daily_brief_skill.ListNotesTool.execute", return_value={"status": "success", "notes": []}):
            with patch("skills.daily_brief_skill.GetDailyBriefTool._fetch_recent_sessions_recap", return_value=[]):
                tool = GetDailyBriefTool()
                res = tool.execute(verbose=False)
                self.assertEqual(res["status"], "success")
                self.assertIn("brief_text", res)
                self.assertIn("raw_data", res)
                self.assertTrue(len(res["brief_text"]) > 0)
                self.assertIn("No urgent notes", res["brief_text"])

    def test_client_tracker_overdue_and_upcoming(self):
        """Tests that pending deliverables and payments are properly surfaced when ClientTrackerSkill is present."""
        mock_skill = MockClientTrackerSkill()
        skill_manager.loaded_skills["client_tracker"] = mock_skill
        skill_manager.enabled_skills["client_tracker"] = True

        tool = GetDailyBriefTool()
        res = tool.execute(verbose=False)

        self.assertEqual(res["status"], "success")
        brief_text = res["brief_text"]
        self.assertIn("Apex Corp", brief_text)
        self.assertIn("Nexus Labs", brief_text)
        self.assertIn("overdue deliverable", brief_text.lower())
        self.assertIn("pending payment", brief_text.lower())

    def test_graceful_degradation_without_client_tracker(self):
        """Tests that when ClientTrackerSkill is absent, brief executes cleanly without client section."""
        if "client_tracker" in skill_manager.loaded_skills:
            del skill_manager.loaded_skills["client_tracker"]

        tool = GetDailyBriefTool()
        res = tool.execute(verbose=False)

        self.assertEqual(res["status"], "success")
        self.assertIsNone(res["raw_data"]["client_deliverables"])
        self.assertIsNone(res["raw_data"]["client_payments"])
        self.assertNotIn("overdue deliverable", res["brief_text"].lower())

    def test_recent_sessions_recap(self):
        """Tests that recent SQLite sessions are surfaced in the brief."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
            db_path = tf.name

        try:
            custom_db = Database(db_path=db_path)
            custom_memory = MemoryStore(database=custom_db)

            # Create 2 sessions with user messages
            s1 = custom_memory.create_session()
            custom_memory.save_message(Message(session_id=s1, role="user", content="Build React landing page"))

            s2 = custom_memory.create_session()
            custom_memory.save_message(Message(session_id=s2, role="user", content="Debug FastAPI authentication"))

            with patch("memory.database.db", custom_db):
                tool = GetDailyBriefTool()
                res = tool.execute(verbose=False)
                self.assertEqual(res["status"], "success")
                raw_sessions = res["raw_data"]["recent_sessions"]
                self.assertTrue(any("Debug FastAPI" in s or "Build React" in s for s in raw_sessions))
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)

    def test_once_per_day_gating_logic(self):
        """Tests the state.json gating logic ensuring auto-brief fires only once per day."""
        # Clear state
        save_state({})
        self.assertTrue(should_trigger_daily_brief())

        # First trigger should succeed
        res1 = check_and_trigger_daily_brief(force=False)
        self.assertIsNotNone(res1)
        self.assertEqual(res1["status"], "success")

        # Second trigger on same day should be gated (return None)
        self.assertFalse(should_trigger_daily_brief())
        res2 = check_and_trigger_daily_brief(force=False)
        self.assertIsNone(res2)

        # Force trigger should bypass gating
        res_forced = check_and_trigger_daily_brief(force=True)
        self.assertIsNotNone(res_forced)
        self.assertEqual(res_forced["status"], "success")

        # Fake yesterday's date to test next-day rollover
        yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        save_state({"last_brief_date": yesterday_str})
        self.assertTrue(should_trigger_daily_brief())
        res_next_day = check_and_trigger_daily_brief(force=False)
        self.assertIsNotNone(res_next_day)

    def test_verbose_hardware_metrics(self):
        """Tests that verbose=True includes CPU and RAM metrics."""
        tool = GetDailyBriefTool()
        res = tool.execute(verbose=True)
        self.assertEqual(res["status"], "success")
        self.assertIn("CPU", res["brief_text"])
        self.assertIn("RAM", res["brief_text"])


if __name__ == "__main__":
    unittest.main()
