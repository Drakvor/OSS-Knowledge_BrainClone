"""
HTTP client for Mem0 service
"""

import httpx
import logging
from typing import List, Dict, Optional
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

class Mem0Client:
    """Client for communicating with Mem0 service"""
    
    def __init__(self, base_url: str = "http://localhost:8006"):
        self.base_url = base_url.rstrip('/')
        self.timeout = httpx.Timeout(30.0)
        
    async def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Optional[Dict]:
        """HTTP request helper"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if method.upper() == "GET":
                    response = await client.get(url)
                elif method.upper() == "POST":
                    response = await client.post(url, json=data)
                else:
                    return None
                
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} from {url}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error to {url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in Mem0 request to {url}: {str(e)}")
            return None
    
    async def search_user_memories(self, query: str, user_id: int, limit: int = 5) -> List[Dict]:
        """Search user memories"""
        data = {
            "query": query,
            "user_id": f"user_{user_id}"
        }
        
        result = await self._make_request("POST", "/search", data)
        
        if not result:
            return []
        
        memories_raw = result.get("results", []) if isinstance(result, dict) else result
        
        if isinstance(memories_raw, dict):
            memories = memories_raw.get("results", [])
        elif isinstance(memories_raw, list):
            memories = memories_raw
        else:
            return []
        
        if not isinstance(memories, list):
            return []
        
        return [
            memory for memory in memories 
            if isinstance(memory, dict) and memory.get("metadata", {}).get("level") == "user"
        ][:limit]
    
    async def search_session_memories(self, query: str, session_id: str, limit: int = 10) -> List[Dict]:
        """Search session memories"""
        data = {
            "query": query,
            "user_id": f"session_{session_id}"
        }
        
        result = await self._make_request("POST", "/search", data)
        
        if not result:
            return []
        
        memories_raw = result.get("results", []) if isinstance(result, dict) else result
        
        if isinstance(memories_raw, dict):
            memories = memories_raw.get("results", [])
        elif isinstance(memories_raw, list):
            memories = memories_raw
        else:
            return []
        
        if not isinstance(memories, list):
            return []
        
        return [
            memory for memory in memories 
            if isinstance(memory, dict) and memory.get("metadata", {}).get("level") == "session"
        ][:limit]
    
    async def search_combined_memories(
        self, 
        query: str, 
        user_id: int, 
        session_id: str,
        user_limit: int = 3,
        session_limit: int = 5
    ) -> Dict[str, List[Dict]]:
        """Search both user and session memories in parallel"""
        user_task = self.search_user_memories(query, user_id, user_limit)
        session_task = self.search_session_memories(query, session_id, session_limit)
        
        user_memories, session_memories = await asyncio.gather(
            user_task, session_task, return_exceptions=True
        )
        
        if isinstance(user_memories, Exception):
            user_memories = []
        
        if isinstance(session_memories, Exception):
            session_memories = []
        
        return {
            "user_memories": user_memories,
            "session_memories": session_memories
        }
    
    async def add_conversation_memory(
        self, 
        query: str, 
        response: str, 
        user_id: int, 
        session_id: str,
        is_important: bool = False
    ) -> bool:
        """Add conversation to mem0 with inference for important conversations"""
        session_metadata = {
            "type": "conversation_context",
            "session_id": session_id,
            "level": "session",
            "timestamp": datetime.now().isoformat()
        }
        
        session_data = {
            "messages": [
                {"role": "user", "content": query},
                {"role": "assistant", "content": response}
            ],
            "user_id": f"session_{session_id}",
            "metadata": session_metadata,
            "infer": False
        }
        
        session_result = await self._make_request("POST", "/memories", session_data)
        session_success = session_result is not None
        
        user_success = True
        if is_important:
            user_metadata = {
                "type": "important_conversation",
                "session_id": session_id,
                "level": "user",
                "confidence": 0.9,
                "timestamp": datetime.now().isoformat()
            }
            
            user_data = {
                "messages": [
                    {"role": "user", "content": query},
                    {"role": "assistant", "content": response}
                ],
                "user_id": f"user_{user_id}",
                "metadata": user_metadata,
                "infer": True  # Trigger mem0 inference for important conversations
            }
            
            user_result = await self._make_request("POST", "/memories", user_data)
            user_success = user_result is not None
        
        return session_success and user_success
    
    async def health_check(self) -> bool:
        """Check Mem0 service health"""
        result = await self._make_request("GET", "/health")
        if result:
            status = result.get("status") == "healthy"
            memory_status = result.get("memory_engine") == "available"
            return status and memory_status
        return False

