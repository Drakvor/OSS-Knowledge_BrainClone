"""
Base Chunking Strategy Interface
===============================

Abstract base classes and models for chunking strategies.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from app.processors.base.base_models import ProcessedChunk


class ChunkingStrategyType(Enum):
    """Available chunking strategy types"""
    FIXED_SIZE = "fixed_size"
    SEMANTIC = "semantic"
    SLIDING_WINDOW = "sliding_window"
    SENTENCE_BOUNDARY = "sentence_boundary"
    PARAGRAPH_BOUNDARY = "paragraph_boundary"
    HYBRID = "hybrid"
    EXCEL_ROW = "excel_row"
    EXCEL_COLUMN = "excel_column"
    EXCEL_HYBRID = "excel_hybrid"


@dataclass
class ChunkingConfig:
    """Configuration for chunking strategies"""
    strategy_type: ChunkingStrategyType
    chunk_size: int = 512
    overlap: int = 50
    min_chunk_size: int = 50
    max_chunk_size: int = 2000
    separator: str = "\n"
    semantic_threshold: float = 0.5
    use_metadata: bool = True
    custom_params: Dict[str, Any] = None

    def __post_init__(self):
        if self.custom_params is None:
            self.custom_params = {}


@dataclass
class ChunkingResult:
    """Result from chunking operation"""
    chunks: List[ProcessedChunk]
    strategy_used: ChunkingStrategyType
    total_chunks: int
    avg_chunk_size: float
    metadata: Dict[str, Any]
    processing_time_ms: float


class BaseChunkingStrategy(ABC):
    """Abstract base class for all chunking strategies"""
    
    def __init__(self, config: ChunkingConfig):
        self.config = config
        self.strategy_type = config.strategy_type
    
    @abstractmethod
    async def chunk_text(
        self, 
        text: str, 
        source_metadata: Dict[str, Any] = None
    ) -> ChunkingResult:
        """
        Chunk input text according to strategy.
        
        Args:
            text: Input text to chunk
            source_metadata: Optional metadata about source document
            
        Returns:
            ChunkingResult with processed chunks
        """
        pass
    
    @abstractmethod
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get information about this chunking strategy"""
        pass
    
    def _create_chunk_id(self, base_id: str, chunk_index: int) -> str:
        """Create unique chunk identifier"""
        return f"{base_id}_{self.strategy_type.value}_{chunk_index}"
    
    def _calculate_chunk_stats(self, chunks: List[ProcessedChunk]) -> Dict[str, Any]:
        """Calculate statistics about chunks"""
        if not chunks:
            return {"total": 0, "avg_size": 0, "min_size": 0, "max_size": 0}
        
        sizes = [len(chunk.content) for chunk in chunks]
        return {
            "total": len(chunks),
            "avg_size": sum(sizes) / len(sizes),
            "min_size": min(sizes),
            "max_size": max(sizes),
            "total_chars": sum(sizes)
        }