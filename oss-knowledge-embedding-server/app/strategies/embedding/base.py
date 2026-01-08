"""
Base Embedding Strategy Interface
=================================

Abstract base classes and models for embedding strategies.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from app.processors.base.base_models import ProcessedChunk, ChunkEmbedding


class EmbeddingStrategyType(Enum):
    """Available embedding strategy types"""
    BGE_M3_KOREAN = "bge_m3_korean"
    SENTENCE_BERT = "sentence_bert"
    OPENAI_ADA = "openai_ada"
    MULTILINGUAL_E5 = "multilingual_e5"
    COHERE_EMBED = "cohere_embed"


@dataclass
class EmbeddingConfig:
    """Configuration for embedding strategies"""
    strategy_type: EmbeddingStrategyType
    model_name: str
    device: str = "auto"
    batch_size: int = 32
    max_sequence_length: int = 512
    normalize_embeddings: bool = True
    show_progress: bool = True
    custom_params: Dict[str, Any] = None

    def __post_init__(self):
        if self.custom_params is None:
            self.custom_params = {}


@dataclass
class EmbeddingResult:
    """Result from embedding operation"""
    embeddings: List[ChunkEmbedding]
    strategy_used: EmbeddingStrategyType
    model_info: Dict[str, Any]
    total_embeddings: int
    avg_embedding_time_ms: float
    processing_time_ms: float


class BaseEmbeddingStrategy(ABC):
    """Abstract base class for all embedding strategies"""
    
    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self.strategy_type = config.strategy_type
        self.model_name = config.model_name
        self.device = config.device
        self.batch_size = config.batch_size
        self.initialized = False
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the embedding model"""
        pass
    
    @abstractmethod
    async def generate_embeddings(
        self, 
        chunks: List[ProcessedChunk],
        show_progress: bool = True
    ) -> EmbeddingResult:
        """
        Generate embeddings for processed chunks.
        
        Args:
            chunks: List of processed chunks to embed
            show_progress: Whether to show progress bars
            
        Returns:
            EmbeddingResult with generated embeddings
        """
        pass
    
    @abstractmethod
    async def generate_single_embedding(self, text: str) -> List[float]:
        """Generate single embedding for search queries"""
        pass
    
    @abstractmethod
    def get_embedding_dimension(self) -> int:
        """Get embedding vector dimension"""
        pass
    
    @abstractmethod
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get information about this embedding strategy"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if embedding service is healthy"""
        pass
    
    @abstractmethod
    async def shutdown(self):
        """Shutdown embedding service and cleanup"""
        pass
    
    def _calculate_embedding_stats(self, embeddings: List[ChunkEmbedding]) -> Dict[str, Any]:
        """Calculate statistics about embeddings"""
        if not embeddings:
            return {"total": 0, "avg_dimension": 0, "dimension_consistency": True}
        
        dimensions = [len(emb.embedding) for emb in embeddings]
        dimension_consistency = all(d == dimensions[0] for d in dimensions)
        
        return {
            "total": len(embeddings),
            "avg_dimension": sum(dimensions) / len(dimensions),
            "dimension_consistency": dimension_consistency,
            "expected_dimension": self.get_embedding_dimension()
        }