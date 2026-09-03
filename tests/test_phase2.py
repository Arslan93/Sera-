import unittest
import os
import tempfile
from unittest.mock import MagicMock, patch
from pathlib import Path

from models.message import Message
from memory.database import Database
from memory.memory_store import MemoryStore
from core.orchestrator import Orchestrator
from core.llm_client import LLMProvider
from tools.base_tool import BaseTool
from tools.tool_registry import ToolRegistry, get_default_tool_registry
from tools.app_tools import OpenAppTool, CloseAppTool
from tools.file_tools import OpenFileTool, OpenFolderTool, ListFilesTool, SearchFileTool, WriteFileTool, ReadFileTool
from tools.web_tools import SearchWebTool, OpenUrlTool
from tools.system_tools import GetSystemInfoTool
from tools.screenshot_tools import TakeScreenshotTool

class TestPhase2Tools(unittest.TestCase):
    def setUp(self):
        self.registry = get_default_tool_registry()

    def test_tool_registry_schemas(self):
        schemas = self.registry.get_tool_schemas()
        self.assertGreaterEqual(len(schemas), 11)
        tool_names = [s["function"]["name"] for s in schemas]
        self.assertIn("open_app", tool_names)
        self.assertIn("close_app", tool_names)
        self.assertIn("open_folder", tool_names)
        self.assertIn("open_file", tool_names)
        self.assertIn("list_files", tool_names)
        self.assertIn("search_file", tool_names)
        self.assertIn("write_file", tool_names)
        self.assertIn("read_file", tool_names)
        self.assertIn("search_web", tool_names)
        self.assertIn("open_url", tool_names)
        self.assertIn("get_system_info", tool_names)
        self.assertIn("take_screenshot", tool_names)

    def test_write_and_read_file_tool(self):
        w_tool = WriteFileTool()
        r_tool = ReadFileTool()
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "demo.html")
            code_content = "<html><body><h1>Hello World</h1></body></html>"
            w_res = w_tool.execute(file_path=file_path, content=code_content)
            self.assertEqual(w_res["status"], "success")
            self.assertTrue(os.path.exists(file_path))

            r_res = r_tool.execute(file_path=file_path)
            self.assertEqual(r_res["status"], "success")
            self.assertEqual(r_res["content"], code_content)

    @patch("os.startfile", create=True)
    def test_open_app_tool(self, mock_startfile):
        tool = OpenAppTool()
        res = tool.execute(app_name="notepad")
        self.assertEqual(res["status"], "success")

    def test_search_file_tool(self):
        tool = SearchFileTool()
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "naruto_game.exe"
            test_file.write_text("dummy binary")
            res = tool.execute(query="naruto", search_root=temp_dir)
            self.assertEqual(res["status"], "success")
            self.assertEqual(len(res["matches"]), 1)
            self.assertIn("naruto_game.exe", res["matches"][0]["name"])

    def test_system_info_tool(self):
        tool = GetSystemInfoTool()
        res = tool.execute()
        self.assertEqual(res["status"], "success")
        self.assertIn("cpu", res)
        self.assertIn("ram", res)
        self.assertIn("disk", res)

    @patch("webbrowser.open")
    def test_web_search_tool(self, mock_web_open):
        tool = SearchWebTool()
        res = tool.execute(query="python programming")
        self.assertEqual(res["status"], "success")
        mock_web_open.assert_called_once()

    @patch("webbrowser.open")
    def test_open_url_tool(self, mock_web_open):
        tool = OpenUrlTool()
        res = tool.execute(url="https://github.com")
        self.assertEqual(res["status"], "success")
        mock_web_open.assert_called_once_with("https://github.com")

    def test_list_files_tool(self):
        tool = ListFilesTool()
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test file
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("hello")
            res = tool.execute(folder_path=temp_dir)
            self.assertEqual(res["status"], "success")
            self.assertEqual(res["total_items"], 1)
            self.assertEqual(res["items"][0]["name"], "test.txt")

    @patch("pyautogui.screenshot")
    def test_take_screenshot_tool(self, mock_screenshot):
        mock_img = MagicMock()
        mock_screenshot.return_value = mock_img
        tool = TakeScreenshotTool()
        res = tool.execute(custom_name="test_shot")
        self.assertEqual(res["status"], "success")
        mock_img.save.assert_called_once()
        self.assertTrue(res["filename"].startswith("test_shot_"))

    def test_orchestrator_tool_calling_loop(self):
        # Test full orchestrator tool execution loop
        class MockToolLLMProvider(LLMProvider):
            def __init__(self):
                self.call_count = 0

            def generate_response(self, messages, tools=None, stream=False):
                self.call_count += 1
                if self.call_count == 1:
                    # First turn: LLM emits tool call
                    class MockFunction:
                        name = "get_system_info"
                        arguments = "{}"
                    class MockToolCall:
                        id = "call_sys_1"
                        type = "function"
                        function = MockFunction()
                    class MockMessage:
                        role = "assistant"
                        content = None
                        tool_calls = [MockToolCall()]
                    class MockChoice:
                        message = MockMessage()
                    mock_resp = MagicMock()
                    mock_resp.choices = [MockChoice()]
                    return mock_resp
                else:
                    # Second turn: LLM receives tool output and returns final answer object
                    class MockMessageFinal:
                        role = "assistant"
                        content = "Your CPU usage is currently 15%."
                        tool_calls = None
                    class MockChoiceFinal:
                        message = MockMessageFinal()
                    mock_resp_final = MagicMock()
                    mock_resp_final.choices = [MockChoiceFinal()]
                    return mock_resp_final

        temp_db_fd, temp_db_path = tempfile.mkstemp(suffix='.db')
        try:
            db = Database(db_path=temp_db_path)
            memory = MemoryStore(database=db)
            mock_llm = MockToolLLMProvider()
            orchestrator = Orchestrator(
                llm_client=mock_llm,
                memory=memory,
                tool_registry=self.registry,
                system_prompt="You are SERA."
            )

            response_stream = orchestrator.handle_user_message("What is my CPU usage?")
            final_text = "".join(list(response_stream))
            self.assertEqual(final_text, "Your CPU usage is currently 15%.")

            # Check messages in memory
            history = memory.get_conversation_history(orchestrator.session_id)
            self.assertEqual(len(history), 4) # user -> assistant(tool_call) -> tool(result) -> assistant(final)
            self.assertEqual(history[0].role, "user")
            self.assertEqual(history[1].role, "assistant")
            self.assertEqual(history[2].role, "tool")
            self.assertEqual(history[3].role, "assistant")
            self.assertEqual(history[3].content, "Your CPU usage is currently 15%.")
        finally:
            os.close(temp_db_fd)
            if os.path.exists(temp_db_path):
                os.remove(temp_db_path)

if __name__ == '__main__':
    unittest.main()
