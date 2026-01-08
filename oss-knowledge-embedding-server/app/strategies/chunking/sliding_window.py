"""
Sliding Window Chunking Strategy
===============================

Overlapping window-based chunking for better context preservation.
Creates overlapping chunks that maintain context across boundaries.
"""

import time
from typing import Dict, Any, List
from datetime import datetime

from app.processors.base.base_models import ProcessedChunk
from app.strategies.chunking.base import BaseChunkingStrategy, ChunkingResult, ChunkingStrategyType


class SlidingWindowChunkingStrategy(BaseChunkingStrategy):
    """Sliding window chunking with configurable overlap"""
    
    def __init__(self, config):
        super().__init__(config)
        self.window_size = config.chunk_size
        self.step_size = config.chunk_size - config.overlap
        self.overlap = config.overlap
        self.separator = config.separator
        
        # Ensure step size is positive
        if self.step_size <= 0:
            self.step_size = max(1, self.window_size // 4)
    
    async def chunk_text(
        self, 
        text: str, 
        source_metadata: Dict[str, Any] = None
    ) -> ChunkingResult:
        """Chunk text using sliding window approach"""
        
        start_time = time.time()
        source_metadata = source_metadata or {}
        
        if not text.strip():
            return ChunkingResult(
                chunks=[],
                strategy_used=self.strategy_type,
                total_chunks=0,
                avg_chunk_size=0,
                metadata={"strategy": "sliding_window", "empty_input": True},
                processing_time_ms=0
            )
        
        chunks = []
        chunk_index = 0
        
        # Create overlapping windows
        for start in range(0, len(text), self.step_size):
            end = min(start + self.window_size, len(text))
            window_text = text[start:end].strip()
            
            # Skip if window is too small
            if len(window_text) < self.config.min_chunk_size:
                continue
            
            # Calculate overlap information
            overlap_start = max(0, start - self.step_size) if start > 0 else 0
            overlap_end = min(start + self.overlap, len(text)) if start > 0 else 0
            overlap_text = text[overlap_start:start] if start > 0 else ""
            
            chunk = ProcessedChunk(
                chunk_id=self._create_chunk_id(
                    source_metadata.get("job_id", "unknown"), 
                    chunk_index
                ),
                content=window_text,
                chunk_type="sliding_window",
                source_file=source_metadata.get("source_file", "unknown"),
                start_position=start,
                end_position=end,
                metadata={
                    "chunk_strategy": "sliding_window",
                    "char_start": start,
                    "char_end": end,
                    "window_size": self.window_size,
                    "step_size": self.step_size,
                    "overlap_size": len(overlap_text),
                    "chunk_index": chunk_index,
                    "overlap_content": overlap_text[:100] + "..." if len(overlap_text) > 100 else overlap_text
                }
            )
            chunks.append(chunk)
            chunk_index += 1
            
            # Break if we've reached the end
            if end >= len(text):
                break
        
        processing_time = (time.time() - start_time) * 1000
        stats = self._calculate_chunk_stats(chunks)
        
        # Calculate overlap statistics
        overlap_stats = self._calculate_overlap_stats(chunks, text)
        
        return ChunkingResult(
            chunks=chunks,
            strategy_used=self.strategy_type,
            total_chunks=len(chunks),
            avg_chunk_size=stats["avg_size"],
            metadata={
                "strategy": "sliding_window",
                "config": {
                    "window_size": self.window_size,
                    "step_size": self.step_size,
                    "overlap": self.overlap
                },
                "stats": stats,
                "overlap_stats": overlap_stats
            },
            processing_time_ms=processing_time
        )
    
    def _calculate_overlap_stats(self, chunks: List[ProcessedChunk], original_text: str) -> Dict[str, Any]:
        """Calculate overlap statistics between chunks"""
        
        if len(chunks) < 2:
            return {"avg_overlap": 0, "max_overlap": 0, "min_overlap": 0}
        
        overlaps = []
        for i in range(1, len(chunks)):
            prev_chunk = chunks[i-1]
            curr_chunk = chunks[i]
            
            # Calculate character-level overlap
            prev_end = prev_chunk.end_position
            curr_start = curr_chunk.start_position
            
            if prev_end > curr_start:
                overlap_size = prev_end - curr_start
                overlaps.append(overlap_size)
            else:
                overlaps.append(0)
        
        if not overlaps:
            return {"avg_overlap": 0, "max_overlap": 0, "min_overlap": 0}
        
        return {
            "avg_overlap": sum(overlaps) / len(overlaps),
            "max_overlap": max(overlaps),
            "min_overlap": min(overlaps),
            "total_overlaps": len(overlaps)
        }
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get sliding window strategy information"""
        return {
            "name": "Sliding Window Chunking",
            "type": self.strategy_type.value,
            "description": "Overlapping window-based chunking for context preservation",
            "parameters": {
                "window_size": self.window_size,
                "step_size": self.step_size,
                "overlap": self.overlap
            },
            "pros": [
                "Maintains context across boundaries",
                "Reduces information loss",
                "Configurable overlap",
                "Good for sequence processing"
            ],
            "cons": [
                "Increased storage requirements",
                "Potential information redundancy",
                "More complex processing",
                "Higher computational cost"
            ],
            "best_for": [
                "Named entity recognition",
                "Context-dependent analysis",
                "Sequential data processing",
                "Information retrieval with context"
            ]
        }