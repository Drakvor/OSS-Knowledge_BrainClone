"""
Markdown-Optimized Storage Schemas
==================================

Storage schemas optimized for markdown content in both Qdrant and Neo4j.
"""

import logging
from typing import Dict, Any, List
from dataclasses import asdict

from app.markdown.base import MarkdownChunk, MarkdownRelationship

logger = logging.getLogger(__name__)


class MarkdownQdrantSchema:
    """Qdrant storage schema optimized for markdown chunks."""
    
    @staticmethod
    def chunk_to_point(chunk: MarkdownChunk, embedding: List[float]) -> Dict[str, Any]:
        """Convert markdown chunk to Qdrant point format."""
        
        # Build payload with markdown-specific metadata
        payload = {
            # Core content
            "chunk_id": chunk.chunk_id,
            "content": chunk.content,
            "chunk_type": chunk.chunk_type,
            "word_count": chunk.word_count,
            "created_at": chunk.created_at.isoformat(),
            
            # Position information
            "position_start": chunk.position_start,
            "position_end": chunk.position_end,
            "document_range": chunk.position_end - chunk.position_start,
            
            # Structural metadata
            "element_count": len(chunk.elements),
            "element_types": chunk.structural_metadata.get("element_types", []),
            
            # Markdown-specific structural features
            "has_headers": any(elem.element_type.value == "header" for elem in chunk.elements),
            "has_code": chunk.structural_metadata.get("has_code", False),
            "has_tables": chunk.structural_metadata.get("has_table", False),
            "has_lists": chunk.structural_metadata.get("has_list", False),
            "has_links": any(elem.element_type.value == "link" for elem in chunk.elements),
            "has_images": any(elem.element_type.value == "image" for elem in chunk.elements),
            
            # Code-specific metadata
            "primary_language": chunk.structural_metadata.get("primary_language"),
            "language_category": chunk.structural_metadata.get("language_category"),
            "code_complexity": chunk.semantic_metadata.get("code_complexity"),
            
            # Semantic metadata
            "themes": chunk.semantic_metadata.get("themes", []),
            "technical_concepts": chunk.semantic_metadata.get("technical_concepts", []),
            "content_category": chunk.semantic_metadata.get("content_category", "general"),
            "technical_level": chunk.semantic_metadata.get("technical_level", "low"),
            
            # Strategy-specific metadata
            "strategy_used": chunk.structural_metadata.get("strategy_used"),
            "coherence_score": chunk.semantic_metadata.get("coherence_score", 0.0),
            "attention_score": chunk.structural_metadata.get("attention_score", 0.0),
            "topic_id": chunk.structural_metadata.get("topic_id"),
            "modal_type": chunk.semantic_metadata.get("content_modality"),
            
            # Hierarchical metadata
            "hierarchy_path": chunk.structural_metadata.get("hierarchy_path", []),
            "header_level": chunk.structural_metadata.get("header_level", 0),
            
            # Cross-reference metadata  
            "reference_count": chunk.structural_metadata.get("reference_count", 0),
            "reference_types": chunk.semantic_metadata.get("reference_types", []),
            "connectivity_score": chunk.semantic_metadata.get("connectivity_score", 0.0),
            
            # Table metadata
            "table_rows": chunk.structural_metadata.get("table_rows"),
            "table_columns": chunk.structural_metadata.get("table_columns"),
            "table_headers": chunk.semantic_metadata.get("table_headers", []),
            
            # Multi-modal metadata
            "fusion_weight": chunk.semantic_metadata.get("fusion_weight", 1.0),
            
            # Structure preservation metadata
            "preserved_structure": chunk.structural_metadata.get("preserved_structure", False),
            "formatting_density": chunk.semantic_metadata.get("formatting_density", 0.0),
            "structure_complexity": chunk.semantic_metadata.get("structure_complexity", 1)
        }
        
        # Use chunk_id as point_id after hashing for Qdrant compatibility
        point_id = abs(hash(chunk.chunk_id)) % (2**31)  # Ensure positive 32-bit int
        
        return {
            "id": point_id,
            "vector": embedding,
            "payload": payload
        }
    
    @staticmethod
    def get_collection_config() -> Dict[str, Any]:
        """Get Qdrant collection configuration for markdown content."""
        return {
            "vectors": {
                "size": 3072,  # Azure OpenAI text-embedding-3-large dimension
                "distance": "Cosine"
            },
            "optimizers_config": {
                "default_segment_number": 2,
                "max_segment_size": 20000,
                "memmap_threshold": 50000,
                "indexing_threshold": 10000,
                "flush_interval_sec": 10,
                "max_optimization_threads": 2
            },
            "hnsw_config": {
                "m": 16,
                "ef_construct": 200,
                "full_scan_threshold": 10000,
                "max_indexing_threads": 2
            }
        }
    
    @staticmethod
    def get_search_filters() -> Dict[str, List[str]]:
        """Get available search filters for markdown content."""
        return {
            "content_filters": [
                "chunk_type", "content_category", "technical_level", 
                "has_code", "has_tables", "has_headers"
            ],
            "structural_filters": [
                "element_count", "word_count", "header_level",
                "primary_language", "language_category"
            ],
            "semantic_filters": [
                "themes", "technical_concepts", "coherence_score",
                "attention_score", "connectivity_score"
            ],
            "strategy_filters": [
                "strategy_used", "topic_id", "modal_type"
            ]
        }


class MarkdownNeo4jSchema:
    """Neo4j storage schema optimized for markdown relationships."""
    
    @staticmethod
    def chunk_to_node(chunk: MarkdownChunk) -> Dict[str, Any]:
        """Convert markdown chunk to Neo4j node properties."""
        
        properties = {
            # Identifiers
            "chunk_id": chunk.chunk_id,
            "chunk_type": chunk.chunk_type,
            
            # Content properties
            "content_preview": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
            "word_count": chunk.word_count,
            "created_at": chunk.created_at.isoformat(),
            
            # Position
            "position_start": chunk.position_start,
            "position_end": chunk.position_end,
            
            # Structural properties
            "element_count": len(chunk.elements),
            "element_types": chunk.structural_metadata.get("element_types", []),
            
            # Markdown features
            "has_headers": any(elem.element_type.value == "header" for elem in chunk.elements),
            "has_code": chunk.structural_metadata.get("has_code", False),
            "has_tables": chunk.structural_metadata.get("has_table", False),
            "primary_language": chunk.structural_metadata.get("primary_language", ""),
            
            # Semantic properties
            "themes": chunk.semantic_metadata.get("themes", []),
            "content_category": chunk.semantic_metadata.get("content_category", "general"),
            "technical_level": chunk.semantic_metadata.get("technical_level", "low"),
            
            # Strategy metadata
            "strategy_used": chunk.structural_metadata.get("strategy_used", "unknown"),
            "coherence_score": chunk.semantic_metadata.get("coherence_score", 0.0),
            "attention_score": chunk.structural_metadata.get("attention_score", 0.0),
            
            # Hierarchical metadata
            "hierarchy_path": chunk.structural_metadata.get("hierarchy_path", []),
            "header_level": chunk.structural_metadata.get("header_level", 0),
            
            # Cross-reference metadata
            "reference_count": chunk.structural_metadata.get("reference_count", 0),
            "connectivity_score": chunk.semantic_metadata.get("connectivity_score", 0.0),
            
            # Labels for Neo4j
            "labels": MarkdownNeo4jSchema._generate_labels(chunk)
        }
        
        return properties
    
    @staticmethod
    def _generate_labels(chunk: MarkdownChunk) -> List[str]:
        """Generate Neo4j labels for a chunk based on its properties."""
        labels = ["MarkdownChunk"]
        
        # Content type labels
        if chunk.structural_metadata.get("has_code", False):
            labels.append("CodeContent")
        if chunk.structural_metadata.get("has_table", False):
            labels.append("TableContent")
        if any(elem.element_type.value == "header" for elem in chunk.elements):
            labels.append("HeaderContent")
        
        # Category labels
        category = chunk.semantic_metadata.get("content_category", "general")
        labels.append(f"Category{category.title()}")
        
        # Technical level labels
        tech_level = chunk.semantic_metadata.get("technical_level", "low")
        labels.append(f"TechnicalLevel{tech_level.title()}")
        
        # Strategy labels
        strategy = chunk.structural_metadata.get("strategy_used", "unknown")
        if strategy != "unknown":
            labels.append(f"Strategy{strategy.replace('_', '').title()}")
        
        # Language labels
        if chunk.structural_metadata.get("primary_language"):
            lang = chunk.structural_metadata["primary_language"]
            labels.append(f"Language{lang.title()}")
        
        return labels
    
    @staticmethod
    def relationship_to_edge(relationship: MarkdownRelationship) -> Dict[str, Any]:
        """Convert markdown relationship to Neo4j edge properties."""
        
        # Map relationship types to Neo4j relationship types
        rel_type_mapping = {
            "parent_child": "PARENT_OF",
            "sibling": "SIBLING_OF", 
            "sequential": "FOLLOWS",
            "thematic": "THEMATICALLY_RELATED",
            "cross_modal": "CROSS_MODAL_RELATED",
            "semantic_overlap": "SEMANTICALLY_OVERLAPS",
            "citation": "CITES",
            "mutual_reference": "MUTUALLY_REFERENCES",
            "explanation_implementation": "EXPLAINS",
            "same_language": "SAME_LANGUAGE_AS",
            "shared_schema": "SHARES_SCHEMA",
            "same_topic": "SAME_TOPIC_AS",
            "high_attention": "HIGH_ATTENTION_RELATED",
            "structural_similarity": "STRUCTURALLY_SIMILAR"
        }
        
        neo4j_type = rel_type_mapping.get(relationship.relationship_type, "RELATED")
        
        properties = {
            "relationship_type": relationship.relationship_type,
            "confidence": relationship.confidence,
            "metadata": relationship.relationship_metadata
        }
        
        return {
            "type": neo4j_type,
            "properties": properties,
            "source": relationship.source_chunk_id,
            "target": relationship.target_chunk_id
        }
    
    @staticmethod
    def get_indexes() -> List[str]:
        """Get recommended indexes for markdown content."""
        return [
            # Core indexes
            "CREATE INDEX chunk_id_index IF NOT EXISTS FOR (c:MarkdownChunk) ON (c.chunk_id)",
            "CREATE INDEX chunk_type_index IF NOT EXISTS FOR (c:MarkdownChunk) ON (c.chunk_type)",
            "CREATE INDEX position_index IF NOT EXISTS FOR (c:MarkdownChunk) ON (c.position_start)",
            
            # Content indexes  
            "CREATE INDEX content_category_index IF NOT EXISTS FOR (c:MarkdownChunk) ON (c.content_category)",
            "CREATE INDEX technical_level_index IF NOT EXISTS FOR (c:MarkdownChunk) ON (c.technical_level)",
            "CREATE INDEX language_index IF NOT EXISTS FOR (c:MarkdownChunk) ON (c.primary_language)",
            
            # Strategy indexes
            "CREATE INDEX strategy_index IF NOT EXISTS FOR (c:MarkdownChunk) ON (c.strategy_used)",
            "CREATE INDEX hierarchy_level_index IF NOT EXISTS FOR (c:MarkdownChunk) ON (c.header_level)",
            
            # Performance indexes
            "CREATE INDEX coherence_index IF NOT EXISTS FOR (c:MarkdownChunk) ON (c.coherence_score)",
            "CREATE INDEX attention_index IF NOT EXISTS FOR (c:MarkdownChunk) ON (c.attention_score)",
            "CREATE INDEX connectivity_index IF NOT EXISTS FOR (c:MarkdownChunk) ON (c.connectivity_score)",
            
            # Relationship indexes
            "CREATE INDEX rel_type_index IF NOT EXISTS FOR ()-[r]-() ON (r.relationship_type)",
            "CREATE INDEX rel_confidence_index IF NOT EXISTS FOR ()-[r]-() ON (r.confidence)"
        ]
    
    @staticmethod
    def get_constraints() -> List[str]:
        """Get recommended constraints for data integrity."""
        return [
            "CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS FOR (c:MarkdownChunk) REQUIRE c.chunk_id IS UNIQUE",
            "CREATE CONSTRAINT chunk_id_exists IF NOT EXISTS FOR (c:MarkdownChunk) REQUIRE c.chunk_id IS NOT NULL"
        ]


class MarkdownHybridSearchSchema:
    """Schema for hybrid search across vector and graph databases."""
    
    @staticmethod
    def get_vector_search_config() -> Dict[str, Any]:
        """Configuration for vector-based search."""
        return {
            "search_params": {
                "hnsw_ef": 128,
                "exact": False
            },
            "filters": {
                "content_type_filters": ["has_code", "has_tables", "has_headers"],
                "semantic_filters": ["content_category", "technical_level", "themes"],
                "structural_filters": ["strategy_used", "header_level", "primary_language"],
                "quality_filters": ["coherence_score", "attention_score", "connectivity_score"]
            },
            "scoring": {
                "boost_factors": {
                    "high_attention": 1.2,
                    "high_coherence": 1.1,
                    "code_content": 1.15,
                    "technical_content": 1.1
                }
            }
        }
    
    @staticmethod
    def get_graph_traversal_patterns() -> Dict[str, str]:
        """Common graph traversal patterns for markdown content."""
        return {
            "hierarchical_navigation": """
                MATCH (start:MarkdownChunk {chunk_id: $chunk_id})
                MATCH (start)-[:PARENT_OF|SIBLING_OF*1..3]-(related)
                WHERE related.header_level <= start.header_level + 2
                RETURN related, type(r) as relationship_type
                ORDER BY related.position_start
            """,
            
            "code_context_search": """
                MATCH (start:MarkdownChunk {chunk_id: $chunk_id})
                MATCH (start)-[:EXPLAINS|SAME_LANGUAGE_AS]-(code:CodeContent)
                OPTIONAL MATCH (code)-[:FOLLOWS*1..2]-(context)
                RETURN code, context, type(r) as relationship_type
                ORDER BY code.attention_score DESC
            """,
            
            "thematic_exploration": """
                MATCH (start:MarkdownChunk {chunk_id: $chunk_id})
                MATCH (start)-[:THEMATICALLY_RELATED|SAME_TOPIC_AS]-(related)
                WHERE related.coherence_score > 0.5
                RETURN related, type(r) as relationship_type
                ORDER BY related.coherence_score DESC
            """,
            
            "cross_reference_following": """
                MATCH (start:MarkdownChunk {chunk_id: $chunk_id})
                MATCH (start)-[:CITES|MUTUALLY_REFERENCES*1..2]-(referenced)
                RETURN referenced, type(r) as relationship_type
                ORDER BY referenced.connectivity_score DESC
            """,
            
            "structural_similarity": """
                MATCH (start:MarkdownChunk {chunk_id: $chunk_id})
                MATCH (start)-[:STRUCTURALLY_SIMILAR]-(similar)
                WHERE similar.strategy_used = start.strategy_used
                RETURN similar, type(r) as relationship_type
                ORDER BY similar.attention_score DESC
            """
        }
    
    @staticmethod
    def get_fusion_weights() -> Dict[str, float]:
        """Weights for fusing vector and graph search results."""
        return {
            "default": {
                "vector_weight": 0.6,
                "graph_weight": 0.3,
                "metadata_weight": 0.1
            },
            "code_focused": {
                "vector_weight": 0.5,
                "graph_weight": 0.4,
                "metadata_weight": 0.1
            },
            "structure_focused": {
                "vector_weight": 0.4,
                "graph_weight": 0.5,
                "metadata_weight": 0.1
            },
            "content_focused": {
                "vector_weight": 0.7,
                "graph_weight": 0.2,
                "metadata_weight": 0.1
            }
        }
    
    @staticmethod
    def get_search_templates() -> Dict[str, Dict[str, Any]]:
        """Search templates for different markdown query types."""
        return {
            "technical_query": {
                "vector_boost": ["has_code", "technical_level:high"],
                "graph_pattern": "code_context_search",
                "fusion_profile": "code_focused",
                "result_filters": ["CodeContent", "TechnicalLevelHigh"]
            },
            
            "structural_query": {
                "vector_boost": ["has_headers", "hierarchy_path"],
                "graph_pattern": "hierarchical_navigation", 
                "fusion_profile": "structure_focused",
                "result_filters": ["HeaderContent"]
            },
            
            "conceptual_query": {
                "vector_boost": ["themes", "coherence_score"],
                "graph_pattern": "thematic_exploration",
                "fusion_profile": "content_focused", 
                "result_filters": ["CategoryGeneral", "CategoryTechnical"]
            },
            
            "reference_query": {
                "vector_boost": ["reference_count", "connectivity_score"],
                "graph_pattern": "cross_reference_following",
                "fusion_profile": "default",
                "result_filters": []
            }
        }