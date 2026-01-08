"""
Markdown Strategy Factory
========================

Factory for creating and managing markdown chunking strategies.
"""

import logging
from typing import Dict, Type, Any

from app.markdown.base import MarkdownChunkingStrategy
from app.markdown.strategies.structure_aware_hierarchical import StructureAwareHierarchicalChunker
from app.markdown.strategies.semantic_block_fusion import SemanticBlockFusionChunker
from app.markdown.strategies.cross_reference_linking import CrossReferenceLinkingChunker
from app.markdown.strategies.code_context_coupling import CodeContextCouplingChunker
from app.markdown.strategies.remaining_strategies import (
    MultiModalEmbeddingFusionChunker,
    SlidingSemanticWindowsChunker,
    TableAwareContextualChunker,
    TopicModelingCoherenceChunker,
    AttentionWeightedChunker,
    MarkdownNativeEnhancementChunker
)

logger = logging.getLogger(__name__)


class MarkdownStrategyFactory:
    """Factory for creating markdown chunking strategies."""
    
    def __init__(self):
        self._strategies: Dict[MarkdownChunkingStrategy, Type] = {
            MarkdownChunkingStrategy.STRUCTURE_AWARE_HIERARCHICAL: StructureAwareHierarchicalChunker,
            MarkdownChunkingStrategy.SEMANTIC_BLOCK_FUSION: SemanticBlockFusionChunker,
            MarkdownChunkingStrategy.CROSS_REFERENCE_LINKING: CrossReferenceLinkingChunker,
            MarkdownChunkingStrategy.CODE_CONTEXT_COUPLING: CodeContextCouplingChunker,
            MarkdownChunkingStrategy.MULTIMODAL_EMBEDDING_FUSION: MultiModalEmbeddingFusionChunker,
            MarkdownChunkingStrategy.SLIDING_SEMANTIC_WINDOWS: SlidingSemanticWindowsChunker,
            MarkdownChunkingStrategy.TABLE_AWARE_CONTEXTUAL: TableAwareContextualChunker,
            MarkdownChunkingStrategy.TOPIC_MODELING_COHERENCE: TopicModelingCoherenceChunker,
            MarkdownChunkingStrategy.ATTENTION_WEIGHTED: AttentionWeightedChunker,
            MarkdownChunkingStrategy.MARKDOWN_NATIVE_ENHANCEMENT: MarkdownNativeEnhancementChunker
        }
    
    def create_strategy(self, strategy_type: MarkdownChunkingStrategy, **kwargs) -> Any:
        """Create a chunking strategy instance."""
        if strategy_type not in self._strategies:
            raise ValueError(f"Unknown strategy type: {strategy_type}")
        
        strategy_class = self._strategies[strategy_type]
        
        try:
            return strategy_class(**kwargs)
        except Exception as e:
            logger.error(f"Failed to create strategy {strategy_type}: {e}")
            raise
    
    def get_available_strategies(self) -> list[MarkdownChunkingStrategy]:
        """Get list of available strategies."""
        return list(self._strategies.keys())
    
    def get_strategy_info(self, strategy_type: MarkdownChunkingStrategy) -> Dict[str, Any]:
        """Get information about a specific strategy."""
        strategy_info = {
            MarkdownChunkingStrategy.STRUCTURE_AWARE_HIERARCHICAL: {
                "name": "Structure-Aware Hierarchical",
                "description": "Respects natural document hierarchy defined by markdown headers",
                "best_for": ["Technical documentation", "Structured content", "API documentation"],
                "pros": ["Preserves document structure", "Maintains context hierarchy", "Good for navigation"],
                "cons": ["May create large chunks", "Less flexible chunking"]
            },
            MarkdownChunkingStrategy.SEMANTIC_BLOCK_FUSION: {
                "name": "Semantic Block Fusion", 
                "description": "Combines related markdown elements into coherent semantic units",
                "best_for": ["Mixed content", "Tutorial documentation", "Complex layouts"],
                "pros": ["Intelligent content grouping", "Preserves semantic relationships", "Flexible chunk sizes"],
                "cons": ["More complex processing", "May miss some relationships"]
            },
            MarkdownChunkingStrategy.CROSS_REFERENCE_LINKING: {
                "name": "Cross-Reference Linking",
                "description": "Uses internal links and references to create relationship-aware chunks",
                "best_for": ["Wiki-style content", "Interconnected documentation", "Reference materials"],
                "pros": ["Preserves link relationships", "Good for connected content", "Builds citation graphs"],
                "cons": ["Requires link-rich content", "Complex relationship mapping"]
            },
            MarkdownChunkingStrategy.CODE_CONTEXT_COUPLING: {
                "name": "Code-Context Coupling",
                "description": "Pairs code blocks with their surrounding explanatory text",
                "best_for": ["Code tutorials", "API examples", "Technical guides"],
                "pros": ["Preserves code-explanation relationships", "Language-aware processing", "Good for technical content"],
                "cons": ["Focused on code content", "May not handle non-code well"]
            },
            MarkdownChunkingStrategy.MULTIMODAL_EMBEDDING_FUSION: {
                "name": "Multi-Modal Embedding Fusion",
                "description": "Generates separate embeddings for different content types and fuses them",
                "best_for": ["Mixed media content", "Complex documents", "Multi-format materials"],
                "pros": ["Content-type aware", "Optimized embeddings", "Handles diverse content"],
                "cons": ["More complex processing", "Requires fusion logic"]
            },
            MarkdownChunkingStrategy.SLIDING_SEMANTIC_WINDOWS: {
                "name": "Sliding Semantic Windows",
                "description": "Creates overlapping chunks based on semantic similarity",
                "best_for": ["Continuous narrative", "Dense information", "Context-dependent content"],
                "pros": ["Smooth context transitions", "Overlap prevents information loss", "Semantic awareness"],
                "cons": ["May create redundant information", "More chunks to process"]
            },
            MarkdownChunkingStrategy.TABLE_AWARE_CONTEXTUAL: {
                "name": "Table-Aware Contextual",
                "description": "Special handling for markdown tables with surrounding context",
                "best_for": ["Data documentation", "Specification sheets", "Reports with tables"],
                "pros": ["Preserves table structure", "Includes contextual information", "Good for data content"],
                "cons": ["Specialized for table content", "May not handle other content well"]
            },
            MarkdownChunkingStrategy.TOPIC_MODELING_COHERENCE: {
                "name": "Topic Modeling with Coherence",
                "description": "Uses topic modeling to group related content across boundaries",
                "best_for": ["Large documents", "Multi-topic content", "Knowledge bases"],
                "pros": ["Topic-aware grouping", "Good for large documents", "Coherence-based"],
                "cons": ["Requires topic modeling", "May lose document structure"]
            },
            MarkdownChunkingStrategy.ATTENTION_WEIGHTED: {
                "name": "Attention-Weighted",
                "description": "Uses attention patterns to identify important content relationships",
                "best_for": ["Dense information", "Important content highlighting", "Summary generation"],
                "pros": ["Focuses on important content", "Attention-aware processing", "Good for key information"],
                "cons": ["Attention calculation complexity", "May miss subtle relationships"]
            },
            MarkdownChunkingStrategy.MARKDOWN_NATIVE_ENHANCEMENT: {
                "name": "Markdown-Native Enhancement",
                "description": "Enhances embeddings with markdown-specific structural information",
                "best_for": ["Structure-dependent search", "Format-aware applications", "Markdown-specific tasks"],
                "pros": ["Preserves markdown structure", "Format-aware embeddings", "Good for markdown-specific search"],
                "cons": ["Markdown-specific", "May not generalize to other formats"]
            }
        }
        
        return strategy_info.get(strategy_type, {
            "name": strategy_type.value,
            "description": "Strategy description not available",
            "best_for": [],
            "pros": [],
            "cons": []
        })