"""
Excel Hybrid Chunking Strategy
==============================

Combines row and column awareness for optimal Excel data processing.
Creates chunks that preserve both tabular structure and semantic relationships.
"""

import time
from typing import Dict, Any, List, Tuple
from datetime import datetime
import pandas as pd

from app.processors.base.base_models import ProcessedChunk
from app.strategies.chunking.base import BaseChunkingStrategy, ChunkingResult, ChunkingStrategyType


class ExcelHybridChunkingStrategy(BaseChunkingStrategy):
    """Hybrid approach combining row groups with column awareness"""
    
    def __init__(self, config):
        super().__init__(config)
        self.rows_per_chunk = config.custom_params.get('rows_per_chunk', 5)
        self.key_columns = config.custom_params.get('key_columns', [])  # Important columns to always include
        self.chunk_by_similarity = config.custom_params.get('chunk_by_similarity', True)
        self.preserve_relationships = config.custom_params.get('preserve_relationships', True)
        self.min_semantic_similarity = config.custom_params.get('min_semantic_similarity', 0.3)
    
    async def chunk_text(
        self, 
        text: str, 
        source_metadata: Dict[str, Any] = None
    ) -> ChunkingResult:
        """Chunk Excel data using hybrid row/column approach"""
        
        start_time = time.time()
        source_metadata = source_metadata or {}
        
        if not text.strip():
            return ChunkingResult(
                chunks=[],
                strategy_used=ChunkingStrategyType.HYBRID,
                total_chunks=0,
                avg_chunk_size=0,
                metadata={"strategy": "excel_hybrid", "empty_input": True},
                processing_time_ms=0
            )
        
        # Parse Excel data into structured format
        parsed_data = self._parse_excel_structure(text)
        
        if not parsed_data or not parsed_data['rows']:
            return ChunkingResult(
                chunks=[],
                strategy_used=ChunkingStrategyType.HYBRID,
                total_chunks=0,
                avg_chunk_size=0,
                metadata={"strategy": "excel_hybrid", "no_data_found": True},
                processing_time_ms=(time.time() - start_time) * 1000
            )
        
        # Group rows into semantic chunks
        if self.chunk_by_similarity:
            row_groups = self._group_rows_by_similarity(parsed_data)
        else:
            row_groups = self._group_rows_sequentially(parsed_data)
        
        chunks = []
        chunk_index = 0
        
        for group in row_groups:
            chunk_content = self._create_hybrid_chunk_content(group, parsed_data['headers'])
            
            if len(chunk_content) >= self.config.min_chunk_size:
                chunk = ProcessedChunk(
                    chunk_id=self._create_chunk_id(
                        source_metadata.get("job_id", "unknown"), 
                        chunk_index
                    ),
                    content=chunk_content,
                    chunk_type="excel_hybrid",
                    source_file=source_metadata.get("source_file", "unknown"),
                    start_position=group['start_row'],
                    end_position=group['end_row'],
                    metadata={
                        "chunk_strategy": "excel_hybrid",
                        "rows_in_chunk": len(group['rows']),
                        "row_start": group['start_row'],
                        "row_end": group['end_row'],
                        "chunk_index": chunk_index,
                        "semantic_theme": group.get('theme', 'mixed'),
                        "key_columns_present": [col for col in self.key_columns if col in parsed_data.get('headers', [])],
                        "similarity_score": group.get('similarity_score', 0.0)
                    }
                )
                chunks.append(chunk)
                chunk_index += 1
        
        processing_time = (time.time() - start_time) * 1000
        stats = self._calculate_chunk_stats(chunks)
        
        return ChunkingResult(
            chunks=chunks,
            strategy_used=ChunkingStrategyType.HYBRID,
            total_chunks=len(chunks),
            avg_chunk_size=stats["avg_size"],
            metadata={
                "strategy": "excel_hybrid",
                "config": {
                    "rows_per_chunk": self.rows_per_chunk,
                    "key_columns": self.key_columns,
                    "chunk_by_similarity": self.chunk_by_similarity,
                    "preserve_relationships": self.preserve_relationships
                },
                "stats": stats,
                "total_rows": len(parsed_data['rows']),
                "headers_found": parsed_data.get('headers', []),
                "groups_created": len(row_groups)
            },
            processing_time_ms=processing_time
        )
    
    def _parse_excel_structure(self, text: str) -> Dict[str, Any]:
        """Parse text into structured Excel-like format"""
        
        lines = text.split('\n')
        headers = None
        rows = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Parse key=value format (common in Excel exports)
            if '=' in line and ',' in line:
                row_data = {}
                pairs = line.split(', ')
                
                for pair in pairs:
                    if '=' in pair:
                        key, value = pair.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        row_data[key] = value
                
                # Extract headers from first row
                if headers is None:
                    headers = list(row_data.keys())
                
                # Convert to list format matching headers
                row_list = []
                for header in headers:
                    row_list.append(row_data.get(header, ''))
                
                rows.append(row_list)
        
        return {
            "headers": headers or [],
            "rows": rows
        }
    
    def _group_rows_by_similarity(self, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Group rows based on content similarity"""
        
        rows = parsed_data['rows']
        headers = parsed_data['headers']
        
        if not rows:
            return []
        
        groups = []
        current_group = {
            'rows': [],
            'start_row': 0,
            'end_row': 0,
            'theme': 'unknown',
            'similarity_score': 0.0
        }
        
        for i, row in enumerate(rows):
            # Simple similarity check based on key columns
            if self._should_group_with_current(row, current_group, headers):
                current_group['rows'].append(row)
                current_group['end_row'] = i
            else:
                # Start new group
                if current_group['rows']:
                    current_group['theme'] = self._identify_group_theme(current_group['rows'], headers)
                    current_group['similarity_score'] = self._calculate_group_coherence(current_group['rows'], headers)
                    groups.append(current_group)
                
                current_group = {
                    'rows': [row],
                    'start_row': i,
                    'end_row': i,
                    'theme': 'unknown',
                    'similarity_score': 0.0
                }
            
            # Limit group size
            if len(current_group['rows']) >= self.rows_per_chunk:
                current_group['theme'] = self._identify_group_theme(current_group['rows'], headers)
                current_group['similarity_score'] = self._calculate_group_coherence(current_group['rows'], headers)
                groups.append(current_group)
                
                current_group = {
                    'rows': [],
                    'start_row': i + 1,
                    'end_row': i + 1,
                    'theme': 'unknown',
                    'similarity_score': 0.0
                }
        
        # Add final group
        if current_group['rows']:
            current_group['theme'] = self._identify_group_theme(current_group['rows'], headers)
            current_group['similarity_score'] = self._calculate_group_coherence(current_group['rows'], headers)
            groups.append(current_group)
        
        return groups
    
    def _group_rows_sequentially(self, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Group rows sequentially without similarity analysis"""
        
        rows = parsed_data['rows']
        groups = []
        
        for i in range(0, len(rows), self.rows_per_chunk):
            chunk_rows = rows[i:i + self.rows_per_chunk]
            
            group = {
                'rows': chunk_rows,
                'start_row': i,
                'end_row': min(i + self.rows_per_chunk - 1, len(rows) - 1),
                'theme': f"sequential_group_{len(groups) + 1}",
                'similarity_score': 1.0  # Perfect "similarity" for sequential grouping
            }
            
            groups.append(group)
        
        return groups
    
    def _should_group_with_current(self, row: List[str], current_group: Dict[str, Any], headers: List[str]) -> bool:
        """Determine if row should be grouped with current group"""
        
        if not current_group['rows']:
            return True
        
        if len(current_group['rows']) >= self.rows_per_chunk:
            return False
        
        # Check key columns for similarity
        if self.key_columns and headers:
            similarity_score = 0.0
            comparisons = 0
            
            for key_col in self.key_columns:
                if key_col in headers:
                    col_index = headers.index(key_col)
                    if col_index < len(row) and col_index < len(current_group['rows'][-1]):
                        # Ensure values are strings before calling .lower()
                        current_value = str(row[col_index]).lower()
                        previous_value = str(current_group['rows'][-1][col_index]).lower()
                        
                        # Simple similarity check
                        if current_value == previous_value:
                            similarity_score += 1.0
                        elif current_value in previous_value or previous_value in current_value:
                            similarity_score += 0.5
                        
                        comparisons += 1
            
            if comparisons > 0:
                avg_similarity = similarity_score / comparisons
                return avg_similarity >= self.min_semantic_similarity
        
        return True
    
    def _identify_group_theme(self, rows: List[List[str]], headers: List[str]) -> str:
        """Identify the semantic theme of a group of rows"""
        
        if not rows or not headers:
            return "unknown"
        
        # Look for common patterns in key columns
        themes = []
        
        # Check problem type patterns (for ITSM data)
        type_indicators = {
            "network": ["네트워크", "연결", "스위치", "포트"],
            "performance": ["성능", "속도", "지연", "응답"],
            "security": ["보안", "로그", "접근", "인증"],
            "hardware": ["하드웨어", "프린터", "장비"],
            "software": ["소프트웨어", "애플리케이션", "앱"]
        }
        
        # Analyze text content across rows
        all_text = ""
        for row in rows:
            all_text += " ".join(str(cell) for cell in row).lower()
        
        for theme, keywords in type_indicators.items():
            if any(keyword in all_text for keyword in keywords):
                themes.append(theme)
        
        return "_".join(themes) if themes else "mixed"
    
    def _calculate_group_coherence(self, rows: List[List[str]], headers: List[str]) -> float:
        """Calculate how coherent/similar the rows in a group are"""
        
        if len(rows) <= 1:
            return 1.0
        
        # Simple coherence based on text overlap
        coherence_scores = []
        
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                row1_text = set(" ".join(str(cell) for cell in rows[i]).lower().split())
                row2_text = set(" ".join(str(cell) for cell in rows[j]).lower().split())
                
                intersection = len(row1_text.intersection(row2_text))
                union = len(row1_text.union(row2_text))
                
                jaccard = intersection / union if union > 0 else 0
                coherence_scores.append(jaccard)
        
        return sum(coherence_scores) / len(coherence_scores) if coherence_scores else 0.0
    
    def _create_hybrid_chunk_content(self, group: Dict[str, Any], headers: List[str]) -> str:
        """Create content for hybrid chunk combining structure and semantics"""
        
        content_parts = []
        
        # Add group theme and metadata
        content_parts.append(f"=== Data Group: {group['theme']} ===")
        content_parts.append(f"Rows: {group['start_row']} to {group['end_row']}")
        content_parts.append(f"Coherence Score: {group['similarity_score']:.3f}")
        content_parts.append("")
        
        # Add headers
        if headers:
            content_parts.append("=== Column Headers ===")
            content_parts.append(" | ".join(headers))
            content_parts.append("")
        
        # Add structured data
        content_parts.append("=== Row Data ===")
        
        for i, row in enumerate(group['rows']):
            if headers and len(row) == len(headers):
                # Create key=value pairs
                row_pairs = []
                for header, value in zip(headers, row):
                    # Highlight key columns
                    if header in self.key_columns:
                        row_pairs.append(f"**{header}**: {value}")
                    else:
                        row_pairs.append(f"{header}: {value}")
                
                content_parts.append(f"Row {group['start_row'] + i + 1}: {' | '.join(row_pairs)}")
            else:
                content_parts.append(f"Row {group['start_row'] + i + 1}: {' | '.join(row)}")
        
        # Add semantic analysis
        content_parts.append("")
        content_parts.append("=== Semantic Analysis ===")
        content_parts.append(f"Theme: {group['theme']}")
        
        if self.key_columns and headers:
            content_parts.append("Key Fields in this group:")
            for key_col in self.key_columns:
                if key_col in headers:
                    col_index = headers.index(key_col)
                    values = [row[col_index] for row in group['rows'] if col_index < len(row)]
                    unique_values = list(set(values))
                    
                    content_parts.append(f"  {key_col}: {len(unique_values)} unique values")
                    if len(unique_values) <= 5:
                        content_parts.append(f"    Values: {', '.join(unique_values)}")
        
        return "\n".join(content_parts)
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get Excel hybrid strategy information"""
        return {
            "name": "Excel Hybrid Chunking",
            "type": "excel_hybrid",
            "description": "Combines row grouping with semantic awareness for optimal Excel processing",
            "parameters": {
                "rows_per_chunk": self.rows_per_chunk,
                "key_columns": self.key_columns,
                "chunk_by_similarity": self.chunk_by_similarity,
                "preserve_relationships": self.preserve_relationships,
                "min_semantic_similarity": self.min_semantic_similarity
            },
            "pros": [
                "Preserves tabular structure",
                "Groups semantically similar rows",
                "Maintains column context",
                "Identifies data themes and patterns",
                "Balances structure with meaning"
            ],
            "cons": [
                "More complex processing",
                "Requires semantic analysis",
                "May create uneven chunk sizes",
                "Depends on key column identification"
            ],
            "best_for": [
                "ITSM ticket analysis",
                "Structured data with semantic patterns",
                "Excel reports with categorizable data",
                "Data that benefits from thematic grouping"
            ]
        }