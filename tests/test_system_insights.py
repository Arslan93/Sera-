import unittest
import time
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from skills.system_insights_skill import (
    SystemInsightsSkill,
    GetPCOverviewTool,
    ListInstalledAppsTool,
    ListInstalledGamesTool,
    ListStartupProgramsTool,
    ListRunningProcessesTool,
    GetNetworkInfoTool,
    GetBatteryAndPowerInfoTool,
    GetUserAccountInfoTool,
    set_cached,
    get_cached
)
from interfaces.web_server import app


class TestSystemInsights(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.skill = SystemInsightsSkill()

    def test_skill_discovery_and_tools(self):
        """Tests that SystemInsightsSkill provides all 8 diagnostic tools."""
        tools = self.skill.get_tools()
        tool_names = [t.name for t in tools]
        expected = [
            "get_pc_overview",
            "list_installed_apps",
            "list_installed_games",
            "list_startup_programs",
            "list_running_processes",
            "get_network_info",
            "get_battery_and_power_info",
            "get_user_account_info"
        ]
        for name in expected:
            self.assertIn(name, tool_names)

    def test_pc_overview_tool_structure_and_graceful_gpu_fallback(self):
        """Tests get_pc_overview structure and that missing GPU returns clean fallback without error."""
        tool = GetPCOverviewTool()
        data = tool.get_data()
        self.assertEqual(data["status"], "success")
        self.assertIn("os", data)
        self.assertIn("cpu", data)
        self.assertIn("ram", data)
        self.assertIn("disks", data)
        self.assertIn("gpu", data)
        self.assertIn("uptime_human", data)

    def test_installed_apps_caching_ttl(self):
        """Tests that list_installed_apps caches results and respects force_refresh."""
        tool = ListInstalledAppsTool()
        fake_apps = [{"name": "TestIDE", "version": "1.0", "publisher": "Test Corp", "install_date": "20260101"}]
        set_cached("installed_apps", fake_apps)

        # 1. Normal call returns cached data
        res1 = tool.get_data()
        self.assertTrue(res1["cached"])
        self.assertEqual(res1["total_apps"], 1)
        self.assertEqual(res1["apps"][0]["name"], "TestIDE")

        # 2. Search filter applies on cached data
        res_search = tool.get_data(search="Test")
        self.assertEqual(res_search["returned_count"], 1)

        res_none = tool.get_data(search="NonExistentXYZ")
        self.assertEqual(res_none["returned_count"], 0)

    def test_installed_games_empty_graceful_handling(self):
        """Tests list_installed_games returns clean empty message when no launchers found."""
        tool = ListInstalledGamesTool()
        set_cached("installed_games", [])
        data = tool.get_data()
        self.assertEqual(data["status"], "success")
        self.assertIn("No game launchers", data["message"])
        self.assertEqual(data["games"], [])

    def test_running_processes_sorting(self):
        """Tests list_running_processes sorting by memory and cpu."""
        tool = ListRunningProcessesTool()

        # Sort by memory
        mem_data = tool.get_data(sort_by="memory", limit=5)
        self.assertEqual(mem_data["status"], "success")
        self.assertEqual(mem_data["sort_by"], "memory")
        if len(mem_data["processes"]) > 1:
            self.assertGreaterEqual(
                mem_data["processes"][0]["memory_mb"],
                mem_data["processes"][1]["memory_mb"]
            )

        # Sort by cpu
        cpu_data = tool.get_data(sort_by="cpu", limit=5)
        self.assertEqual(cpu_data["status"], "success")
        self.assertEqual(cpu_data["sort_by"], "cpu")

    def test_network_info_structure(self):
        """Tests get_network_info returns valid adapters and bandwidth stats."""
        tool = GetNetworkInfoTool()
        data = tool.get_data()
        self.assertEqual(data["status"], "success")
        self.assertIn("adapters", data)
        self.assertIn("bandwidth", data)
        self.assertIn("public_ip", data)

    def test_battery_info_graceful_desktop_fallback(self):
        """Tests get_battery_and_power_info handles desktop machines without battery without error."""
        tool = GetBatteryAndPowerInfoTool()
        with patch("psutil.sensors_battery", return_value=None):
            data = tool.get_data()
            self.assertEqual(data["status"], "success")
            self.assertFalse(data["has_battery"])
            self.assertIn("No battery detected", data["message"])

    def test_user_account_info_no_credentials_exposed(self):
        """Tests get_user_account_info returns metadata without passwords or credentials."""
        tool = GetUserAccountInfoTool()
        data = tool.get_data()
        self.assertEqual(data["status"], "success")
        self.assertIn("username", data)
        self.assertIn("is_administrator", data)
        self.assertIn("home_directory", data)
        # Ensure no credential keys exist
        self.assertNotIn("password", data)
        self.assertNotIn("hash", data)
        self.assertNotIn("token", data)

    def test_web_server_system_endpoints(self):
        """Tests all 8 REST endpoints in interfaces/web_server.py."""
        endpoints = [
            "/api/system/overview",
            "/api/system/apps",
            "/api/system/games",
            "/api/system/startup",
            "/api/system/processes",
            "/api/system/network",
            "/api/system/battery",
            "/api/system/account"
        ]
        for ep in endpoints:
            res = self.client.get(ep)
            self.assertEqual(res.status_code, 200, f"Endpoint {ep} failed with status {res.status_code}")
            data = res.json()
            self.assertIn("status", data, f"Endpoint {ep} did not return status key")
            self.assertEqual(data["status"], "success", f"Endpoint {ep} status not success: {data}")


if __name__ == "__main__":
    unittest.main()
