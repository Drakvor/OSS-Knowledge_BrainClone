"""
Excel Row-Based Chunking Strategy
=================================

Chunks Excel data by rows, preserving the tabular structure.
Each chunk contains one or more complete rows with column context.
"""

import time
from typing import Dict, Any, List
from datetime import datetime
import pandas as pd

from app.processors.base.base_models import ProcessedChunk
from app.strategies.chunking.base import BaseChunkingStrategy, ChunkingResult, ChunkingStrategyType


class ExcelRowChunkingStrategy(BaseChunkingStrategy):
    """Row-based chunking that treats each row as a semantic unit"""
    
    def __init__(self, config):
        super().__init__(config)
        self.rows_per_chunk = config.custom_params.get('rows_per_chunk', 1)
        self.include_headers = config.custom_params.get('include_headers', True)
        self.preserve_structure = config.custom_params.get('preserve_structure', True)
    
    async def chunk_text(
        self, 
        text: str, 
        source_metadata: Dict[str, Any] = None
    ) -> ChunkingResult:
        """Chunk Excel data by rows"""
        
        start_time = time.time()
        source_metadata = source_metadata or {}
        
        if not text.strip():
            return ChunkingResult(
                chunks=[],
                strategy_used=ChunkingStrategyType.EXCEL_ROW,
                total_chunks=0,
                avg_chunk_size=0,
                metadata={"strategy": "excel_row", "empty_input": True},
                processing_time_ms=0
            )
        
        # Parse Excel-like data from text
        rows = self._parse_excel_text(text)
        
        if not rows:
            return ChunkingResult(
                chunks=[],
                strategy_used=ChunkingStrategyType.FIXED_SIZE,
                total_chunks=0,
                avg_chunk_size=0,
                metadata={"strategy": "excel_row", "no_rows_found": True},
                processing_time_ms=(time.time() - start_time) * 1000
            )
        
        # Extract headers if available
        headers = rows[0] if rows and self._looks_like_header(rows[0]) else None
        data_rows = rows[1:] if headers else rows
        
        chunks = []
        chunk_index = 0
        
        # Create chunks by grouping rows
        for i in range(0, len(data_rows), self.rows_per_chunk):
            chunk_rows = data_rows[i:i + self.rows_per_chunk]
            
            if not chunk_rows:
                continue
                
            chunk_content = self._create_chunk_content(headers, chunk_rows)
            
            if len(chunk_content) >= self.config.min_chunk_size:
                chunk = ProcessedChunk(
                    chunk_id=self._create_chunk_id(
                        source_metadata.get("job_id", "unknown"), 
                        chunk_index
                    ),
                    content=chunk_content,
                    chunk_type="excel_row",
                    source_file=source_metadata.get("source_file", "unknown"),
                    start_position=i,
                    end_position=min(i + self.rows_per_chunk, len(data_rows)),
                    metadata={
                        "chunk_strategy": "excel_row",
                        "rows_per_chunk": len(chunk_rows),
                        "row_start": i,
                        "row_end": min(i + self.rows_per_chunk, len(data_rows)),
                        "chunk_index": chunk_index,
                        "has_headers": headers is not None,
                        "columns_count": len(headers) if headers else len(chunk_rows[0]) if chunk_rows else 0
                    }
                )
                chunks.append(chunk)
                chunk_index += 1
        
        processing_time = (time.time() - start_time) * 1000
        stats = self._calculate_chunk_stats(chunks)
        
        return ChunkingResult(
            chunks=chunks,
            strategy_used=ChunkingStrategyType.EXCEL_ROW,
            total_chunks=len(chunks),
            avg_chunk_size=stats["avg_size"],
            metadata={
                "strategy": "excel_row",
                "config": {
                    "rows_per_chunk": self.rows_per_chunk,
                    "include_headers": self.include_headers,
                    "preserve_structure": self.preserve_structure
                },
                "stats": stats,
                "total_data_rows": len(data_rows),
                "headers_detected": headers is not None
            },
            processing_time_ms=processing_time
        )
    
    def _parse_excel_text(self, text: str) -> List[List[str]]:
        """Parse text that was extracted from Excel into rows and columns"""
        
        rows = []
        
        # Split by lines
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for key-value patterns (column=value, column=value)
            if '=' in line and ',' in line:
                # Parse key=value pairs
                pairs = []
                for pair in line.split(', '):
                    if '=' in pair:
                        key, value = pair.split('=', 1)
                        pairs.append(f"{key.strip()}: {value.strip()}")
                
                if pairs:
                    rows.append(pairs)
            
            # Look for tab-separated values
            elif '\t' in line:
                columns = line.split('\t')
                rows.append([col.strip() for col in columns])
            
            # Look for comma-separated values (but not key=value pairs)
            elif ',' in line and '=' not in line:
                columns = line.split(',')
                rows.append([col.strip() for col in columns])
            
            # Single column data
            else:
                rows.append([line])
        
        return rows
    
    def _looks_like_header(self, row: List[str]) -> bool:
        """Determine if a row looks like a header row"""
        
        if not row:
            return False
        
        # Headers often contain column names without values
        header_indicators = ['ID', '번호', '이름', '제목', '상태', '유형', '설명', '날짜', '시간']
        
        for cell in row:
            cell_lower = str(cell).lower()
            if any(indicator.lower() in cell_lower for indicator in header_indicators):
                return True
            
            # Headers typically don't contain "=" signs (data does)
            if '=' in cell:
                return False
        
        return True
    
    def _create_chunk_content(self, headers: List[str], data_rows: List[List[str]]) -> str:
        """Create formatted chunk content from headers and data rows"""
        
        content_parts = []
        
        # Add headers if available and requested
        if headers and self.include_headers:
            if self.preserve_structure:
                content_parts.append("=== Headers ===")
                content_parts.append(" | ".join(headers))
                content_parts.append("=== Data ===")
            else:
                content_parts.append(f"Columns: {', '.join(headers)}")
        
        # Add data rows
        for i, row in enumerate(data_rows):
            if self.preserve_structure:
                if headers and len(row) == len(headers):
                    # Create structured row with column names
                    row_data = []
                    for header, value in zip(headers, row):
                        row_data.append(f"{header}: {value}")
                    content_parts.append(f"Row {i+1}: {' | '.join(row_data)}")
                else:
                    # Just show the row data
                    content_parts.append(f"Row {i+1}: {' | '.join(row)}")
            else:
                # Simple concatenation
                content_parts.append(" ".join(row))
        
        return "\n".join(content_parts)
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get Excel row strategy information"""
        return {
            "name": "Excel Row Chunking",
            "type": "excel_row",
            "description": "Row-based chunking that preserves Excel tabular structure",
            "parameters": {
                "rows_per_chunk": self.rows_per_chunk,
                "include_headers": self.include_headers,
                "preserve_structure": self.preserve_structure
            },
            "pros": [
                "Preserves tabular data structure",
                "Maintains row integrity", 
                "Includes column context",
                "Good for structured data analysis"
            ],
            "cons": [
                "May create variable chunk sizes",
                "Limited text context across rows",
                "Depends on data parsing quality"
            ],
            "best_for": [
                "ITSM ticket data",
                "Structured Excel reports",
                "Database-like data",
                "Row-based analysis tasks"
            ]
        }