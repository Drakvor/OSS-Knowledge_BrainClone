"""
RETRIEVE task implementation
Retrieves information from Search Server (RAG) or directly from Qdrant/Neo4j
"""

import logging
import httpx
import os
from typing import Dict, Any, Optional
from app.tasks.base_task import BaseTask
from app.integrations.qdrant_client import QdrantClientService
from app.integrations.neo4j_client import Neo4jClientService
from app.utils.query_decomposer import QueryDecomposer

logger = logging.getLogger(__name__)

class RetrieveTask(BaseTask):
    """Task for retrieving information via RAG, Qdrant, or Neo4j"""
    
    def __init__(self, task, search_server_url: str = None):
        super().__init__(task)
        import os
        self.search_server_url = search_server_url or os.getenv("SEARCH_SERVER_URL", "http://localhost:8002")
        self.timeout = 30.0
        self.qdrant_client = QdrantClientService()
        self.neo4j_client = Neo4jClientService()
        self.use_direct_integration = os.getenv("USE_DIRECT_INTEGRATION", "false").lower() == "true"
        self._query_decomposer = None  # Lazy initialization
    
    def _get_query_decomposer(self) -> Optional[QueryDecomposer]:
        """Get or create QueryDecomposer instance (lazy initialization)"""
        if self._query_decomposer is None:
            try:
                self._query_decomposer = QueryDecomposer()
            except Exception as e:
                logger.warning(f"Failed to initialize QueryDecomposer: {e}")
                return None
        return self._query_decomposer
    
    async def _decompose_query_if_enabled(
        self,
        query: str,
        collection: Optional[str] = None,
        plan_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Decompose query if decomposition is enabled, otherwise return original.
        
        Args:
            query: Original query
            collection: Collection name for context
            plan_context: Plan context for chat history
            
        Returns:
            Optimized query or original query
        """
        decomposer = self._get_query_decomposer()
        if decomposer is None:
            return query
        
        # Extract chat context from plan_context if available
        chat_context = None
        if plan_context:
            chat_context = {
                "chat_history": plan_context.get("chat_history", [])
            }
        
        try:
            optimized_query = await decomposer.decompose_query(
                query=query,
                collection=collection,
                chat_context=chat_context
            )
            return optimized_query
        except Exception as e:
            logger.warning(f"Query decomposition failed, using original query: {e}")
            return query
    
    async def execute(self, plan_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute RETRIEVE task by calling Search Server, Qdrant, or Neo4j"""
        self.mark_started()
        
        try:
            params = self.task.parameters
            extra = params.extra or {}
            
            # Determine retrieval method
            retrieval_method = extra.get("method", "search_server")  # search_server, qdrant, neo4j, or hybrid
            
            if retrieval_method == "qdrant" and self.use_direct_integration:
                result = await self._retrieve_from_qdrant(params, plan_context, extra)
            elif retrieval_method == "neo4j" and self.use_direct_integration:
                result = await self._retrieve_from_neo4j(params, plan_context, extra)
            elif retrieval_method == "hybrid" and self.use_direct_integration:
                result = await self._retrieve_hybrid(params, plan_context, extra)
            else:
                # Default: Use Search Server
                result = await self._retrieve_from_search_server(params, plan_context)
            
            self.mark_completed(result)
            return result
            
        except Exception as e:
            error_msg = f"RETRIEVE task failed: {str(e)}"
            logger.error(error_msg)
            self.mark_failed(error_msg)
            raise
    
    async def _retrieve_from_search_server(self, params, plan_context: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve via Search Server (default method)"""
        original_query = params.search_query or plan_context.get("query", "")
        collection = params.collection or plan_context.get("collection", "general")
        limit = params.limit or 5
        
        # Decompose/optimize query for vector search
        optimized_query = await self._decompose_query_if_enabled(
            query=original_query,
            collection=collection,
            plan_context=plan_context
        )
        
        # Use optimized query for search
        search_query = optimized_query
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.search_server_url}/search/response",
                json={
                    "query": search_query,
                    "collection": collection,
                    "limit": limit,
                    "threshold": 0.3,
                    "include_metadata": True,
                    "include_content": True,
                    "max_tokens": 1000,
                    "temperature": 0.7
                }
            )
            response.raise_for_status()
            data = response.json()
        
        return {
            "method": "search_server",
            "original_query": original_query,
            "optimized_query": optimized_query,
            "search_query": search_query,  # Keep for backward compatibility
            "collection": collection,
            "response": data.get("response", ""),
            "sources": data.get("sources", []),
            "search_results": data.get("search_results", [])
        }
    
    async def _retrieve_from_qdrant(self, params, plan_context: Dict[str, Any], extra: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve directly from Qdrant"""
        # This requires embedding the query first
        # For now, we'll use Search Server's embedding, but in future could use embedding service directly
        original_query = params.search_query or plan_context.get("query", "")
        collection = params.collection or plan_context.get("collection", "general")
        limit = params.limit or 5
        score_threshold = extra.get("score_threshold", 0.7)
        
        # Decompose/optimize query for vector search
        optimized_query = await self._decompose_query_if_enabled(
            query=original_query,
            collection=collection,
            plan_context=plan_context
        )
        
        # Use optimized query for embedding and search
        search_query = optimized_query
        
        # Get embedding from Search Server (or embedding service if available)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Get embedding
            embed_response = await client.post(
                f"{self.search_server_url}/embed",
                json={"text": search_query}
            )
            if embed_response.status_code != 200:
                # Fallback to Search Server
                return await self._retrieve_from_search_server(params, plan_context)
            
            query_vector = embed_response.json().get("embedding", [])
        
        # Search Qdrant
        results = await self.qdrant_client.vector_search(
            query_vector=query_vector,
            collection=collection,
            limit=limit,
            score_threshold=score_threshold,
            filters=extra.get("filters")
        )
        
        return {
            "method": "qdrant",
            "original_query": original_query,
            "optimized_query": optimized_query,
            "search_query": search_query,  # Keep for backward compatibility
            "collection": collection,
            "search_results": results,
            "sources": [r.get("source_file", "unknown") for r in results]
        }
    
    async def _retrieve_from_neo4j(self, params, plan_context: Dict[str, Any], extra: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve from Neo4j graph"""
        topic = params.search_query or extra.get("topic") or plan_context.get("query", "")
        max_depth = extra.get("max_depth", 3)
        limit = params.limit or 5
        
        # Get topic hierarchy
        hierarchy = await self.neo4j_client.get_topic_hierarchy(
            topic=topic,
            max_depth=max_depth,
            limit=limit
        )
        
        # Get related documents
        documents = await self.neo4j_client.find_related_documents(
            topic=topic,
            relationship_type=extra.get("relationship_type"),
            limit=limit
        )
        
        return {
            "method": "neo4j",
            "topic": topic,
            "hierarchy": hierarchy,
            "related_documents": documents
        }
    
    async def _retrieve_hybrid(self, params, plan_context: Dict[str, Any], extra: Dict[str, Any]) -> Dict[str, Any]:
        """Hybrid retrieval from both Qdrant and Neo4j"""
        qdrant_result = await self._retrieve_from_qdrant(params, plan_context, extra)
        neo4j_result = await self._retrieve_from_neo4j(params, plan_context, extra)
        
        # Extract original and optimized queries from qdrant_result (which has decomposition)
        original_query = qdrant_result.get("original_query", params.search_query or plan_context.get("query", ""))
        optimized_query = qdrant_result.get("optimized_query", original_query)
        
        return {
            "method": "hybrid",
            "original_query": original_query,
            "optimized_query": optimized_query,
            "search_query": optimized_query,  # Keep for backward compatibility
            "qdrant_results": qdrant_result,
            "neo4j_results": neo4j_result
        }

