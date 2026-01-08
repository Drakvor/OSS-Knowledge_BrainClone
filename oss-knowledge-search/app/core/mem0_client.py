"""
Mem0 Memory Service Client

사용자별 장기 기억과 세션별 단기 기억을 관리하는 클라이언트
"""

import httpx
import logging
from typing import List, Dict, Optional
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class Mem0Service:
    """Mem0 메모리 서비스와 통신하는 클라이언트"""
    
    def __init__(self, base_url: str = "http://localhost:8005"):
        self.base_url = base_url.rstrip('/')
        self.timeout = httpx.Timeout(30.0)
        
    async def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Optional[Dict]:
        """HTTP 요청을 보내고 응답을 반환"""
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
    
    async def add_user_memory(
        self, 
        message: str, 
        user_id: int, 
        memory_type: str = "user_preference",
        category: str = "general",
        confidence: float = 0.8
    ) -> bool:
        """사용자의 장기 기억 추가"""
        metadata = {
            "type": memory_type,
            "category": category,
            "confidence": confidence,
            "source": "conversation",
            "level": "user",
            "timestamp": datetime.now().isoformat()
        }
        
        data = {
            "messages": [{"role": "user", "content": message}],
            "user_id": f"user_{user_id}",
            "metadata": metadata
        }
        
        result = await self._make_request("POST", "/memories", data)
        return result is not None
    
    async def search_user_memories(self, query: str, user_id: int, limit: int = 5) -> List[Dict]:
        """사용자의 장기 기억 검색"""
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
        ]
    
    async def add_session_memory(
        self, 
        message: str, 
        session_id: str, 
        memory_type: str = "conversation_context",
        topic: str = "general",
        message_count: int = 0
    ) -> bool:
        """세션의 단기 기억 추가"""
        metadata = {
            "type": memory_type,
            "session_id": session_id,
            "topic": topic,
            "message_count": message_count,
            "level": "session",
            "timestamp": datetime.now().isoformat()
        }
        
        data = {
            "messages": [{"role": "user", "content": message}],
            "user_id": f"session_{session_id}",
            "metadata": metadata
        }
        
        result = await self._make_request("POST", "/memories", data)
        return result is not None
    
    async def search_session_memories(self, query: str, session_id: str, limit: int = 10) -> List[Dict]:
        """세션의 단기 기억 검색"""
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
        ]
    
    async def search_combined_memories(
        self, 
        query: str, 
        user_id: int, 
        session_id: str,
        user_limit: int = 3,
        session_limit: int = 5
    ) -> Dict[str, List[Dict]]:
        """사용자 기억과 세션 기억을 통합 검색"""
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
        """대화 내용을 적절한 메모리 레벨에 저장"""
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
                "infer": True
            }
            
            user_result = await self._make_request("POST", "/memories", user_data)
            user_success = user_result is not None
        
        return session_success and user_success
    
    async def get_user_memories(self, user_id: int) -> List[Dict]:
        """사용자의 모든 메모리 조회"""
        result = await self._make_request("GET", f"/memory/get/user_{user_id}")
        if result and result.get("success"):
            memories = result.get("memories", [])
            if not isinstance(memories, list):
                return []
            return [
                memory for memory in memories 
                if isinstance(memory, dict) and memory.get("metadata", {}).get("level") == "user"
            ]
        return []
    
    async def get_session_memories(self, session_id: str) -> List[Dict]:
        """세션의 모든 메모리 조회"""
        result = await self._make_request("GET", f"/memory/get/session_{session_id}")
        if result and result.get("success"):
            memories = result.get("memories", [])
            if not isinstance(memories, list):
                return []
            return [
                memory for memory in memories 
                if isinstance(memory, dict) and memory.get("metadata", {}).get("level") == "session"
            ]
        return []
    
    async def health_check(self) -> bool:
        """Mem0 서비스 상태 확인"""
        result = await self._make_request("GET", "/health")
        if result:
            status = result.get("status") == "healthy"
            memory_status = result.get("memory_engine") == "available"
            return status and memory_status
        return False


_mem0_service_instance = None

def get_mem0_service(base_url: str = "http://localhost:8005") -> Mem0Service:
    """Mem0Service 싱글톤 인스턴스 반환"""
    global _mem0_service_instance
    if _mem0_service_instance is None:
        _mem0_service_instance = Mem0Service(base_url)
    return _mem0_service_instance
