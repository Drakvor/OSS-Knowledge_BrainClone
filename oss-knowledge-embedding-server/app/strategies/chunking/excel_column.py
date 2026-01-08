"""
Excel Column-Based Chunking Strategy
====================================

Chunks Excel data by columns, creating embeddings for column-specific content.
Useful for analyzing specific fields or attributes across the dataset.
"""

import time
from typing import Dict, Any, List
from datetime import datetime
import pandas as pd

from app.processors.base.base_models import ProcessedChunk
from app.strategies.chunking.base import BaseChunkingStrategy, ChunkingResult, ChunkingStrategyType


class ExcelColumnChunkingStrategy(BaseChunkingStrategy):
    """Column-based chunking that groups data by columns"""
    
    def __init__(self, config):
        super().__init__(config)
        self.columns_per_chunk = config.custom_params.get('columns_per_chunk', 1)
        self.include_column_names = config.custom_params.get('include_column_names', True)
        self.sample_rows = config.custom_params.get('sample_rows', 10)  # Max rows per column chunk
        self.target_columns = config.custom_params.get('target_columns', [])  # Specific columns to focus on
    
    async def chunk_text(
        self, 
        text: str, 
        source_metadata: Dict[str, Any] = None
    ) -> ChunkingResult:
        """Chunk Excel data by columns"""
        
        start_time = time.time()
        source_metadata = source_metadata or {}
        
        if not text.strip():
            return ChunkingResult(
                chunks=[],
                strategy_used=ChunkingStrategyType.EXCEL_COLUMN,
                total_chunks=0,
                avg_chunk_size=0,
                metadata={"strategy": "excel_column", "empty_input": True},
                processing_time_ms=0
            )
        
        # Parse Excel-like data from text
        parsed_data = self._parse_excel_data(text)
        
        if not parsed_data or not parsed_data.get('columns'):
            return ChunkingResult(
                chunks=[],
                strategy_used=ChunkingStrategyType.EXCEL_COLUMN,
                total_chunks=0,
                avg_chunk_size=0,
                metadata={"strategy": "excel_column", "no_columns_found": True},
                processing_time_ms=(time.time() - start_time) * 1000
            )
        
        chunks = []
        chunk_index = 0
        
        column_data = parsed_data['columns']
        column_names = list(column_data.keys())
        
        # Filter to target columns if specified
        if self.target_columns:
            column_names = [col for col in column_names if any(target.lower() in col.lower() for target in self.target_columns)]
        
        # Create chunks by grouping columns
        for i in range(0, len(column_names), self.columns_per_chunk):
            chunk_columns = column_names[i:i + self.columns_per_chunk]
            
            if not chunk_columns:
                continue
            
            chunk_content = self._create_column_chunk_content(chunk_columns, column_data)
            
            if len(chunk_content) >= self.config.min_chunk_size:
                chunk = ProcessedChunk(
                    chunk_id=self._create_chunk_id(
                        source_metadata.get("job_id", "unknown"), 
                        chunk_index
                    ),
                    content=chunk_content,
                    chunk_type="excel_column",
                    source_file=source_metadata.get("source_file", "unknown"),
                    start_position=i,
                    end_position=min(i + self.columns_per_chunk, len(column_names)),
                    metadata={
                        "chunk_strategy": "excel_column",
                        "columns_per_chunk": len(chunk_columns),
                        "column_names": chunk_columns,
                        "chunk_index": chunk_index,
                        "sample_size": self.sample_rows,
                        "column_types": self._analyze_column_types(chunk_columns, column_data)
                    }
                )
                chunks.append(chunk)
                chunk_index += 1
        
        processing_time = (time.time() - start_time) * 1000
        stats = self._calculate_chunk_stats(chunks)
        
        return ChunkingResult(
            chunks=chunks,
            strategy_used=ChunkingStrategyType.FIXED_SIZE,
            total_chunks=len(chunks),
            avg_chunk_size=stats["avg_size"],
            metadata={
                "strategy": "excel_column",
                "config": {
                    "columns_per_chunk": self.columns_per_chunk,
                    "include_column_names": self.include_column_names,
                    "sample_rows": self.sample_rows,
                    "target_columns": self.target_columns
                },
                "stats": stats,
                "total_columns": len(column_names),
                "columns_processed": column_names
            },
            processing_time_ms=processing_time
        )
    
    def _parse_excel_data(self, text: str) -> Dict[str, Any]:
        """Parse text into column-based data structure"""
        
        columns = {}
        current_column = None
        
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for key=value patterns
            if '=' in line and ',' in line:
                pairs = line.split(', ')
                for pair in pairs:
                    if '=' in pair:
                        key, value = pair.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        if key not in columns:
                            columns[key] = []
                        columns[key].append(value)
        
        return {"columns": columns}
    
    def _create_column_chunk_content(self, column_names: List[str], column_data: Dict[str, List[str]]) -> str:
        """Create chunk content focused on specific columns"""
        
        content_parts = []
        
        for column_name in column_names:
            if column_name not in column_data:
                continue
            
            values = column_data[column_name]
            
            # Add column header
            if self.include_column_names:
                content_parts.append(f"=== {column_name} ===")
            
            # Sample values from the column
            sample_values = values[:self.sample_rows] if len(values) > self.sample_rows else values
            
            # Add column analysis
            unique_values = list(set(values))
            content_parts.append(f"Total values: {len(values)}")
            content_parts.append(f"Unique values: {len(unique_values)}")
            
            # Add sample values
            content_parts.append("Sample values:")
            for i, value in enumerate(sample_values):
                content_parts.append(f"  {i+1}. {value}")
            
            # Add value patterns/analysis
            if len(unique_values) <= 10:  # Show all unique values for small sets
                content_parts.append(f"All unique values: {', '.join(unique_values)}")
            else:
                # Show most common values
                value_counts = {}
                for value in values:
                    value_counts[value] = value_counts.get(value, 0) + 1
                
                sorted_values = sorted(value_counts.items(), key=lambda x: x[1], reverse=True)
                top_values = sorted_values[:5]
                
                content_parts.append("Most common values:")
                for value, count in top_values:
                    content_parts.append(f"  '{value}' ({count} times)")
            
            # Add column characteristics
            column_type = self._analyze_column_type(values)
            content_parts.append(f"Column type: {column_type}")
            
            content_parts.append("")  # Empty line between columns
        
        return "\n".join(content_parts)
    
    def _analyze_column_type(self, values: List[str]) -> str:
        """Analyze the type and characteristics of a column"""
        
        if not values:
            return "empty"
        
        # Check for common patterns
        numeric_count = 0
        date_count = 0
        korean_count = 0
        
        for value in values[:20]:  # Sample first 20 values
            value = value.strip()
            
            # Check if numeric
            if value.replace('.', '').replace('-', '').isdigit():
                numeric_count += 1
            
            # Check for dates
            if any(date_indicator in value for date_indicator in ['2024', '2023', '-', '/', ':']):
                date_count += 1
            
            # Check for Korean text
            if any('\uac00' <= char <= '\ud7af' for char in value):
                korean_count += 1
        
        total = len(values[:20])
        
        if numeric_count / total > 0.7:
            return "numeric"
        elif date_count / total > 0.5:
            return "datetime"
        elif korean_count / total > 0.5:
            return "korean_text"
        else:
            return "mixed_text"
    
    def _analyze_column_types(self, column_names: List[str], column_data: Dict[str, List[str]]) -> Dict[str, str]:
        """Analyze types for multiple columns"""
        
        types = {}
        for column_name in column_names:
            if column_name in column_data:
                types[column_name] = self._analyze_column_type(column_data[column_name])
        
        return types
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get Excel column strategy information"""
        return {
            "name": "Excel Column Chunking",
            "type": "excel_column",
            "description": "Column-based chunking for analyzing specific fields across Excel data",
            "parameters": {
                "columns_per_chunk": self.columns_per_chunk,
                "include_column_names": self.include_column_names,
                "sample_rows": self.sample_rows,
                "target_columns": self.target_columns
            },
            "pros": [
                "Focuses on specific data fields",
                "Good for column-based analysis",
                "Identifies data patterns and types",
                "Useful for schema understanding"
            ],
            "cons": [
                "Loses row-level relationships",
                "May miss cross-column patterns",
                "Limited context between fields"
            ],
            "best_for": [
                "Data profiling and analysis",
                "Field-specific search",
                "Schema discovery",
                "Data quality assessment"
            ]
        }