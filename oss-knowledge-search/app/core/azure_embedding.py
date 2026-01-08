"""
Azure OpenAI Embedding Service for Search Server
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

import os
import sys

# Set comprehensive Pydantic compatibility mode before importing OpenAI
os.environ.setdefault('PYDANTIC_V1_COMPAT', '1')
os.environ.setdefault('PYDANTIC_V1', '1')

# Suppress Pydantic warnings globally
import warnings
warnings.filterwarnings("ignore", message="Field .* has conflict with protected namespace")
warnings.filterwarnings("ignore", message="Fields must not use names with leading underscores")

from openai import AzureOpenAI
import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)


class AzureEmbeddingService:
    """Azure OpenAI embedding service for search queries"""
    
    def __init__(self):
        self.client: Optional[AzureOpenAI] = None
        # Use regular embedding model for general search (not memory)
        self.deployment_name = settings.AZURE_EMBEDDING_DEPLOYMENT
        self.model_name = settings.AZURE_EMBEDDING_MODEL
        self.vector_size = settings.VECTOR_SIZE  # 3072 for text-embedding-3-large
        self.batch_size = 16  # Azure OpenAI batch size
        self.initialized = False
        
        logger.info(f"Azure Embedding Service initialized - Deployment: {self.deployment_name}, Model: {self.model_name}, Vector Size: {self.vector_size}")
    
    async def initialize(self) -> bool:
        """Initialize Azure OpenAI client"""
        
        if self.initialized:
            return True
        
        try:
            # Try to suppress Pydantic warnings/errors
            import warnings
            warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

            self.client = AzureOpenAI(
                api_key=settings.OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
            )

            # Test the connection with a simple embedding
            test_response = self.client.embeddings.create(
                model=self.deployment_name,
                input="test connection"
            )

            if test_response.data and len(test_response.data) > 0:
                actual_dim = len(test_response.data[0].embedding)
                logger.info(f"Azure embeddings connected successfully - Dimension: {actual_dim}")
                self.vector_size = actual_dim
                self.initialized = True
                return True
            else:
                raise Exception("No embedding data returned from test")

        except Exception as e:
            logger.error(f"Failed to initialize Azure embedding service: {e}")
            # If it's a pydantic error, try to provide a more specific workaround
            if "pydantic" in str(e).lower() or "__pydantic" in str(e):
                logger.error("Pydantic compatibility issue detected. Trying fallback approach...")
                try:
                    # Try importing with environment variable set
                    os.environ['PYDANTIC_V1'] = '1'
                    import importlib
                    import openai
                    importlib.reload(openai)

                    self.client = AzureOpenAI(
                        api_key=settings.OPENAI_API_KEY,
                        api_version=settings.AZURE_OPENAI_API_VERSION,
                        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
                    )

                    test_response = self.client.embeddings.create(
                        model=self.deployment_name,
                        input="test connection"
                    )

                    if test_response.data and len(test_response.data) > 0:
                        actual_dim = len(test_response.data[0].embedding)
                        logger.info(f"Azure embeddings connected successfully with fallback - Dimension: {actual_dim}")
                        self.vector_size = actual_dim
                        self.initialized = True
                        return True
                except Exception as fallback_error:
                    logger.error(f"Fallback approach also failed: {fallback_error}")

            raise Exception(f"Azure embedding initialization failed: {e}")
    
    async def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a search query"""

        logger.info(f"embed_query called with query: '{query}', initialized: {self.initialized}")

        if not self.initialized:
            logger.info("Initializing Azure embedding service...")
            init_result = await self.initialize()
            logger.info(f"Initialization result: {init_result}")

        if not query.strip():
            logger.warning("Empty query provided")
            return []

        try:
            logger.info(f"Creating embedding with model: {self.deployment_name}")
            response = self.client.embeddings.create(
                model=self.deployment_name,
                input=query
            )

            if response.data and len(response.data) > 0:
                embedding = response.data[0].embedding
                logger.info(f"Generated query embedding - Dimension: {len(embedding)}")
                return embedding
            else:
                logger.error("No embedding data returned from Azure")
                raise Exception("No embedding data returned")

        except Exception as e:
            logger.error(f"Query embedding generation failed: {e}")
            raise Exception(f"Failed to generate query embedding: {e}")
    
    async def embed_queries(self, queries: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple search queries"""
        
        if not self.initialized:
            await self.initialize()
        
        if not queries:
            return []
        
        try:
            # Process in batches
            all_embeddings = []
            
            for i in range(0, len(queries), self.batch_size):
                batch = queries[i:i + self.batch_size]
                
                response = self.client.embeddings.create(
                    model=self.deployment_name,
                    input=batch
                )
                
                batch_embeddings = [data.embedding for data in response.data]
                all_embeddings.extend(batch_embeddings)
            
            logger.info(f"Generated {len(all_embeddings)} query embeddings")
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Batch query embedding generation failed: {e}")
            raise Exception(f"Failed to generate query embeddings: {e}")
    
    async def close(self):
        """Clean up resources"""
        if self.client:
            # Azure OpenAI client doesn't need explicit cleanup
            self.client = None
            self.initialized = False
            logger.info("Azure embedding service closed")
    
    def get_vector_size(self) -> int:
        """Get the vector dimension size"""
        return self.vector_size
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "service": "azure_openai",
            "deployment": self.deployment_name,
            "model": self.model_name,
            "vector_size": self.vector_size,
            "batch_size": self.batch_size,
            "initialized": self.initialized
        }