"""
Pydantic models for context management
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class ChatMessage(BaseModel):
    role: str
    content: str
    department_id: Optional[int] = None

class ChatContext(BaseModel):
    session_id: str
    user_id: Optional[int] = None
    current_query: Optional[str] = None
    chat_history: List[ChatMessage] = []
    context_summary: Optional[str] = None
    user_memories: List[Dict[str, Any]] = []
    session_memories: List[Dict[str, Any]] = []
    attachments_text: List[str] = []

