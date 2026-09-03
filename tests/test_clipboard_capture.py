import unittest
import os
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

from skills.base_skill import BaseSkill
from skills.skill_manager import SkillManager
from skills.clipboard_capture_skill import (
    classify_content,
    file_captured_content,
    ProcessClipboardCaptureTool,
    AddLinkToReadLaterTool,
    ClipboardCaptureSkill,
    CAPTURES_FILE,
    READ_LATER_FILE
)
from skills.notes_skill import NOTES_FILE
from core.clipboard_listener import ClipboardCaptureListener


class TestClipboardCapture(unittest.TestCase):
    def setUp(self):
        self.orig_captures = None
        if CAPTURES_FILE.exists():
            try:
                with open(CAPTURES_FILE, "r", encoding="utf-8") as f:
                    self.orig_captures = json.load(f)
            except Exception:
                self.orig_captures = None

        self.orig_read_later = None
        if READ_LATER_FILE.exists():
            try:
                with open(READ_LATER_FILE, "r", encoding="utf-8") as f:
                    self.orig_read_later = json.load(f)
            except Exception:
                self.orig_read_later = None

        self.orig_notes = None
        if NOTES_FILE.exists():
            try:
                with open(NOTES_FILE, "r", encoding="utf-8") as f:
                    self.orig_notes = json.load(f)
            except Exception:
                self.orig_notes = None

        # Clean slate
        CAPTURES_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CAPTURES_FILE, "w", encoding="utf-8") as f:
            json.dump({"captures": []}, f)
        with open(READ_LATER_FILE, "w", encoding="utf-8") as f:
            json.dump({"links": []}, f)

    def tearDown(self):
        if self.orig_captures is not None:
            with open(CAPTURES_FILE, "w", encoding="utf-8") as f:
                json.dump(self.orig_captures, f, indent=2)
        elif CAPTURES_FILE.exists():
            CAPTURES_FILE.unlink(missing_ok=True)

        if self.orig_read_later is not None:
            with open(READ_LATER_FILE, "w", encoding="utf-8") as f:
                json.dump(self.orig_read_later, f, indent=2)
        elif READ_LATER_FILE.exists():
            READ_LATER_FILE.unlink(missing_ok=True)

        if self.orig_notes is not None:
            with open(NOTES_FILE, "w", encoding="utf-8") as f:
                json.dump(self.orig_notes, f, indent=2)

    def test_skill_discovery(self):
        """Tests that ClipboardCaptureSkill is discovered by SkillManager with its tools."""
        manager = SkillManager()
        skills = manager.discover_and_load_skills()
        self.assertIn("clipboard_capture", skills)
        skill = skills["clipboard_capture"]
        self.assertIsInstance(skill, BaseSkill)
        tools = skill.get_tools()
        self.assertEqual(len(tools), 2)
        tool_names = [t.name for t in tools]
        self.assertIn("process_clipboard_capture", tool_names)
        self.assertIn("add_link_to_read_later", tool_names)

    def test_classification_heuristics(self):
        """Tests that heuristic classification correctly identifies links, code, tasks, and notes."""
        # 1. Links
        self.assertEqual(classify_content("https://arxiv.org/abs/2303.08774"), "link")
        self.assertEqual(classify_content("http://github.com/Arslan93/Jarvis"), "link")
        self.assertEqual(classify_content("www.google.com"), "link")

        # 2. Code
        python_snippet = (
            "def calculate_total(items):\n"
            "    return sum(item['price'] for item in items)"
        )
        self.assertEqual(classify_content(python_snippet), "code")

        js_snippet = "const handleSubmit = async (e) => { e.preventDefault(); console.log(data); };"
        self.assertEqual(classify_content(js_snippet), "code")

        html_snippet = "<div class='container'><p>Hello World</p></div>"
        self.assertEqual(classify_content(html_snippet), "code")

        # 3. Tasks
        self.assertEqual(classify_content("TODO: Review RGPV syllabus for semester 5"), "task")
        self.assertEqual(classify_content("[ ] Email internship recruiter at Shippoz"), "task")
        self.assertEqual(classify_content("Remember to update resume with DeepGuard project"), "task")

        # 4. Notes
        self.assertEqual(classify_content("B-Trees maintain sorted data and allow searches in logarithmic time."), "note")
        self.assertEqual(classify_content("Discussed architecture for autonomous agent with Arslan."), "note")

    def test_file_captured_content_and_captures_audit_logging(self):
        """Tests that all captured content is audited in captures.json and routed appropriately."""
        # 1. Link capture
        link_res = file_captured_content("https://fastapi.tiangolo.com/tutorial/")
        self.assertEqual(link_res["status"], "success")
        self.assertEqual(link_res["classification"], "link")
        self.assertIn("read_later.json", link_res["filed_to"])

        # Check read_later.json
        with open(READ_LATER_FILE, "r", encoding="utf-8") as f:
            read_later_data = json.load(f)
            self.assertEqual(len(read_later_data["links"]), 1)
            self.assertEqual(read_later_data["links"][0]["url"], "https://fastapi.tiangolo.com/tutorial/")

        # 2. Code capture
        code_res = file_captured_content("import psutil\ndef get_stats(): return psutil.cpu_percent()")
        self.assertEqual(code_res["status"], "success")
        self.assertEqual(code_res["classification"], "code")
        self.assertIn("notes.json", code_res["filed_to"])

        # 3. Task capture
        task_res = file_captured_content("TODO: Prepare presentation slides for hackathon")
        self.assertEqual(task_res["status"], "success")
        self.assertEqual(task_res["classification"], "task")
        self.assertIn("notes.json", task_res["filed_to"])

        # 4. Check captures.json audit trail
        with open(CAPTURES_FILE, "r", encoding="utf-8") as f:
            captures_data = json.load(f)
            self.assertEqual(len(captures_data["captures"]), 3)
            classes = [c["classification"] for c in captures_data["captures"]]
            self.assertIn("link", classes)
            self.assertIn("code", classes)
            self.assertIn("task", classes)

    def test_process_clipboard_capture_tool(self):
        """Tests ProcessClipboardCaptureTool execution."""
        tool = ProcessClipboardCaptureTool()
        res = tool.execute(raw_content="https://news.ycombinator.com")
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["classification"], "link")

    def test_add_link_to_read_later_tool(self):
        """Tests AddLinkToReadLaterTool saves URL and title."""
        tool = AddLinkToReadLaterTool()
        res = tool.execute(url="https://react.dev", title="React Docs")
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["link"]["url"], "https://react.dev")
        self.assertEqual(res["link"]["title"], "React Docs")

    def test_debounce_logic_prevents_rapid_double_trigger(self):
        """Tests that ClipboardCaptureListener ignores triggers within the debounce window."""
        mock_callback = MagicMock()
        listener = ClipboardCaptureListener(
            on_capture=mock_callback,
            debounce_seconds=2.0
        )

        with patch("pyperclip.paste", return_value="Test clipboard text"):
            # First trigger should process
            listener._handle_trigger()
            time.sleep(0.1)  # allow thread to start
            self.assertEqual(mock_callback.call_count, 1)

            # Rapid second trigger (0.1s later) within 2.0s debounce should be ignored
            listener._handle_trigger()
            self.assertEqual(mock_callback.call_count, 1)

            # Advance past cooldown window
            listener.last_trigger_time = time.time() - 3.0
            listener._handle_trigger()
            time.sleep(0.1)
            self.assertEqual(mock_callback.call_count, 2)

    def test_empty_clipboard_ignored(self):
        """Tests that empty or whitespace-only clipboard content is ignored."""
        mock_callback = MagicMock()
        listener = ClipboardCaptureListener(on_capture=mock_callback)

        with patch("pyperclip.paste", return_value="   \n\t  "):
            listener._handle_trigger()
            self.assertEqual(mock_callback.call_count, 0)

    @patch("keyboard.add_hotkey")
    @patch("keyboard.remove_hotkey")
    def test_listener_start_and_stop_lifecycle(self, mock_remove, mock_add):
        """Tests listener start and stop lifecycle with mocked keyboard library."""
        listener = ClipboardCaptureListener(hotkey="ctrl+shift+s")

        self.assertFalse(listener.is_listening)
        started = listener.start()
        self.assertTrue(started)
        self.assertTrue(listener.is_listening)
        mock_add.assert_called_once()

        # Stop
        listener.stop()
        self.assertFalse(listener.is_listening)
        mock_remove.assert_called_once_with("ctrl+shift+s")


if __name__ == "__main__":
    unittest.main()
