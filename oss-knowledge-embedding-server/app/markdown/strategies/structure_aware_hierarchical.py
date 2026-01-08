"""
Structure-Aware Hierarchical Chunking Strategy
==============================================

Respects natural document hierarchy defined by markdown headers.
Creates chunks that align with document sections while maintaining
parent-child relationships between header levels.
"""

import uuid
import logging
from typing import List, Dict, Any
from datetime import datetime

from app.markdown.base import (
    MarkdownElement, MarkdownElementType, MarkdownChunk, 
    MarkdownRelationship, MarkdownChunkingStrategy
)

logger = logging.getLogger(__name__)


class StructureAwareHierarchicalChunker:
    """Hierarchical chunking based on markdown structure."""
    
    def __init__(self, min_chunk_size: int = 20, max_chunk_size: int = 1000):
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.strategy = MarkdownChunkingStrategy.STRUCTURE_AWARE_HIERARCHICAL
    
    def chunk(self, elements: List[MarkdownElement]) -> tuple[List[MarkdownChunk], List[MarkdownRelationship]]:
        """Create hierarchical chunks based on header structure."""
        chunks = []
        relationships = []
        
        # Build header hierarchy
        header_stack = []  # Stack to track current hierarchy
        current_section = []  # Elements in current section
        section_start = 0
        
        for i, element in enumerate(elements):
            if element.element_type == MarkdownElementType.HEADER:
                # Process current section before starting new one
                if current_section:
                    chunk = self._create_section_chunk(
                        current_section, section_start, header_stack
                    )
                    if chunk:
                        chunks.append(chunk)
                
                # Update header hierarchy
                self._update_header_stack(header_stack, element)
                
                # Start new section
                current_section = [element]
                section_start = i
            else:
                current_section.append(element)
        
        # Process final section
        if current_section:
            chunk = self._create_section_chunk(
                current_section, section_start, header_stack
            )
            if chunk:
                chunks.append(chunk)
        
        # Create hierarchical relationships
        relationships = self._create_hierarchical_relationships(chunks)
        
        logger.info(f"Created {len(chunks)} hierarchical chunks with {len(relationships)} relationships")
        return chunks, relationships
    
    def _update_header_stack(self, header_stack: List[MarkdownElement], new_header: MarkdownElement):
        """Update header hierarchy stack."""
        new_level = new_header.level
        
        # Remove headers at same or deeper level
        while header_stack and header_stack[-1].level >= new_level:
            header_stack.pop()
        
        # Add new header
        header_stack.append(new_header)
    
    def _create_section_chunk(
        self, 
        elements: List[MarkdownElement], 
        section_start: int,
        header_stack: List[MarkdownElement]
    ) -> MarkdownChunk:
        """Create a chunk for a document section."""
        if not elements:
            return None
        
        # Build content from elements
        content_parts = []
        element_types = set()
        
        for element in elements:
            content_parts.append(element.content)
            element_types.add(element.element_type.value)
        
        content = '\n\n'.join(content_parts)
        
        # Skip if too small
        if len(content) < self.min_chunk_size:
            return None
        
        # Truncate if too large
        if len(content) > self.max_chunk_size:
            content = content[:self.max_chunk_size] + "..."
        
        # Build hierarchical path
        hierarchy_path = [h.content for h in header_stack]
        current_level = header_stack[-1].level if header_stack else 0
        
        chunk_id = f"md_hierarchical_{uuid.uuid4().hex[:8]}"
        
        return MarkdownChunk(
            chunk_id=chunk_id,
            content=content,
            elements=elements,
            chunk_type="hierarchical_section",
            structural_metadata={
                "hierarchy_path": hierarchy_path,
                "header_level": current_level,
                "section_type": self._determine_section_type(elements),
                "element_count": len(elements),
                "element_types": list(element_types)
            },
            semantic_metadata={
                "has_code": any(e.element_type == MarkdownElementType.CODE_BLOCK for e in elements),
                "has_tables": any(e.element_type == MarkdownElementType.TABLE for e in elements),
                "has_lists": any(e.element_type == MarkdownElementType.LIST for e in elements),
                "has_links": any(e.element_type == MarkdownElementType.LINK for e in elements)
            },
            position_start=elements[0].position,
            position_end=elements[-1].position,
            word_count=len(content.split())
        )
    
    def _determine_section_type(self, elements: List[MarkdownElement]) -> str:
        """Determine the type of section based on its elements."""
        element_types = [e.element_type for e in elements]
        
        if MarkdownElementType.CODE_BLOCK in element_types:
            return "code_section"
        elif MarkdownElementType.TABLE in element_types:
            return "data_section"
        elif MarkdownElementType.LIST in element_types:
            return "list_section"
        elif any(e.element_type == MarkdownElementType.HEADER for e in elements):
            return "header_section"
        else:
            return "content_section"
    
    def _create_hierarchical_relationships(self, chunks: List[MarkdownChunk]) -> List[MarkdownRelationship]:
        """Create parent-child and sibling relationships."""
        relationships = []
        
        # Group chunks by hierarchy level
        level_groups = {}
        for chunk in chunks:
            level = chunk.structural_metadata.get("header_level", 0)
            if level not in level_groups:
                level_groups[level] = []
            level_groups[level].append(chunk)
        
        # Create parent-child relationships
        sorted_levels = sorted(level_groups.keys())
        for i in range(len(sorted_levels) - 1):
            parent_level = sorted_levels[i]
            child_level = sorted_levels[i + 1]
            
            for parent_chunk in level_groups[parent_level]:
                for child_chunk in level_groups[child_level]:
                    # Check if child belongs to parent by hierarchy path
                    parent_path = parent_chunk.structural_metadata["hierarchy_path"]
                    child_path = child_chunk.structural_metadata["hierarchy_path"]
                    
                    if (len(child_path) > len(parent_path) and 
                        child_path[:len(parent_path)] == parent_path):
                        
                        relationships.append(MarkdownRelationship(
                            source_chunk_id=parent_chunk.chunk_id,
                            target_chunk_id=child_chunk.chunk_id,
                            relationship_type="parent_child",
                            relationship_metadata={
                                "parent_level": parent_level,
                                "child_level": child_level,
                                "hierarchy_distance": child_level - parent_level
                            }
                        ))
        
        # Create sibling relationships
        for level, chunks_at_level in level_groups.items():
            for i in range(len(chunks_at_level) - 1):
                current = chunks_at_level[i]
                next_chunk = chunks_at_level[i + 1]
                
                relationships.append(MarkdownRelationship(
                    source_chunk_id=current.chunk_id,
                    target_chunk_id=next_chunk.chunk_id,
                    relationship_type="sibling",
                    relationship_metadata={
                        "level": level,
                        "sequence_position": i
                    }
                ))
        
        return relationships