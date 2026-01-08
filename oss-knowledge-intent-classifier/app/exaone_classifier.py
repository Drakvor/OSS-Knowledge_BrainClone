"""
Azure OpenAI-based intent classifier (replaces EXAONE/Ollama)
Uses Azure OpenAI for intent classification
"""

import logging
import os
from typing import Dict, Any, Optional
from app.azure_classifier import AzureIntentClassifier

logger = logging.getLogger(__name__)

class EXAONEClassifier:
    """
    Wrapper for AzureIntentClassifier (maintains backward compatibility)
    Previously used EXAONE via Ollama, now uses Azure OpenAI
    """
    
    def __init__(self, ollama_url: str = None, model: str = None):
        # Initialize Azure classifier instead
        self.azure_classifier = AzureIntentClassifier()
        logger.info("EXAONE Classifier initialized (using Azure OpenAI)")
    
    async def classify_intent(
        self, 
        message: str, 
        chat_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Classify intent using Azure OpenAI (delegates to AzureIntentClassifier)
        
        Returns:
            {
                "intent": "CASUAL" | "DIRECT" | "COMPLEX" | "CONTEXT" | "UNKNOWN",
                "reasoning": str
            }
        """
        return await self.azure_classifier.classify_intent(message, chat_context)

