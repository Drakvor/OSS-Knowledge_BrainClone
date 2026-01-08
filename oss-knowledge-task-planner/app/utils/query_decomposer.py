"""
Query decomposition/rewriting for vector search optimization
Rewrites queries to optimize for cosine similarity matching with document corpus
"""

import logging
import os
import time
from typing import Dict, Any, Optional
from app.utils.azure_client import create_azure_openai_client

logger = logging.getLogger(__name__)


class QueryDecomposer:
    """
    Decomposes and rewrites queries to optimize for vector search (cosine similarity).
    Uses LLM to convert natural language queries into search-optimized queries
    that match the language style and terminology of the document corpus.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = None
        self.initialized = False
        self.enabled = os.getenv("QUERY_DECOMPOSITION_ENABLED", "true").lower() == "true"
        self.deployment = os.getenv("QUERY_DECOMPOSITION_DEPLOYMENT") or os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini")
        self.temperature = float(os.getenv("QUERY_DECOMPOSITION_TEMPERATURE", "0.2"))
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Azure OpenAI client"""
        if not self.enabled:
            self.logger.info("Query decomposition is disabled via QUERY_DECOMPOSITION_ENABLED")
            return
        
        try:
            self.client = create_azure_openai_client()
            self.initialized = True
            self.logger.info(f"QueryDecomposer initialized (deployment: {self.deployment}, temperature: {self.temperature})")
        except Exception as e:
            self.logger.error(f"Failed to initialize Azure OpenAI client for QueryDecomposer: {e}")
            self.initialized = False
    
    def _build_decomposition_prompt(self, query: str, collection: Optional[str] = None, chat_context: Optional[Dict[str, Any]] = None) -> str:
        """Build prompt for query decomposition"""
        collection_info = f"\nCollection: \"{collection}\"" if collection else ""
        
        prompt = f"""You are a query optimizer for a RAG system. Rewrite the user's query to optimize for vector search (cosine similarity) with the document corpus.

Original Query: "{query}"{collection_info}

Instructions:
- Remove conversational phrases ("말해줘", "대해서", etc.)
- Extract the core intent and key concepts
- Rewrite using language and terminology that matches the document corpus
- The goal is maximum cosine similarity - use terms/phrases that appear in the documents
- Keep the query concise (2-5 key terms/phrases)
- Match the style of the corpus (technical, natural language, or domain-specific as appropriate)
- Preserve semantic meaning while improving retrieval match
- Return ONLY the rewritten query, no explanation

Examples:
- "최근 장애 사태에 대해서 말해줘" → "장애 인시던트" (if corpus uses technical terms)
- "최근 장애 사태에 대해서 말해줘" → "최근 장애" (if corpus uses natural language)
- "아키텍처 관련 자료 찾아줘" → "아키텍처 설계" or "아키텍처" (depending on corpus style)
"""
        
        # Add chat context if provided (for better understanding of intent)
        if chat_context and chat_context.get("chat_history"):
            prompt += "\n\nRecent chat context (for understanding intent):\n"
            for msg in chat_context.get("chat_history", [])[-2:]:  # Last 2 messages
                role = msg.get("role", "user")
                content = msg.get("content", "")[:100]  # First 100 chars
                prompt += f"- {role}: {content}\n"
        
        return prompt
    
    async def decompose_query(
        self,
        query: str,
        collection: Optional[str] = None,
        chat_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Decompose and rewrite a query to optimize for vector search.
        
        Args:
            query: Original user query
            collection: Optional collection name (for context-aware rewriting)
            chat_context: Optional chat context
            
        Returns:
            Rewritten query optimized for vector search, or original query if decomposition fails
        """
        if not self.enabled:
            self.logger.debug("Query decomposition disabled, returning original query")
            return query
        
        if not self.initialized or not self.client:
            self.logger.warning("QueryDecomposer not initialized, returning original query")
            return query
        
        if not query or not query.strip():
            self.logger.warning("Empty query provided, returning as-is")
            return query
        
        start_time = time.time()
        original_query = query.strip()
        original_length = len(original_query)
        
        try:
            # Build decomposition prompt
            prompt = self._build_decomposition_prompt(original_query, collection, chat_context)
            
            # Call Azure OpenAI for query rewriting
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a query optimizer. Return ONLY the rewritten query, no explanation or additional text."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=self.temperature
            )
            
            # Extract rewritten query
            rewritten_query = response.choices[0].message.content.strip()
            
            # Remove quotes if the LLM wrapped the response in quotes
            if rewritten_query.startswith('"') and rewritten_query.endswith('"'):
                rewritten_query = rewritten_query[1:-1]
            elif rewritten_query.startswith("'") and rewritten_query.endswith("'"):
                rewritten_query = rewritten_query[1:-1]
            
            elapsed_time = time.time() - start_time
            rewritten_length = len(rewritten_query)
            
            self.logger.info(
                f"Query decomposed: '{original_query}' → '{rewritten_query}' "
                f"(length: {original_length}→{rewritten_length}, time: {elapsed_time:.3f}s)"
            )
            
            # Validate rewritten query is not empty
            if not rewritten_query:
                self.logger.warning("Decomposition returned empty query, using original")
                return original_query
            
            return rewritten_query
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            self.logger.error(
                f"Query decomposition failed after {elapsed_time:.3f}s: {e}. "
                f"Falling back to original query: '{original_query}'"
            )
            return original_query

