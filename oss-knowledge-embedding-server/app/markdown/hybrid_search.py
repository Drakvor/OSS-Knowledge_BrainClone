"""
Markdown-Aware Hybrid Search Algorithm
====================================

Advanced hybrid search combining vector similarity, graph traversal, and markdown-specific 
metadata scoring for optimal retrieval of markdown content.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime
import numpy as np

from app.markdown.base import MarkdownChunk, MarkdownRelationship
from app.markdown.storage_schemas import (
    MarkdownQdrantSchema, 
    MarkdownNeo4jSchema, 
    MarkdownHybridSearchSchema
)

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Represents a search result with unified scoring."""
    chunk_id: str
    content: str
    chunk_type: str
    vector_score: float = 0.0
    graph_score: float = 0.0
    metadata_score: float = 0.0
    combined_score: float = 0.0
    relationship_context: List[Dict[str, Any]] = None
    structural_metadata: Dict[str, Any] = None
    semantic_metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.relationship_context is None:
            self.relationship_context = []


@dataclass
class HybridSearchConfig:
    """Configuration for hybrid search behavior."""
    vector_weight: float = 0.6
    graph_weight: float = 0.3
    metadata_weight: float = 0.1
    top_k_vector: int = 50
    top_k_graph: int = 30
    final_top_k: int = 20
    boost_factors: Dict[str, float] = None
    graph_traversal_depth: int = 2
    semantic_threshold: float = 0.5
    
    def __post_init__(self):
        if self.boost_factors is None:
            self.boost_factors = {
                "high_attention": 1.2,
                "high_coherence": 1.1,
                "code_content": 1.15,
                "technical_content": 1.1,
                "header_content": 1.05
            }


class MarkdownVectorSearchEngine:
    """Vector search engine optimized for markdown content."""
    
    def __init__(self, qdrant_client, collection_name: str = "markdown_chunks"):
        self.qdrant_client = qdrant_client
        self.collection_name = collection_name
        self.schema = MarkdownQdrantSchema()
    
    async def search(self, 
                    query_vector: List[float],
                    filters: Optional[Dict[str, Any]] = None,
                    top_k: int = 50,
                    boost_factors: Optional[Dict[str, float]] = None) -> List[SearchResult]:
        """Perform vector search with markdown-specific filtering and boosting."""
        
        try:
            # Build Qdrant filter conditions
            qdrant_filter = self._build_qdrant_filter(filters) if filters else None
            
            # Execute vector search
            search_results = await self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=qdrant_filter,
                limit=top_k,
                search_params={"hnsw_ef": 128, "exact": False}
            )
            
            # Convert to SearchResult objects with boosting
            results = []
            for result in search_results:
                payload = result.payload
                
                # Calculate base vector score
                vector_score = float(result.score)
                
                # Apply boost factors
                if boost_factors:
                    vector_score = self._apply_boost_factors(vector_score, payload, boost_factors)
                
                search_result = SearchResult(
                    chunk_id=payload["chunk_id"],
                    content=payload["content"],
                    chunk_type=payload["chunk_type"],
                    vector_score=vector_score,
                    structural_metadata=self._extract_structural_metadata(payload),
                    semantic_metadata=self._extract_semantic_metadata(payload)
                )
                results.append(search_result)
            
            logger.info(f"Vector search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
    
    def _build_qdrant_filter(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Build Qdrant filter conditions from search filters."""
        conditions = []
        
        for field, value in filters.items():
            if isinstance(value, bool):
                conditions.append({"key": field, "match": {"value": value}})
            elif isinstance(value, (int, float)):
                conditions.append({"key": field, "range": {"gte": value}})
            elif isinstance(value, str):
                conditions.append({"key": field, "match": {"value": value}})
            elif isinstance(value, list):
                # For list values, check if any element matches
                conditions.append({"key": field, "match": {"any": value}})
        
        return {"must": conditions} if conditions else None
    
    def _apply_boost_factors(self, score: float, payload: Dict[str, Any], 
                           boost_factors: Dict[str, float]) -> float:
        """Apply boost factors based on content characteristics."""
        boosted_score = score
        
        # High attention boost
        if (payload.get("attention_score", 0) > 0.8 and 
            "high_attention" in boost_factors):
            boosted_score *= boost_factors["high_attention"]
        
        # High coherence boost
        if (payload.get("coherence_score", 0) > 0.7 and 
            "high_coherence" in boost_factors):
            boosted_score *= boost_factors["high_coherence"]
        
        # Code content boost
        if (payload.get("has_code", False) and 
            "code_content" in boost_factors):
            boosted_score *= boost_factors["code_content"]
        
        # Technical content boost
        if (payload.get("technical_level") == "high" and 
            "technical_content" in boost_factors):
            boosted_score *= boost_factors["technical_content"]
        
        # Header content boost
        if (payload.get("has_headers", False) and 
            "header_content" in boost_factors):
            boosted_score *= boost_factors["header_content"]
        
        return boosted_score
    
    def _extract_structural_metadata(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structural metadata from payload."""
        return {
            "element_count": payload.get("element_count", 0),
            "element_types": payload.get("element_types", []),
            "has_headers": payload.get("has_headers", False),
            "has_code": payload.get("has_code", False),
            "has_tables": payload.get("has_tables", False),
            "has_lists": payload.get("has_lists", False),
            "primary_language": payload.get("primary_language"),
            "strategy_used": payload.get("strategy_used"),
            "hierarchy_path": payload.get("hierarchy_path", []),
            "header_level": payload.get("header_level", 0)
        }
    
    def _extract_semantic_metadata(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Extract semantic metadata from payload."""
        return {
            "themes": payload.get("themes", []),
            "technical_concepts": payload.get("technical_concepts", []),
            "content_category": payload.get("content_category", "general"),
            "technical_level": payload.get("technical_level", "low"),
            "coherence_score": payload.get("coherence_score", 0.0),
            "attention_score": payload.get("attention_score", 0.0),
            "connectivity_score": payload.get("connectivity_score", 0.0)
        }


class MarkdownGraphSearchEngine:
    """Graph search engine for exploring markdown relationships."""
    
    def __init__(self, neo4j_driver):
        self.driver = neo4j_driver
        self.schema = MarkdownNeo4jSchema()
        self.traversal_patterns = MarkdownHybridSearchSchema.get_graph_traversal_patterns()
    
    async def search(self, 
                    seed_chunks: List[str],
                    traversal_pattern: str = "thematic_exploration",
                    max_depth: int = 2,
                    min_confidence: float = 0.3) -> List[SearchResult]:
        """Perform graph traversal search from seed chunks."""
        
        try:
            results = []
            
            async with self.driver.session() as session:
                for chunk_id in seed_chunks:
                    # Get traversal pattern query
                    query = self.traversal_patterns.get(
                        traversal_pattern, 
                        self.traversal_patterns["thematic_exploration"]
                    )
                    
                    # Execute graph traversal
                    graph_results = await session.run(
                        query,
                        chunk_id=chunk_id,
                        max_depth=max_depth,
                        min_confidence=min_confidence
                    )
                    
                    # Process results
                    async for record in graph_results:
                        related_node = record.get("related", record.get("code", record.get("context", record.get("referenced", record.get("similar")))))
                        relationship_type = record.get("relationship_type", "related")
                        
                        if related_node:
                            graph_score = self._calculate_graph_score(
                                related_node, relationship_type
                            )
                            
                            search_result = SearchResult(
                                chunk_id=related_node["chunk_id"],
                                content=related_node.get("content_preview", ""),
                                chunk_type=related_node.get("chunk_type", "unknown"),
                                graph_score=graph_score,
                                relationship_context=[{
                                    "type": relationship_type,
                                    "source": chunk_id,
                                    "confidence": related_node.get("connectivity_score", 0.5)
                                }],
                                structural_metadata=self._extract_graph_structural_metadata(related_node),
                                semantic_metadata=self._extract_graph_semantic_metadata(related_node)
                            )
                            results.append(search_result)
            
            # Deduplicate and sort by graph score
            unique_results = self._deduplicate_graph_results(results)
            unique_results.sort(key=lambda x: x.graph_score, reverse=True)
            
            logger.info(f"Graph search returned {len(unique_results)} unique results")
            return unique_results
            
        except Exception as e:
            logger.error(f"Graph search failed: {e}")
            return []
    
    def _calculate_graph_score(self, node: Dict[str, Any], relationship_type: str) -> float:
        """Calculate graph-based relevance score."""
        base_score = 0.5
        
        # Relationship type weights
        relationship_weights = {
            "PARENT_OF": 0.9,
            "SIBLING_OF": 0.8,
            "FOLLOWS": 0.7,
            "THEMATICALLY_RELATED": 0.8,
            "EXPLAINS": 0.9,
            "CITES": 0.6,
            "SAME_TOPIC_AS": 0.8,
            "STRUCTURALLY_SIMILAR": 0.6
        }
        
        rel_weight = relationship_weights.get(relationship_type, 0.5)
        
        # Node quality factors
        coherence = node.get("coherence_score", 0.5)
        attention = node.get("attention_score", 0.5)
        connectivity = node.get("connectivity_score", 0.5)
        
        # Combined score
        graph_score = (
            base_score * 0.3 +
            rel_weight * 0.4 +
            coherence * 0.1 +
            attention * 0.1 +
            connectivity * 0.1
        )
        
        return min(graph_score, 1.0)
    
    def _extract_graph_structural_metadata(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structural metadata from Neo4j node."""
        return {
            "element_count": node.get("element_count", 0),
            "has_headers": node.get("has_headers", False),
            "has_code": node.get("has_code", False),
            "has_tables": node.get("has_tables", False),
            "primary_language": node.get("primary_language", ""),
            "strategy_used": node.get("strategy_used", ""),
            "header_level": node.get("header_level", 0)
        }
    
    def _extract_graph_semantic_metadata(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """Extract semantic metadata from Neo4j node."""
        return {
            "themes": node.get("themes", []),
            "content_category": node.get("content_category", "general"),
            "technical_level": node.get("technical_level", "low"),
            "coherence_score": node.get("coherence_score", 0.0),
            "attention_score": node.get("attention_score", 0.0),
            "connectivity_score": node.get("connectivity_score", 0.0)
        }
    
    def _deduplicate_graph_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate results and merge relationship contexts."""
        seen = {}
        
        for result in results:
            if result.chunk_id in seen:
                # Merge relationship contexts
                seen[result.chunk_id].relationship_context.extend(result.relationship_context)
                # Keep higher graph score
                if result.graph_score > seen[result.chunk_id].graph_score:
                    seen[result.chunk_id].graph_score = result.graph_score
            else:
                seen[result.chunk_id] = result
        
        return list(seen.values())


class MarkdownMetadataScorer:
    """Scores chunks based on markdown-specific metadata features."""
    
    @staticmethod
    def score_chunk(result: SearchResult, 
                   query_context: Dict[str, Any] = None) -> float:
        """Calculate metadata-based relevance score."""
        
        if not result.structural_metadata or not result.semantic_metadata:
            return 0.1
        
        score_components = []
        
        # Content quality score
        coherence = result.semantic_metadata.get("coherence_score", 0.5)
        attention = result.semantic_metadata.get("attention_score", 0.5)
        connectivity = result.semantic_metadata.get("connectivity_score", 0.5)
        
        quality_score = (coherence + attention + connectivity) / 3
        score_components.append(quality_score * 0.4)
        
        # Structural richness score
        element_count = result.structural_metadata.get("element_count", 0)
        has_code = result.structural_metadata.get("has_code", False)
        has_tables = result.structural_metadata.get("has_tables", False)
        has_headers = result.structural_metadata.get("has_headers", False)
        
        richness_score = min(element_count / 10, 1.0) * 0.5
        if has_code: richness_score += 0.2
        if has_tables: richness_score += 0.2
        if has_headers: richness_score += 0.1
        
        score_components.append(min(richness_score, 1.0) * 0.3)
        
        # Context relevance score
        context_score = 0.5
        if query_context:
            context_score = MarkdownMetadataScorer._calculate_context_relevance(
                result, query_context
            )
        
        score_components.append(context_score * 0.3)
        
        return sum(score_components)
    
    @staticmethod
    def _calculate_context_relevance(result: SearchResult, 
                                   query_context: Dict[str, Any]) -> float:
        """Calculate how well the result matches query context."""
        relevance_score = 0.5
        
        # Technical level matching
        query_tech_level = query_context.get("technical_level")
        result_tech_level = result.semantic_metadata.get("technical_level")
        if query_tech_level and result_tech_level == query_tech_level:
            relevance_score += 0.2
        
        # Content category matching
        query_category = query_context.get("content_category")
        result_category = result.semantic_metadata.get("content_category")
        if query_category and result_category == query_category:
            relevance_score += 0.2
        
        # Theme overlap
        query_themes = query_context.get("themes", [])
        result_themes = result.semantic_metadata.get("themes", [])
        if query_themes and result_themes:
            overlap = len(set(query_themes) & set(result_themes))
            if overlap > 0:
                relevance_score += min(overlap / len(query_themes), 0.3)
        
        return min(relevance_score, 1.0)


class MarkdownHybridSearchEngine:
    """Main hybrid search engine combining vector, graph, and metadata search."""
    
    def __init__(self, 
                 qdrant_client,
                 neo4j_driver,
                 collection_name: str = "markdown_chunks"):
        self.vector_engine = MarkdownVectorSearchEngine(qdrant_client, collection_name)
        self.graph_engine = MarkdownGraphSearchEngine(neo4j_driver)
        self.metadata_scorer = MarkdownMetadataScorer()
        self.fusion_weights = MarkdownHybridSearchSchema.get_fusion_weights()
        self.search_templates = MarkdownHybridSearchSchema.get_search_templates()
    
    async def search(self,
                    query_vector: List[float],
                    query_text: str = "",
                    query_type: str = "conceptual_query",
                    config: Optional[HybridSearchConfig] = None,
                    filters: Optional[Dict[str, Any]] = None,
                    query_context: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Perform hybrid search combining all search modalities."""
        
        if config is None:
            config = HybridSearchConfig()
        
        try:
            # Get search template for query type
            template = self.search_templates.get(query_type, self.search_templates["conceptual_query"])
            fusion_profile = template["fusion_profile"]
            
            # Update config weights based on fusion profile
            profile_weights = self.fusion_weights[fusion_profile]
            config.vector_weight = profile_weights["vector_weight"]
            config.graph_weight = profile_weights["graph_weight"] 
            config.metadata_weight = profile_weights["metadata_weight"]
            
            # Phase 1: Vector search
            logger.info("Executing vector search phase")
            vector_results = await self.vector_engine.search(
                query_vector=query_vector,
                filters=filters,
                top_k=config.top_k_vector,
                boost_factors=config.boost_factors
            )
            
            # Phase 2: Graph search using top vector results as seeds
            logger.info("Executing graph search phase")
            seed_chunks = [r.chunk_id for r in vector_results[:10]]  # Top 10 as seeds
            graph_pattern = template["graph_pattern"]
            
            graph_results = await self.graph_engine.search(
                seed_chunks=seed_chunks,
                traversal_pattern=graph_pattern,
                max_depth=config.graph_traversal_depth,
                min_confidence=config.semantic_threshold
            )
            
            # Phase 3: Combine and score all results
            logger.info("Combining and scoring results")
            combined_results = self._combine_results(vector_results, graph_results)
            
            # Phase 4: Apply metadata scoring
            for result in combined_results:
                result.metadata_score = self.metadata_scorer.score_chunk(
                    result, query_context
                )
            
            # Phase 5: Calculate final hybrid scores
            final_results = self._calculate_hybrid_scores(combined_results, config)
            
            # Phase 6: Re-rank and filter
            final_results.sort(key=lambda x: x.combined_score, reverse=True)
            
            # Apply result filters from template
            if template.get("result_filters"):
                final_results = self._apply_result_filters(
                    final_results, template["result_filters"]
                )
            
            # Return top-k results
            top_results = final_results[:config.final_top_k]
            
            logger.info(f"Hybrid search completed: {len(top_results)} final results")
            self._log_search_statistics(vector_results, graph_results, final_results, top_results)
            
            return top_results
            
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return []
    
    def _combine_results(self, 
                        vector_results: List[SearchResult],
                        graph_results: List[SearchResult]) -> List[SearchResult]:
        """Combine vector and graph results, merging duplicates."""
        
        combined = {}
        
        # Add vector results
        for result in vector_results:
            combined[result.chunk_id] = result
        
        # Add or merge graph results
        for result in graph_results:
            if result.chunk_id in combined:
                # Merge with existing result
                existing = combined[result.chunk_id]
                existing.graph_score = result.graph_score
                existing.relationship_context.extend(result.relationship_context)
            else:
                # Add new result
                combined[result.chunk_id] = result
        
        return list(combined.values())
    
    def _calculate_hybrid_scores(self, 
                               results: List[SearchResult],
                               config: HybridSearchConfig) -> List[SearchResult]:
        """Calculate final hybrid scores using weighted combination."""
        
        for result in results:
            # Normalize individual scores
            vector_score = result.vector_score
            graph_score = result.graph_score
            metadata_score = result.metadata_score
            
            # Calculate weighted combination
            combined_score = (
                vector_score * config.vector_weight +
                graph_score * config.graph_weight +
                metadata_score * config.metadata_weight
            )
            
            result.combined_score = combined_score
        
        return results
    
    def _apply_result_filters(self, 
                            results: List[SearchResult],
                            filters: List[str]) -> List[SearchResult]:
        """Apply result filters based on content characteristics."""
        
        if not filters:
            return results
        
        filtered_results = []
        
        for result in results:
            should_include = True
            
            for filter_name in filters:
                if filter_name == "CodeContent" and not result.structural_metadata.get("has_code", False):
                    should_include = False
                    break
                elif filter_name == "TechnicalLevelHigh" and result.semantic_metadata.get("technical_level") != "high":
                    should_include = False
                    break
                elif filter_name == "HeaderContent" and not result.structural_metadata.get("has_headers", False):
                    should_include = False
                    break
                # Add more filter conditions as needed
            
            if should_include:
                filtered_results.append(result)
        
        return filtered_results
    
    def _log_search_statistics(self, 
                             vector_results: List[SearchResult],
                             graph_results: List[SearchResult],
                             combined_results: List[SearchResult],
                             final_results: List[SearchResult]):
        """Log detailed search statistics for analysis."""
        
        logger.info(f"Search Statistics:")
        logger.info(f"  Vector results: {len(vector_results)}")
        logger.info(f"  Graph results: {len(graph_results)}")
        logger.info(f"  Combined unique: {len(combined_results)}")
        logger.info(f"  Final top-k: {len(final_results)}")
        
        if final_results:
            avg_vector_score = np.mean([r.vector_score for r in final_results])
            avg_graph_score = np.mean([r.graph_score for r in final_results])
            avg_metadata_score = np.mean([r.metadata_score for r in final_results])
            avg_combined_score = np.mean([r.combined_score for r in final_results])
            
            logger.info(f"  Average scores - Vector: {avg_vector_score:.3f}, "
                       f"Graph: {avg_graph_score:.3f}, "
                       f"Metadata: {avg_metadata_score:.3f}, "
                       f"Combined: {avg_combined_score:.3f}")
    
    async def get_search_explanation(self, 
                                   query_text: str,
                                   results: List[SearchResult],
                                   config: HybridSearchConfig) -> Dict[str, Any]:
        """Generate explanation of search process and results."""
        
        explanation = {
            "query": query_text,
            "search_config": {
                "vector_weight": config.vector_weight,
                "graph_weight": config.graph_weight,
                "metadata_weight": config.metadata_weight,
                "top_k": config.final_top_k
            },
            "result_breakdown": {
                "total_results": len(results),
                "has_vector_scores": sum(1 for r in results if r.vector_score > 0),
                "has_graph_scores": sum(1 for r in results if r.graph_score > 0),
                "has_relationship_context": sum(1 for r in results if r.relationship_context)
            },
            "content_distribution": {
                "code_content": sum(1 for r in results if r.structural_metadata.get("has_code", False)),
                "table_content": sum(1 for r in results if r.structural_metadata.get("has_tables", False)),
                "header_content": sum(1 for r in results if r.structural_metadata.get("has_headers", False))
            },
            "quality_metrics": {
                "avg_coherence": np.mean([r.semantic_metadata.get("coherence_score", 0) for r in results]),
                "avg_attention": np.mean([r.semantic_metadata.get("attention_score", 0) for r in results]),
                "avg_connectivity": np.mean([r.semantic_metadata.get("connectivity_score", 0) for r in results])
            }
        }
        
        return explanation


# Factory function for easy instantiation
def create_hybrid_search_engine(qdrant_client, neo4j_driver, collection_name: str = "markdown_chunks") -> MarkdownHybridSearchEngine:
    """Factory function to create a configured hybrid search engine."""
    return MarkdownHybridSearchEngine(
        qdrant_client=qdrant_client,
        neo4j_driver=neo4j_driver,
        collection_name=collection_name
    )