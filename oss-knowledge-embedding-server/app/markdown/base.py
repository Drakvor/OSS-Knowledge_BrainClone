"""
Markdown Processing Base Classes
===============================

Base models and enums for markdown-specific processing.
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime


class MarkdownElementType(Enum):
    """Types of markdown elements."""
    HEADER = "header"
    PARAGRAPH = "paragraph"
    CODE_BLOCK = "code_block"
    INLINE_CODE = "inline_code"
    LIST = "list"
    LIST_ITEM = "list_item"
    TABLE = "table"
    TABLE_ROW = "table_row"
    BLOCKQUOTE = "blockquote"
    LINK = "link"
    IMAGE = "image"
    HORIZONTAL_RULE = "horizontal_rule"
    LINE_BREAK = "line_break"
    EMPHASIS = "emphasis"
    STRONG = "strong"


class MarkdownChunkingStrategy(Enum):
    """Markdown-specific chunking strategies."""
    STRUCTURE_AWARE_HIERARCHICAL = "structure_aware_hierarchical"
    SEMANTIC_BLOCK_FUSION = "semantic_block_fusion"
    CROSS_REFERENCE_LINKING = "cross_reference_linking"
    CODE_CONTEXT_COUPLING = "code_context_coupling"
    MULTIMODAL_EMBEDDING_FUSION = "multimodal_embedding_fusion"
    SLIDING_SEMANTIC_WINDOWS = "sliding_semantic_windows"
    TABLE_AWARE_CONTEXTUAL = "table_aware_contextual"
    TOPIC_MODELING_COHERENCE = "topic_modeling_coherence"
    ATTENTION_WEIGHTED = "attention_weighted"
    MARKDOWN_NATIVE_ENHANCEMENT = "markdown_native_enhancement"


@dataclass
class MarkdownElement:
    """Represents a parsed markdown element."""
    element_type: MarkdownElementType
    content: str
    metadata: Dict[str, Any]
    position: int
    level: Optional[int] = None  # For headers
    language: Optional[str] = None  # For code blocks
    url: Optional[str] = None  # For links/images
    alt_text: Optional[str] = None  # For images
    list_type: Optional[str] = None  # For lists (ordered/unordered)
    
    
@dataclass
class MarkdownChunk:
    """Represents a processed markdown chunk with enhanced metadata."""
    chunk_id: str
    content: str
    elements: List[MarkdownElement]
    chunk_type: str
    structural_metadata: Dict[str, Any]
    semantic_metadata: Dict[str, Any]
    position_start: int
    position_end: int
    word_count: int
    created_at: datetime = datetime.now()
    

@dataclass
class MarkdownRelationship:
    """Represents relationships between markdown chunks."""
    source_chunk_id: str
    target_chunk_id: str
    relationship_type: str
    relationship_metadata: Dict[str, Any]
    confidence: float = 1.0
    

@dataclass
class MarkdownProcessingResult:
    """Result of markdown processing."""
    chunks: List[MarkdownChunk]
    relationships: List[MarkdownRelationship]
    document_metadata: Dict[str, Any]
    processing_stats: Dict[str, Any]
    strategy_used: MarkdownChunkingStrategy
    processing_time_ms: float