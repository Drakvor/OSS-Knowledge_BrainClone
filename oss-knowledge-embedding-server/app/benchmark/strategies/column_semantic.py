"""
Column-Semantic Excel Chunking Strategy
=======================================

Strategy 3: Column-centric chunking with semantic field analysis.
Groups related columns together and creates field-specific chunks.
"""

import pandas as pd
from typing import List, Tuple, Dict, Any, Set
import logging
import numpy as np
from collections import defaultdict

from app.benchmark.base import BenchmarkStrategy, BenchmarkConfig, StrategyType
from app.processors.base.base_models import ProcessedChunk, ChunkRelationship

logger = logging.getLogger(__name__)


class ColumnSemanticStrategy(BenchmarkStrategy):
    """Column-semantic chunking strategy implementation"""
    
    def __init__(self, config: BenchmarkConfig):
        super().__init__(config)
        self.min_rows_per_chunk = 3
        self.max_rows_per_chunk = 8
        self.semantic_column_groups = None  # Will be determined dynamically
    
    async def process_excel_data(self, excel_data: pd.DataFrame) -> Tuple[List[ProcessedChunk], List[ChunkRelationship]]:
        """Process Excel data using column-semantic chunking"""
        
        chunks = []
        relationships = []
        
        headers = list(excel_data.columns)
        total_rows = len(excel_data)
        
        logger.info(f"Processing {total_rows} rows with column-semantic analysis of {len(headers)} columns")
        
        # Step 1: Analyze column semantics and group related columns
        column_groups = self._analyze_column_semantics(excel_data, headers)
        
        # Step 2: Create chunks for each column group
        chunk_id_counter = 0
        
        for group_name, group_columns in column_groups.items():
            # Create chunks for this column group
            group_chunks, group_relationships = self._create_column_group_chunks(
                excel_data, group_columns, group_name, chunk_id_counter
            )
            
            chunks.extend(group_chunks)
            relationships.extend(group_relationships)
            chunk_id_counter += len(group_chunks)
        
        # Step 3: Create cross-group relationships
        cross_relationships = self._create_cross_group_relationships(chunks, column_groups)
        relationships.extend(cross_relationships)
        
        logger.info(f"Created {len(chunks)} column-semantic chunks with {len(relationships)} relationships")
        logger.info(f"Column groups: {list(column_groups.keys())}")
        
        return chunks, relationships
    
    def _analyze_column_semantics(self, data: pd.DataFrame, headers: List[str]) -> Dict[str, List[str]]:
        """Analyze column semantics and group related columns"""
        
        column_groups = defaultdict(list)
        
        # Korean ITSM-specific column grouping patterns
        identifier_patterns = ['id', 'ID', '아이디', '번호', '코드', '식별자']
        description_patterns = ['설명', '상세', '내용', '요약', 'description', 'desc']
        status_patterns = ['상태', '진행', '단계', 'status', 'state']
        person_patterns = ['담당자', '요청자', '처리자', '사용자', 'user', 'person']
        time_patterns = ['시간', '날짜', '일시', '생성', '수정', 'time', 'date', 'created', 'updated']
        category_patterns = ['유형', '분류', '카테고리', 'type', 'category', 'class']
        priority_patterns = ['우선순위', '중요도', '긴급', 'priority', 'urgent']
        
        # Classify columns into semantic groups
        for header in headers:
            header_lower = header.lower()
            assigned = False
            
            # Check each pattern group
            if any(pattern in header_lower for pattern in identifier_patterns):
                column_groups['식별자_그룹'].append(header)
                assigned = True
            elif any(pattern in header_lower for pattern in description_patterns):
                column_groups['설명_그룹'].append(header)
                assigned = True
            elif any(pattern in header_lower for pattern in status_patterns):
                column_groups['상태_그룹'].append(header)
                assigned = True
            elif any(pattern in header_lower for pattern in person_patterns):
                column_groups['담당자_그룹'].append(header)
                assigned = True
            elif any(pattern in header_lower for pattern in time_patterns):
                column_groups['시간_그룹'].append(header)
                assigned = True
            elif any(pattern in header_lower for pattern in category_patterns):
                column_groups['분류_그룹'].append(header)
                assigned = True
            elif any(pattern in header_lower for pattern in priority_patterns):
                column_groups['우선순위_그룹'].append(header)
                assigned = True
            
            if not assigned:
                column_groups['기타_그룹'].append(header)
        
        # Ensure at least one group exists
        if not column_groups:
            column_groups['전체_컬럼'] = headers
        
        return dict(column_groups)
    
    def _create_column_group_chunks(self, data: pd.DataFrame, columns: List[str], 
                                  group_name: str, base_chunk_id: int) -> Tuple[List[ProcessedChunk], List[ChunkRelationship]]:
        """Create chunks for a specific column group"""
        
        chunks = []
        relationships = []
        
        # Determine optimal chunk size based on data density
        chunk_size = self._calculate_optimal_chunk_size(data[columns])
        
        # Create chunks for this column group
        total_rows = len(data)
        
        for chunk_idx in range(0, total_rows, chunk_size):
            end_idx = min(chunk_idx + chunk_size, total_rows)
            chunk_data = data[columns].iloc[chunk_idx:end_idx]
            
            # Create chunk content focused on this column group
            chunk_content = self._create_column_group_content(chunk_data, columns, group_name, chunk_idx, end_idx)
            
            chunk_id = self.create_chunk_id(f"colgroup_{group_name}", base_chunk_id + len(chunks))
            
            metadata = {
                "strategy": self.strategy_type.value,
                "chunk_type": "column_group",
                "column_group": group_name,
                "columns": columns,
                "row_start": chunk_idx,
                "row_end": end_idx - 1,
                "row_count": len(chunk_data),
                "group_focus": group_name,
                "column_count": len(columns)
            }
            
            processed_chunk = ProcessedChunk(
                chunk_id=chunk_id,
                content=chunk_content,
                chunk_type="column_semantic",
                metadata=metadata,
                source_file=self.config.test_data_path,
                processing_metadata={"strategy": "column_semantic"}
            )
            
            chunks.append(processed_chunk)
            
            # Create sequential relationships within column group
            if len(chunks) > 1:
                prev_chunk = chunks[-2]
                relationship = ChunkRelationship(
                    relationship_id=f"colseq_{prev_chunk.chunk_id}_{chunk_id}",
                    from_chunk_id=prev_chunk.chunk_id,
                    to_chunk_id=chunk_id,
                    relationship_type="column_sequence",
                    confidence=0.8,
                    description="Same column group sequence",
                    metadata={
                        "connection_type": "same_column_group",
                        "column_group": group_name,
                        "sequence_order": len(chunks) - 1
                    }
                )
                relationships.append(relationship)
        
        return chunks, relationships
    
    def _calculate_optimal_chunk_size(self, group_data: pd.DataFrame) -> int:
        """Calculate optimal chunk size based on data density"""
        
        # Calculate average content length per row
        avg_content_length = 0
        for col in group_data.columns:
            col_lengths = group_data[col].astype(str).str.len().mean()
            avg_content_length += col_lengths
        
        # Adjust chunk size based on content density
        if avg_content_length > 500:  # High density
            return self.min_rows_per_chunk
        elif avg_content_length > 200:  # Medium density
            return (self.min_rows_per_chunk + self.max_rows_per_chunk) // 2
        else:  # Low density
            return self.max_rows_per_chunk
    
    def _create_column_group_content(self, chunk_data: pd.DataFrame, columns: List[str], 
                                   group_name: str, start_idx: int, end_idx: int) -> str:
        """Create content for column group chunk"""
        
        content_lines = [
            f"컬럼 그룹: {group_name}",
            f"포함 컬럼: {', '.join(columns)}",
            f"데이터 행 범위: {start_idx + 1}-{end_idx}",
            "=" * 50
        ]
        
        # Add column group analysis
        content_lines.append(f"\\n{group_name} 분석:")
        
        # Add summary statistics for each column
        for col in columns:
            non_null_count = chunk_data[col].notna().sum()
            unique_count = chunk_data[col].nunique()
            
            content_lines.append(f"- {col}: {non_null_count}/{len(chunk_data)}개 값, {unique_count}개 고유값")
        
        content_lines.append("\\n데이터:")
        
        # Add actual data rows with emphasis on this column group
        for idx, (_, row) in enumerate(chunk_data.iterrows()):
            row_values = []
            for col in columns:
                value = str(row[col]) if pd.notna(row[col]) else "[비어있음]"
                row_values.append(f"{col}: {value}")
            
            content_lines.append(f"행 {start_idx + idx + 1}: " + " | ".join(row_values))
        
        return "\\n".join(content_lines)
    
    def _create_cross_group_relationships(self, chunks: List[ProcessedChunk], 
                                        column_groups: Dict[str, List[str]]) -> List[ChunkRelationship]:
        """Create relationships between different column groups"""
        
        relationships = []
        
        # Group chunks by their column groups
        chunks_by_group = defaultdict(list)
        for chunk in chunks:
            group_name = chunk.metadata.get("column_group", "unknown")
            chunks_by_group[group_name].append(chunk)
        
        # Create cross-group relationships for chunks covering the same row ranges
        group_names = list(chunks_by_group.keys())
        
        for i, group1 in enumerate(group_names):
            for group2 in group_names[i + 1:]:
                # Find chunks with overlapping row ranges
                for chunk1 in chunks_by_group[group1]:
                    for chunk2 in chunks_by_group[group2]:
                        # Check for row overlap
                        start1, end1 = chunk1.metadata["row_start"], chunk1.metadata["row_end"]
                        start2, end2 = chunk2.metadata["row_start"], chunk2.metadata["row_end"]
                        
                        overlap_start = max(start1, start2)
                        overlap_end = min(end1, end2)
                        
                        if overlap_start <= overlap_end:  # There is overlap
                            overlap_rows = overlap_end - overlap_start + 1
                            
                            relationship = ChunkRelationship(
                                relationship_id=f"cross_{chunk1.chunk_id}_{chunk2.chunk_id}",
                                from_chunk_id=chunk1.chunk_id,
                                to_chunk_id=chunk2.chunk_id,
                                relationship_type="cross_column_group",
                                confidence=0.7,
                                description="Cross column group overlap",
                                metadata={
                                    "connection_type": "row_overlap",
                                    "group1": group1,
                                    "group2": group2,
                                    "overlap_rows": overlap_rows,
                                    "overlap_start": overlap_start,
                                    "overlap_end": overlap_end
                                }
                            )
                            relationships.append(relationship)
        
        return relationships
    
    def get_search_config(self) -> Dict[str, Any]:
        """Get column-semantic search configuration"""
        return {
            "strategy_name": "column_semantic",
            "search_type": "column_aware_semantic",
            "embedding_fields": ["content"],
            "boost_fields": {
                "column_group_analysis": 1.2,
                "data_content": 1.0,
                "column_metadata": 0.8
            },
            "filter_metadata": {
                "strategy": self.strategy_type.value,
                "chunk_type": "column_group"
            },
            "column_group_weights": {
                "식별자_그룹": 1.1,
                "설명_그룹": 1.3,
                "상태_그룹": 1.0,
                "담당자_그룹": 0.9,
                "시간_그룹": 0.8,
                "분류_그룹": 1.0,
                "우선순위_그룹": 1.1,
                "기타_그룹": 0.7
            },
            "relationship_traversal": {
                "enabled": True,
                "max_depth": 2,
                "relationship_types": ["column_sequence", "cross_column_group"],
                "prefer_same_group": True
            }
        }
    
    def get_strategy_description(self) -> str:
        """Get strategy description"""
        return (
            f"Column-Semantic Chunking: Groups semantically related columns together. "
            f"Creates Korean ITSM-aware column groups (식별자, 설명, 상태, 담당자, 시간, etc.). "
            f"Chunk size: {self.min_rows_per_chunk}-{self.max_rows_per_chunk} rows based on content density."
        )