
import sqlite3
import os
import logging
from typing import Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class Database:
    """
    Handles the connection to the SQLite database and table creation.
    """
    def __init__(self, db_path: str = "data/sera.db"):
        """
        Initializes the Database object.
        Args:
            db_path (str): The path to the SQLite database file.
        """
        # Ensure the data directory exists
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    @contextmanager
    def get_connection(self):
        """
        Provides a transactional database connection as a context manager.
        This ensures the connection is properly closed and transactions
        are committed or rolled back automatically.
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            logger.debug("Database connection opened.")
            yield conn
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}", exc_info=True)
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
                logger.debug("Database connection closed.")

    def create_tables(self):
        """
        Creates the necessary tables in the database if they don't exist.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id INTEGER,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        tool_calls TEXT,
                        tool_call_id TEXT,
                        name TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES sessions (id)
                    )
                """)
                # Auto-migrate columns if table already existed without them
                cursor.execute("PRAGMA table_info(messages)")
                existing_cols = [row["name"] for row in cursor.fetchall()]
                for col in ["tool_calls", "tool_call_id", "name"]:
                    if col not in existing_cols:
                        cursor.execute(f"ALTER TABLE messages ADD COLUMN {col} TEXT")
                logger.info("Tables created or verified.")
        except sqlite3.Error as e:
            logger.error(f"Error creating tables: {e}")
            raise

db = Database()
