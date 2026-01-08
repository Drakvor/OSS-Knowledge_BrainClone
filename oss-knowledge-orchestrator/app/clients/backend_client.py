"""
HTTP client for Backend (Java) service
"""

import logging
import os
from typing import Dict, Any, Optional, List
from app.utils.base_http_client import BaseHTTPClient

logger = logging.getLogger(__name__)

class BackendClient(BaseHTTPClient):
    """HTTP client for Backend service"""
    
    def __init__(self, base_url: str = None):
        super().__init__(
            base_url=base_url,
            timeout=30.0,
            env_var="BACKEND_SERVICE_URL"
        )
    
    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        department_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Save a chat message to the backend
        
        Args:
            session_id: Chat session identifier
            role: Message role ("user" or "assistant")
            content: Message content
            department_id: Optional department ID
            
        Returns:
            Saved message dictionary
        """
        return await self._request(
            "POST",
            f"/chat/sessions/{session_id}/messages",
            json_data={
                "role": role,
                "content": content,
                "departmentId": department_id
            }
        )
    
    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session information
        
        Args:
            session_id: Chat session identifier
            
        Returns:
            Session information dictionary or None
        """
        result = await self._request(
            "GET",
            f"/chat/sessions/{session_id}",
            raise_on_error=False
        )
        return result
    
    async def create_session(
        self,
        user_id: int,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new chat session
        
        Args:
            user_id: User identifier
            title: Optional session title
            
        Returns:
            Created session dictionary
        """
        return await self._request(
            "POST",
            "/chat/sessions",
            json_data={
                "userId": user_id,
                "title": title or "New Chat"
            }
        )

