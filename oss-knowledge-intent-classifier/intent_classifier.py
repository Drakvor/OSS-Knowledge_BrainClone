from typing import Literal, Dict, Any, Optional
import asyncio

# Updated intent categories
IntentType = Literal["CASUAL", "COMPLEX", "CONTEXT", "UNKNOWN"]

# Keep old types for backward compatibility during transition
OldIntentType = Literal["GREETING", "CONTEXT_QUERY", "RAG_QUERY", "OTHER"]

class IntentClassifier:
    """
    Intent classifier wrapper that uses EXAONE classifier
    Maintains backward compatibility with old intent types
    """
    def __init__(self):
        print("Initializing Intent Classifier with EXAONE")
        # Lazy import to avoid circular dependencies
        self.exaone_classifier = None
        self._initialized = False
    
    def _ensure_initialized(self):
        """Lazy initialization of EXAONE classifier"""
        if not self._initialized:
            from app.exaone_classifier import EXAONEClassifier
            self.exaone_classifier = EXAONEClassifier()
            self._initialized = True
    
    async def classify_intent_async(
        self, 
        message: str, 
        chat_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Async intent classification using EXAONE
        
        Returns:
            {
                "intent": IntentType,
                "reasoning": str
            }
        """
        self._ensure_initialized()
        return await self.exaone_classifier.classify_intent(message, chat_context)
    
    def classify_intent(self, message: str, chat_history: list = None) -> IntentType:
        """
        Synchronous wrapper for backward compatibility
        Falls back to rule-based if EXAONE is not available
        """
        try:
            self._ensure_initialized()
            # Run async method in sync context
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running, create a new one
                import nest_asyncio
                nest_asyncio.apply()
            result = loop.run_until_complete(
                self.exaone_classifier.classify_intent(message, {"chat_history": chat_history} if chat_history else None)
            )
            return result.get("intent", "UNKNOWN")
        except Exception as e:
            print(f"EXAONE classification failed, using fallback: {e}")
            # Fallback to rule-based
            return self._classify_intent_fallback(message)
    
    def _classify_intent_fallback(self, message: str) -> IntentType:
        """Fallback rule-based classification - strict matching only"""
        message_lower = message.lower().strip()
        
        # CASUAL (greetings) - must be clear match
        greetings = ["안녕", "안녕하세요", "좋은 아침", "고마워", "감사", "반가워", "hello", "hi"]
        if any(greeting in message_lower for greeting in greetings):
            return "CASUAL"
        
        # CONTEXT (context queries) - must be clear match
        context_keywords = ["내가 뭐라고", "뭐 물어봤", "뭐 말했", "다시 말", "다시 설명", "그거 뭐였지", "앞서", "이전", "아까"]
        if any(keyword in message_lower for keyword in context_keywords):
            return "CONTEXT"
        
        # COMPLEX - only if clearly a question or request
        question_words = ["뭐", "무엇", "어떻게", "어디", "언제", "누구", "왜", "what", "how", "where", "when", "who", "why"]
        if any(word in message_lower for word in question_words) and len(message_lower) > 3:
            return "COMPLEX"
        
        # Default to UNKNOWN if unable to match
        return "UNKNOWN"
    
    def generate_context_response(self, message: str, session_id: str = None) -> str:
        """Deprecated: Context handling is now done by Context Manager"""
        return "이전 대화 맥락을 참고하여 도움을 드리겠습니다."
    
    def generate_response(self, message: str, chat_history: list = None) -> str:
        """Generate response for UNKNOWN intent"""
        return "안녕하세요! OSS 지식베이스 어시스턴트입니다. 질문에 도움을 드리겠습니다."

# Global intent classifier instance
intent_classifier = IntentClassifier()
