"""
HTTP client for Context Manager service
"""

import logging
import os
from typing import Dict, Any, Optional, List
from app.utils.base_http_client import BaseHTTPClient

logger = logging.getLogger(__name__)

class ContextManagerClient(BaseHTTPClient):
    """HTTP client for Context Manager service"""
    
    def __init__(self, base_url: str = None):
        super().__init__(
            base_url=base_url,
            timeout=30.0,
            env_var="CONTEXT_MANAGER_URL"
        )
    
    async def build_context(
        self,
        session_id: str,
        user_id: str,
        current_query: str,
        chat_history_limit: int = 6,
        user_memory_limit: int = 3,
        session_memory_limit: int = 5,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Build chat context using Context Manager
        
        Args:
            session_id: Chat session identifier
            user_id: User identifier
            current_query: Current user query
            chat_history_limit: Number of recent messages to retrieve
            user_memory_limit: Number of user memories to retrieve
            session_memory_limit: Number of session memories to retrieve
            attachments: Optional file attachments
            
        Returns:
            Dictionary containing enriched chat context
        """
        return await self._request(
            "POST",
            "/context/build",
            json_data={
                "session_id": session_id,
                "user_id": user_id,
                "current_query": current_query,
                "chat_history_limit": chat_history_limit,
                "user_memory_limit": user_memory_limit,
                "session_memory_limit": session_memory_limit,
                "attachments": attachments or []
            }
        )
    
    async def add_memory(
        self,
        message: str,
        user_id: str,
        session_id: str,
        memory_type: str = "conversation_context",
        is_important: bool = False
    ) -> bool:
        """
        Add a memory to mem0 via Context Manager
        
        Args:
            message: Message content to store
            user_id: User identifier
            session_id: Session identifier
            memory_type: Type of memory
            is_important: Whether this is an important memory
            
        Returns:
            True if successful, False otherwise
        """
        result = await self._request(
            "POST",
            "/memory/add",
            json_data={
                "message": message,
                "user_id": user_id,
                "session_id": session_id,
                "memory_type": memory_type,
                "is_important": is_important
            },
            raise_on_error=False
        )
        return result.get("success", False) if result else False
    
    async def search_memories(
        self,
        query: str,
        user_id: str,
        session_id: str,
        user_limit: int = 3,
        session_limit: int = 5
    ) -> Dict[str, List[Dict]]:
        """
        Search memories via Context Manager
        
        Args:
            query: Search query
            user_id: User identifier
            session_id: Session identifier
            user_limit: Maximum number of user memories
            session_limit: Maximum number of session memories
            
        Returns:
            Dictionary with user_memories and session_memories
        """
        result = await self._request(
            "POST",
            "/memory/search",
            json_data={
                "query": query,
                "user_id": user_id,
                "session_id": session_id,
                "user_limit": user_limit,
                "session_limit": session_limit
            },
            raise_on_error=False
        )
        return result if result else {"user_memories": [], "session_memories": []}

