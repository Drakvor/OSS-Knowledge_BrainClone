"""
Routing logic based on intent classification
"""

import logging
from typing import Dict, Any, Optional
from app.fallback_llm import FallbackLLM

logger = logging.getLogger(__name__)

class IntentRouter:
    """Routes requests based on intent classification"""
    
    def __init__(self, fallback_llm: FallbackLLM):
        self.fallback_llm = fallback_llm
        logger.info("Intent Router initialized")
    
    async def route(
        self,
        intent: str,
        message: str,
        collection: Optional[str] = None,
        chat_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Route based on intent classification
        
        Returns:
            {
                "intent": str,
                "response": str (for CASUAL/UNKNOWN),
                "route_to": str (for DIRECT/COMPLEX/CONTEXT),
                "reasoning": str
            }
        """
        reasoning = f"Routing based on intent: {intent}"
        
        if intent == "CASUAL":
            # Direct response without any DB calls
            response = self._get_casual_response(message)
            return {
                "intent": "CASUAL",
                "response": response,
                "route_to": None,
                "reasoning": reasoning
            }
        
        elif intent == "COMPLEX":
            # Route to Task Planner (orchestrator will decide based on config whether to use planner or go straight to RAG)
            return {
                "intent": "COMPLEX",
                "response": None,
                "route_to": "task_planner",
                "reasoning": reasoning
            }
        
        elif intent == "CONTEXT":
            # Route to Context Manager for context-aware response
            return {
                "intent": "CONTEXT",
                "response": None,
                "route_to": "context_manager",
                "reasoning": reasoning
            }
        
        elif intent == "UNKNOWN":
            # Use fallback LLM
            response = await self.fallback_llm.generate_response(message, chat_context)
            return {
                "intent": "UNKNOWN",
                "response": response,
                "route_to": None,
                "reasoning": reasoning
            }
        
        else:
            # Default to UNKNOWN
            response = await self.fallback_llm.generate_response(message, chat_context)
            return {
                "intent": "UNKNOWN",
                "response": response,
                "route_to": None,
                "reasoning": f"Unknown intent type: {intent}"
            }
    
    def _get_casual_response(self, message: str) -> str:
        """Generate casual response for greetings/simple queries"""
        message_lower = message.lower().strip()
        
        greetings = ["안녕", "안녕하세요", "좋은 아침", "좋은 저녁", "반가워"]
        thanks = ["고마워", "감사", "thank", "thanks"]
        
        if any(g in message_lower for g in greetings):
            return "안녕하세요! OSS 지식베이스 어시스턴트입니다. 질문에 도움을 드릴 수 있습니다. 무엇을 도와드릴까요?"
        
        if any(t in message_lower for t in thanks):
            return "천만에요! 추가로 도움이 필요하시면 언제든지 말씀해주세요."
        
        # Default casual response
        return "안녕하세요! 무엇을 도와드릴까요?"

