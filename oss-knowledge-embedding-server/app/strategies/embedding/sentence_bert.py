"""
Sentence-BERT Embedding Strategy
===============================

General-purpose sentence-transformers embedding strategy.
Supports multiple multilingual and English models.
"""

import time
import logging
import torch
from typing import List, Dict, Any
from datetime import datetime
from sentence_transformers import SentenceTransformer

from app.strategies.embedding.base import BaseEmbeddingStrategy, EmbeddingResult, EmbeddingStrategyType
from app.processors.base.base_models import ProcessedChunk, ChunkEmbedding
from app.core.exceptions import EmbeddingError

logger = logging.getLogger(__name__)


class SentenceBERTEmbeddingStrategy(BaseEmbeddingStrategy):
    """Sentence-BERT embedding strategy implementation"""
    
    def __init__(self, config):
        super().__init__(config)
        self.model = None
        self.vector_dimension = None
        
        # Default models if none specified
        if not self.model_name:
            self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
    
    async def initialize(self) -> bool:
        """Initialize Sentence-BERT model"""
        try:
            logger.info(f"Initializing Sentence-BERT model: {self.model_name}")
            
            # Load model
            self.model = SentenceTransformer(
                self.model_name,
                device=self._get_device()
            )
            
            # Get embedding dimension
            test_embedding = self.model.encode(["test"], convert_to_tensor=False)[0]
            self.vector_dimension = len(test_embedding)
            
            self.initialized = True
            logger.info(f"Sentence-BERT model loaded - Dimension: {self.vector_dimension}")
            return True
            
        except Exception as e:
            logger.error(f"Sentence-BERT initialization failed: {e}")
            return False
    
    def _get_device(self) -> str:
        """Get optimal device for model"""
        if self.device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return "mps"
            else:
                return "cpu"
        return self.device
    
    async def generate_embeddings(
        self, 
        chunks: List[ProcessedChunk],
        show_progress: bool = True
    ) -> EmbeddingResult:
        """Generate Sentence-BERT embeddings for chunks"""
        
        start_time = time.time()
        
        if not self.initialized:
            await self.initialize()
        
        if not chunks:
            return EmbeddingResult(
                embeddings=[],
                strategy_used=self.strategy_type,
                model_info=self._get_model_info(),
                total_embeddings=0,
                avg_embedding_time_ms=0,
                processing_time_ms=0
            )
        
        try:
            # Extract texts
            texts = [chunk.content for chunk in chunks]
            
            # Generate embeddings in batches
            all_embeddings = []
            
            for i in range(0, len(texts), self.batch_size):
                batch_texts = texts[i:i + self.batch_size]
                batch_chunks = chunks[i:i + self.batch_size]
                
                # Generate embeddings
                batch_vectors = self.model.encode(
                    batch_texts,
                    convert_to_tensor=False,
                    show_progress_bar=show_progress and i == 0,
                    batch_size=min(self.batch_size, len(batch_texts)),
                    normalize_embeddings=self.config.normalize_embeddings
                )
                
                # Create ChunkEmbedding objects
                for chunk, vector in zip(batch_chunks, batch_vectors):
                    embedding = ChunkEmbedding(
                        chunk_id=chunk.chunk_id,
                        embedding=vector.tolist(),
                        model_used=self.model_name,
                        embedding_dimension=self.vector_dimension,
                        created_at=datetime.now()
                    )
                    all_embeddings.append(embedding)
                
                # Clear cache between batches
                if self.device in ["cuda", "mps"]:
                    torch.cuda.empty_cache() if self.device == "cuda" else None
            
            processing_time = (time.time() - start_time) * 1000
            avg_time_per_embedding = processing_time / len(all_embeddings) if all_embeddings else 0
            
            logger.info(f"Generated {len(all_embeddings)} Sentence-BERT embeddings")
            
            return EmbeddingResult(
                embeddings=all_embeddings,
                strategy_used=self.strategy_type,
                model_info=self._get_model_info(),
                total_embeddings=len(all_embeddings),
                avg_embedding_time_ms=avg_time_per_embedding,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Sentence-BERT embedding generation failed: {e}")
            raise EmbeddingError(f"Sentence-BERT embedding failed: {e}", self.model_name)
    
    async def generate_single_embedding(self, text: str) -> List[float]:
        """Generate single embedding for search queries"""
        if not self.initialized:
            await self.initialize()
        
        try:
            vector = self.model.encode(
                [text],
                convert_to_tensor=False,
                normalize_embeddings=self.config.normalize_embeddings
            )[0]
            
            return vector.tolist()
            
        except Exception as e:
            logger.error(f"Sentence-BERT single embedding failed: {e}")
            raise EmbeddingError(f"Single embedding failed: {e}", self.model_name)
    
    def get_embedding_dimension(self) -> int:
        """Get embedding dimension"""
        return self.vector_dimension or 384  # Default for MiniLM
    
    def _get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        device_memory = None
        if self.device == "cuda" and torch.cuda.is_available():
            device_memory = {
                "allocated": torch.cuda.memory_allocated(),
                "cached": torch.cuda.memory_reserved()
            }
        
        return {
            "model_name": self.model_name,
            "device": self._get_device(),
            "vector_dimension": self.vector_dimension,
            "batch_size": self.batch_size,
            "initialized": self.initialized,
            "device_memory": device_memory
        }
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get Sentence-BERT strategy information"""
        
        # Model-specific information
        model_info = {
            "sentence-transformers/all-MiniLM-L6-v2": {
                "dimension": 384,
                "size": "90MB",
                "speed": "Fast",
                "quality": "Good"
            },
            "sentence-transformers/all-mpnet-base-v2": {
                "dimension": 768,
                "size": "420MB", 
                "speed": "Medium",
                "quality": "High"
            },
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": {
                "dimension": 384,
                "size": "420MB",
                "speed": "Medium",
                "quality": "Good"
            }
        }
        
        current_model_info = model_info.get(self.model_name, {
            "dimension": self.vector_dimension or "Unknown",
            "size": "Unknown",
            "speed": "Unknown",
            "quality": "Unknown"
        })
        
        return {
            "name": "Sentence-BERT Embeddings",
            "type": self.strategy_type.value,
            "description": "General-purpose sentence embeddings using transformers",
            "model_name": self.model_name,
            "vector_dimension": self.vector_dimension,
            "device": self._get_device(),
            "batch_size": self.batch_size,
            "parameters": {
                "normalize_embeddings": self.config.normalize_embeddings,
                "max_sequence_length": self.config.max_sequence_length
            },
            "model_stats": current_model_info,
            "pros": [
                "Wide variety of available models",
                "Good general-purpose performance", 
                "Relatively fast inference",
                "Small to medium model sizes"
            ],
            "cons": [
                "May not be optimized for Korean",
                "Limited context length",
                "Quality varies by model choice"
            ],
            "best_for": [
                "English text processing",
                "General semantic search",
                "Quick prototyping",
                "Resource-constrained environments"
            ],
            "available_models": [
                "all-MiniLM-L6-v2 (384D, fast)",
                "all-mpnet-base-v2 (768D, high quality)",
                "paraphrase-multilingual-MiniLM-L12-v2 (384D, multilingual)"
            ]
        }
    
    async def health_check(self) -> bool:
        """Check Sentence-BERT service health"""
        try:
            if not self.initialized:
                await self.initialize()
            
            # Test with simple text
            test_embedding = await self.generate_single_embedding("health check")
            return len(test_embedding) == self.vector_dimension
            
        except Exception as e:
            logger.error(f"Sentence-BERT health check failed: {e}")
            return False
    
    async def shutdown(self):
        """Shutdown Sentence-BERT service"""
        try:
            if self.model:
                # Move to CPU to free GPU memory
                if self.device in ["cuda", "mps"]:
                    self.model = self.model.to("cpu")
                del self.model
                self.model = None
            
            # Clear cache
            if self.device == "cuda":
                torch.cuda.empty_cache()
            elif self.device == "mps":
                try:
                    torch.mps.empty_cache()
                except AttributeError:
                    pass
            
            self.initialized = False
            logger.info("Sentence-BERT strategy shutdown complete")
            
        except Exception as e:
            logger.error(f"Sentence-BERT shutdown error: {e}")