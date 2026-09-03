import unittest
import os
import json
from pathlib import Path
from datetime import datetime, timedelta

from skills.base_skill import BaseSkill
from skills.skill_manager import SkillManager, skill_manager
from skills.job_tracker_skill import (
    LogApplicationTool,
    UpdateApplicationStageTool,
    ListPendingFollowupsTool,
    GetApplicationStatsTool,
    JobTrackerSkill,
    load_job_applications,
    save_job_applications,
    JOB_APPLICATIONS_FILE
)
from skills.daily_brief_skill import GetDailyBriefTool


class TestJobTrackerSkill(unittest.TestCase):
    def setUp(self):
        self.original_job_data = None
        if JOB_APPLICATIONS_FILE.exists():
            try:
                with open(JOB_APPLICATIONS_FILE, "r", encoding="utf-8") as f:
                    self.original_job_data = json.load(f)
            except Exception:
                self.original_job_data = None

        save_job_applications({"applications": []})

    def tearDown(self):
        if self.original_job_data is not None:
            save_job_applications(self.original_job_data)
        elif JOB_APPLICATIONS_FILE.exists():
            JOB_APPLICATIONS_FILE.unlink(missing_ok=True)

    def test_skill_discovery(self):
        """Tests that JobTrackerSkill is discovered by SkillManager with all 4 tools."""
        manager = SkillManager()
        skills = manager.discover_and_load_skills()
        self.assertIn("job_tracker", skills)
        skill = skills["job_tracker"]
        self.assertIsInstance(skill, BaseSkill)
        tools = skill.get_tools()
        self.assertEqual(len(tools), 4)
        tool_names = [t.name for t in tools]
        self.assertIn("log_application", tool_names)
        self.assertIn("update_application_stage", tool_names)
        self.assertIn("list_pending_followups", tool_names)
        self.assertIn("get_application_stats", tool_names)

    def test_log_application_default_stage(self):
        """Tests that logging an application creates record with default stage 'applied'."""
        tool = LogApplicationTool()
        res = tool.execute(
            company="Shippoz E-commerce",
            role="AI Engineer Intern",
            platform="LinkedIn",
            notes="Applied through company career portal"
        )

        self.assertEqual(res["status"], "success")
        app = res["application"]
        self.assertEqual(app["company"], "Shippoz E-commerce")
        self.assertEqual(app["role"], "AI Engineer Intern")
        self.assertEqual(app["platform"], "LinkedIn")
        self.assertEqual(app["stage"], "applied")
        self.assertIsNotNone(app["id"])
        self.assertIsNotNone(app["applied_date"])

        # Check storage persistence
        data = load_job_applications()
        self.assertEqual(len(data["applications"]), 1)
        self.assertEqual(data["applications"][0]["company"], "Shippoz E-commerce")

    def test_update_application_stage_fuzzy_match_and_append_notes(self):
        """Tests fuzzy matching of company name and note appending instead of overwriting."""
        log_tool = LogApplicationTool()
        log_tool.execute(
            company="Google India Pvt Ltd",
            role="Software Engineer - AI/ML",
            platform="Company site",
            notes="Submitted resume and portfolio."
        )

        update_tool = UpdateApplicationStageTool()
        # Fuzzy match using "Google"
        res = update_tool.execute(
            company="Google",
            stage="interview",
            notes="Technical round 1 scheduled with engineering manager.",
            next_followup_date="2026-09-10"
        )

        self.assertEqual(res["status"], "success")
        updated_app = res["application"]
        self.assertEqual(updated_app["stage"], "interview")
        self.assertEqual(updated_app["next_followup_date"], "2026-09-10")

        # Verify notes are appended with separator, not overwritten
        expected_notes = "Submitted resume and portfolio. | Technical round 1 scheduled with engineering manager."
        self.assertEqual(updated_app["notes"], expected_notes)

    def test_update_application_invalid_stage_and_missing_company(self):
        """Tests error responses on invalid stages or unknown companies."""
        update_tool = UpdateApplicationStageTool()
        # Non-existent company
        res_missing = update_tool.execute(company="NonExistentCorpXYZ", stage="interview")
        self.assertEqual(res_missing["status"], "error")
        self.assertIn("No job application found", res_missing["message"])

        # Create one app, then test invalid stage
        LogApplicationTool().execute(company="Microsoft", role="Dev")
        res_invalid_stage = update_tool.execute(company="Microsoft", stage="flying_to_mars")
        self.assertEqual(res_invalid_stage["status"], "error")
        self.assertIn("Invalid stage", res_invalid_stage["message"])

    def test_list_pending_followups_auto_suggests_14_day_old(self):
        """Tests that list_pending_followups detects scheduled and 14+ day old applications."""
        today = datetime.now().date()
        date_18_days_ago = str(today - timedelta(days=18))
        date_in_3_days = str(today + timedelta(days=3))
        date_in_25_days = str(today + timedelta(days=25))

        test_data = {
            "applications": [
                {
                    "id": "1",
                    "company": "Amazon",
                    "role": "Cloud Support Intern",
                    "stage": "applied",
                    "applied_date": date_18_days_ago,
                    "next_followup_date": None,
                    "notes": "No response yet"
                },
                {
                    "id": "2",
                    "company": "Microsoft",
                    "role": "SWE Intern",
                    "stage": "interview",
                    "applied_date": str(today - timedelta(days=5)),
                    "next_followup_date": date_in_3_days,
                    "notes": "Follow up on round 2 results"
                },
                {
                    "id": "3",
                    "company": "Adobe",
                    "role": "Frontend Intern",
                    "stage": "applied",
                    "applied_date": str(today - timedelta(days=2)),
                    "next_followup_date": date_in_25_days,
                    "notes": "Follow up scheduled far in advance"
                }
            ]
        }
        save_job_applications(test_data)

        tool = ListPendingFollowupsTool()
        res = tool.execute(within_days=7)

        self.assertEqual(res["status"], "success")
        followups = res["followups"]
        self.assertEqual(len(followups), 2)  # Amazon (18 days old) and Microsoft (due in 3 days)

        companies = [f["company"] for f in followups]
        self.assertIn("Amazon", companies)
        self.assertIn("Microsoft", companies)
        self.assertNotIn("Adobe", companies)

        # Amazon should be auto_suggested and marked overdue
        amazon_item = next(f for f in followups if f["company"] == "Amazon")
        self.assertEqual(amazon_item["type"], "auto_suggested")
        self.assertTrue(amazon_item["is_overdue"])
        self.assertEqual(amazon_item["days_since_applied"], 18)

    def test_get_application_stats_tally(self):
        """Tests that get_application_stats tallies each stage correctly."""
        test_data = {
            "applications": [
                {"id": "1", "company": "A", "stage": "applied"},
                {"id": "2", "company": "B", "stage": "applied"},
                {"id": "3", "company": "C", "stage": "applied"},
                {"id": "4", "company": "D", "stage": "oa_test"},
                {"id": "5", "company": "E", "stage": "interview"},
                {"id": "6", "company": "F", "stage": "interview"},
                {"id": "7", "company": "G", "stage": "offer"},
                {"id": "8", "company": "H", "stage": "rejected"},
                {"id": "9", "company": "I", "stage": "rejected"},
                {"id": "10", "company": "J", "stage": "ghosted"},
            ]
        }
        save_job_applications(test_data)

        tool = GetApplicationStatsTool()
        res = tool.execute()

        self.assertEqual(res["status"], "success")
        self.assertEqual(res["total_applications"], 10)
        counts = res["stage_counts"]
        self.assertEqual(counts["applied"], 3)
        self.assertEqual(counts["oa_test"], 1)
        self.assertEqual(counts["interview"], 2)
        self.assertEqual(counts["offer"], 1)
        self.assertEqual(counts["rejected"], 2)
        self.assertEqual(counts["ghosted"], 1)

        self.assertIn("3 applied", res["summary"])
        self.assertIn("2 in interview", res["summary"])
        self.assertIn("1 offer", res["summary"])

    def test_daily_brief_includes_job_followups(self):
        """Tests that daily brief surfaces job application follow-ups when skill is present."""
        manager = SkillManager()
        manager.discover_and_load_skills()

        today = datetime.now().date()
        test_data = {
            "applications": [
                {
                    "id": "job-1",
                    "company": "DeepMind",
                    "role": "Research Engineer Intern",
                    "stage": "interview",
                    "applied_date": str(today - timedelta(days=7)),
                    "next_followup_date": str(today + timedelta(days=1)),
                    "notes": "Follow up after interview"
                }
            ]
        }
        save_job_applications(test_data)

        brief_tool = GetDailyBriefTool()
        res = brief_tool.execute(verbose=False)

        self.assertEqual(res["status"], "success")
        self.assertIn("DeepMind", res["brief_text"])
        self.assertIn("job application follow-up", res["brief_text"].lower())
        self.assertIsNotNone(res["raw_data"]["job_followups"])


if __name__ == "__main__":
    unittest.main()
