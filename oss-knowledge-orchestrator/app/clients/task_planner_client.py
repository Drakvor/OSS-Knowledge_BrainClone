"""
HTTP client for Task Planner service
"""

import logging
import os
from typing import Dict, Any, Optional
from app.utils.base_http_client import BaseHTTPClient

logger = logging.getLogger(__name__)

class TaskPlannerClient(BaseHTTPClient):
    """HTTP client for Task Planner service"""
    
    def __init__(self, base_url: str = None):
        super().__init__(
            base_url=base_url,
            timeout=120.0,  # Longer timeout for complex task planning
            env_var="TASK_PLANNER_URL"
        )
    
    async def create_plan(
        self,
        query: str,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        chat_context: Optional[Dict[str, Any]] = None,
        collection: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a task plan from a query
        
        Args:
            query: User query
            user_id: Optional user ID
            session_id: Optional session ID
            chat_context: Optional chat context
            collection: Optional collection name to search
            
        Returns:
            Plan dictionary with tasks
        """
        return await self._request(
            "POST",
            "/plan",
            json_data={
                "query": query,
                "user_id": user_id,
                "session_id": session_id,
                "chat_context": chat_context,
                "collection": collection
            }
        )
    
    async def execute_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task plan
        
        Args:
            plan: Plan dictionary (from create_plan)
            
        Returns:
            Execution result with final response
        """
        return await self._request(
            "POST",
            "/execute",
            json_data=plan
        )

