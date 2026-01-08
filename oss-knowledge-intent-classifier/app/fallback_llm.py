"""
Fallback LLM for UNKNOWN intents
Uses Azure OpenAI (same as other LLM calls in the system)
"""

import logging
import os
from typing import Dict, Any, Optional
from app.utils.azure_client import create_azure_openai_client

logger = logging.getLogger(__name__)

class FallbackLLM:
    """Fallback LLM for handling UNKNOWN intents using Azure OpenAI"""
    
    def __init__(
        self,
        azure_openai_endpoint: str = None,
        azure_openai_key: str = None,
        azure_deployment: str = None
    ):
        # Azure OpenAI config
        self.azure_endpoint = azure_openai_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT", "https://multiagent-openai-service.openai.azure.com/")
        self.azure_key = azure_openai_key or os.getenv("OPENAI_API_KEY", "")
        self.azure_deployment = azure_deployment or os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini")
        self.azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
        
        self.client: Optional[Any] = None
        self.initialized = False
        
        logger.info(f"Fallback LLM initialized - Using Azure OpenAI: {self.azure_endpoint}")
    
    def _build_fallback_prompt(self, message: str, chat_context: Optional[Dict[str, Any]] = None) -> str:
        """Build prompt for fallback response"""
        prompt = f"""You are a helpful assistant for an OSS Knowledge Base system. 
The user's query could not be clearly classified, so provide a helpful, friendly response.

User message: "{message}"

Provide a helpful response that:
1. Acknowledges the query
2. Offers to help clarify or rephrase
3. Suggests what kind of information might be useful

Keep the response concise and in Korean if the query is in Korean, otherwise in English.
"""
        
        if chat_context:
            if chat_context.get("chat_history"):
                prompt += f"\n\nRecent conversation context:\n"
                for msg in chat_context.get("chat_history", [])[-2:]:  # Last 2 messages
                    prompt += f"- {msg.get('role', 'user')}: {msg.get('content', '')[:100]}\n"
        
        return prompt
    
    def _initialize_client(self):
        """Initialize Azure OpenAI client using shared factory"""
        try:
            self.client = create_azure_openai_client(
                api_key=self.azure_key,
                api_version=self.azure_api_version,
                azure_endpoint=self.azure_endpoint,
                deployment=self.azure_deployment
            )
            self.initialized = True
            logger.info("Azure OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI client: {e}")
            raise
    
    async def generate_response(
        self, 
        message: str, 
        chat_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate fallback response using Azure OpenAI"""
        try:
            self._initialize_client()
            
            prompt = self._build_fallback_prompt(message, chat_context)
            
            response = self.client.chat.completions.create(
                model=self.azure_deployment,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant for an OSS Knowledge Base system."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Azure OpenAI fallback error: {e}")
            return "죄송합니다. 일시적인 오류가 발생했습니다. 다시 시도해주세요."

