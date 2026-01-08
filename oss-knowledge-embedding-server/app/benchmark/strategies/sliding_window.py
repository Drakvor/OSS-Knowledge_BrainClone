"""
Sliding Window Excel Chunking Strategy
======================================

Strategy 6: Sliding window approach with configurable overlap.
Creates overlapping chunks to maintain context between adjacent data.
"""

import pandas as pd
from typing import List, Tuple, Dict, Any
import logging

from app.benchmark.base import BenchmarkStrategy, BenchmarkConfig, StrategyType
from app.processors.base.base_models import ProcessedChunk, ChunkRelationship

logger = logging.getLogger(__name__)


class SlidingWindowStrategy(BenchmarkStrategy):
    """Sliding window chunking strategy implementation"""
    
    def __init__(self, config: BenchmarkConfig):
        super().__init__(config)
        self.window_size = 6  # Number of rows per window
        self.overlap_size = 2  # Number of overlapping rows
        self.step_size = self.window_size - self.overlap_size  # Actual step between windows
        
    async def process_excel_data(self, excel_data: pd.DataFrame) -> Tuple[List[ProcessedChunk], List[ChunkRelationship]]:
        """Process Excel data using sliding window chunking"""
        
        chunks = []
        relationships = []
        
        headers = list(excel_data.columns)
        total_rows = len(excel_data)
        
        logger.info(f"Processing {total_rows} rows with sliding window (size={self.window_size}, overlap={self.overlap_size})")
        
        # Calculate window positions
        window_positions = []
        start_idx = 0
        
        while start_idx < total_rows:
            end_idx = min(start_idx + self.window_size, total_rows)
            window_positions.append((start_idx, end_idx))
            
            # Break if this window covers all remaining data
            if end_idx >= total_rows:
                break
                
            start_idx += self.step_size
        
        logger.info(f"Created {len(window_positions)} sliding windows")
        
        # Create chunks for each window
        for window_idx, (start_idx, end_idx) in enumerate(window_positions):
            window_data = excel_data.iloc[start_idx:end_idx]
            
            # Identify overlap regions
            overlap_info = self._calculate_overlap_info(window_idx, window_positions, start_idx, end_idx)
            
            # Create window chunk content
            chunk_content = self._create_window_chunk_content(
                window_data, headers, start_idx, end_idx, window_idx, overlap_info
            )
            
            chunk_id = self.create_chunk_id("window", window_idx)
            
            metadata = {
                "strategy": self.strategy_type.value,
                "chunk_type": "sliding_window",
                "window_id": window_idx,
                "window_size": self.window_size,
                "overlap_size": self.overlap_size,
                "row_start": start_idx,
                "row_end": end_idx - 1,
                "actual_rows": len(window_data),
                "columns": headers,
                "overlap_info": overlap_info,
                "window_position": {
                    "is_first": window_idx == 0,
                    "is_last": end_idx >= total_rows,
                    "total_windows": len(window_positions)
                }
            }
            
            processed_chunk = ProcessedChunk(
                chunk_id=chunk_id,
                content=chunk_content,
                chunk_type="sliding_window",
                metadata=metadata,
                source_file=self.config.test_data_path,
                processing_metadata={"strategy": "sliding_window"}
            )
            
            chunks.append(processed_chunk)
            
            # Create overlap relationships with previous window
            if window_idx > 0:
                prev_chunk = chunks[window_idx - 1]
                overlap_relationship = self._create_overlap_relationship(
                    prev_chunk, processed_chunk, overlap_info
                )
                relationships.append(overlap_relationship)
        
        # Create additional contextual relationships
        context_relationships = self._create_contextual_relationships(chunks)
        relationships.extend(context_relationships)
        
        logger.info(f"Created {len(chunks)} sliding window chunks with {len(relationships)} relationships")
        return chunks, relationships
    
    def _calculate_overlap_info(self, window_idx: int, window_positions: List[Tuple[int, int]], 
                              start_idx: int, end_idx: int) -> Dict[str, Any]:
        """Calculate overlap information for current window"""
        
        overlap_info = {
            "has_prev_overlap": False,
            "has_next_overlap": False,
            "prev_overlap_rows": 0,
            "next_overlap_rows": 0,
            "prev_overlap_start": None,
            "prev_overlap_end": None,
            "next_overlap_start": None,
            "next_overlap_end": None
        }
        
        # Check overlap with previous window
        if window_idx > 0:
            prev_start, prev_end = window_positions[window_idx - 1]
            if prev_end > start_idx:  # There is overlap
                overlap_start = start_idx
                overlap_end = min(prev_end, end_idx)
                overlap_info.update({
                    "has_prev_overlap": True,
                    "prev_overlap_rows": overlap_end - overlap_start,
                    "prev_overlap_start": overlap_start,
                    "prev_overlap_end": overlap_end
                })
        
        # Check overlap with next window
        if window_idx < len(window_positions) - 1:
            next_start, next_end = window_positions[window_idx + 1]
            if next_start < end_idx:  # There is overlap
                overlap_start = next_start
                overlap_end = min(end_idx, next_end)
                overlap_info.update({
                    "has_next_overlap": True,
                    "next_overlap_rows": overlap_end - overlap_start,
                    "next_overlap_start": overlap_start,
                    "next_overlap_end": overlap_end
                })
        
        return overlap_info
    
    def _create_window_chunk_content(self, window_data: pd.DataFrame, headers: List[str], 
                                   start_idx: int, end_idx: int, window_idx: int, 
                                   overlap_info: Dict[str, Any]) -> str:
        """Create content for sliding window chunk"""
        
        content_lines = [
            f"슬라이딩 윈도우 청크 #{window_idx + 1}",
            f"윈도우 범위: 행 {start_idx + 1}-{end_idx}",
            f"윈도우 크기: {len(window_data)}행",
            f"오버랩 정보: 이전 {overlap_info['prev_overlap_rows']}행, 다음 {overlap_info['next_overlap_rows']}행",
            "=" * 50
        ]
        
        # Add overlap analysis
        content_lines.append("\\n오버랩 분석:")
        if overlap_info["has_prev_overlap"]:
            content_lines.append(f"- 이전 윈도우와 겹침: 행 {overlap_info['prev_overlap_start']+1}-{overlap_info['prev_overlap_end']}")
        else:
            content_lines.append("- 이전 윈도우와 겹침: 없음")
            
        if overlap_info["has_next_overlap"]:
            content_lines.append(f"- 다음 윈도우와 겹침: 행 {overlap_info['next_overlap_start']+1}-{overlap_info['next_overlap_end']}")
        else:
            content_lines.append("- 다음 윈도우와 겹침: 없음")
        
        content_lines.append("\\n윈도우 데이터:")
        
        # Add window data with overlap highlighting
        for i, (original_idx, row) in enumerate(window_data.iterrows()):
            row_number = original_idx + 1
            
            # Mark overlapping rows
            row_marker = ""
            if overlap_info["has_prev_overlap"] and overlap_info["prev_overlap_start"] <= original_idx < overlap_info["prev_overlap_end"]:
                row_marker = " [이전 윈도우와 겹침]"
            elif overlap_info["has_next_overlap"] and overlap_info["next_overlap_start"] <= original_idx < overlap_info["next_overlap_end"]:
                row_marker = " [다음 윈도우와 겹침]"
            
            row_values = []
            for header in headers:
                value = str(row[header]) if pd.notna(row[header]) else "[비어있음]"
                row_values.append(f"{header}: {value}")
            
            content_lines.append(f"행 {row_number}{row_marker}: " + " | ".join(row_values))
        
        return "\\n".join(content_lines)
    
    def _create_overlap_relationship(self, prev_chunk: ProcessedChunk, current_chunk: ProcessedChunk, 
                                   overlap_info: Dict[str, Any]) -> ChunkRelationship:
        """Create overlap relationship between adjacent windows"""
        
        return ChunkRelationship(
            relationship_id=f"overlap_{prev_chunk.chunk_id}_{current_chunk.chunk_id}",
            from_chunk_id=prev_chunk.chunk_id,
            to_chunk_id=current_chunk.chunk_id,
            relationship_type="sliding_overlap",
            confidence=0.8,
            description="Sliding window overlap",
            metadata={
                "connection_type": "sliding_window_overlap",
                "overlap_rows": overlap_info["prev_overlap_rows"],
                "overlap_start": overlap_info["prev_overlap_start"],
                "overlap_end": overlap_info["prev_overlap_end"],
                "window_step": self.step_size,
                "overlap_ratio": overlap_info["prev_overlap_rows"] / self.window_size if self.window_size > 0 else 0
            }
        )
    
    def _create_contextual_relationships(self, chunks: List[ProcessedChunk]) -> List[ChunkRelationship]:
        """Create additional contextual relationships between windows"""
        
        relationships = []
        
        # Create relationships between windows that are 2 steps apart (non-overlapping but contextually related)
        for i in range(len(chunks) - 2):
            chunk1 = chunks[i]
            chunk2 = chunks[i + 2]  # Skip one window
            
            # Check if these windows are contextually related (e.g., same data patterns)
            context_strength = self._calculate_context_similarity(chunk1, chunk2)
            
            if context_strength > 0.3:  # Threshold for contextual relationship
                relationship = ChunkRelationship(
                    relationship_id=f"context_{chunk1.chunk_id}_{chunk2.chunk_id}",
                    from_chunk_id=chunk1.chunk_id,
                    to_chunk_id=chunk2.chunk_id,
                    relationship_type="contextual_similarity",
                    confidence=context_strength,
                    description="Non-adjacent contextual similarity",
                    metadata={
                        "connection_type": "non_adjacent_context",
                        "context_strength": context_strength,
                        "window_gap": 1,
                        "similarity_type": "content_pattern"
                    }
                )
                relationships.append(relationship)
        
        # Create long-range relationships for first and last chunks in sequences
        if len(chunks) >= 4:
            # Connect every 4th window to show long-range patterns
            for i in range(0, len(chunks) - 4, 4):
                chunk1 = chunks[i]
                chunk2 = chunks[i + 4]
                
                relationship = ChunkRelationship(
                    relationship_id=f"longrange_{chunk1.chunk_id}_{chunk2.chunk_id}",
                    from_chunk_id=chunk1.chunk_id,
                    to_chunk_id=chunk2.chunk_id,
                    relationship_type="long_range_pattern",
                    confidence=0.6,
                    description="Long-range sliding window pattern",
                    metadata={
                        "connection_type": "sliding_window_pattern",
                        "window_distance": 4,
                        "pattern_type": "long_range_similarity"
                    }
                )
                relationships.append(relationship)
        
        return relationships
    
    def _calculate_context_similarity(self, chunk1: ProcessedChunk, chunk2: ProcessedChunk) -> float:
        """Calculate contextual similarity between two non-adjacent chunks"""
        
        # Simple similarity based on metadata patterns
        similarity_score = 0.0
        
        # Check if both chunks have similar row counts
        rows1 = chunk1.metadata.get("actual_rows", 0)
        rows2 = chunk2.metadata.get("actual_rows", 0)
        
        if rows1 > 0 and rows2 > 0:
            row_similarity = 1.0 - abs(rows1 - rows2) / max(rows1, rows2)
            similarity_score += row_similarity * 0.3
        
        # Check overlap patterns
        overlap1 = chunk1.metadata.get("overlap_info", {})
        overlap2 = chunk2.metadata.get("overlap_info", {})
        
        if overlap1.get("prev_overlap_rows", 0) == overlap2.get("prev_overlap_rows", 0):
            similarity_score += 0.3
        
        if overlap1.get("next_overlap_rows", 0) == overlap2.get("next_overlap_rows", 0):
            similarity_score += 0.3
        
        # Base similarity for being part of the same sliding window sequence
        similarity_score += 0.1
        
        return min(similarity_score, 1.0)
    
    def get_search_config(self) -> Dict[str, Any]:
        """Get sliding window search configuration"""
        return {
            "strategy_name": "sliding_window",
            "search_type": "overlap_aware_semantic",
            "embedding_fields": ["content"],
            "boost_fields": {
                "window_data": 1.0,
                "overlap_analysis": 0.8,
                "context_content": 1.2,
                "overlapping_rows": 1.3  # Boost overlapping content
            },
            "filter_metadata": {
                "strategy": self.strategy_type.value,
                "chunk_type": "sliding_window"
            },
            "overlap_weights": {
                "high_overlap": 1.4,  # >50% overlap
                "medium_overlap": 1.2,  # 25-50% overlap
                "low_overlap": 1.0    # <25% overlap
            },
            "window_position_weights": {
                "first_window": 1.1,
                "middle_window": 1.0,
                "last_window": 1.1
            },
            "relationship_traversal": {
                "enabled": True,
                "max_depth": 3,
                "relationship_types": ["sliding_overlap", "contextual_similarity", "long_range_pattern"],
                "overlap_boost": True,
                "traverse_overlaps": True
            }
        }
    
    def get_strategy_description(self) -> str:
        """Get strategy description"""
        return (
            f"Sliding Window Chunking: Creates overlapping windows of {self.window_size} rows. "
            f"Overlap of {self.overlap_size} rows between adjacent windows. "
            f"Maintains context continuity and creates overlap-based relationships."
        )