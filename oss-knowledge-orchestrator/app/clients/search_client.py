"""
HTTP client for Search Server service
"""

import logging
import os
from typing import Dict, Any, Optional
from app.utils.base_http_client import BaseHTTPClient

logger = logging.getLogger(__name__)

class SearchClient(BaseHTTPClient):
    """HTTP client for Search Server service"""
    
    def __init__(self, base_url: str = None):
        super().__init__(
            base_url=base_url,
            timeout=60.0,  # Longer timeout for search operations
            env_var="SEARCH_SERVER_URL"
        )
    
    async def search_and_generate(
        self,
        query: str,
        collection: str = "general",
        limit: int = 10,
        threshold: float = 0.7,
        chat_context: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Perform RAG search and generate response
        
        Args:
            query: Search query
            collection: Collection to search
            limit: Maximum number of results
            threshold: Similarity threshold
            chat_context: Optional chat context
            user_id: Optional user ID
            session_id: Optional session ID
            stream: Whether to stream response
            
        Returns:
            Dictionary with search results and generated response
        """
        return await self._request(
            "POST",
            "/search/response",
            json_data={
                "query": query,
                "collection": collection,
                "limit": limit,
                "threshold": threshold,
                "include_metadata": True,
                "include_content": True,
                "max_tokens": 1000,
                "temperature": 0.7,
                "chat_context": chat_context,
                "user_id": user_id,
                "session_id": session_id,
                "stream": stream
            }
        )

