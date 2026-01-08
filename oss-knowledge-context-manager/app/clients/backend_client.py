"""
HTTP client for Backend API
"""

import httpx
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class BackendClient:
    """Client for communicating with Backend service"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url.rstrip('/')
        self.timeout = httpx.Timeout(30.0)
        
    async def _make_request(self, method: str, endpoint: str, params: Dict = None, headers: Dict = None) -> Optional[Dict]:
        """HTTP request helper"""
        url = f"{self.base_url}{endpoint}"
        request_headers = headers or {}
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if method.upper() == "GET":
                    response = await client.get(url, params=params, headers=request_headers)
                else:
                    return None
                
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            error_text = e.response.text[:500] if e.response.text else "No error text"
            logger.error(f"HTTP error {e.response.status_code} from {url}: {error_text}")
            if e.response.status_code == 401:
                logger.error(f"Authentication required for {url} - Backend requires auth token")
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error to {url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in Backend request to {url}: {str(e)}")
            return None
    
    async def get_chat_messages(self, session_id: str, limit: int = 6) -> List[Dict]:
        """Get recent chat messages for a session (sliding window)"""
        # Backend endpoint: GET /chat/sessions/{sessionId}/messages/ordered
        # Note: Backend returns all messages, we'll take the last N
        logger.debug(f"Requesting messages for session {session_id} with limit {limit}")
        result = await self._make_request(
            "GET",
            f"/chat/sessions/{session_id}/messages/ordered"
        )
        
        if not result:
            logger.warning(f"No messages retrieved for session {session_id} (result is None or empty)")
            return []
        
        # Convert Backend response to our format
        messages = []
        if isinstance(result, list):
            # Take the last N messages (most recent)
            recent_messages = result[-limit:] if len(result) > limit else result
            logger.info(f"Retrieved {len(result)} total messages from Backend, using last {len(recent_messages)} for session {session_id}")
            for msg in recent_messages:
                messages.append({
                    "role": msg.get("messageType", "user"),
                    "content": msg.get("content", ""),
                    "department_id": msg.get("departmentId")
                })
        else:
            logger.warning(f"Unexpected response format for session {session_id}: {type(result)}, value: {result}")
        
        return messages
    
    async def get_session_summary(self, session_id: str) -> Optional[str]:
        """Get session summary if available"""
        # Backend endpoint: GET /chat/sessions/{id}
        result = await self._make_request("GET", f"/chat/sessions/{session_id}")
        
        if result and result.get("summary"):
            return result.get("summary")
        
        return None

