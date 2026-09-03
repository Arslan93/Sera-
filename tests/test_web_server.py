import unittest
from fastapi.testclient import TestClient
from interfaces.web_server import app

class TestWebServer(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_serve_index_html(self):
        """Tests that root endpoint serves the web frontend."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("SERA", response.text)

    def test_get_skills_api(self):
        """Tests GET /api/skills endpoint."""
        response = self.client.get("/api/skills")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("skills", data)
        self.assertTrue(any(s["name"] == "crm_business" for s in data["skills"]))

    def test_get_system_info_api(self):
        """Tests GET /api/system-info endpoint."""
        response = self.client.get("/api/system-info")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("cpu", data)
        self.assertIn("ram", data)

    def test_get_leads_api(self):
        """Tests GET /api/leads endpoint."""
        response = self.client.get("/api/leads")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("leads", data)

    def test_get_profile_api(self):
        """Tests GET /api/profile endpoint."""
        response = self.client.get("/api/profile")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("profile", data)
        self.assertIn("preferences", data)

    def test_toggle_skill_api(self):
        """Tests POST /api/skills/toggle endpoint."""
        response = self.client.post("/api/skills/toggle", json={"skill_name": "quick_notes", "enable": False})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["enabled"])

        # Re-enable
        res_re = self.client.post("/api/skills/toggle", json={"skill_name": "quick_notes", "enable": True})
        self.assertEqual(res_re.status_code, 200)
        self.assertTrue(res_re.json()["enabled"])

    def test_serve_static_assets(self):
        """Tests that app.css and app.js are served correctly."""
        res_css = self.client.get("/app.css")
        self.assertEqual(res_css.status_code, 200)
        self.assertIn("surface-base", res_css.text)

        res_js = self.client.get("/app.js")
        self.assertEqual(res_js.status_code, 200)
        self.assertIn("SERA", res_js.text)

    def test_daily_brief_api(self):
        """Tests GET /api/daily-brief endpoint."""
        response = self.client.get("/api/daily-brief")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "success")
        self.assertIn("brief_text", data)

    def test_job_tracker_endpoints(self):
        """Tests GET /api/jobs, /api/jobs/stats, and /api/jobs/followups."""
        res_jobs = self.client.get("/api/jobs")
        self.assertEqual(res_jobs.status_code, 200)
        self.assertIn("applications", res_jobs.json())

        res_stats = self.client.get("/api/jobs/stats")
        self.assertEqual(res_stats.status_code, 200)
        self.assertEqual(res_stats.json().get("status"), "success")

        res_followups = self.client.get("/api/jobs/followups")
        self.assertEqual(res_followups.status_code, 200)
        self.assertEqual(res_followups.json().get("status"), "success")

    def test_study_session_endpoints(self):
        """Tests GET /api/study/status and /api/study/stats."""
        res_status = self.client.get("/api/study/status")
        self.assertEqual(res_status.status_code, 200)
        self.assertIn("recent_sessions", res_status.json())

        res_stats = self.client.get("/api/study/stats")
        self.assertEqual(res_stats.status_code, 200)
        self.assertEqual(res_stats.json().get("status"), "success")

    def test_clipboard_and_read_later_endpoints(self):
        """Tests GET /api/captures, /api/read-later, and /api/clipboard/status."""
        res_cap = self.client.get("/api/captures")
        self.assertEqual(res_cap.status_code, 200)
        self.assertIn("captures", res_cap.json())

        res_rl = self.client.get("/api/read-later")
        self.assertEqual(res_rl.status_code, 200)
        self.assertIn("links", res_rl.json())

        res_status = self.client.get("/api/clipboard/status")
        self.assertEqual(res_status.status_code, 200)
        self.assertIn("listening", res_status.json())


if __name__ == '__main__':
    unittest.main()

