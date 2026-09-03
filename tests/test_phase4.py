import unittest
import os
import tempfile
from pathlib import Path
from tools.coding_tools import ExecuteCodeTool, EditFileTool
from tools.file_tools import WriteFileTool

class TestPhase4Coding(unittest.TestCase):
    def setUp(self):
        self.code_tool = ExecuteCodeTool()
        self.edit_tool = EditFileTool()
        self.write_tool = WriteFileTool()

    def test_execute_python_code_success(self):
        res = self.code_tool.execute(language="python", code="print(21 * 2)")
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["exit_code"], 0)
        self.assertEqual(res["stdout"], "42")

    def test_execute_python_error_capture(self):
        res = self.code_tool.execute(language="python", code="raise ValueError('Intentional Error')")
        self.assertEqual(res["status"], "error")
        self.assertNotEqual(res["exit_code"], 0)
        self.assertIn("ValueError: Intentional Error", res["stderr"])

    def test_execute_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "test_calc.py")
            self.write_tool.execute(file_path=file_path, content="print('Calculated: 100')")
            res = self.code_tool.execute(language="python", file_path=file_path)
            self.assertEqual(res["status"], "success")
            self.assertEqual(res["stdout"], "Calculated: 100")

    def test_execute_timeout(self):
        res = self.code_tool.execute(language="python", code="import time; time.sleep(5)", timeout=1)
        self.assertEqual(res["status"], "error")
        self.assertIn("TimeoutError", res["output"])

    def test_edit_file_and_reexecute_self_debug(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "buggy.py")
            # Buggy code
            self.write_tool.execute(file_path=file_path, content="def add(a, b):\n    return a - b\n\nassert add(2, 3) == 5\nprint('Passed!')")
            
            # First execution fails
            res1 = self.code_tool.execute(language="python", file_path=file_path)
            self.assertEqual(res1["status"], "error")
            self.assertIn("AssertionError", res1["stderr"])

            # Self-debug fix with edit_tool
            edit_res = self.edit_tool.execute(file_path=file_path, target_text="return a - b", replacement_text="return a + b")
            self.assertEqual(edit_res["status"], "success")

            # Second execution passes
            res2 = self.code_tool.execute(language="python", file_path=file_path)
            self.assertEqual(res2["status"], "success")
            self.assertEqual(res2["stdout"], "Passed!")

if __name__ == '__main__':
    unittest.main()
