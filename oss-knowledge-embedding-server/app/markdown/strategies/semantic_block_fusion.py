"""
Semantic Block Fusion Strategy
==============================

Combines related markdown elements like text paragraphs, code blocks, 
lists, and tables into coherent semantic units. Groups consecutive 
related elements together and detects topic boundaries.
"""

import uuid
import logging
from typing import List, Dict, Any, Set
from datetime import datetime

from app.markdown.base import (
    MarkdownElement, MarkdownElementType, MarkdownChunk, 
    MarkdownRelationship, MarkdownChunkingStrategy
)

logger = logging.getLogger(__name__)


class SemanticBlockFusionChunker:
    """Chunks elements by semantic relatedness and content type."""
    
    def __init__(self, min_chunk_size: int = 150, max_chunk_size: int = 1200):
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.strategy = MarkdownChunkingStrategy.SEMANTIC_BLOCK_FUSION
        
        # Element affinity groups - elements that work well together
        self.element_affinities = {
            MarkdownElementType.PARAGRAPH: {MarkdownElementType.PARAGRAPH, MarkdownElementType.BLOCKQUOTE},
            MarkdownElementType.CODE_BLOCK: {MarkdownElementType.PARAGRAPH, MarkdownElementType.HEADER},
            MarkdownElementType.LIST: {MarkdownElementType.PARAGRAPH, MarkdownElementType.LIST},
            MarkdownElementType.TABLE: {MarkdownElementType.PARAGRAPH, MarkdownElementType.HEADER},
            MarkdownElementType.BLOCKQUOTE: {MarkdownElementType.PARAGRAPH, MarkdownElementType.BLOCKQUOTE},
            MarkdownElementType.HEADER: {MarkdownElementType.PARAGRAPH, MarkdownElementType.LIST, MarkdownElementType.CODE_BLOCK}
        }
    
    def chunk(self, elements: List[MarkdownElement]) -> tuple[List[MarkdownChunk], List[MarkdownRelationship]]:
        """Create semantic blocks by fusing related elements."""
        chunks = []
        relationships = []
        
        if not elements:
            return chunks, relationships
        
        # Group elements into semantic blocks
        semantic_blocks = self._create_semantic_blocks(elements)
        
        # Convert blocks to chunks
        for block_idx, block in enumerate(semantic_blocks):
            chunk = self._create_semantic_chunk(block, block_idx)
            if chunk:
                chunks.append(chunk)
        
        # Create relationships between chunks
        relationships = self._create_semantic_relationships(chunks)
        
        logger.info(f"Created {len(chunks)} semantic blocks with {len(relationships)} relationships")
        return chunks, relationships
    
    def _create_semantic_blocks(self, elements: List[MarkdownElement]) -> List[List[MarkdownElement]]:
        """Group elements into semantically coherent blocks."""
        if not elements:
            return []
        
        blocks = []
        current_block = [elements[0]]
        current_theme = self._get_element_theme(elements[0])
        current_size = len(elements[0].content)
        
        for element in elements[1:]:
            element_theme = self._get_element_theme(element)
            element_size = len(element.content)
            
            # Check if element should be in current block
            should_group = (
                self._are_semantically_related(current_block[-1], element) and
                current_size + element_size <= self.max_chunk_size and
                self._themes_compatible(current_theme, element_theme)
            )
            
            if should_group:
                current_block.append(element)
                current_size += element_size
                current_theme = self._merge_themes(current_theme, element_theme)
            else:
                # Start new block
                if current_size >= self.min_chunk_size:
                    blocks.append(current_block)
                else:
                    # Merge small blocks with previous if possible
                    if blocks and self._can_merge_blocks(blocks[-1], current_block):
                        blocks[-1].extend(current_block)
                    else:
                        blocks.append(current_block)
                
                current_block = [element]
                current_theme = element_theme
                current_size = element_size
        
        # Add final block
        if current_block:
            if current_size >= self.min_chunk_size or not blocks:
                blocks.append(current_block)
            elif blocks:
                blocks[-1].extend(current_block)
        
        return blocks
    
    def _are_semantically_related(self, elem1: MarkdownElement, elem2: MarkdownElement) -> bool:
        """Check if two elements are semantically related."""
        # Check element type affinity
        if elem1.element_type in self.element_affinities:
            if elem2.element_type in self.element_affinities[elem1.element_type]:
                return True
        
        # Special cases for semantic relationships
        
        # Code blocks often relate to preceding paragraphs (explanations)
        if (elem1.element_type == MarkdownElementType.PARAGRAPH and 
            elem2.element_type == MarkdownElementType.CODE_BLOCK):
            return self._paragraph_explains_code(elem1, elem2)
        
        # Headers group with following content
        if (elem1.element_type == MarkdownElementType.HEADER and
            elem2.element_type in {MarkdownElementType.PARAGRAPH, MarkdownElementType.LIST}):
            return True
        
        # Lists of similar type can be grouped
        if (elem1.element_type == MarkdownElementType.LIST and 
            elem2.element_type == MarkdownElementType.LIST):
            return elem1.list_type == elem2.list_type
        
        # Tables group with explanatory paragraphs
        if (elem1.element_type == MarkdownElementType.PARAGRAPH and 
            elem2.element_type == MarkdownElementType.TABLE):
            return self._paragraph_explains_table(elem1, elem2)
        
        return False
    
    def _paragraph_explains_code(self, paragraph: MarkdownElement, code: MarkdownElement) -> bool:
        """Check if paragraph explains the following code block."""
        para_words = set(paragraph.content.lower().split())
        code_words = set(code.content.lower().split())
        
        # Look for explanatory keywords
        explanatory_keywords = {'example', 'following', 'code', 'function', 'method', 'class'}
        has_explanatory = bool(para_words & explanatory_keywords)
        
        # Look for shared technical terms
        shared_terms = para_words & code_words
        has_shared_terms = len(shared_terms) > 1
        
        return has_explanatory or has_shared_terms
    
    def _paragraph_explains_table(self, paragraph: MarkdownElement, table: MarkdownElement) -> bool:
        """Check if paragraph explains the following table."""
        para_lower = paragraph.content.lower()
        table_headers = table.metadata.get('headers', [])
        
        # Check if paragraph mentions table headers
        header_mentions = sum(1 for header in table_headers 
                             if header.lower() in para_lower)
        
        # Look for table-related keywords
        table_keywords = {'table', 'data', 'column', 'row', 'following', 'above', 'below'}
        has_table_keywords = any(keyword in para_lower for keyword in table_keywords)
        
        return header_mentions > 0 or has_table_keywords
    
    def _get_element_theme(self, element: MarkdownElement) -> Set[str]:
        """Extract thematic keywords from element."""
        content = element.content.lower()
        
        # Technical themes
        themes = set()
        
        if element.element_type == MarkdownElementType.CODE_BLOCK:
            themes.add('code')
            if element.language:
                themes.add(f'lang_{element.language}')
        
        elif element.element_type == MarkdownElementType.TABLE:
            themes.add('data')
            themes.add('table')
        
        elif element.element_type == MarkdownElementType.LIST:
            themes.add('list')
            if element.list_type:
                themes.add(element.list_type)
        
        elif element.element_type == MarkdownElementType.HEADER:
            themes.add('header')
            themes.add(f'level_{element.level}')
        
        # Content-based themes
        technical_keywords = ['api', 'function', 'method', 'class', 'variable', 'config']
        documentation_keywords = ['guide', 'tutorial', 'example', 'usage', 'how to']
        reference_keywords = ['reference', 'documentation', 'spec', 'specification']
        
        if any(keyword in content for keyword in technical_keywords):
            themes.add('technical')
        if any(keyword in content for keyword in documentation_keywords):
            themes.add('documentation')
        if any(keyword in content for keyword in reference_keywords):
            themes.add('reference')
        
        return themes
    
    def _themes_compatible(self, theme1: Set[str], theme2: Set[str]) -> bool:
        """Check if two themes are compatible for grouping."""
        # Empty themes are compatible with anything
        if not theme1 or not theme2:
            return True
        
        # Shared themes indicate compatibility
        shared = theme1 & theme2
        if shared:
            return True
        
        # Compatible theme pairs
        compatible_pairs = [
            ('code', 'technical'),
            ('documentation', 'technical'),
            ('table', 'data'),
            ('list', 'documentation')
        ]
        
        for t1, t2 in compatible_pairs:
            if (t1 in theme1 and t2 in theme2) or (t2 in theme1 and t1 in theme2):
                return True
        
        return False
    
    def _merge_themes(self, theme1: Set[str], theme2: Set[str]) -> Set[str]:
        """Merge two theme sets."""
        return theme1 | theme2
    
    def _can_merge_blocks(self, block1: List[MarkdownElement], block2: List[MarkdownElement]) -> bool:
        """Check if two small blocks can be merged."""
        total_size = sum(len(elem.content) for elem in block1 + block2)
        return total_size <= self.max_chunk_size
    
    def _create_semantic_chunk(self, block: List[MarkdownElement], block_idx: int) -> MarkdownChunk:
        """Create a chunk from a semantic block."""
        if not block:
            return None
        
        # Build content
        content_parts = []
        element_types = set()
        themes = set()
        
        for element in block:
            content_parts.append(element.content)
            element_types.add(element.element_type.value)
            themes.update(self._get_element_theme(element))
        
        content = '\n\n'.join(content_parts)
        
        # Determine block type
        block_type = self._determine_block_type(block)
        
        chunk_id = f"md_semantic_{uuid.uuid4().hex[:8]}"
        
        return MarkdownChunk(
            chunk_id=chunk_id,
            content=content,
            elements=block,
            chunk_type=f"semantic_{block_type}",
            structural_metadata={
                "block_index": block_idx,
                "element_count": len(block),
                "element_types": list(element_types),
                "dominant_type": max(element_types, key=lambda t: 
                    sum(1 for e in block if e.element_type.value == t))
            },
            semantic_metadata={
                "themes": list(themes),
                "has_code": "code" in themes,
                "has_data": "data" in themes or "table" in themes,
                "content_category": self._categorize_content(themes),
                "technical_level": self._assess_technical_level(block)
            },
            position_start=block[0].position,
            position_end=block[-1].position,
            word_count=len(content.split())
        )
    
    def _determine_block_type(self, block: List[MarkdownElement]) -> str:
        """Determine the type of semantic block."""
        types = [elem.element_type for elem in block]
        
        if MarkdownElementType.CODE_BLOCK in types:
            return "code_explanation"
        elif MarkdownElementType.TABLE in types:
            return "data_presentation"
        elif MarkdownElementType.LIST in types:
            return "structured_content"
        elif MarkdownElementType.HEADER in types:
            return "section_content"
        else:
            return "prose_content"
    
    def _categorize_content(self, themes: Set[str]) -> str:
        """Categorize content based on themes."""
        if 'code' in themes or 'technical' in themes:
            return 'technical'
        elif 'documentation' in themes:
            return 'documentation'
        elif 'reference' in themes:
            return 'reference'
        elif 'data' in themes or 'table' in themes:
            return 'data'
        else:
            return 'general'
    
    def _assess_technical_level(self, block: List[MarkdownElement]) -> str:
        """Assess technical complexity level."""
        code_blocks = sum(1 for e in block if e.element_type == MarkdownElementType.CODE_BLOCK)
        technical_terms = 0
        
        for element in block:
            content_lower = element.content.lower()
            technical_keywords = ['function', 'method', 'class', 'api', 'parameter', 'return']
            technical_terms += sum(1 for keyword in technical_keywords if keyword in content_lower)
        
        if code_blocks > 0 or technical_terms > 5:
            return 'high'
        elif technical_terms > 2:
            return 'medium'
        else:
            return 'low'
    
    def _create_semantic_relationships(self, chunks: List[MarkdownChunk]) -> List[MarkdownRelationship]:
        """Create relationships between semantic chunks."""
        relationships = []
        
        # Sequential relationships
        for i in range(len(chunks) - 1):
            current = chunks[i]
            next_chunk = chunks[i + 1]
            
            relationships.append(MarkdownRelationship(
                source_chunk_id=current.chunk_id,
                target_chunk_id=next_chunk.chunk_id,
                relationship_type="sequential",
                relationship_metadata={
                    "sequence_position": i,
                    "content_transition": self._analyze_content_transition(current, next_chunk)
                }
            ))
        
        # Thematic relationships
        for i, chunk1 in enumerate(chunks):
            themes1 = set(chunk1.semantic_metadata.get('themes', []))
            
            for j, chunk2 in enumerate(chunks[i + 2:], i + 2):  # Skip adjacent chunks
                themes2 = set(chunk2.semantic_metadata.get('themes', []))
                
                shared_themes = themes1 & themes2
                if len(shared_themes) >= 2:  # Strong thematic connection
                    relationships.append(MarkdownRelationship(
                        source_chunk_id=chunk1.chunk_id,
                        target_chunk_id=chunk2.chunk_id,
                        relationship_type="thematic",
                        relationship_metadata={
                            "shared_themes": list(shared_themes),
                            "theme_similarity": len(shared_themes) / len(themes1 | themes2)
                        },
                        confidence=len(shared_themes) / 3.0  # Normalize confidence
                    ))
        
        return relationships
    
    def _analyze_content_transition(self, chunk1: MarkdownChunk, chunk2: MarkdownChunk) -> str:
        """Analyze the type of transition between chunks."""
        type1 = chunk1.chunk_type
        type2 = chunk2.chunk_type
        
        if 'code' in type1 and 'prose' in type2:
            return 'code_to_explanation'
        elif 'prose' in type1 and 'code' in type2:
            return 'explanation_to_code'
        elif 'data' in type1 and 'prose' in type2:
            return 'data_to_analysis'
        elif type1 == type2:
            return 'same_type_continuation'
        else:
            return 'topic_shift'