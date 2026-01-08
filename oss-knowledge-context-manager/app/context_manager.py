"""
Core context management logic
Handles chat context building, mem0 integration, and memory management.
"""

import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.clients.backend_client import BackendClient
from app.clients.mem0_client import Mem0Client
from app.models.context_models import ChatContext, ChatMessage

logger = logging.getLogger(__name__)

class ContextManager:
    """Manages chat context building and mem0 integration"""
    
    def __init__(
        self,
        backend_url: str = None,
        mem0_url: str = None
    ):
        self.logger = logging.getLogger(__name__)
        
        # Initialize clients
        backend_url = backend_url or os.getenv("BACKEND_URL", "http://localhost:8080")
        mem0_url = mem0_url or os.getenv("MEM0_URL", "http://localhost:8006")  # Updated to match deploy script port
        
        self.backend_client = BackendClient(backend_url)
        self.mem0_client = Mem0Client(mem0_url)
        
        # Configuration
        self.sliding_window_size = int(os.getenv("SLIDING_WINDOW_SIZE", "6"))  # Last 6 messages = 3 turns
        self.auto_save_important = os.getenv("MEM0_AUTO_SAVE_IMPORTANT", "true").lower() == "true"
        
        self.logger.info(f"Context Manager initialized - Backend: {backend_url}, Mem0: {mem0_url}")
    
    async def build_context(
        self,
        session_id: str,
        user_id: Optional[int] = None,
        current_query: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Build complete chat context:
        - Retrieve messages from Backend (sliding window)
        - Search mem0 memories (user + session)
        - Extract attachment text
        - Get context summary
        """
        self.logger.debug(f"Building context for session {session_id}, user {user_id}")
        
        # 1. Get chat history from Backend (sliding window)
        self.logger.debug(f"Retrieving chat history for session {session_id} (limit: {self.sliding_window_size})")
        chat_history = await self.backend_client.get_chat_messages(
            session_id=session_id,
            limit=self.sliding_window_size
        )
        self.logger.debug(f"Retrieved {len(chat_history)} messages from Backend for session {session_id}")
        
        # 2. Get session summary
        context_summary = await self.backend_client.get_session_summary(session_id)
        
        # 3. Search mem0 memories (if user_id provided)
        user_memories = []
        session_memories = []
        if user_id and current_query:
            memories = await self.mem0_client.search_combined_memories(
                query=current_query,
                user_id=user_id,
                session_id=session_id,
                user_limit=3,
                session_limit=5
            )
            user_memories = memories.get("user_memories", [])
            session_memories = memories.get("session_memories", [])
        
        # 4. Extract attachment text
        attachments_text = []
        if attachments:
            attachments_text = self._extract_attachment_text(attachments)
        
        # Build context object
        context = {
            "session_id": session_id,
            "user_id": user_id,
            "current_query": current_query,
            "chat_history": chat_history,
            "context_summary": context_summary,
            "user_memories": user_memories,
            "session_memories": session_memories,
            "attachments_text": attachments_text
        }
        
        self.logger.debug(f"Context built: {len(chat_history)} messages, {len(user_memories)} user memories, {len(session_memories)} session memories")
        
        return context
    
    async def add_conversation_memory(
        self,
        query: str,
        response: str,
        user_id: int,
        session_id: str,
        is_important: Optional[bool] = None
    ) -> bool:
        """
        Add conversation to mem0 with importance detection.
        If is_important is None, auto-detect based on:
        - Response length > 200
        - Keywords (좋아, 싫어, 선호, 취향, 습관)
        - Auto-save setting
        """
        # Auto-detect importance if not provided
        if is_important is None:
            response_len_check = len(response) > 200
            keyword_check = any(keyword in query.lower() for keyword in ['좋아', '싫어', '선호', '취향', '습관'])
            auto_save_check = self.auto_save_important
            
            is_important = (
                response_len_check or
                keyword_check or
                auto_save_check
            )
        
        self.logger.debug(f"Adding conversation memory - user: {user_id}, session: {session_id}, important: {is_important}")
        
        result = await self.mem0_client.add_conversation_memory(
            query=query,
            response=response,
            user_id=user_id,
            session_id=session_id,
            is_important=is_important
        )
        
        return result
    
    async def search_memories(
        self,
        query: str,
        user_id: int,
        session_id: str,
        user_limit: int = 3,
        session_limit: int = 5
    ) -> Dict[str, List[Dict]]:
        """Search mem0 memories (user + session)"""
        return await self.mem0_client.search_combined_memories(
            query=query,
            user_id=user_id,
            session_id=session_id,
            user_limit=user_limit,
            session_limit=session_limit
        )
    
    def _extract_attachment_text(self, attachments: List[Dict[str, Any]]) -> List[str]:
        """Extract text from attachments (txt, md, py, js, etc.)"""
        texts = []
        
        for attachment in attachments:
            # Handle different attachment formats
            if isinstance(attachment, dict):
                # If attachment has text content directly
                if "text" in attachment:
                    texts.append(attachment["text"])
                # If attachment has file content
                elif "content" in attachment:
                    content = attachment["content"]
                    # Check if it's a text file
                    file_type = attachment.get("type", "").lower()
                    if file_type in ["text/plain", "text/markdown", "text/x-python", "text/javascript"]:
                        texts.append(content)
                # If attachment has file path
                elif "path" in attachment:
                    # In a real implementation, read the file
                    # For now, just log
                    self.logger.debug(f"Attachment with path: {attachment.get('path')}")
        
        return texts

