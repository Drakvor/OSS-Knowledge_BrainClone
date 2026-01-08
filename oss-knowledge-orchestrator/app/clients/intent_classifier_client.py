"""
HTTP client for Intent Classifier service
"""

import logging
import os
from typing import Dict, Any, Optional
from app.utils.base_http_client import BaseHTTPClient

logger = logging.getLogger(__name__)

class IntentClassifierClient(BaseHTTPClient):
    """HTTP client for Intent Classifier service"""
    
    def __init__(self, base_url: str = None):
        super().__init__(
            base_url=base_url,
            timeout=30.0,
            env_var="INTENT_CLASSIFIER_URL"
        )
    
    async def classify_intent(
        self,
        message: str,
        chat_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Classify intent using Intent Classifier service
        
        Args:
            message: User message to classify
            chat_context: Optional chat context for classification
            
        Returns:
            Dictionary with intent and reasoning:
            {
                "intent": "CASUAL" | "COMPLEX" | "CONTEXT" | "UNKNOWN",
                "reasoning": str
            }
        """
        result = await self._request(
            "POST",
            "/classify",
            json_data={
                "message": message,
                "chat_context": chat_context
            },
            raise_on_error=False
        )
        
        # Return UNKNOWN on error
        if not result:
            return {
                "intent": "UNKNOWN",
                "reasoning": "Intent classification request failed"
            }
        return result

