
import logging
import json
from typing import List
from models.message import Message
from memory.database import db

logger = logging.getLogger(__name__)

class MemoryStore:
    """
    Handles all database operations for sessions and messages.
    """

    def __init__(self, database=db):
        self.db = database
        # Ensure tables are created on startup
        self.db.create_tables()

    def create_session(self) -> int:
        """
        Creates a new session in the database.
        Returns:
            int: The ID of the newly created session.
        """
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO sessions DEFAULT VALUES")
                session_id = cursor.lastrowid
                logger.info(f"Created new session with ID: {session_id}")
                return session_id
        except Exception as e:
            logger.error(f"Failed to create session: {e}", exc_info=True)
            raise

    def save_message(self, message: Message):
        """
        Saves a message to the database for a given session.
        """
        try:
            with self.db.get_connection() as conn:
                tool_calls_json = None
                if message.tool_calls:
                    # Pydantic models need to be converted to dicts for JSON serialization
                    tool_calls_list = [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                        }
                        for tc in message.tool_calls
                    ]
                    tool_calls_json = json.dumps(tool_calls_list)

                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO messages (session_id, role, content, tool_calls, tool_call_id, name) VALUES (?, ?, ?, ?, ?, ?)",
                    (message.session_id, message.role, message.content, tool_calls_json, message.tool_call_id, message.name)
                )
                # Also update the session's updated_at timestamp
                cursor.execute("UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (message.session_id,))
                logger.debug(f"Saved message for session {message.session_id}")
        except Exception as e:
            logger.error(f"Failed to save message for session {message.session_id}: {e}", exc_info=True)
            raise

    def get_conversation_history(self, session_id: int, limit: int = 20) -> List[Message]:
        """
        Retrieves the recent conversation history for a given session.
        """
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, role, content, created_at, tool_calls, tool_call_id, name FROM messages
                    WHERE session_id = ? ORDER BY id DESC LIMIT ?
                    """,
                    (session_id, limit)
                )
                rows = cursor.fetchall()
                # Reverse the list to have the oldest message first
                history = []
                for row in reversed(rows):
                    tool_calls = None
                    if row['tool_calls']:
                        tool_calls = json.loads(row['tool_calls'])

                    msg = Message(session_id=session_id, role=row['role'], content=row['content'], tool_calls=tool_calls, tool_call_id=row['tool_call_id'], name=row['name'])
                    history.append(msg)
                return history
        except Exception as e:
            logger.error(f"Failed to retrieve history for session {session_id}: {e}", exc_info=True)
            raise

    def list_sessions(self):
        """
        Lists all conversation sessions.
        """
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, created_at, updated_at FROM sessions ORDER BY updated_at DESC")
                sessions = [dict(row) for row in cursor.fetchall()]
                return sessions
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}", exc_info=True)
            raise

memory_store = MemoryStore()
