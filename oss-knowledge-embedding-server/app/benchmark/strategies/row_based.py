"""
Row-Based Excel Chunking Strategy
=================================

Strategy 1: Simple row-based chunking with configurable row grouping.
Each chunk contains N consecutive rows with column headers for context.
"""

import pandas as pd
from typing import List, Tuple, Dict, Any
import logging
from dataclasses import asdict

from app.benchmark.base import BenchmarkStrategy, BenchmarkConfig, StrategyType
from app.processors.base.base_models import ProcessedChunk, ChunkRelationship

logger = logging.getLogger(__name__)


class RowBasedStrategy(BenchmarkStrategy):
    """Row-based chunking strategy implementation"""
    
    def __init__(self, config: BenchmarkConfig):
        super().__init__(config)
        self.rows_per_chunk = 5  # Configurable
        self.include_headers = True
    
    async def process_excel_data(self, excel_data: pd.DataFrame) -> Tuple[List[ProcessedChunk], List[ChunkRelationship]]:
        """Process Excel data using row-based chunking"""
        
        chunks = []
        relationships = []
        
        # Get column headers
        headers = list(excel_data.columns)
        total_rows = len(excel_data)
        
        logger.info(f"Processing {total_rows} rows with {len(headers)} columns using row-based strategy")
        
        # Process in chunks of N rows
        for chunk_idx in range(0, total_rows, self.rows_per_chunk):
            end_idx = min(chunk_idx + self.rows_per_chunk, total_rows)
            chunk_rows = excel_data.iloc[chunk_idx:end_idx]
            
            # Create chunk content
            chunk_content = self._create_chunk_content(headers, chunk_rows)
            
            # Create chunk ID
            chunk_id = self.create_chunk_id("row_chunk", chunk_idx // self.rows_per_chunk)
            
            # Create chunk metadata
            metadata = {
                "strategy": self.strategy_type.value,
                "chunk_type": "row_group",
                "row_start": chunk_idx,
                "row_end": end_idx - 1,
                "row_count": len(chunk_rows),
                "columns": headers,
                "data_source": "excel_data"
            }
            
            # Create ProcessedChunk
            processed_chunk = ProcessedChunk(
                chunk_id=chunk_id,
                content=chunk_content,
                chunk_type="excel_row_group",
                metadata=metadata,
                source_file=self.config.test_data_path,
                processing_metadata={"strategy": "row_based"}
            )
            
            chunks.append(processed_chunk)
            
            # Create relationships between consecutive chunks
            if chunk_idx > 0:
                prev_chunk_id = self.create_chunk_id("row_chunk", (chunk_idx - self.rows_per_chunk) // self.rows_per_chunk)
                relationship = ChunkRelationship(
                    relationship_id=f"seq_{prev_chunk_id}_{chunk_id}",
                    from_chunk_id=prev_chunk_id,
                    to_chunk_id=chunk_id,
                    relationship_type="sequential_rows",
                    confidence=0.9,
                    description="Adjacent row groups",
                    metadata={
                        "connection_type": "adjacent_row_groups",
                        "gap_rows": 0,
                        "sequence_order": chunk_idx // self.rows_per_chunk
                    }
                )
                relationships.append(relationship)
        
        logger.info(f"Created {len(chunks)} row-based chunks with {len(relationships)} relationships")
        return chunks, relationships
    
    def _create_chunk_content(self, headers: List[str], chunk_rows: pd.DataFrame) -> str:
        """Create formatted chunk content from rows"""
        
        content_lines = []
        
        # Add headers if enabled
        if self.include_headers:
            content_lines.append("컬럼: " + " | ".join(headers))
            content_lines.append("-" * 50)
        
        # Add each row
        for _, row in chunk_rows.iterrows():
            row_values = []
            for header in headers:
                value = str(row[header]) if pd.notna(row[header]) else ""
                row_values.append(f"{header}: {value}")
            
            row_content = " | ".join(row_values)
            content_lines.append(row_content)
        
        return "\\n".join(content_lines)
    
    def get_search_config(self) -> Dict[str, Any]:
        """Get row-based search configuration"""
        return {
            "strategy_name": "row_based",
            "search_type": "row_semantic",
            "embedding_fields": ["content"],
            "boost_fields": {
                "row_content": 1.0,
                "column_headers": 0.3
            },
            "filter_metadata": {
                "strategy": self.strategy_type.value,
                "chunk_type": "row_group"
            },
            "relationship_traversal": {
                "enabled": True,
                "max_depth": 2,
                "relationship_types": ["sequential_rows"]
            }
        }
    
    def get_strategy_description(self) -> str:
        """Get strategy description"""
        return (
            f"Row-Based Chunking: Groups {self.rows_per_chunk} consecutive Excel rows per chunk. "
            f"Preserves tabular structure with column headers. "
            f"Creates sequential relationships between adjacent row groups."
        )