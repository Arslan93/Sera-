import unittest
import os
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch

from skills.base_skill import BaseSkill
from skills.skill_manager import SkillManager
from skills.notes_skill import AddNoteTool, ListNotesTool, NOTES_FILE
from skills.study_session_skill import (
    StartStudyTool,
    EndStudyTool,
    QuizMeTool,
    GetStudyStatsTool,
    StudySessionSkill,
    load_study_sessions,
    save_study_sessions,
    STUDY_SESSIONS_FILE
)


class TestStudySessionSkill(unittest.TestCase):
    def setUp(self):
        self.original_study_data = None
        if STUDY_SESSIONS_FILE.exists():
            try:
                with open(STUDY_SESSIONS_FILE, "r", encoding="utf-8") as f:
                    self.original_study_data = json.load(f)
            except Exception:
                self.original_study_data = None

        self.original_notes_data = None
        if NOTES_FILE.exists():
            try:
                with open(NOTES_FILE, "r", encoding="utf-8") as f:
                    self.original_notes_data = json.load(f)
            except Exception:
                self.original_notes_data = None

        # Reset state for clean test runs
        save_study_sessions({"sessions": [], "active_session_id": None})

    def tearDown(self):
        if self.original_study_data is not None:
            save_study_sessions(self.original_study_data)
        elif STUDY_SESSIONS_FILE.exists():
            STUDY_SESSIONS_FILE.unlink(missing_ok=True)

        if self.original_notes_data is not None:
            with open(NOTES_FILE, "w", encoding="utf-8") as f:
                json.dump(self.original_notes_data, f, indent=2, ensure_ascii=False)
        elif NOTES_FILE.exists():
            NOTES_FILE.unlink(missing_ok=True)

    def test_skill_discovery(self):
        """Tests that StudySessionSkill is discovered by SkillManager with all 4 tools."""
        manager = SkillManager()
        skills = manager.discover_and_load_skills()
        self.assertIn("study_session", skills)
        skill = skills["study_session"]
        self.assertIsInstance(skill, BaseSkill)
        tools = skill.get_tools()
        self.assertEqual(len(tools), 4)
        tool_names = [t.name for t in tools]
        self.assertIn("start_study", tool_names)
        self.assertIn("end_study", tool_names)
        self.assertIn("quiz_me", tool_names)
        self.assertIn("get_study_stats", tool_names)

    def test_start_study_rejects_concurrent_session(self):
        """Tests that starting a second session while one is active is rejected."""
        start_tool = StartStudyTool()

        # 1. Start first session
        res1 = start_tool.execute(subject="DBMS")
        self.assertEqual(res1["status"], "success")
        self.assertEqual(res1["subject"], "DBMS")
        self.assertIsNotNone(res1["session_id"])

        # 2. Attempt to start second session concurrently
        res2 = start_tool.execute(subject="Computer Networks")
        self.assertEqual(res2["status"], "error")
        self.assertIn("active session on 'DBMS'", res2["message"])
        self.assertIn("end it first", res2["message"])

        # Check storage integrity
        data = load_study_sessions()
        self.assertEqual(data["active_session_id"], res1["session_id"])
        self.assertEqual(len(data["sessions"]), 1)

    def test_end_study_computes_duration(self):
        """Tests that ending a session calculates duration_minutes and updates record."""
        start_tool = StartStudyTool()
        end_tool = EndStudyTool()

        # Start session
        res_start = start_tool.execute(subject="Operating Systems")
        self.assertEqual(res_start["status"], "success")

        # Fake started_at timestamp 45 minutes in the past
        data = load_study_sessions()
        past_time = (datetime.now() - timedelta(minutes=45)).isoformat()
        data["sessions"][0]["started_at"] = past_time
        save_study_sessions(data)

        # End session
        res_end = end_tool.execute(topics_covered="Virtual memory, paging, page replacement algorithms")
        self.assertEqual(res_end["status"], "success")
        self.assertIn("Nice, 45", res_end["message"])
        self.assertEqual(res_end["subject"], "Operating Systems")
        self.assertAlmostEqual(res_end["duration_minutes"], 45.0, delta=0.5)
        self.assertEqual(res_end["topics_covered"], "Virtual memory, paging, page replacement algorithms")

        # Check data storage
        updated_data = load_study_sessions()
        self.assertIsNone(updated_data["active_session_id"])
        self.assertEqual(updated_data["sessions"][0]["status"], "completed")
        self.assertIsNotNone(updated_data["sessions"][0]["ended_at"])

    def test_end_study_without_active_session(self):
        """Tests that ending when no session is active returns a friendly error."""
        end_tool = EndStudyTool()
        res = end_tool.execute(topics_covered="Done")
        self.assertEqual(res["status"], "error")
        self.assertIn("No active study session", res["message"])

    def test_quiz_me_empty_material(self):
        """Tests that quiz_me returns not_found when no notes exist for the subject."""
        # Ensure notes file has unrelated notes or is empty
        with open(NOTES_FILE, "w", encoding="utf-8") as f:
            json.dump([{"title": "Groceries", "content": "Milk and eggs"}], f)

        quiz_tool = QuizMeTool()
        res = quiz_tool.execute(subject="Compiler Design", num_questions=3)
        self.assertEqual(res["status"], "not_found")
        self.assertIn("No study notes or material found", res["message"])
        self.assertEqual(res["material"], [])

    def test_quiz_me_matching_material(self):
        """Tests that quiz_me retrieves notes matching the subject and formats LLM instruction."""
        with open(NOTES_FILE, "w", encoding="utf-8") as f:
            json.dump([
                {
                    "title": "DBMS Normalization",
                    "content": "1NF eliminates repeating groups. 2NF removes partial dependency. 3NF removes transitive dependency. BCNF is stricter 3NF.",
                    "tag": "DBMS"
                },
                {
                    "title": "ACID Properties",
                    "content": "Atomicity, Consistency, Isolation, Durability in transaction management.",
                    "tag": "DBMS"
                }
            ], f)

        quiz_tool = QuizMeTool()
        res = quiz_tool.execute(subject="DBMS", num_questions=4)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["subject"], "DBMS")
        self.assertEqual(res["num_questions"], 4)
        self.assertEqual(len(res["material"]), 2)
        self.assertIn("instruction_for_llm", res)
        self.assertIn("4 short recall questions", res["instruction_for_llm"])

    def test_get_study_stats_aggregation(self):
        """Tests that get_study_stats aggregates duration per subject sorted descending."""
        now = datetime.now()
        yesterday_iso = (now - timedelta(days=1)).isoformat()
        two_days_ago_iso = (now - timedelta(days=2)).isoformat()
        ten_days_ago_iso = (now - timedelta(days=10)).isoformat()

        test_sessions = {
            "sessions": [
                {
                    "id": "1",
                    "subject": "DBMS",
                    "started_at": yesterday_iso,
                    "ended_at": yesterday_iso,
                    "duration_minutes": 50.0,
                    "topics_covered": "SQL Joins",
                    "status": "completed"
                },
                {
                    "id": "2",
                    "subject": "DBMS",
                    "started_at": two_days_ago_iso,
                    "ended_at": two_days_ago_iso,
                    "duration_minutes": 40.0,
                    "topics_covered": "Indexing",
                    "status": "completed"
                },
                {
                    "id": "3",
                    "subject": "Computer Networks",
                    "started_at": yesterday_iso,
                    "ended_at": yesterday_iso,
                    "duration_minutes": 60.0,
                    "topics_covered": "OSI Layer",
                    "status": "completed"
                },
                {
                    "id": "4",
                    "subject": "Operating Systems",
                    "started_at": ten_days_ago_iso,  # Outside 7-day window
                    "ended_at": ten_days_ago_iso,
                    "duration_minutes": 100.0,
                    "topics_covered": "Deadlocks",
                    "status": "completed"
                }
            ],
            "active_session_id": None
        }
        save_study_sessions(test_sessions)

        stats_tool = GetStudyStatsTool()
        res = stats_tool.execute(days=7)

        self.assertEqual(res["status"], "success")
        self.assertEqual(res["days"], 7)
        self.assertEqual(res["total_minutes"], 150.0)  # 50 + 40 + 60 (OS is excluded because it's 10 days ago)

        breakdown = res["breakdown"]
        self.assertEqual(len(breakdown), 2)
        # Most studied subject should be DBMS (90.0m total, 2 sessions)
        self.assertEqual(breakdown[0]["subject"], "DBMS")
        self.assertEqual(breakdown[0]["total_minutes"], 90.0)
        self.assertEqual(breakdown[0]["session_count"], 2)

        # Second most studied subject should be Computer Networks (60.0m total, 1 session)
        self.assertEqual(breakdown[1]["subject"], "Computer Networks")
        self.assertEqual(breakdown[1]["total_minutes"], 60.0)
        self.assertEqual(breakdown[1]["session_count"], 1)

    def test_notes_auto_tagging_with_active_session(self):
        """Tests that saving a note during an active study session auto-tags the note."""
        start_tool = StartStudyTool()
        start_tool.execute(subject="Computer Networks")

        add_note_tool = AddNoteTool()
        add_res = add_note_tool.execute(
            title="TCP 3-Way Handshake",
            content="SYN, SYN-ACK, ACK sequence for reliable connection."
        )

        self.assertEqual(add_res["status"], "success")

        # Verify the saved note in notes.json has the active subject tag
        list_notes_tool = ListNotesTool()
        notes_res = list_notes_tool.execute()
        self.assertEqual(notes_res["status"], "success")
        notes = notes_res["notes"]
        matching_note = next((n for n in notes if n.get("title") == "TCP 3-Way Handshake"), None)
        self.assertIsNotNone(matching_note)
        self.assertEqual(matching_note.get("tag"), "Computer Networks")


if __name__ == "__main__":
    unittest.main()
