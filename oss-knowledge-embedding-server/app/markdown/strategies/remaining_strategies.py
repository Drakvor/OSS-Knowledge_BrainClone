"""
Remaining Markdown Chunking Strategies (5-10)
=============================================

Implementation of the remaining 6 markdown-specific chunking strategies:
5. Multi-Modal Embedding Fusion
6. Sliding Semantic Windows  
7. Table-Aware Contextual Chunking
8. Topic Modeling with Coherence Scoring
9. Attention-Weighted Chunking
10. Markdown-Native Embedding Enhancement
"""

import uuid
import logging
import re
from typing import List, Dict, Any, Set, Optional
from datetime import datetime
from collections import defaultdict

from app.markdown.base import (
    MarkdownElement, MarkdownElementType, MarkdownChunk, 
    MarkdownRelationship, MarkdownChunkingStrategy
)

logger = logging.getLogger(__name__)


class MultiModalEmbeddingFusionChunker:
    """Strategy 5: Multi-Modal Embedding Fusion"""
    
    def __init__(self, min_chunk_size: int = 200, max_chunk_size: int = 1000):
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.strategy = MarkdownChunkingStrategy.MULTIMODAL_EMBEDDING_FUSION
    
    def chunk(self, elements: List[MarkdownElement]) -> tuple[List[MarkdownChunk], List[MarkdownRelationship]]:
        """Create chunks optimized for multi-modal embeddings."""
        chunks = []
        relationships = []
        
        # Group elements by content type for specialized processing
        content_groups = self._group_by_content_type(elements)
        
        for group_type, group_elements in content_groups.items():
            group_chunks = self._create_modal_chunks(group_elements, group_type)
            chunks.extend(group_chunks)
        
        # Create cross-modal relationships
        relationships = self._create_cross_modal_relationships(chunks)
        
        logger.info(f"Created {len(chunks)} multi-modal chunks with {len(relationships)} relationships")
        return chunks, relationships
    
    def _group_by_content_type(self, elements: List[MarkdownElement]) -> Dict[str, List[MarkdownElement]]:
        """Group elements by content type for modal processing."""
        groups = {
            'text': [],
            'code': [],
            'structured': [],  # tables, lists
            'media': []  # images, links
        }
        
        for element in elements:
            if element.element_type in {MarkdownElementType.PARAGRAPH, MarkdownElementType.HEADER, MarkdownElementType.BLOCKQUOTE}:
                groups['text'].append(element)
            elif element.element_type == MarkdownElementType.CODE_BLOCK:
                groups['code'].append(element)
            elif element.element_type in {MarkdownElementType.TABLE, MarkdownElementType.LIST}:
                groups['structured'].append(element)
            elif element.element_type in {MarkdownElementType.IMAGE, MarkdownElementType.LINK}:
                groups['media'].append(element)
        
        return {k: v for k, v in groups.items() if v}  # Remove empty groups
    
    def _create_modal_chunks(self, elements: List[MarkdownElement], modal_type: str) -> List[MarkdownChunk]:
        """Create chunks optimized for specific content modality."""
        chunks = []
        current_chunk = []
        current_size = 0
        
        for element in elements:
            element_size = len(element.content)
            
            if current_size + element_size > self.max_chunk_size and current_chunk:
                chunk = self._create_chunk(current_chunk, modal_type)
                if chunk:
                    chunks.append(chunk)
                current_chunk = [element]
                current_size = element_size
            else:
                current_chunk.append(element)
                current_size += element_size
        
        if current_chunk:
            chunk = self._create_chunk(current_chunk, modal_type)
            if chunk:
                chunks.append(chunk)
        
        return chunks
    
    def _create_chunk(self, elements: List[MarkdownElement], modal_type: str) -> Optional[MarkdownChunk]:
        """Create a modal-specific chunk."""
        if not elements:
            return None
        
        content = '\n\n'.join(elem.content for elem in elements)
        if len(content) < self.min_chunk_size:
            return None
        
        chunk_id = f"md_multimodal_{modal_type}_{uuid.uuid4().hex[:8]}"
        
        return MarkdownChunk(
            chunk_id=chunk_id,
            content=content,
            elements=elements,
            chunk_type=f"multimodal_{modal_type}",
            structural_metadata={
                "modal_type": modal_type,
                "element_count": len(elements)
            },
            semantic_metadata={
                "content_modality": modal_type,
                "fusion_weight": self._get_fusion_weight(modal_type)
            },
            position_start=elements[0].position,
            position_end=elements[-1].position,
            word_count=len(content.split())
        )
    
    def _get_fusion_weight(self, modal_type: str) -> float:
        """Get fusion weight for different modalities."""
        weights = {
            'text': 0.4,
            'code': 0.3,
            'structured': 0.2,
            'media': 0.1
        }
        return weights.get(modal_type, 0.25)
    
    def _create_cross_modal_relationships(self, chunks: List[MarkdownChunk]) -> List[MarkdownRelationship]:
        """Create relationships between different modalities."""
        relationships = []
        
        for i, chunk1 in enumerate(chunks):
            modal1 = chunk1.semantic_metadata.get('content_modality')
            for chunk2 in chunks[i + 1:]:
                modal2 = chunk2.semantic_metadata.get('content_modality')
                
                if modal1 != modal2 and self._are_modally_related(chunk1, chunk2):
                    relationships.append(MarkdownRelationship(
                        source_chunk_id=chunk1.chunk_id,
                        target_chunk_id=chunk2.chunk_id,
                        relationship_type="cross_modal",
                        relationship_metadata={
                            "source_modality": modal1,
                            "target_modality": modal2
                        }
                    ))
        
        return relationships
    
    def _are_modally_related(self, chunk1: MarkdownChunk, chunk2: MarkdownChunk) -> bool:
        """Check if chunks from different modalities are related."""
        # Simplified proximity-based relationship
        return abs(chunk1.position_start - chunk2.position_start) < 500


class SlidingSemanticWindowsChunker:
    """Strategy 6: Sliding Semantic Windows"""
    
    def __init__(self, window_size: int = 5, overlap: int = 2, min_chunk_size: int = 150):
        self.window_size = window_size
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size
        self.strategy = MarkdownChunkingStrategy.SLIDING_SEMANTIC_WINDOWS
    
    def chunk(self, elements: List[MarkdownElement]) -> tuple[List[MarkdownChunk], List[MarkdownRelationship]]:
        """Create sliding windows based on semantic coherence."""
        chunks = []
        relationships = []
        
        # Create sliding windows
        for i in range(0, len(elements) - self.window_size + 1, self.window_size - self.overlap):
            window_elements = elements[i:i + self.window_size]
            
            # Calculate semantic coherence
            coherence = self._calculate_coherence(window_elements)
            
            if coherence > 0.3:  # Threshold for semantic coherence
                chunk = self._create_window_chunk(window_elements, i, coherence)
                if chunk:
                    chunks.append(chunk)
        
        # Create overlap relationships
        relationships = self._create_overlap_relationships(chunks)
        
        logger.info(f"Created {len(chunks)} semantic window chunks with {len(relationships)} relationships")
        return chunks, relationships
    
    def _calculate_coherence(self, elements: List[MarkdownElement]) -> float:
        """Calculate semantic coherence of elements."""
        if len(elements) < 2:
            return 1.0
        
        # Simple keyword-based coherence
        all_words = []
        for element in elements:
            words = set(word.lower() for word in element.content.split() if len(word) > 3)
            all_words.append(words)
        
        # Calculate pairwise word overlap
        total_pairs = 0
        overlap_sum = 0
        
        for i in range(len(all_words)):
            for j in range(i + 1, len(all_words)):
                total_pairs += 1
                shared = len(all_words[i] & all_words[j])
                union = len(all_words[i] | all_words[j])
                if union > 0:
                    overlap_sum += shared / union
        
        return overlap_sum / total_pairs if total_pairs > 0 else 0.0
    
    def _create_window_chunk(self, elements: List[MarkdownElement], window_idx: int, coherence: float) -> Optional[MarkdownChunk]:
        """Create a chunk from a semantic window."""
        content = '\n\n'.join(elem.content for elem in elements)
        
        if len(content) < self.min_chunk_size:
            return None
        
        chunk_id = f"md_semantic_window_{uuid.uuid4().hex[:8]}"
        
        return MarkdownChunk(
            chunk_id=chunk_id,
            content=content,
            elements=elements,
            chunk_type="semantic_window",
            structural_metadata={
                "window_index": window_idx,
                "window_size": len(elements),
                "coherence_score": coherence
            },
            semantic_metadata={
                "semantic_coherence": coherence,
                "window_overlap": self.overlap
            },
            position_start=elements[0].position,
            position_end=elements[-1].position,
            word_count=len(content.split())
        )
    
    def _create_overlap_relationships(self, chunks: List[MarkdownChunk]) -> List[MarkdownRelationship]:
        """Create relationships between overlapping windows."""
        relationships = []
        
        for i, chunk in enumerate(chunks[:-1]):
            next_chunk = chunks[i + 1]
            
            relationships.append(MarkdownRelationship(
                source_chunk_id=chunk.chunk_id,
                target_chunk_id=next_chunk.chunk_id,
                relationship_type="semantic_overlap",
                relationship_metadata={
                    "overlap_elements": self.overlap
                }
            ))
        
        return relationships


class TableAwareContextualChunker:
    """Strategy 7: Table-Aware Contextual Chunking"""
    
    def __init__(self, context_range: int = 2):
        self.context_range = context_range
        self.strategy = MarkdownChunkingStrategy.TABLE_AWARE_CONTEXTUAL
    
    def chunk(self, elements: List[MarkdownElement]) -> tuple[List[MarkdownChunk], List[MarkdownRelationship]]:
        """Create chunks that preserve table context."""
        chunks = []
        relationships = []
        processed_indices = set()
        
        # Find tables and create table-context chunks
        for i, element in enumerate(elements):
            if element.element_type == MarkdownElementType.TABLE and i not in processed_indices:
                table_chunk = self._create_table_context_chunk(elements, i)
                if table_chunk:
                    chunks.append(table_chunk)
                    # Mark surrounding elements as processed
                    start_idx = max(0, i - self.context_range)
                    end_idx = min(len(elements), i + self.context_range + 1)
                    processed_indices.update(range(start_idx, end_idx))
        
        # Process remaining elements
        remaining_chunks = self._process_remaining_elements(elements, processed_indices)
        chunks.extend(remaining_chunks)
        
        relationships = self._create_table_relationships(chunks)
        
        logger.info(f"Created {len(chunks)} table-aware chunks with {len(relationships)} relationships")
        return chunks, relationships
    
    def _create_table_context_chunk(self, elements: List[MarkdownElement], table_index: int) -> Optional[MarkdownChunk]:
        """Create a chunk centered on a table with context."""
        start_idx = max(0, table_index - self.context_range)
        end_idx = min(len(elements), table_index + self.context_range + 1)
        
        context_elements = elements[start_idx:end_idx]
        table_element = elements[table_index]
        
        content = '\n\n'.join(elem.content for elem in context_elements)
        
        chunk_id = f"md_table_context_{uuid.uuid4().hex[:8]}"
        
        return MarkdownChunk(
            chunk_id=chunk_id,
            content=content,
            elements=context_elements,
            chunk_type="table_contextual",
            structural_metadata={
                "has_table": True,
                "table_rows": table_element.metadata.get('rows', 0),
                "table_columns": table_element.metadata.get('columns', 0),
                "context_elements": len(context_elements) - 1
            },
            semantic_metadata={
                "table_headers": table_element.metadata.get('headers', []),
                "data_focused": True
            },
            position_start=context_elements[0].position,
            position_end=context_elements[-1].position,
            word_count=len(content.split())
        )
    
    def _process_remaining_elements(self, elements: List[MarkdownElement], processed_indices: set) -> List[MarkdownChunk]:
        """Process non-table elements."""
        chunks = []
        current_group = []
        
        for i, element in enumerate(elements):
            if i not in processed_indices:
                current_group.append(element)
            else:
                if current_group:
                    content = '\n\n'.join(elem.content for elem in current_group)
                    if len(content) > 100:  # Minimum size
                        chunk_id = f"md_nontable_{uuid.uuid4().hex[:8]}"
                        chunks.append(MarkdownChunk(
                            chunk_id=chunk_id,
                            content=content,
                            elements=current_group,
                            chunk_type="non_table",
                            structural_metadata={"has_table": False},
                            semantic_metadata={},
                            position_start=current_group[0].position,
                            position_end=current_group[-1].position,
                            word_count=len(content.split())
                        ))
                    current_group = []
        
        # Process final group
        if current_group:
            content = '\n\n'.join(elem.content for elem in current_group)
            if len(content) > 100:
                chunk_id = f"md_nontable_{uuid.uuid4().hex[:8]}"
                chunks.append(MarkdownChunk(
                    chunk_id=chunk_id,
                    content=content,
                    elements=current_group,
                    chunk_type="non_table",
                    structural_metadata={"has_table": False},
                    semantic_metadata={},
                    position_start=current_group[0].position,
                    position_end=current_group[-1].position,
                    word_count=len(content.split())
                ))
        
        return chunks
    
    def _create_table_relationships(self, chunks: List[MarkdownChunk]) -> List[MarkdownRelationship]:
        """Create table-specific relationships."""
        relationships = []
        table_chunks = [c for c in chunks if c.structural_metadata.get('has_table', False)]
        
        # Link table chunks that share headers
        for i, chunk1 in enumerate(table_chunks):
            headers1 = set(chunk1.semantic_metadata.get('table_headers', []))
            for chunk2 in table_chunks[i + 1:]:
                headers2 = set(chunk2.semantic_metadata.get('table_headers', []))
                shared_headers = headers1 & headers2
                
                if shared_headers:
                    relationships.append(MarkdownRelationship(
                        source_chunk_id=chunk1.chunk_id,
                        target_chunk_id=chunk2.chunk_id,
                        relationship_type="shared_schema",
                        relationship_metadata={
                            "shared_headers": list(shared_headers)
                        }
                    ))
        
        return relationships


class TopicModelingCoherenceChunker:
    """Strategy 8: Topic Modeling with Coherence Scoring"""
    
    def __init__(self, num_topics: int = 5, min_chunk_size: int = 200):
        self.num_topics = num_topics
        self.min_chunk_size = min_chunk_size
        self.strategy = MarkdownChunkingStrategy.TOPIC_MODELING_COHERENCE
    
    def chunk(self, elements: List[MarkdownElement]) -> tuple[List[MarkdownChunk], List[MarkdownRelationship]]:
        """Create chunks based on topic modeling."""
        chunks = []
        relationships = []
        
        # Simple topic modeling based on keyword clustering
        topic_assignments = self._assign_topics(elements)
        topic_groups = self._group_by_topic(elements, topic_assignments)
        
        for topic_id, topic_elements in topic_groups.items():
            topic_chunks = self._create_topic_chunks(topic_elements, topic_id)
            chunks.extend(topic_chunks)
        
        relationships = self._create_topic_relationships(chunks)
        
        logger.info(f"Created {len(chunks)} topic-based chunks with {len(relationships)} relationships")
        return chunks, relationships
    
    def _assign_topics(self, elements: List[MarkdownElement]) -> List[int]:
        """Assign topics to elements (simplified clustering)."""
        # Extract keywords from each element
        element_keywords = []
        all_keywords = set()
        
        for element in elements:
            words = set(word.lower() for word in element.content.split() 
                        if len(word) > 4 and word.isalpha())
            element_keywords.append(words)
            all_keywords.update(words)
        
        # Simple topic assignment based on keyword similarity
        topic_assignments = []
        for keywords in element_keywords:
            # Assign topic based on dominant keyword themes
            if any(kw in keywords for kw in ['code', 'function', 'method', 'api']):
                topic_assignments.append(0)  # Technical topic
            elif any(kw in keywords for kw in ['example', 'tutorial', 'guide']):
                topic_assignments.append(1)  # Tutorial topic  
            elif any(kw in keywords for kw in ['data', 'table', 'result']):
                topic_assignments.append(2)  # Data topic
            elif any(kw in keywords for kw in ['install', 'setup', 'config']):
                topic_assignments.append(3)  # Setup topic
            else:
                topic_assignments.append(4)  # General topic
        
        return topic_assignments
    
    def _group_by_topic(self, elements: List[MarkdownElement], topic_assignments: List[int]) -> Dict[int, List[MarkdownElement]]:
        """Group elements by topic."""
        topic_groups = defaultdict(list)
        for element, topic in zip(elements, topic_assignments):
            topic_groups[topic].append(element)
        return dict(topic_groups)
    
    def _create_topic_chunks(self, elements: List[MarkdownElement], topic_id: int) -> List[MarkdownChunk]:
        """Create chunks for a topic."""
        chunks = []
        current_chunk = []
        current_size = 0
        
        for element in elements:
            element_size = len(element.content)
            
            if current_size + element_size > 1000 and current_chunk:  # Max chunk size
                chunk = self._create_topic_chunk(current_chunk, topic_id)
                if chunk:
                    chunks.append(chunk)
                current_chunk = [element]
                current_size = element_size
            else:
                current_chunk.append(element)
                current_size += element_size
        
        if current_chunk:
            chunk = self._create_topic_chunk(current_chunk, topic_id)
            if chunk:
                chunks.append(chunk)
        
        return chunks
    
    def _create_topic_chunk(self, elements: List[MarkdownElement], topic_id: int) -> Optional[MarkdownChunk]:
        """Create a topic-based chunk."""
        content = '\n\n'.join(elem.content for elem in elements)
        
        if len(content) < self.min_chunk_size:
            return None
        
        topic_names = {
            0: 'technical',
            1: 'tutorial', 
            2: 'data',
            3: 'setup',
            4: 'general'
        }
        
        chunk_id = f"md_topic_{topic_names.get(topic_id, 'unknown')}_{uuid.uuid4().hex[:8]}"
        
        return MarkdownChunk(
            chunk_id=chunk_id,
            content=content,
            elements=elements,
            chunk_type=f"topic_{topic_names.get(topic_id, 'unknown')}",
            structural_metadata={
                "topic_id": topic_id,
                "topic_name": topic_names.get(topic_id, 'unknown')
            },
            semantic_metadata={
                "topic_coherence": self._calculate_topic_coherence(elements),
                "dominant_topic": topic_id
            },
            position_start=elements[0].position,
            position_end=elements[-1].position,
            word_count=len(content.split())
        )
    
    def _calculate_topic_coherence(self, elements: List[MarkdownElement]) -> float:
        """Calculate coherence within a topic."""
        # Simplified coherence based on keyword overlap
        all_words = []
        for element in elements:
            words = set(word.lower() for word in element.content.split() if len(word) > 3)
            all_words.append(words)
        
        if len(all_words) < 2:
            return 1.0
        
        total_overlap = 0
        pairs = 0
        
        for i in range(len(all_words)):
            for j in range(i + 1, len(all_words)):
                pairs += 1
                shared = len(all_words[i] & all_words[j])
                union = len(all_words[i] | all_words[j])
                total_overlap += shared / union if union > 0 else 0
        
        return total_overlap / pairs if pairs > 0 else 0.0
    
    def _create_topic_relationships(self, chunks: List[MarkdownChunk]) -> List[MarkdownRelationship]:
        """Create topic-based relationships."""
        relationships = []
        
        # Group by topic
        topic_groups = defaultdict(list)
        for chunk in chunks:
            topic_id = chunk.structural_metadata.get('topic_id')
            topic_groups[topic_id].append(chunk)
        
        # Create intra-topic relationships
        for topic_id, topic_chunks in topic_groups.items():
            for i, chunk1 in enumerate(topic_chunks):
                for chunk2 in topic_chunks[i + 1:]:
                    relationships.append(MarkdownRelationship(
                        source_chunk_id=chunk1.chunk_id,
                        target_chunk_id=chunk2.chunk_id,
                        relationship_type="same_topic",
                        relationship_metadata={
                            "topic_id": topic_id
                        }
                    ))
        
        return relationships


class AttentionWeightedChunker:
    """Strategy 9: Attention-Weighted Chunking (Simplified)"""
    
    def __init__(self, attention_threshold: float = 0.7):
        self.attention_threshold = attention_threshold
        self.strategy = MarkdownChunkingStrategy.ATTENTION_WEIGHTED
    
    def chunk(self, elements: List[MarkdownElement]) -> tuple[List[MarkdownChunk], List[MarkdownRelationship]]:
        """Create chunks based on attention weights."""
        chunks = []
        relationships = []
        
        # Calculate attention weights (simplified)
        attention_weights = self._calculate_attention_weights(elements)
        
        # Create chunks around high-attention content
        high_attention_chunks = self._create_attention_chunks(elements, attention_weights)
        chunks.extend(high_attention_chunks)
        
        relationships = self._create_attention_relationships(chunks)
        
        logger.info(f"Created {len(chunks)} attention-weighted chunks with {len(relationships)} relationships")
        return chunks, relationships
    
    def _calculate_attention_weights(self, elements: List[MarkdownElement]) -> List[float]:
        """Calculate attention weights for elements."""
        weights = []
        
        for element in elements:
            weight = 0.5  # Base weight
            
            # Higher weight for headers
            if element.element_type == MarkdownElementType.HEADER:
                weight += 0.3 / element.level  # Higher level = higher weight
            
            # Higher weight for code blocks
            if element.element_type == MarkdownElementType.CODE_BLOCK:
                weight += 0.2
            
            # Higher weight for elements with emphasis
            if element.element_type == MarkdownElementType.PARAGRAPH:
                if '**' in element.content or '__' in element.content:  # Bold text
                    weight += 0.1
                if '*' in element.content or '_' in element.content:  # Italic text
                    weight += 0.05
            
            # Higher weight for lists and tables
            if element.element_type in {MarkdownElementType.LIST, MarkdownElementType.TABLE}:
                weight += 0.15
            
            weights.append(min(weight, 1.0))  # Cap at 1.0
        
        return weights
    
    def _create_attention_chunks(self, elements: List[MarkdownElement], weights: List[float]) -> List[MarkdownChunk]:
        """Create chunks around high-attention elements."""
        chunks = []
        current_chunk = []
        current_weights = []
        
        for element, weight in zip(elements, weights):
            if weight >= self.attention_threshold:
                # High attention element - start new chunk
                if current_chunk:
                    chunk = self._create_weighted_chunk(current_chunk, current_weights)
                    if chunk:
                        chunks.append(chunk)
                
                current_chunk = [element]
                current_weights = [weight]
            else:
                current_chunk.append(element)
                current_weights.append(weight)
                
                # Check if chunk is getting too large
                if len('\n\n'.join(elem.content for elem in current_chunk)) > 1000:
                    chunk = self._create_weighted_chunk(current_chunk, current_weights)
                    if chunk:
                        chunks.append(chunk)
                    current_chunk = []
                    current_weights = []
        
        # Process final chunk
        if current_chunk:
            chunk = self._create_weighted_chunk(current_chunk, current_weights)
            if chunk:
                chunks.append(chunk)
        
        return chunks
    
    def _create_weighted_chunk(self, elements: List[MarkdownElement], weights: List[float]) -> Optional[MarkdownChunk]:
        """Create a weighted chunk."""
        content = '\n\n'.join(elem.content for elem in elements)
        
        if len(content) < 100:  # Minimum size
            return None
        
        avg_weight = sum(weights) / len(weights) if weights else 0.5
        
        chunk_id = f"md_attention_{uuid.uuid4().hex[:8]}"
        
        return MarkdownChunk(
            chunk_id=chunk_id,
            content=content,
            elements=elements,
            chunk_type="attention_weighted",
            structural_metadata={
                "attention_score": avg_weight,
                "high_attention_elements": sum(1 for w in weights if w >= self.attention_threshold)
            },
            semantic_metadata={
                "attention_distribution": weights,
                "focus_level": "high" if avg_weight > 0.7 else "medium" if avg_weight > 0.5 else "low"
            },
            position_start=elements[0].position,
            position_end=elements[-1].position,
            word_count=len(content.split())
        )
    
    def _create_attention_relationships(self, chunks: List[MarkdownChunk]) -> List[MarkdownRelationship]:
        """Create attention-based relationships."""
        relationships = []
        
        high_attention_chunks = [c for c in chunks 
                               if c.structural_metadata.get('attention_score', 0) > self.attention_threshold]
        
        # Link high-attention chunks
        for i, chunk1 in enumerate(high_attention_chunks):
            for chunk2 in high_attention_chunks[i + 1:]:
                if abs(chunk1.position_start - chunk2.position_start) < 1000:  # Proximity
                    relationships.append(MarkdownRelationship(
                        source_chunk_id=chunk1.chunk_id,
                        target_chunk_id=chunk2.chunk_id,
                        relationship_type="high_attention",
                        relationship_metadata={
                            "attention_correlation": min(
                                chunk1.structural_metadata.get('attention_score', 0),
                                chunk2.structural_metadata.get('attention_score', 0)
                            )
                        }
                    ))
        
        return relationships


class MarkdownNativeEnhancementChunker:
    """Strategy 10: Markdown-Native Embedding Enhancement"""
    
    def __init__(self, preserve_structure: bool = True):
        self.preserve_structure = preserve_structure
        self.strategy = MarkdownChunkingStrategy.MARKDOWN_NATIVE_ENHANCEMENT
    
    def chunk(self, elements: List[MarkdownElement]) -> tuple[List[MarkdownChunk], List[MarkdownRelationship]]:
        """Create chunks that preserve markdown structure for embeddings."""
        chunks = []
        relationships = []
        
        # Group elements while preserving markdown syntax
        structure_groups = self._group_by_structure(elements)
        
        for group in structure_groups:
            chunk = self._create_structure_preserving_chunk(group)
            if chunk:
                chunks.append(chunk)
        
        relationships = self._create_structural_relationships(chunks)
        
        logger.info(f"Created {len(chunks)} structure-preserving chunks with {len(relationships)} relationships")
        return chunks, relationships
    
    def _group_by_structure(self, elements: List[MarkdownElement]) -> List[List[MarkdownElement]]:
        """Group elements while preserving structural information."""
        groups = []
        current_group = []
        current_level = 0
        
        for element in elements:
            if element.element_type == MarkdownElementType.HEADER:
                # New header - check if we should start a new group
                if current_group and (element.level <= current_level):
                    # Same level or higher - finish current group
                    groups.append(current_group)
                    current_group = [element]
                else:
                    # Lower level - continue current group
                    current_group.append(element)
                current_level = element.level
            else:
                current_group.append(element)
                
                # Check size limit
                current_size = sum(len(elem.content) for elem in current_group)
                if current_size > 1200:
                    groups.append(current_group)
                    current_group = []
                    current_level = 0
        
        if current_group:
            groups.append(current_group)
        
        return groups
    
    def _create_structure_preserving_chunk(self, elements: List[MarkdownElement]) -> Optional[MarkdownChunk]:
        """Create chunk that preserves markdown structure."""
        if not elements:
            return None
        
        # Build content with preserved structure
        enhanced_content = self._build_enhanced_content(elements)
        
        if len(enhanced_content) < 100:
            return None
        
        # Extract structural features
        structural_features = self._extract_structural_features(elements)
        
        chunk_id = f"md_native_{uuid.uuid4().hex[:8]}"
        
        return MarkdownChunk(
            chunk_id=chunk_id,
            content=enhanced_content,
            elements=elements,
            chunk_type="markdown_native",
            structural_metadata={
                "preserved_structure": True,
                "structural_features": structural_features,
                "markdown_elements": [elem.element_type.value for elem in elements]
            },
            semantic_metadata={
                "structure_complexity": len(set(elem.element_type for elem in elements)),
                "formatting_density": self._calculate_formatting_density(elements)
            },
            position_start=elements[0].position,
            position_end=elements[-1].position,
            word_count=len(enhanced_content.split())
        )
    
    def _build_enhanced_content(self, elements: List[MarkdownElement]) -> str:
        """Build content with enhanced structural markup."""
        content_parts = []
        
        for element in elements:
            if element.element_type == MarkdownElementType.HEADER:
                # Preserve header level information
                marker = '#' * element.level
                content_parts.append(f"{marker} {element.content}")
            
            elif element.element_type == MarkdownElementType.CODE_BLOCK:
                # Preserve language and code structure
                lang = element.language or ''
                content_parts.append(f"```{lang}\n{element.content}\n```")
            
            elif element.element_type == MarkdownElementType.LIST:
                # Preserve list structure
                content_parts.append(element.content)
            
            elif element.element_type == MarkdownElementType.TABLE:
                # Preserve table structure
                content_parts.append(element.content)
            
            else:
                # Regular content
                content_parts.append(element.content)
        
        return '\n\n'.join(content_parts)
    
    def _extract_structural_features(self, elements: List[MarkdownElement]) -> Dict[str, Any]:
        """Extract structural features for embedding enhancement."""
        features = {
            'header_levels': [],
            'has_code': False,
            'has_table': False,
            'has_list': False,
            'code_languages': [],
            'emphasis_count': 0,
            'link_count': 0
        }
        
        for element in elements:
            if element.element_type == MarkdownElementType.HEADER:
                features['header_levels'].append(element.level)
            elif element.element_type == MarkdownElementType.CODE_BLOCK:
                features['has_code'] = True
                if element.language:
                    features['code_languages'].append(element.language)
            elif element.element_type == MarkdownElementType.TABLE:
                features['has_table'] = True
            elif element.element_type == MarkdownElementType.LIST:
                features['has_list'] = True
            elif element.element_type == MarkdownElementType.LINK:
                features['link_count'] += 1
            
            # Count emphasis markers
            if element.content:
                features['emphasis_count'] += element.content.count('**') + element.content.count('*')
        
        return features
    
    def _calculate_formatting_density(self, elements: List[MarkdownElement]) -> float:
        """Calculate how much formatting is present."""
        total_chars = sum(len(elem.content) for elem in elements)
        if total_chars == 0:
            return 0.0
        
        format_chars = 0
        for element in elements:
            content = element.content
            format_chars += content.count('*') + content.count('_') + content.count('`')
            format_chars += content.count('[') + content.count(']')
            format_chars += content.count('#')
        
        return format_chars / total_chars
    
    def _create_structural_relationships(self, chunks: List[MarkdownChunk]) -> List[MarkdownRelationship]:
        """Create structure-based relationships."""
        relationships = []
        
        # Link chunks with similar structural features
        for i, chunk1 in enumerate(chunks):
            features1 = chunk1.structural_metadata.get('structural_features', {})
            
            for chunk2 in chunks[i + 1:]:
                features2 = chunk2.structural_metadata.get('structural_features', {})
                
                # Check for structural similarity
                similarity = self._calculate_structural_similarity(features1, features2)
                
                if similarity > 0.5:
                    relationships.append(MarkdownRelationship(
                        source_chunk_id=chunk1.chunk_id,
                        target_chunk_id=chunk2.chunk_id,
                        relationship_type="structural_similarity",
                        relationship_metadata={
                            "similarity_score": similarity,
                            "shared_features": self._get_shared_features(features1, features2)
                        }
                    ))
        
        return relationships
    
    def _calculate_structural_similarity(self, features1: Dict[str, Any], features2: Dict[str, Any]) -> float:
        """Calculate structural similarity between feature sets."""
        similarity_score = 0.0
        
        # Header level similarity
        if features1.get('header_levels') and features2.get('header_levels'):
            shared_levels = set(features1['header_levels']) & set(features2['header_levels'])
            total_levels = set(features1['header_levels']) | set(features2['header_levels'])
            if total_levels:
                similarity_score += 0.3 * (len(shared_levels) / len(total_levels))
        
        # Content type similarity
        bool_features = ['has_code', 'has_table', 'has_list']
        matches = sum(1 for feat in bool_features 
                     if features1.get(feat, False) == features2.get(feat, False))
        similarity_score += 0.4 * (matches / len(bool_features))
        
        # Language similarity
        langs1 = set(features1.get('code_languages', []))
        langs2 = set(features2.get('code_languages', []))
        if langs1 or langs2:
            shared_langs = langs1 & langs2
            total_langs = langs1 | langs2
            similarity_score += 0.3 * (len(shared_langs) / len(total_langs) if total_langs else 0)
        
        return similarity_score
    
    def _get_shared_features(self, features1: Dict[str, Any], features2: Dict[str, Any]) -> List[str]:
        """Get list of shared features."""
        shared = []
        
        bool_features = ['has_code', 'has_table', 'has_list']
        for feat in bool_features:
            if features1.get(feat, False) and features2.get(feat, False):
                shared.append(feat)
        
        shared_levels = set(features1.get('header_levels', [])) & set(features2.get('header_levels', []))
        if shared_levels:
            shared.append(f"header_levels_{list(shared_levels)}")
        
        shared_langs = set(features1.get('code_languages', [])) & set(features2.get('code_languages', []))
        if shared_langs:
            shared.append(f"languages_{list(shared_langs)}")
        
        return shared