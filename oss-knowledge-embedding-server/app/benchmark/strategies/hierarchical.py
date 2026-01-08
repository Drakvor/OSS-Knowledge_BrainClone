"""
Hierarchical Excel Chunking Strategy
====================================

Strategy 2: Multi-level hierarchical chunking with sheet->section->row structure.
Creates parent-child relationships and semantic groupings.
"""

import pandas as pd
from typing import List, Tuple, Dict, Any, Optional
import logging
from collections import defaultdict
import hashlib

from app.benchmark.base import BenchmarkStrategy, BenchmarkConfig, StrategyType
from app.processors.base.base_models import ProcessedChunk, ChunkRelationship

logger = logging.getLogger(__name__)


class HierarchicalStrategy(BenchmarkStrategy):
    """Hierarchical chunking strategy implementation"""
    
    def __init__(self, config: BenchmarkConfig):
        super().__init__(config)
        self.section_size = 10  # Rows per section
        self.subsection_size = 3  # Rows per subsection
        self.hierarchy_levels = ["sheet", "section", "subsection", "row"]
    
    async def process_excel_data(self, excel_data: pd.DataFrame) -> Tuple[List[ProcessedChunk], List[ChunkRelationship]]:
        """Process Excel data using hierarchical chunking"""
        
        chunks = []
        relationships = []
        
        headers = list(excel_data.columns)
        total_rows = len(excel_data)
        
        logger.info(f"Processing {total_rows} rows hierarchically with {len(self.hierarchy_levels)} levels")
        
        # Level 1: Sheet-level chunk (summary)
        sheet_chunk = self._create_sheet_chunk(excel_data, headers)
        chunks.append(sheet_chunk)
        
        # Level 2: Section-level chunks
        section_chunks = []
        for section_idx in range(0, total_rows, self.section_size):
            end_idx = min(section_idx + self.section_size, total_rows)
            section_data = excel_data.iloc[section_idx:end_idx]
            
            section_chunk = self._create_section_chunk(section_data, headers, section_idx, end_idx)
            chunks.append(section_chunk)
            section_chunks.append(section_chunk)
            
            # Create parent-child relationship
            relationship = ChunkRelationship(
                relationship_id=f"parent_{sheet_chunk.chunk_id}_{section_chunk.chunk_id}",
                from_chunk_id=sheet_chunk.chunk_id,
                to_chunk_id=section_chunk.chunk_id,
                relationship_type="parent_child",
                confidence=0.9,
                description="Sheet to section relationship",
                metadata={
                    "parent_level": "sheet",
                    "child_level": "section",
                    "hierarchy_depth": 1
                }
            )
            relationships.append(relationship)
            
            # Level 3: Subsection-level chunks
            subsection_chunks = []
            for sub_idx in range(0, len(section_data), self.subsection_size):
                sub_end = min(sub_idx + self.subsection_size, len(section_data))
                subsection_data = section_data.iloc[sub_idx:sub_end]
                
                global_start = section_idx + sub_idx
                global_end = section_idx + sub_end
                
                subsection_chunk = self._create_subsection_chunk(
                    subsection_data, headers, global_start, global_end, section_idx
                )
                chunks.append(subsection_chunk)
                subsection_chunks.append(subsection_chunk)
                
                # Parent-child relationship
                relationship = ChunkRelationship(
                    relationship_id=f"parent_{section_chunk.chunk_id}_{subsection_chunk.chunk_id}",
                    from_chunk_id=section_chunk.chunk_id,
                    to_chunk_id=subsection_chunk.chunk_id,
                    relationship_type="parent_child",
                    confidence=0.85,
                    description="Section to subsection relationship",
                    metadata={
                        "parent_level": "section",
                        "child_level": "subsection",
                        "hierarchy_depth": 2
                    }
                )
                relationships.append(relationship)
            
            # Create sibling relationships within section
            for i in range(len(subsection_chunks) - 1):
                relationship = ChunkRelationship(
                    relationship_id=f"sibling_{subsection_chunks[i].chunk_id}_{subsection_chunks[i + 1].chunk_id}",
                    from_chunk_id=subsection_chunks[i].chunk_id,
                    to_chunk_id=subsection_chunks[i + 1].chunk_id,
                    relationship_type="sibling",
                    confidence=0.7,
                    description="Subsection sibling relationship",
                    metadata={
                        "sibling_level": "subsection",
                        "sequence_order": i + 1
                    }
                )
                relationships.append(relationship)
        
        # Create section-level sibling relationships
        for i in range(len(section_chunks) - 1):
            relationship = ChunkRelationship(
                relationship_id=f"sibling_{section_chunks[i].chunk_id}_{section_chunks[i + 1].chunk_id}",
                from_chunk_id=section_chunks[i].chunk_id,
                to_chunk_id=section_chunks[i + 1].chunk_id,
                relationship_type="sibling",
                confidence=0.75,
                description="Section sibling relationship",
                metadata={
                    "sibling_level": "section",
                    "sequence_order": i + 1
                }
            )
            relationships.append(relationship)
        
        logger.info(f"Created {len(chunks)} hierarchical chunks with {len(relationships)} relationships")
        return chunks, relationships
    
    def _create_sheet_chunk(self, data: pd.DataFrame, headers: List[str]) -> ProcessedChunk:
        """Create sheet-level summary chunk"""
        
        # Generate sheet summary
        summary_lines = [
            f"엑셀 시트 개요",
            f"총 행 수: {len(data)}",
            f"컬럼 수: {len(headers)}",
            f"컬럼 목록: {', '.join(headers)}",
            "",
            "데이터 샘플 (첫 3행):"
        ]
        
        # Add sample rows
        sample_rows = min(3, len(data))
        for i in range(sample_rows):
            row = data.iloc[i]
            row_values = []
            for header in headers:
                value = str(row[header]) if pd.notna(row[header]) else ""
                row_values.append(f"{header}: {value}")
            summary_lines.append(" | ".join(row_values))
        
        chunk_id = self.create_chunk_id("sheet", 0)
        
        metadata = {
            "strategy": self.strategy_type.value,
            "chunk_type": "sheet_summary",
            "hierarchy_level": "sheet",
            "depth": 0,
            "total_rows": len(data),
            "columns": headers,
            "child_sections": len(data) // self.section_size + (1 if len(data) % self.section_size > 0 else 0)
        }
        
        return ProcessedChunk(
            chunk_id=chunk_id,
            content="\\n".join(summary_lines),
            chunk_type="hierarchical_sheet",
            metadata=metadata,
            source_file=self.config.test_data_path,
            processing_metadata={"strategy": "hierarchical"}
        )
    
    def _create_section_chunk(self, section_data: pd.DataFrame, headers: List[str], 
                            start_idx: int, end_idx: int) -> ProcessedChunk:
        """Create section-level chunk"""
        
        section_id = start_idx // self.section_size
        
        content_lines = [
            f"섹션 {section_id + 1} (행 {start_idx + 1}-{end_idx})",
            f"섹션 행 수: {len(section_data)}",
            "=" * 40
        ]
        
        # Add all rows in section
        for idx, (_, row) in enumerate(section_data.iterrows()):
            row_values = []
            for header in headers:
                value = str(row[header]) if pd.notna(row[header]) else ""
                row_values.append(f"{header}: {value}")
            
            content_lines.append(f"행 {start_idx + idx + 1}: " + " | ".join(row_values))
        
        chunk_id = self.create_chunk_id("section", section_id)
        
        metadata = {
            "strategy": self.strategy_type.value,
            "chunk_type": "section",
            "hierarchy_level": "section",
            "depth": 1,
            "section_id": section_id,
            "row_start": start_idx,
            "row_end": end_idx - 1,
            "section_size": len(section_data),
            "columns": headers
        }
        
        return ProcessedChunk(
            chunk_id=chunk_id,
            content="\\n".join(content_lines),
            chunk_type="hierarchical_section",
            metadata=metadata,
            source_file=self.config.test_data_path,
            processing_metadata={"strategy": "hierarchical"}
        )
    
    def _create_subsection_chunk(self, subsection_data: pd.DataFrame, headers: List[str],
                               start_idx: int, end_idx: int, section_start: int) -> ProcessedChunk:
        """Create subsection-level chunk"""
        
        section_id = section_start // self.section_size
        subsection_id = f"{section_id}_{(start_idx - section_start) // self.subsection_size}"
        
        content_lines = [
            f"하위섹션 {subsection_id} (행 {start_idx + 1}-{end_idx})",
            "-" * 30
        ]
        
        # Add subsection rows with more detail
        for idx, (_, row) in enumerate(subsection_data.iterrows()):
            row_values = []
            for header in headers:
                value = str(row[header]) if pd.notna(row[header]) else ""
                row_values.append(f"{header}: {value}")
            
            content_lines.append(" | ".join(row_values))
        
        chunk_id = self.create_chunk_id("subsection", subsection_id.replace("_", "-"))
        
        metadata = {
            "strategy": self.strategy_type.value,
            "chunk_type": "subsection",
            "hierarchy_level": "subsection",
            "depth": 2,
            "section_id": section_id,
            "subsection_id": subsection_id,
            "row_start": start_idx,
            "row_end": end_idx - 1,
            "subsection_size": len(subsection_data),
            "columns": headers
        }
        
        return ProcessedChunk(
            chunk_id=chunk_id,
            content="\\n".join(content_lines),
            chunk_type="hierarchical_subsection",
            metadata=metadata,
            source_file=self.config.test_data_path,
            processing_metadata={"strategy": "hierarchical"}
        )
    
    def get_search_config(self) -> Dict[str, Any]:
        """Get hierarchical search configuration"""
        return {
            "strategy_name": "hierarchical",
            "search_type": "hierarchical_semantic",
            "embedding_fields": ["content"],
            "boost_fields": {
                "sheet_summary": 0.5,
                "section_content": 1.0,
                "subsection_content": 1.5
            },
            "filter_metadata": {
                "strategy": self.strategy_type.value
            },
            "hierarchy_weights": {
                "sheet": 0.3,
                "section": 0.6,
                "subsection": 1.0
            },
            "relationship_traversal": {
                "enabled": True,
                "max_depth": 3,
                "relationship_types": ["parent_child", "sibling"],
                "traverse_up": True,
                "traverse_down": True
            }
        }
    
    def get_strategy_description(self) -> str:
        """Get strategy description"""
        return (
            f"Hierarchical Chunking: Multi-level structure with sheet->section->subsection hierarchy. "
            f"Sections of {self.section_size} rows, subsections of {self.subsection_size} rows. "
            f"Creates parent-child and sibling relationships for contextual search."
        )