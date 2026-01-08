"""
Azure OpenAI-based intent classifier
Uses Azure OpenAI (same as other LLM calls in the system) for intent classification
"""

import logging
import os
from typing import Dict, Any, Optional
from app.utils.azure_client import create_azure_openai_client

logger = logging.getLogger(__name__)

class AzureIntentClassifier:
    """Intent classifier using Azure OpenAI"""
    
    def __init__(
        self,
        api_key: str = None,
        endpoint: str = None,
        api_version: str = None,
        deployment: str = None
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.endpoint = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT", "https://multiagent-openai-service.openai.azure.com/")
        self.api_version = api_version or os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
        self.deployment = deployment or os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini")
        
        self.client: Optional[Any] = None
        self.initialized = False
        
        logger.info(f"Azure Intent Classifier initialized - Endpoint: {self.endpoint}, Deployment: {self.deployment}")
    
    def _initialize_client(self):
        """Initialize Azure OpenAI client using shared factory"""
        try:
            self.client = create_azure_openai_client(
                api_key=self.api_key,
                api_version=self.api_version,
                azure_endpoint=self.endpoint,
                deployment=self.deployment
            )
            self.initialized = True
            logger.info("Azure OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI client: {e}")
            raise
    
    def _build_classification_prompt(self, message: str, chat_context: Optional[Dict[str, Any]] = None) -> str:
        """Build prompt for intent classification"""
        prompt = f"""You are an intent classifier for a RAG (Retrieval-Augmented Generation) system. 
Classify the user's message into one of these intents. Be strict and only classify if you are confident:

1. CASUAL - Simple greetings, casual conversation, or questions that don't require database/vector search
   Examples: "안녕하세요", "고마워", "오늘 날씨는?", "좋은 아침", "반가워요"
   Must be clearly a greeting or casual conversation.

2. COMPLEX - Questions requiring RAG (vector search), task planning, analysis, or any database/vector operations
   Examples: "안전관리 안전 수칙은?", "What is machine learning?", "부서별 예산은?", "안전관리와 인사관리의 공통점을 비교해줘", "부서별 예산을 분석하고 추천해줘"
   Must be clearly a question or request that needs information retrieval, analysis, or planning.

3. CONTEXT - Questions about past conversation context or references to previous messages
   Examples: "내가 뭐라고 했지?", "앞서 말한 내용을 다시 설명해줘", "이전 대화에서 언급한 내용", "그거 뭐였지?"
   Must be clearly referring to previous conversation or context.

4. UNKNOWN - Cannot determine intent, unclear query, or ambiguous message
   Examples: "???", "음...", incomplete sentences, ambiguous messages, or if you're not confident about the classification
   DEFAULT to UNKNOWN if you cannot confidently match to CASUAL, COMPLEX, or CONTEXT.

User message: "{message}"

IMPORTANT: Only classify as CASUAL, COMPLEX, or CONTEXT if you are confident. If uncertain, classify as UNKNOWN.

Respond with ONLY the intent name (CASUAL, COMPLEX, CONTEXT, or UNKNOWN) and a brief reasoning.
Format your response as:
INTENT: <intent_name>
REASONING: <brief explanation>
"""
        
        if chat_context:
            if chat_context.get("chat_history"):
                prompt += f"\n\nChat history (last {len(chat_context.get('chat_history', []))} messages):\n"
                for msg in chat_context.get("chat_history", [])[-3:]:  # Last 3 messages for context
                    prompt += f"- {msg.get('role', 'user')}: {msg.get('content', '')[:100]}\n"
        
        return prompt
    
    async def classify_intent(
        self, 
        message: str, 
        chat_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Classify intent using Azure OpenAI
        
        Returns:
            {
                "intent": "CASUAL" | "DIRECT" | "COMPLEX" | "CONTEXT" | "UNKNOWN",
                "reasoning": str
            }
        """
        try:
            self._initialize_client()
            
            prompt = self._build_classification_prompt(message, chat_context)
            
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": "You are an intent classifier. Respond with only the intent name and reasoning in the specified format."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.3  # Lower temperature for more consistent classification
            )
            
            # Parse response
            content = response.choices[0].message.content.strip()
            
            # Extract intent and reasoning
            intent = "UNKNOWN"
            reasoning = "Could not parse response"
            
            if "INTENT:" in content:
                intent_line = [line for line in content.split("\n") if "INTENT:" in line]
                if intent_line:
                    intent = intent_line[0].split("INTENT:")[-1].strip().upper()
            
            if "REASONING:" in content:
                reasoning_lines = content.split("REASONING:")[-1].strip()
                reasoning = reasoning_lines.split("\n")[0].strip()
            else:
                reasoning = content[:200]  # Use first 200 chars as reasoning
            
            # Validate intent
            valid_intents = ["CASUAL", "COMPLEX", "CONTEXT", "UNKNOWN"]
            if intent not in valid_intents:
                # Try to find intent in content
                for valid_intent in valid_intents:
                    if valid_intent in content.upper():
                        intent = valid_intent
                        break
                else:
                    # If DIRECT was returned (old classification), convert to COMPLEX
                    if intent == "DIRECT":
                        intent = "COMPLEX"
                    else:
                        intent = "UNKNOWN"
            
            logger.debug(f"Classified '{message[:50]}' as {intent}: {reasoning[:50]}")
            
            return {
                "intent": intent,
                "reasoning": reasoning
            }
                
        except Exception as e:
            logger.error(f"Intent classification error: {e}")
            return {
                "intent": "UNKNOWN",
                "reasoning": f"Classification error: {str(e)}"
            }

