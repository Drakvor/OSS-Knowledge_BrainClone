"""
Hybrid Search Engine for Benchmark Evaluation
=============================================

3-phase hybrid search: Vector + Graph + Score Fusion
"""

import asyncio
import logging
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from dataclasses import dataclass

from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer

from app.benchmark.base import StrategyType, TestQuery

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Individual search result"""
    chunk_id: str
    content: str
    vector_score: float
    graph_score: float
    fusion_score: float
    metadata: Dict[str, Any]
    strategy_type: str
    relevance_rank: int


@dataclass
class HybridSearchResults:
    """Complete hybrid search results"""
    query: TestQuery
    strategy_type: StrategyType
    results: List[SearchResult]
    search_metrics: Dict[str, float]
    phase_results: Dict[str, Any]


class HybridSearchEngine:
    """3-phase hybrid search engine for benchmark evaluation"""
    
    def __init__(self, qdrant_host: str = "localhost", qdrant_port: int = 6333,
                 neo4j_uri: str = "neo4j://localhost:7687", neo4j_user: str = "neo4j", 
                 neo4j_password: str = "!alsrksdlswp5", embedding_model: str = "text-embedding-3-large"):
        
        # Initialize vector search
        self.qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
        
        # Initialize graph search
        self.neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(embedding_model)
        
        # Search configuration
        self.vector_weight = 0.5
        self.graph_weight = 0.3
        self.fusion_weight = 0.2
        
        self.max_vector_results = 20
        self.max_graph_results = 15
        self.final_result_limit = 10
        
        logger.info(f"✅ Hybrid search engine initialized with {embedding_model}")
    
    async def search(self, query: TestQuery, strategy_type: StrategyType, 
                    search_config: Dict[str, Any]) -> HybridSearchResults:
        """Perform 3-phase hybrid search"""
        
        collection_name = f"search_test_{strategy_type.value}"
        
        # Phase 1: Vector Search
        vector_results = await self._vector_search_phase(query, collection_name, search_config)
        
        # Phase 2: Graph Search  
        graph_results = await self._graph_search_phase(query, strategy_type, search_config)
        
        # Phase 3: Score Fusion
        fusion_results = self._score_fusion_phase(vector_results, graph_results, search_config)
        
        # Calculate search metrics
        search_metrics = self._calculate_search_metrics(vector_results, graph_results, fusion_results)
        
        # Create final results
        final_results = []
        for i, (chunk_id, scores, content, metadata) in enumerate(fusion_results[:self.final_result_limit]):
            result = SearchResult(
                chunk_id=chunk_id,
                content=content,
                vector_score=scores.get("vector_score", 0.0),
                graph_score=scores.get("graph_score", 0.0),
                fusion_score=scores.get("fusion_score", 0.0),
                metadata=metadata,
                strategy_type=strategy_type.value,
                relevance_rank=i + 1
            )
            final_results.append(result)
        
        phase_results = {
            "vector_phase": {
                "count": len(vector_results),
                "top_score": max([r[1] for r in vector_results]) if vector_results else 0.0
            },
            "graph_phase": {
                "count": len(graph_results),
                "top_score": max([r[1] for r in graph_results]) if graph_results else 0.0
            },
            "fusion_phase": {
                "count": len(fusion_results),
                "top_score": fusion_results[0][1]["fusion_score"] if fusion_results else 0.0
            }
        }
        
        return HybridSearchResults(
            query=query,
            strategy_type=strategy_type,
            results=final_results,
            search_metrics=search_metrics,
            phase_results=phase_results
        )
    
    async def _vector_search_phase(self, query: TestQuery, collection_name: str, 
                                 search_config: Dict[str, Any]) -> List[Tuple[str, float, str, Dict[str, Any]]]:
        """Phase 1: Vector similarity search"""
        
        try:
            # Generate query embedding
            query_vector = self.embedding_model.encode(query.query_text).tolist()
            
            # Create filter for strategy
            search_filter = Filter(
                must=[
                    FieldCondition(
                        key="strategy",
                        match=MatchValue(value=search_config.get("filter_metadata", {}).get("strategy", ""))
                    )
                ]
            )
            
            # Perform vector search
            search_result = self.qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                query_filter=search_filter,
                limit=self.max_vector_results,
                score_threshold=0.1
            )
            
            # Process results
            vector_results = []
            for result in search_result:
                chunk_id = result.payload.get("chunk_id", str(result.id))
                content = result.payload.get("content", "")
                score = float(result.score)
                metadata = result.payload
                
                vector_results.append((chunk_id, score, content, metadata))
            
            logger.info(f"Vector search found {len(vector_results)} results for {collection_name}")
            return vector_results
            
        except Exception as e:
            logger.error(f"Vector search failed for {collection_name}: {e}")
            return []
    
    async def _graph_search_phase(self, query: TestQuery, strategy_type: StrategyType, 
                                search_config: Dict[str, Any]) -> List[Tuple[str, float, str, Dict[str, Any]]]:
        """Phase 2: Graph traversal search"""
        
        try:
            with self.neo4j_driver.session() as session:
                # Build graph query based on strategy type
                graph_query = self._build_graph_query(query, strategy_type, search_config)
                
                # Execute graph query
                result = session.run(graph_query, query_text=query.query_text.lower())
                
                graph_results = []
                for record in result:
                    chunk_id = record.get("chunk_id", "")
                    content = record.get("content", "")
                    graph_score = float(record.get("relevance_score", 0.0))
                    
                    # Create metadata from graph result
                    metadata = {
                        "strategy": strategy_type.value,
                        "graph_relevance": graph_score,
                        "relationship_count": record.get("relationship_count", 0),
                        "path_length": record.get("path_length", 0)
                    }
                    
                    graph_results.append((chunk_id, graph_score, content, metadata))
                
                # Sort by graph score
                graph_results.sort(key=lambda x: x[1], reverse=True)
                
                logger.info(f"Graph search found {len(graph_results)} results for {strategy_type.value}")
                return graph_results[:self.max_graph_results]
                
        except Exception as e:
            logger.error(f"Graph search failed for {strategy_type.value}: {e}")
            return []
    
    def _build_graph_query(self, query: TestQuery, strategy_type: StrategyType, 
                          search_config: Dict[str, Any]) -> str:
        """Build graph query based on strategy type"""
        
        # Base query structure
        base_query = """
        MATCH (n)
        WHERE n.strategy = $strategy_type
        AND toLower(n.content) CONTAINS $query_text
        """
        
        # Strategy-specific graph queries
        if strategy_type == StrategyType.ROW_BASED:
            query = base_query + """
            OPTIONAL MATCH (n)-[r:sequential_rows]-(related)
            RETURN n.chunk_id as chunk_id, n.content as content,
                   1.0 as relevance_score, count(r) as relationship_count, 1 as path_length
            ORDER BY relevance_score DESC
            LIMIT 15
            """
            
        elif strategy_type == StrategyType.HIERARCHICAL:
            query = base_query + """
            OPTIONAL MATCH (n)-[r:parent_child|sibling*1..2]-(related)
            WITH n, count(r) as rel_count
            RETURN n.chunk_id as chunk_id, n.content as content,
                   (1.0 + rel_count * 0.1) as relevance_score, rel_count as relationship_count, 2 as path_length
            ORDER BY relevance_score DESC
            LIMIT 15
            """
            
        elif strategy_type == StrategyType.ENTITY_CENTRIC:
            query = base_query + """
            OPTIONAL MATCH (n)-[r:same_ticket|same_user|same_asset]-(related)
            WITH n, count(r) as rel_count
            RETURN n.chunk_id as chunk_id, n.content as content,
                   (1.2 + rel_count * 0.15) as relevance_score, rel_count as relationship_count, 1 as path_length
            ORDER BY relevance_score DESC
            LIMIT 15
            """
            
        else:
            # Generic query for other strategies
            query = base_query + """
            OPTIONAL MATCH (n)-[r]-(related)
            WITH n, count(r) as rel_count
            RETURN n.chunk_id as chunk_id, n.content as content,
                   (1.0 + rel_count * 0.1) as relevance_score, rel_count as relationship_count, 1 as path_length
            ORDER BY relevance_score DESC
            LIMIT 15
            """
        
        return query.replace("$strategy_type", f"'{strategy_type.value}'")
    
    def _score_fusion_phase(self, vector_results: List[Tuple[str, float, str, Dict[str, Any]]], 
                          graph_results: List[Tuple[str, float, str, Dict[str, Any]]], 
                          search_config: Dict[str, Any]) -> List[Tuple[str, Dict[str, float], str, Dict[str, Any]]]:
        """Phase 3: Score fusion and ranking"""
        
        # Normalize scores
        normalized_vector = self._normalize_scores(vector_results)
        normalized_graph = self._normalize_scores(graph_results)
        
        # Create score dictionary
        all_chunk_ids = set()
        score_map = {}
        content_map = {}
        metadata_map = {}
        
        # Add vector results
        for chunk_id, score, content, metadata in normalized_vector:
            all_chunk_ids.add(chunk_id)
            score_map[chunk_id] = {"vector_score": score, "graph_score": 0.0}
            content_map[chunk_id] = content
            metadata_map[chunk_id] = metadata
        
        # Add graph results
        for chunk_id, score, content, metadata in normalized_graph:
            all_chunk_ids.add(chunk_id)
            if chunk_id in score_map:
                score_map[chunk_id]["graph_score"] = score
            else:
                score_map[chunk_id] = {"vector_score": 0.0, "graph_score": score}
                content_map[chunk_id] = content
                metadata_map[chunk_id] = metadata
        
        # Calculate fusion scores
        fusion_results = []
        for chunk_id in all_chunk_ids:
            scores = score_map[chunk_id]
            vector_score = scores["vector_score"]
            graph_score = scores["graph_score"]
            
            # Calculate fusion score with configurable weights
            fusion_score = (
                vector_score * self.vector_weight +
                graph_score * self.graph_weight +
                (vector_score * graph_score) * self.fusion_weight  # Multiplicative fusion
            )
            
            scores["fusion_score"] = fusion_score
            
            fusion_results.append((
                chunk_id,
                scores,
                content_map[chunk_id],
                metadata_map[chunk_id]
            ))
        
        # Sort by fusion score
        fusion_results.sort(key=lambda x: x[1]["fusion_score"], reverse=True)
        
        return fusion_results
    
    def _normalize_scores(self, results: List[Tuple[str, float, str, Dict[str, Any]]]) -> List[Tuple[str, float, str, Dict[str, Any]]]:
        """Normalize scores to 0-1 range"""
        
        if not results:
            return []
        
        scores = [r[1] for r in results]
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score == min_score:
            return [(r[0], 1.0, r[2], r[3]) for r in results]
        
        normalized = []
        for chunk_id, score, content, metadata in results:
            norm_score = (score - min_score) / (max_score - min_score)
            normalized.append((chunk_id, norm_score, content, metadata))
        
        return normalized
    
    def _calculate_search_metrics(self, vector_results: List, graph_results: List, 
                                fusion_results: List) -> Dict[str, float]:
        """Calculate search performance metrics"""
        
        return {
            "vector_results_count": len(vector_results),
            "graph_results_count": len(graph_results),
            "fusion_results_count": len(fusion_results),
            "vector_graph_overlap": len(set(r[0] for r in vector_results) & 
                                      set(r[0] for r in graph_results)),
            "avg_vector_score": np.mean([r[1] for r in vector_results]) if vector_results else 0.0,
            "avg_graph_score": np.mean([r[1] for r in graph_results]) if graph_results else 0.0,
            "avg_fusion_score": np.mean([r[1]["fusion_score"] for r in fusion_results]) if fusion_results else 0.0,
        }
    
    def close(self):
        """Close database connections"""
        self.neo4j_driver.close()
        self.qdrant_client.close()


class BenchmarkSearchEvaluator:
    """Evaluates search performance across strategies"""
    
    def __init__(self, hybrid_search: HybridSearchEngine):
        self.hybrid_search = hybrid_search
    
    async def evaluate_strategy(self, strategy_type: StrategyType, test_queries: List[TestQuery],
                              search_config: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate search performance for a strategy"""
        
        all_results = []
        
        for query in test_queries:
            search_results = await self.hybrid_search.search(query, strategy_type, search_config)
            all_results.append(search_results)
        
        # Calculate aggregate metrics
        aggregate_metrics = self._calculate_aggregate_metrics(all_results)
        
        return {
            "strategy_type": strategy_type.value,
            "query_results": all_results,
            "aggregate_metrics": aggregate_metrics
        }
    
    def _calculate_aggregate_metrics(self, results: List[HybridSearchResults]) -> Dict[str, float]:
        """Calculate aggregate metrics across all queries"""
        
        if not results:
            return {}
        
        # Average metrics across all queries
        metrics = {
            "avg_vector_results": np.mean([r.search_metrics["vector_results_count"] for r in results]),
            "avg_graph_results": np.mean([r.search_metrics["graph_results_count"] for r in results]),
            "avg_fusion_results": np.mean([r.search_metrics["fusion_results_count"] for r in results]),
            "avg_vector_score": np.mean([r.search_metrics["avg_vector_score"] for r in results]),
            "avg_graph_score": np.mean([r.search_metrics["avg_graph_score"] for r in results]),
            "avg_fusion_score": np.mean([r.search_metrics["avg_fusion_score"] for r in results]),
            "total_queries": len(results)
        }
        
        return metrics