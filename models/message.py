
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Any

@dataclass
class Message:
    """
    Represents a message in a conversation.
    """
    role: str # 'user', 'assistant', or 'tool'
    content: Optional[str]
    session_id: Optional[int] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    # For tool calls
    tool_calls: Optional[List[Any]] = None
    # For tool responses
    tool_call_id: Optional[str] = None
    name: Optional[str] = None
