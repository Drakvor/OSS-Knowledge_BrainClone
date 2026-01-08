"""
Fixed-Size Chunking Strategy
============================

Simple character-based chunking with optional overlap.
Fast and predictable for consistent chunk sizes.
"""

import time
from typing import Dict, Any, List
from datetime import datetime

from app.processors.base.base_models import ProcessedChunk
from app.strategies.chunking.base import BaseChunkingStrategy, ChunkingResult, ChunkingStrategyType


class FixedSizeChunkingStrategy(BaseChunkingStrategy):
    """Character-based fixed-size chunking with overlap"""
    
    def __init__(self, config):
        super().__init__(config)
        self.chunk_size = config.chunk_size
        self.overlap = config.overlap
        self.separator = config.separator
    
    async def chunk_text(
        self, 
        text: str, 
        source_metadata: Dict[str, Any] = None
    ) -> ChunkingResult:
        """Chunk text into fixed-size pieces with overlap"""
        
        start_time = time.time()
        source_metadata = source_metadata or {}
        
        if not text.strip():
            return ChunkingResult(
                chunks=[],
                strategy_used=self.strategy_type,
                total_chunks=0,
                avg_chunk_size=0,
                metadata={"strategy": "fixed_size", "empty_input": True},
                processing_time_ms=0
            )
        
        chunks = []
        chunk_index = 0
        
        # Calculate step size (chunk_size - overlap)
        step_size = max(1, self.chunk_size - self.overlap)
        
        for start in range(0, len(text), step_size):
            end = min(start + self.chunk_size, len(text))
            chunk_text = text[start:end].strip()
            
            if len(chunk_text) >= self.config.min_chunk_size:
                chunk = ProcessedChunk(
                    chunk_id=self._create_chunk_id(
                        source_metadata.get("job_id", "unknown"), 
                        chunk_index
                    ),
                    content=chunk_text,
                    chunk_type="fixed_size",
                    source_file=source_metadata.get("source_file", "unknown"),
                    start_position=start,
                    end_position=end,
                    metadata={
                        "chunk_strategy": "fixed_size",
                        "char_start": start,
                        "char_end": end,
                        "overlap_size": self.overlap,
                        "chunk_index": chunk_index
                    }
                )
                chunks.append(chunk)
                chunk_index += 1
        
        processing_time = (time.time() - start_time) * 1000
        stats = self._calculate_chunk_stats(chunks)
        
        return ChunkingResult(
            chunks=chunks,
            strategy_used=self.strategy_type,
            total_chunks=len(chunks),
            avg_chunk_size=stats["avg_size"],
            metadata={
                "strategy": "fixed_size",
                "config": {
                    "chunk_size": self.chunk_size,
                    "overlap": self.overlap,
                    "step_size": step_size
                },
                "stats": stats
            },
            processing_time_ms=processing_time
        )
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get fixed-size strategy information"""
        return {
            "name": "Fixed Size Chunking",
            "type": self.strategy_type.value,
            "description": "Character-based chunking with fixed size and optional overlap",
            "parameters": {
                "chunk_size": self.chunk_size,
                "overlap": self.overlap,
                "separator": self.separator
            },
            "pros": [
                "Predictable chunk sizes",
                "Fast processing",
                "Simple implementation",
                "Consistent memory usage"
            ],
            "cons": [
                "May break semantic boundaries",
                "No content awareness",
                "Potential loss of context"
            ],
            "best_for": [
                "Large documents",
                "Performance-critical applications",
                "When chunk size consistency is important"
            ]
        }