import unittest
import os
import tempfile
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from core.orchestrator import Orchestrator, MAX_DEBUG_ITERATIONS
from core.llm_client import LLMProvider, GroqProvider
from memory.database import Database
from memory.memory_store import MemoryStore
from tools.tool_registry import ToolRegistry, BaseTool
from tools.file_tools import WriteFileTool, ReadFileTool, DeleteFileTool, MoveFileTool
from tools.app_tools import CloseAppTool
from skills.skill_manager import SkillManager
from skills.crm_skill import CreateLeadTool, ListLeadsTool, UpdateLeadStatusTool

class DummyTool(BaseTool):
    name = "dummy_calculator"
    description = "Adds two numbers."
    parameters = {
        "type": "object",
        "properties": {
            "a": {"type": "integer"},
            "b": {"type": "integer"}
        },
        "required": ["a", "b"]
    }
    def execute(self, a: int, b: int):
        return {"status": "success", "result": a + b}

class FailingTool(BaseTool):
    name = "failing_tool"
    description = "Always fails to test safety bounds."
    parameters = {"type": "object", "properties": {}}
    def execute(self):
        return {"status": "error", "error": "Persistent failure"}

class TestE2EIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix='.db')
        self.db = Database(db_path=self.temp_db_path)
        self.memory = MemoryStore(database=self.db)
        self.tool_reg = ToolRegistry()
        self.tool_reg.register_tool(DummyTool())

    def tearDown(self):
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_full_agentic_loop_simulation(self):
        """Tests full cycle: user prompt -> LLM emits tool call -> Tool executes -> LLM returns final answer."""
        class MockFunc:
            name = "dummy_calculator"
            arguments = json.dumps({"a": 15, "b": 27})

        class MockToolCallObj:
            id = "call_123"
            type = "function"
            function = MockFunc()

        class MockChoiceTool:
            class MockMsg:
                role = "assistant"
                content = None
                tool_calls = [MockToolCallObj()]
            message = MockMsg()

        class MockChoiceFinal:
            class MockMsg:
                role = "assistant"
                content = "The sum of 15 and 27 is 42."
                tool_calls = None
            message = MockMsg()

        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.generate_response.side_effect = [
            MagicMock(choices=[MockChoiceTool()]),
            MagicMock(choices=[MockChoiceFinal()])
        ]

        orchestrator = Orchestrator(
            llm_client=mock_llm,
            memory=self.memory,
            tool_registry=self.tool_reg,
            system_prompt="You are SERA."
        )

        responses = list(orchestrator.handle_user_message("What is 15 + 27?"))
        self.assertEqual(len(responses), 1)
        self.assertEqual(responses[0], "The sum of 15 and 27 is 42.")

        # Verify conversation memory recorded all turns (user, assistant-tool-call, tool-result, assistant-final)
        history = self.memory.get_conversation_history(orchestrator.session_id)
        self.assertEqual(len(history), 4)
        self.assertEqual(history[0].role, "user")
        self.assertEqual(history[1].role, "assistant")
        self.assertEqual(history[2].role, "tool")
        self.assertIn("42", history[2].content)
        self.assertEqual(history[3].role, "assistant")

    def test_self_debug_safety_cap_bounds(self):
        """Tests that orchestrator hits MAX_DEBUG_ITERATIONS cap and does not infinite loop."""
        self.tool_reg.register_tool(FailingTool())

        class MockFailFunc:
            name = "failing_tool"
            arguments = "{}"

        class MockFailToolCallObj:
            id = "call_fail"
            type = "function"
            function = MockFailFunc()

        class MockInfiniteFailChoice:
            class MockMsg:
                role = "assistant"
                content = None
                tool_calls = [MockFailToolCallObj()]
            message = MockMsg()

        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.generate_response.return_value = MagicMock(choices=[MockInfiniteFailChoice()])

        orchestrator = Orchestrator(
            llm_client=mock_llm,
            memory=self.memory,
            tool_registry=self.tool_reg,
            system_prompt="You are SERA."
        )

        responses = list(orchestrator.handle_user_message("Do impossible task"))
        self.assertEqual(len(responses), 1)
        self.assertIn("Self-Debug Limit Reached", responses[0])
        self.assertEqual(mock_llm.generate_response.call_count, MAX_DEBUG_ITERATIONS)

    def test_model_fallback_chain(self):
        """Tests that GroqProvider tries fallback models when primary model fails."""
        mock_client = MagicMock()
        # First model 400s, second model succeeds
        mock_success_res = MagicMock()
        mock_client.chat.completions.create.side_effect = [
            Exception("400 Model not found"),
            mock_success_res
        ]

        provider = GroqProvider(
            api_key="mock_key",
            model="invalid-primary-model",
            fallback_models=["invalid-primary-model", "llama-3.3-70b-versatile"]
        )
        provider.client = mock_client

        res = provider.generate_response([{"role": "user", "content": "Hi"}])
        self.assertEqual(res, mock_success_res)
        self.assertEqual(mock_client.chat.completions.create.call_count, 2)

    def test_file_tools_delete_and_move(self):
        """Tests DeleteFileTool, MoveFileTool, and safety blocks."""
        write_tool = WriteFileTool()
        delete_tool = DeleteFileTool()
        move_tool = MoveFileTool()

        with tempfile.TemporaryDirectory() as temp_dir:
            file_a = os.path.join(temp_dir, "file_a.txt")
            file_b = os.path.join(temp_dir, "file_b.txt")
            
            write_tool.execute(file_path=file_a, content="Test Content")
            self.assertTrue(os.path.exists(file_a))

            # Move test
            move_res = move_tool.execute(source_path=file_a, destination_path=file_b)
            self.assertEqual(move_res["status"], "success")
            self.assertFalse(os.path.exists(file_a))
            self.assertTrue(os.path.exists(file_b))

            # Delete test
            del_res = delete_tool.execute(file_path=file_b)
            self.assertEqual(del_res["status"], "success")
            self.assertFalse(os.path.exists(file_b))

    def test_close_app_system_protection(self):
        """Tests that CloseAppTool blocks attempts to kill system-critical processes."""
        close_tool = CloseAppTool()
        res_system = close_tool.execute("explorer")
        self.assertEqual(res_system["status"], "error")
        self.assertIn("blocked", res_system["message"].lower())

        res_python = close_tool.execute("python.exe")
        self.assertEqual(res_python["status"], "error")
        self.assertIn("blocked", res_python["message"].lower())

    def test_crm_skill_lifecycle(self):
        """Tests CreateLeadTool, ListLeadsTool, and UpdateLeadStatusTool."""
        create_tool = CreateLeadTool()
        list_tool = ListLeadsTool()
        update_tool = UpdateLeadStatusTool()

        c_res = create_tool.execute(
            name="Alice Enterprise",
            email="alice@enterprise.com",
            deal_value="$10,000",
            notes="Interested in AI Automation"
        )
        self.assertEqual(c_res["status"], "success")
        lead_id = c_res["lead"]["id"]

        u_res = update_tool.execute(lead_identifier=lead_id, new_status="Won", new_notes="Contract Signed")
        self.assertEqual(u_res["status"], "success")
        self.assertEqual(u_res["lead"]["status"], "Won")

        l_res = list_tool.execute(filter_status="Won")
        self.assertEqual(l_res["status"], "success")
        self.assertTrue(any(l["id"] == lead_id for l in l_res["leads"]))

    def test_skill_permission_system(self):
        """Tests enabling and disabling skills in SkillManager."""
        manager = SkillManager()
        manager.discover_and_load_skills()
        self.assertIn("crm_business", manager.loaded_skills)

        # Disable crm_business
        self.assertTrue(manager.disable_skill("crm_business"))
        self.assertFalse(manager.is_skill_enabled("crm_business"))
        self.assertIsNone(self.tool_reg.get_tool("create_lead"))

        # Re-enable crm_business
        self.assertTrue(manager.enable_skill("crm_business"))
        self.assertTrue(manager.is_skill_enabled("crm_business"))

if __name__ == '__main__':
    unittest.main()
