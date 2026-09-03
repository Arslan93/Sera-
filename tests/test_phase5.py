import unittest
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from skills.base_skill import BaseSkill
from skills.skill_manager import SkillManager
from skills.notes_skill import AddNoteTool, ListNotesTool, NotesSkill
from voice.wake_word import WakeWordListener
from interfaces.terminal import TerminalInterface
from memory.database import Database
from memory.memory_store import MemoryStore
from core.orchestrator import Orchestrator
from core.llm_client import LLMProvider

class TestPhase5PolishAndSkills(unittest.TestCase):
    def test_notes_skill_tools(self):
        add_tool = AddNoteTool()
        list_tool = ListNotesTool()
        
        # Test add note
        add_res = add_tool.execute(title="Test Meeting", content="Discuss Phase 5 launch.")
        self.assertEqual(add_res["status"], "success")

        # Test list notes
        list_res = list_tool.execute()
        self.assertEqual(list_res["status"], "success")
        self.assertGreaterEqual(len(list_res["notes"]), 1)
        titles = [n["title"] for n in list_res["notes"]]
        self.assertIn("Test Meeting", titles)

    def test_skill_manager_discovery(self):
        manager = SkillManager()
        skills = manager.discover_and_load_skills()
        self.assertIn("quick_notes", skills)
        self.assertIn("dev_workflow", skills)
        summary = manager.get_loaded_skills_summary()
        self.assertTrue(any(s["name"] == "dev_workflow" for s in summary))

    def test_dev_workflow_tools(self):
        from skills.dev_workflow_skill import GetDevPreferencesTool, ScaffoldProjectTool
        pref_tool = GetDevPreferencesTool()
        scaffold_tool = ScaffoldProjectTool()

        # Test preferences reading
        pref_res = pref_tool.execute()
        self.assertEqual(pref_res["status"], "success")
        self.assertIn("React.js", pref_res["preferences"]["primary_stack"])

        # Test scaffold project
        with tempfile.TemporaryDirectory() as temp_dir:
            scaffold_res = scaffold_tool.execute(project_type="react_component", destination_folder=temp_dir, name="HeroCard")
            self.assertEqual(scaffold_res["status"], "success")
            hero_file = Path(temp_dir) / "HeroCard.jsx"
            self.assertTrue(hero_file.exists())
            self.assertIn("Tailwind CSS", hero_file.read_text(encoding="utf-8"))


    def test_wake_word_listener_lifecycle(self):
        mock_stt = MagicMock()
        listener = WakeWordListener(stt_instance=mock_stt, wake_words=["hey sera"])
        self.assertFalse(listener.is_listening)

        with patch("sounddevice.rec"), patch("sounddevice.wait"):
            dummy_callback = MagicMock()
            listener.start(on_wake=dummy_callback)
            self.assertTrue(listener.is_listening)
            listener.stop()
            self.assertFalse(listener.is_listening)

    from voice.voice_handler import VoiceHandler

    @patch.object(VoiceHandler, "speak_async")
    def test_terminal_phase5_commands(self, mock_speak):
        class MockLLM(LLMProvider):
            def generate_response(self, messages, tools=None, stream=False):
                class MockChoice:
                    message = MagicMock(role="assistant", content="Hello!", tool_calls=None)
                mock_res = MagicMock()
                mock_res.choices = [MockChoice()]
                return mock_res

        temp_db_fd, temp_db_path = tempfile.mkstemp(suffix='.db')
        try:
            db = Database(db_path=temp_db_path)
            memory = MemoryStore(database=db)
            orch = Orchestrator(llm_client=MockLLM(), memory=memory, system_prompt="You are SERA.")
            terminal = TerminalInterface(orch)

            # Test /skills command
            self.assertTrue(terminal._handle_command('/skills'))

            # Test /wake command
            with patch("sounddevice.rec"), patch("sounddevice.wait"):
                self.assertTrue(terminal._handle_command('/wake'))
                self.assertTrue(terminal.wake_listener.is_listening)
                self.assertTrue(terminal._handle_command('/wake'))
                self.assertFalse(terminal.wake_listener.is_listening)
        finally:
            os.close(temp_db_fd)
            if os.path.exists(temp_db_path):
                os.remove(temp_db_path)

if __name__ == '__main__':
    unittest.main()
