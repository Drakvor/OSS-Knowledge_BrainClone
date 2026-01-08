"""
Qdrant client for vector retrieval in Task Planner
"""

import logging
import os
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

logger = logging.getLogger(__name__)

class QdrantClientService:
    """Qdrant client for vector retrieval"""
    
    def __init__(self):
        self.client: Optional[QdrantClient] = None
        self.host = os.getenv("QDRANT_HOST", "20.249.165.27")
        self.port = int(os.getenv("QDRANT_PORT", "6333"))
        self.timeout = int(os.getenv("QDRANT_TIMEOUT", "30"))
        self.initialized = False
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"QdrantClientService initialized - Host: {self.host}:{self.port}")
    
    async def initialize(self) -> bool:
        """Initialize Qdrant client"""
        if self.initialized and self.client:
            return True
        
        try:
            self.client = QdrantClient(
                host=self.host,
                port=self.port,
                timeout=self.timeout
            )
            
            # Test connection
            collections = self.client.get_collections()
            self.logger.info(f"Qdrant connected successfully - Found {len(collections.collections)} collections")
            
            self.initialized = True
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Qdrant client: {e}")
            return False
    
    async def vector_search(
        self,
        query_vector: List[float],
        collection: str = "general",
        limit: int = 10,
        score_threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search
        
        Args:
            query_vector: Query embedding vector
            collection: Collection name to search
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            filters: Optional metadata filters
            
        Returns:
            List of search results with content and metadata
        """
        if not self.initialized:
            await self.initialize()
        
        if not self.client:
            raise Exception("Qdrant client not initialized")
        
        try:
            # Build filter conditions
            filter_condition = None
            if filters:
                conditions = []
                for field, value in filters.items():
                    if isinstance(value, (str, int, float, bool)):
                        conditions.append(
                            FieldCondition(
                                key=field,
                                match=MatchValue(value=value)
                            )
                        )
                
                if conditions:
                    filter_condition = Filter(must=conditions)
            
            # Perform search
            results = self.client.search(
                collection_name=collection,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=filter_condition,
                with_payload=True,
                with_vectors=False
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "id": result.id,
                    "score": result.score,
                    "content": result.payload.get("content", ""),
                    "metadata": {k: v for k, v in result.payload.items() if k != "content"},
                    "source_file": result.payload.get("source_file", "unknown")
                })
            
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Qdrant vector search failed: {e}")
            raise
    
    async def get_collection_info(self, collection: str) -> Dict[str, Any]:
        """Get information about a collection"""
        if not self.initialized:
            await self.initialize()
        
        if not self.client:
            raise Exception("Qdrant client not initialized")
        
        try:
            collection_info = self.client.get_collection(collection)
            return {
                "name": collection,
                "vectors_count": collection_info.vectors_count,
                "points_count": collection_info.points_count,
                "config": collection_info.config.dict() if hasattr(collection_info.config, 'dict') else str(collection_info.config)
            }
        except Exception as e:
            self.logger.error(f"Failed to get collection info: {e}")
            return {"name": collection, "error": str(e)}

