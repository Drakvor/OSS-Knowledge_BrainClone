"""
Excel Chunking Strategies
Production-ready implementations of proven benchmark strategies
"""

import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime

from app.processors.base.base_models import ProcessedChunk, ChunkRelationship
from app.processors.excel.excel_models import ExcelProcessingOptions, ExcelChunkType

logger = logging.getLogger(__name__)


class SlidingWindowStrategy:
    """Sliding Window chunking strategy - optimized for speed and continuity"""
    
    def __init__(self, options: ExcelProcessingOptions):
        self.options = options
        self.window_size = options.sliding_window_size
        self.overlap = options.sliding_window_overlap
    
    def create_chunks(
        self, 
        headers: List[str], 
        rows: List[Dict[str, Any]], 
        sheet_name: str, 
        job_id: str
    ) -> Tuple[List[ProcessedChunk], List[ChunkRelationship]]:
        """Create sliding window chunks with overlapping context"""
        
        chunks = []
        relationships = []
        
        if not rows:
            return chunks, relationships
        
        logger.info(f"Creating sliding window chunks: {len(rows)} rows, window_size={self.window_size}, overlap={self.overlap}")
        
        # Calculate step size (window_size - overlap)
        step = max(1, self.window_size - self.overlap)
        
        # Create overlapping windows
        for i in range(0, len(rows), step):
            window_end = min(i + self.window_size, len(rows))
            window_rows = rows[i:window_end]
            
            if not window_rows:
                break
            
            # Calculate overlaps
            prev_overlap = min(i, self.overlap) if i > 0 else 0
            next_overlap = min(self.overlap, len(rows) - window_end) if window_end < len(rows) else 0
            
            # Create chunk content
            content = self._create_window_content(
                headers, window_rows, i, window_end, prev_overlap, next_overlap
            )
            
            chunk_id = f"{job_id}_{sheet_name}_window_{i}"
            chunk = ProcessedChunk(
                chunk_id=chunk_id,
                content=content,
                chunk_type=ExcelChunkType.DATA_SAMPLE.value,
                source_file=sheet_name,
                container=self.options.container,
                start_position=i,
                end_position=window_end,
                metadata={
                    "chunking_strategy": "sliding_window",
                    "window_size": len(window_rows),
                    "window_start": i,
                    "window_end": window_end,
                    "prev_overlap": prev_overlap,
                    "next_overlap": next_overlap,
                    "total_rows": len(rows)
                }
            )
            chunks.append(chunk)
        
        # Create overlap relationships
        for i in range(len(chunks) - 1):
            current_chunk = chunks[i]
            next_chunk = chunks[i + 1]
            
            # Calculate overlap size
            current_end = current_chunk.metadata["window_end"]
            next_start = next_chunk.metadata["window_start"]
            overlap_size = max(0, current_end - next_start)
            
            if overlap_size > 0:
                relationship = ChunkRelationship(
                    relationship_id=f"{job_id}_{sheet_name}_overlap_{i}_{i+1}",
                    from_chunk_id=current_chunk.chunk_id,
                    to_chunk_id=next_chunk.chunk_id,
                    relationship_type="overlap",
                    confidence=0.9,
                    description=f"Window overlap of {overlap_size} rows",
                    metadata={
                        "overlap_size": overlap_size,
                        "relationship_nature": "sequential_overlap"
                    }
                )
                relationships.append(relationship)
            
            # Create similarity relationship
            similarity_relationship = ChunkRelationship(
                relationship_id=f"{job_id}_{sheet_name}_similarity_{i}_{i+1}",
                from_chunk_id=current_chunk.chunk_id,
                to_chunk_id=next_chunk.chunk_id,
                relationship_type="similarity",
                confidence=0.7,
                description="Adjacent window similarity",
                metadata={"relationship_nature": "sequential_similarity"}
            )
            relationships.append(similarity_relationship)
        
        logger.info(f"Created {len(chunks)} sliding window chunks with {len(relationships)} relationships")
        return chunks, relationships
    
    def _create_window_content(
        self, 
        headers: List[str], 
        window_rows: List[Dict[str, Any]], 
        start_idx: int, 
        end_idx: int,
        prev_overlap: int, 
        next_overlap: int
    ) -> str:
        """Create content for sliding window chunk"""
        
        content_lines = [
            f"슬라이딩 윈도우 청크 #{(start_idx // max(1, self.window_size - self.overlap)) + 1}",
            f"윈도우 범위: 행 {start_idx + 1}-{end_idx}",
            f"윈도우 크기: {len(window_rows)}행",
            f"오버랩 정보: 이전 {prev_overlap}행, 다음 {next_overlap}행",
            "=" * 50,
            "",
            "오버랩 분석:",
            f"- 이전 윈도우와 겹침: {'행 ' + str(start_idx + 1) + '-' + str(start_idx + prev_overlap) if prev_overlap > 0 else '없음'}",
            f"- 다음 윈도우와 겹침: {'행 ' + str(end_idx - next_overlap + 1) + '-' + str(end_idx) if next_overlap > 0 else '없음'}",
            "",
            "윈도우 데이터:"
        ]
        
        # Add all rows in window with compact format
        for idx, row in enumerate(window_rows):
            row_num = start_idx + idx + 1
            row_values = []
            
            # Show key columns first, then others
            for header in headers[:10]:  # Limit to first 10 columns for readability
                value = row.get(header)
                if value is not None:
                    value_str = str(value)[:50]  # Truncate long values
                    row_values.append(f"{header}: {value_str}")
            
            content_lines.append(f"행 {row_num}: {' | '.join(row_values)}")
        
        return "\n".join(content_lines)


class HierarchicalStrategy:
    """Hierarchical chunking strategy - optimized for rich contextual relationships"""
    
    def __init__(self, options: ExcelProcessingOptions):
        self.options = options
        self.section_size = options.hierarchical_section_size
        self.subsection_size = options.hierarchical_subsection_size
    
    def create_chunks(
        self, 
        headers: List[str], 
        rows: List[Dict[str, Any]], 
        sheet_name: str, 
        job_id: str
    ) -> Tuple[List[ProcessedChunk], List[ChunkRelationship]]:
        """Create hierarchical chunks with sheet->section->subsection structure"""
        
        chunks = []
        relationships = []
        
        if not rows:
            return chunks, relationships
        
        logger.info(f"Creating hierarchical chunks: {len(rows)} rows, section_size={self.section_size}, subsection_size={self.subsection_size}")
        
        # Level 1: Sheet-level chunk (overview)
        sheet_chunk = self._create_sheet_chunk(headers, rows, sheet_name, job_id)
        chunks.append(sheet_chunk)
        
        # Level 2: Section-level chunks
        section_chunks = []
        for section_idx in range(0, len(rows), self.section_size):
            end_idx = min(section_idx + self.section_size, len(rows))
            section_rows = rows[section_idx:end_idx]
            
            section_chunk = self._create_section_chunk(
                headers, section_rows, section_idx, end_idx, sheet_name, job_id
            )
            chunks.append(section_chunk)
            section_chunks.append(section_chunk)
            
            # Create parent-child relationship
            relationship = ChunkRelationship(
                relationship_id=f"{job_id}_{sheet_name}_parent_{sheet_chunk.chunk_id}_{section_chunk.chunk_id}",
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
            for sub_idx in range(0, len(section_rows), self.subsection_size):
                sub_end = min(sub_idx + self.subsection_size, len(section_rows))
                subsection_rows = section_rows[sub_idx:sub_end]
                
                global_start = section_idx + sub_idx
                global_end = section_idx + sub_end
                
                subsection_chunk = self._create_subsection_chunk(
                    headers, subsection_rows, global_start, global_end, section_idx, sheet_name, job_id
                )
                chunks.append(subsection_chunk)
                subsection_chunks.append(subsection_chunk)
                
                # Parent-child relationship
                relationship = ChunkRelationship(
                    relationship_id=f"{job_id}_{sheet_name}_parent_{section_chunk.chunk_id}_{subsection_chunk.chunk_id}",
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
                    relationship_id=f"{job_id}_{sheet_name}_sibling_{subsection_chunks[i].chunk_id}_{subsection_chunks[i + 1].chunk_id}",
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
                relationship_id=f"{job_id}_{sheet_name}_sibling_{section_chunks[i].chunk_id}_{section_chunks[i + 1].chunk_id}",
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
    
    def _create_sheet_chunk(
        self, 
        headers: List[str], 
        rows: List[Dict[str, Any]], 
        sheet_name: str, 
        job_id: str
    ) -> ProcessedChunk:
        """Create sheet-level overview chunk"""
        
        content_lines = [
            f"엑셀 시트 '{sheet_name}' 개요",
            f"총 행 수: {len(rows)}",
            f"컬럼 수: {len(headers)}",
            f"컬럼 목록: {', '.join(headers[:10])}" + ("..." if len(headers) > 10 else ""),
            "",
            "데이터 샘플 (첫 3행):"
        ]
        
        # Add sample rows
        sample_count = min(3, len(rows))
        for i in range(sample_count):
            row = rows[i]
            row_values = []
            for header in headers[:8]:  # Show first 8 columns
                value = row.get(header)
                if value is not None:
                    value_str = str(value)[:30]
                    row_values.append(f"{header}: {value_str}")
            content_lines.append(" | ".join(row_values))
        
        chunk_id = f"{job_id}_{sheet_name}_sheet_overview"
        
        return ProcessedChunk(
            chunk_id=chunk_id,
            content="\n".join(content_lines),
            chunk_type=ExcelChunkType.SCHEMA.value,
            source_file=sheet_name,
            container=self.options.container,
            metadata={
                "chunking_strategy": "hierarchical",
                "chunk_level": "sheet",
                "hierarchy_depth": 0,
                "total_rows": len(rows),
                "total_columns": len(headers),
                "child_sections": (len(rows) // self.section_size) + (1 if len(rows) % self.section_size > 0 else 0)
            }
        )
    
    def _create_section_chunk(
        self, 
        headers: List[str], 
        section_rows: List[Dict[str, Any]], 
        start_idx: int, 
        end_idx: int,
        sheet_name: str, 
        job_id: str
    ) -> ProcessedChunk:
        """Create section-level chunk"""
        
        section_id = start_idx // self.section_size
        
        content_lines = [
            f"섹션 {section_id + 1} (행 {start_idx + 1}-{end_idx})",
            f"섹션 행 수: {len(section_rows)}",
            "=" * 40,
            ""
        ]
        
        # Add all rows in section with structured format
        for idx, row in enumerate(section_rows):
            row_num = start_idx + idx + 1
            row_values = []
            for header in headers[:8]:  # Show first 8 columns
                value = row.get(header)
                if value is not None:
                    value_str = str(value)[:40]
                    row_values.append(f"{header}: {value_str}")
            
            content_lines.append(f"행 {row_num}: {' | '.join(row_values)}")
        
        chunk_id = f"{job_id}_{sheet_name}_section_{section_id}"
        
        return ProcessedChunk(
            chunk_id=chunk_id,
            content="\n".join(content_lines),
            chunk_type=ExcelChunkType.DATA_SAMPLE.value,
            source_file=sheet_name,
            container=self.options.container,
            start_position=start_idx,
            end_position=end_idx,
            metadata={
                "chunking_strategy": "hierarchical",
                "chunk_level": "section",
                "hierarchy_depth": 1,
                "section_id": section_id,
                "row_start": start_idx,
                "row_end": end_idx - 1,
                "section_size": len(section_rows)
            }
        )
    
    def _create_subsection_chunk(
        self, 
        headers: List[str], 
        subsection_rows: List[Dict[str, Any]], 
        start_idx: int, 
        end_idx: int,
        section_start: int,
        sheet_name: str, 
        job_id: str
    ) -> ProcessedChunk:
        """Create subsection-level chunk"""
        
        section_id = section_start // self.section_size
        subsection_id = f"{section_id}_{(start_idx - section_start) // self.subsection_size}"
        
        content_lines = [
            f"하위섹션 {subsection_id} (행 {start_idx + 1}-{end_idx})",
            "-" * 30,
            ""
        ]
        
        # Add subsection rows with detailed content
        for idx, row in enumerate(subsection_rows):
            row_num = start_idx + idx + 1
            row_values = []
            for header in headers[:10]:  # Show more columns at this level
                value = row.get(header)
                if value is not None:
                    value_str = str(value)[:50]
                    row_values.append(f"{header}: {value_str}")
            
            content_lines.append(" | ".join(row_values))
        
        chunk_id = f"{job_id}_{sheet_name}_subsection_{subsection_id.replace('_', '-')}"
        
        return ProcessedChunk(
            chunk_id=chunk_id,
            content="\n".join(content_lines),
            chunk_type=ExcelChunkType.DATA_SAMPLE.value,
            source_file=sheet_name,
            container=self.options.container,
            start_position=start_idx,
            end_position=end_idx,
            metadata={
                "chunking_strategy": "hierarchical",
                "chunk_level": "subsection",
                "hierarchy_depth": 2,
                "section_id": section_id,
                "subsection_id": subsection_id,
                "row_start": start_idx,
                "row_end": end_idx - 1,
                "subsection_size": len(subsection_rows)
            }
        )