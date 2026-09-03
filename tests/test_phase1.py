import unittest
import os
import tempfile
from unittest.mock import MagicMock
from models.message import Message
from memory.database import Database
from memory.memory_store import MemoryStore
from core.orchestrator import Orchestrator
from interfaces.terminal import TerminalInterface
from core.llm_client import LLMProvider

class MockLLMProvider(LLMProvider):
    def __init__(self, response_text="Hello! I am SERA."):
        self.response_text = response_text

    def generate_response(self, messages, tools=None, stream=False):
        class MockDelta:
            def __init__(self, content):
                self.content = content
        class MockChoice:
            def __init__(self, content):
                self.delta = MockDelta(content)
                self.message = MagicMock(role="assistant", content=content, tool_calls=None)
        class MockChunk:
            def __init__(self, content):
                self.choices = [MockChoice(content)]

        if stream:
            def chunk_gen():
                words = self.response_text.split()
                for i, w in enumerate(words):
                    yield MockChunk(w + (" " if i < len(words) - 1 else ""))
            return chunk_gen()
        else:
            mock_resp = MagicMock()
            mock_resp.choices = [MockChoice(self.response_text)]
            return mock_resp

class TestPhase1(unittest.TestCase):
    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix='.db')
        self.db = Database(db_path=self.temp_db_path)
        self.memory = MemoryStore(database=self.db)
        self.llm_client = MockLLMProvider()
        self.orchestrator = Orchestrator(
            llm_client=self.llm_client,
            memory=self.memory,
            tool_registry=None,
            system_prompt="You are SERA."
        )

    def tearDown(self):
        try:
            os.close(self.temp_db_fd)
            if os.path.exists(self.temp_db_path):
                os.remove(self.temp_db_path)
        except Exception:
            pass

    def test_database_table_creation(self):
        self.assertTrue(os.path.exists(self.temp_db_path))
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row['name'] for row in cursor.fetchall()]
            self.assertIn('sessions', tables)
            self.assertIn('messages', tables)

    def test_memory_store_session_and_messages(self):
        session_id = self.memory.create_session()
        self.assertIsInstance(session_id, int)

        user_msg = Message(session_id=session_id, role="user", content="Hi Sera")
        self.memory.save_message(user_msg)

        assistant_msg = Message(session_id=session_id, role="assistant", content="Hello Sir, how can I help?")
        self.memory.save_message(assistant_msg)

        history = self.memory.get_conversation_history(session_id)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].role, "user")
        self.assertEqual(history[0].content, "Hi Sera")
        self.assertEqual(history[1].role, "assistant")
        self.assertEqual(history[1].content, "Hello Sir, how can I help?")

    def test_orchestrator_handle_user_message(self):
        response_stream = self.orchestrator.handle_user_message("Tell me about yourself")
        chunks = list(response_stream)
        full_response = "".join(chunks)
        self.assertEqual(full_response, "Hello! I am SERA.")

        history = self.memory.get_conversation_history(self.orchestrator.session_id)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].role, "user")
        self.assertEqual(history[0].content, "Tell me about yourself")
        self.assertEqual(history[1].role, "assistant")
        self.assertEqual(history[1].content, "Hello! I am SERA.")

    def test_terminal_interface_commands(self):
        terminal = TerminalInterface(self.orchestrator)
        self.assertTrue(terminal._handle_command('/help'))
        old_session = self.orchestrator.session_id
        self.assertTrue(terminal._handle_command('/new'))
        self.assertNotEqual(old_session, self.orchestrator.session_id)
        self.assertTrue(terminal._handle_command('/history'))
        self.assertFalse(terminal._handle_command('not_a_command'))

if __name__ == '__main__':
    unittest.main()
