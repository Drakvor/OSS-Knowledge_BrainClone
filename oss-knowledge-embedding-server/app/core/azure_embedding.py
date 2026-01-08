"""
Azure OpenAI Embedding Service
Production-ready embedding generation using Azure OpenAI
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
from app.processors.base.base_models import ProcessedChunk, ChunkEmbedding
from app.core.exceptions import EmbeddingError

logger = logging.getLogger(__name__)


class AzureEmbeddingService:
    """Azure OpenAI embedding service"""
    
    def __init__(self):
        self.client: Optional[AzureOpenAI] = None
        self.deployment_name = settings.AZURE_EMBEDDING_DEPLOYMENT
        self.model_name = settings.AZURE_EMBEDDING_MODEL
        self.vector_size = 3072  # text-embedding-3-large dimension
        self.batch_size = 16  # Azure OpenAI batch size
        self.initialized = False
        
        logger.info(f"Azure Embedding Service initialized - Deployment: {self.deployment_name}, Model: {self.model_name}")
    
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
                raise EmbeddingError("No embedding data returned from test")

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

            raise EmbeddingError(f"Azure embedding initialization failed: {e}")
    
    async def generate_single_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        embeddings = await self.generate_embeddings([text])
        return embeddings[0] if embeddings else []
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts using Azure OpenAI"""
        
        if not self.initialized:
            await self.initialize()
        
        if not texts:
            return []
        
        try:
            # Process in batches
            all_embeddings = []
            
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i:i + self.batch_size]
                
                response = self.client.embeddings.create(
                    model=self.deployment_name,
                    input=batch
                )
                
                batch_embeddings = [data.embedding for data in response.data]
                all_embeddings.extend(batch_embeddings)
            
            logger.info(f"Generated {len(all_embeddings)} Azure embeddings")
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Azure embedding generation failed: {e}")
            raise EmbeddingError(f"Failed to generate Azure embeddings: {e}")
    
    async def embed_chunks(self, chunks: List[ProcessedChunk]) -> List[ChunkEmbedding]:
        """Generate embeddings for processed chunks"""
        
        if not chunks:
            return []
        
        # Extract text content from chunks
        texts = []
        for chunk in chunks:
            # Combine content with metadata for richer embeddings
            text = chunk.content
            if chunk.metadata.get('title'):
                text = f"Title: {chunk.metadata['title']}\n\n{text}"
            texts.append(text)
        
        # Generate embeddings
        embeddings = await self.generate_embeddings(texts)
        
        # Create ChunkEmbedding objects
        chunk_embeddings = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_embedding = ChunkEmbedding(
                chunk_id=chunk.chunk_id,
                embedding=embedding,
                model_used=f"azure-{self.model_name}",
                embedding_dimension=len(embedding)
            )
            chunk_embeddings.append(chunk_embedding)
        
        logger.info(f"Created {len(chunk_embeddings)} chunk embeddings using Azure OpenAI")
        return chunk_embeddings
    
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


# Create a configurable embedding service
class EmbeddingService:
    """Configurable embedding service that can use either BGE or Azure"""
    
    def __init__(self, use_azure: bool = True):
        self.use_azure = use_azure
        
        if use_azure:
            self.service = AzureEmbeddingService()
        else:
            from app.core.embedding import BGEEmbeddingService
            self.service = BGEEmbeddingService()
    
    async def initialize(self) -> bool:
        return await self.service.initialize()
    
    async def generate_single_embedding(self, text: str) -> List[float]:
        return await self.service.generate_single_embedding(text)
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        return await self.service.generate_embeddings(texts)
    
    async def embed_chunks(self, chunks: List[ProcessedChunk]) -> List[ChunkEmbedding]:
        return await self.service.embed_chunks(chunks)
    
    def get_vector_size(self) -> int:
        return self.service.get_vector_size()
    
    def get_model_info(self) -> Dict[str, Any]:
        return self.service.get_model_info()