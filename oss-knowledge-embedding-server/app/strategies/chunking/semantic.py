"""
Semantic Chunking Strategy
==========================

Content-aware chunking that preserves semantic meaning.
Uses sentence boundaries and semantic similarity to create coherent chunks.
"""

import time
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.processors.base.base_models import ProcessedChunk
from app.strategies.chunking.base import BaseChunkingStrategy, ChunkingResult, ChunkingStrategyType


class SemanticChunkingStrategy(BaseChunkingStrategy):
    """Semantic-aware chunking preserving content meaning"""
    
    def __init__(self, config):
        super().__init__(config)
        self.semantic_threshold = config.semantic_threshold
        self.target_size = config.chunk_size
        self.max_size = config.max_chunk_size
        self.min_size = config.min_chunk_size
    
    async def chunk_text(
        self, 
        text: str, 
        source_metadata: Dict[str, Any] = None
    ) -> ChunkingResult:
        """Chunk text semantically based on content structure"""
        
        start_time = time.time()
        source_metadata = source_metadata or {}
        
        if not text.strip():
            return ChunkingResult(
                chunks=[],
                strategy_used=self.strategy_type,
                total_chunks=0,
                avg_chunk_size=0,
                metadata={"strategy": "semantic", "empty_input": True},
                processing_time_ms=0
            )
        
        # Step 1: Split into sentences
        sentences = self._split_into_sentences(text)
        
        # Step 2: Group sentences into semantic chunks
        chunks = self._create_semantic_chunks(sentences, source_metadata)
        
        processing_time = (time.time() - start_time) * 1000
        stats = self._calculate_chunk_stats(chunks)
        
        return ChunkingResult(
            chunks=chunks,
            strategy_used=self.strategy_type,
            total_chunks=len(chunks),
            avg_chunk_size=stats["avg_size"],
            metadata={
                "strategy": "semantic",
                "config": {
                    "semantic_threshold": self.semantic_threshold,
                    "target_size": self.target_size,
                    "max_size": self.max_size,
                    "min_size": self.min_size
                },
                "stats": stats,
                "sentences_processed": len(sentences)
            },
            processing_time_ms=processing_time
        )
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using Korean-aware rules"""
        
        # Korean sentence endings
        korean_endings = r'[.!?。！？]'
        
        # Split on sentence boundaries
        sentences = re.split(f'({korean_endings})', text)
        
        # Recombine sentences with their endings
        combined_sentences = []
        for i in range(0, len(sentences) - 1, 2):
            sentence = sentences[i].strip()
            if i + 1 < len(sentences):
                sentence += sentences[i + 1]
            
            if sentence.strip():
                combined_sentences.append(sentence.strip())
        
        # Handle case where text doesn't end with sentence marker
        if len(sentences) % 2 == 1 and sentences[-1].strip():
            combined_sentences.append(sentences[-1].strip())
        
        return combined_sentences
    
    def _create_semantic_chunks(
        self, 
        sentences: List[str], 
        source_metadata: Dict[str, Any]
    ) -> List[ProcessedChunk]:
        """Group sentences into semantically coherent chunks"""
        
        if not sentences:
            return []
        
        chunks = []
        current_chunk_sentences = []
        current_chunk_size = 0
        chunk_index = 0
        position = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            # Check if adding this sentence would exceed max size
            if (current_chunk_size + sentence_length > self.max_size 
                and current_chunk_sentences):
                
                # Create chunk from current sentences
                chunk = self._create_chunk_from_sentences(
                    current_chunk_sentences, 
                    chunk_index, 
                    source_metadata,
                    position - current_chunk_size
                )
                chunks.append(chunk)
                
                # Reset for next chunk
                current_chunk_sentences = [sentence]
                current_chunk_size = sentence_length
                chunk_index += 1
            else:
                # Add sentence to current chunk
                current_chunk_sentences.append(sentence)
                current_chunk_size += sentence_length
            
            position += sentence_length
        
        # Create final chunk if there are remaining sentences
        if current_chunk_sentences:
            chunk = self._create_chunk_from_sentences(
                current_chunk_sentences, 
                chunk_index, 
                source_metadata,
                position - current_chunk_size
            )
            chunks.append(chunk)
        
        return chunks
    
    def _create_chunk_from_sentences(
        self,
        sentences: List[str],
        chunk_index: int,
        source_metadata: Dict[str, Any],
        start_position: int
    ) -> ProcessedChunk:
        """Create ProcessedChunk from list of sentences"""
        
        content = " ".join(sentences)
        
        return ProcessedChunk(
            chunk_id=self._create_chunk_id(
                source_metadata.get("job_id", "unknown"), 
                chunk_index
            ),
            content=content,
            chunk_type="semantic",
            source_file=source_metadata.get("source_file", "unknown"),
            start_position=start_position,
            end_position=start_position + len(content),
            metadata={
                "chunk_strategy": "semantic",
                "sentence_count": len(sentences),
                "chunk_index": chunk_index,
                "coherence_score": self._calculate_coherence_score(sentences),
                "semantic_boundaries": True
            }
        )
    
    def _calculate_coherence_score(self, sentences: List[str]) -> float:
        """Calculate simple coherence score for chunk quality"""
        
        if len(sentences) <= 1:
            return 1.0
        
        # Simple heuristic: more sentences with consistent length = higher coherence
        lengths = [len(s) for s in sentences]
        avg_length = sum(lengths) / len(lengths)
        variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
        
        # Normalize coherence score (lower variance = higher coherence)
        coherence = max(0.0, 1.0 - (variance / (avg_length ** 2)))
        return min(1.0, coherence)
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get semantic strategy information"""
        return {
            "name": "Semantic Chunking",
            "type": self.strategy_type.value,
            "description": "Content-aware chunking that preserves semantic boundaries",
            "parameters": {
                "semantic_threshold": self.semantic_threshold,
                "target_size": self.target_size,
                "max_size": self.max_size,
                "min_size": self.min_size
            },
            "pros": [
                "Preserves semantic meaning",
                "Respects sentence boundaries",
                "Better context preservation",
                "Korean-aware sentence splitting"
            ],
            "cons": [
                "Variable chunk sizes",
                "Slower processing",
                "More complex implementation",
                "Requires language-specific rules"
            ],
            "best_for": [
                "Question-answering systems",
                "Semantic search",
                "Content analysis",
                "Korean text processing"
            ]
        }