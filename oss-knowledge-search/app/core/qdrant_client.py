"""
Qdrant Vector Database Client for Search Operations
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct, Filter, FieldCondition, MatchValue
from qdrant_client.http import models

from app.config import settings

logger = logging.getLogger(__name__)


class QdrantService:
    """Qdrant vector database service for search operations"""
    
    def __init__(self):
        self.client: Optional[QdrantClient] = None
        self.collection_name = settings.QDRANT_COLLECTION
        self.vector_size = settings.VECTOR_SIZE
        self.host = settings.QDRANT_HOST
        self.port = settings.QDRANT_PORT
        self.timeout = settings.QDRANT_TIMEOUT
        self.initialized = False
        
        logger.info(f"Qdrant Service initialized - Host: {self.host}:{self.port}, Base Collection: {self.collection_name}")

    def get_collection_name(self, container: str) -> str:
        """Get collection name for a specific container"""
        # Import here to avoid circular imports
        from app.services.container_validation_service import container_validator

        try:
            collection_name = container_validator.get_container_collection_name(container)
            logger.info(f"Mapped container '{container}' to collection '{collection_name}'")
            return collection_name
        except Exception as e:
            logger.error(f"Failed to get collection name for container '{container}': {e}")
            # Fallback to container name for backward compatibility
            return container.lower().replace(' ', '-')

    async def initialize(self) -> bool:
        """Initialize Qdrant client and verify collection"""
        
        if self.initialized:
            return True
        
        try:
            self.client = QdrantClient(
                host=self.host,
                port=self.port,
                timeout=self.timeout
            )
            
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if self.collection_name not in collection_names:
                logger.error(
                    f"Collection '{self.collection_name}' not found. "
                    f"Available collections: {collection_names}"
                )
                return False
            
            # Get collection info to verify vector size (with error handling)
            try:
                collection_info = self.client.get_collection(self.collection_name)
                vector_config = collection_info.config.params.vectors
                
                # Handle different vector config structures
                actual_size = None
                
                # Single vector (default) - has 'size' attribute
                if hasattr(vector_config, 'size'):
                    actual_size = vector_config.size
                # Named vectors - dictionary with vector names as keys
                elif isinstance(vector_config, dict):
                    # Try 'embedding' first (most common for this use case)
                    if 'embedding' in vector_config:
                        if hasattr(vector_config['embedding'], 'size'):
                            actual_size = vector_config['embedding'].size
                    # Fallback to 'default' if exists
                    elif 'default' in vector_config:
                        if hasattr(vector_config['default'], 'size'):
                            actual_size = vector_config['default'].size
                    # Try first available vector
                    elif len(vector_config) > 0:
                        first_vector = next(iter(vector_config.values()))
                        if hasattr(first_vector, 'size'):
                            actual_size = first_vector.size
                
                if actual_size is None:
                    logger.warning(
                        f"Cannot determine vector size from collection '{self.collection_name}' config. "
                        f"Using configured default: {self.vector_size}"
                    )
                    actual_size = self.vector_size
                
                if actual_size != self.vector_size:
                    logger.warning(
                        f"Vector size mismatch: expected {self.vector_size}, got {actual_size}"
                    )
                    self.vector_size = actual_size
                    
            except Exception as e:
                logger.warning(
                    f"Failed to get collection config (Qdrant version compatibility issue): {e}"
                )
                logger.info(f"Using default vector size: {self.vector_size}")
            
            # Test connection with a simple count
            count = self.client.count(collection_name=self.collection_name)
            logger.info(f"Qdrant connected successfully - Collection: {self.collection_name}, Vector size: {self.vector_size}, Points: {count.count}")
            
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant service: {e}")
            return False
    
    async def vector_search(
        self,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None,
        collection_name: Optional[str] = None,
        container: Optional[str] = None,
        vector_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Perform vector similarity search"""
        
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
            
            # Use specified collection, or container-specific collection, or default
            if collection_name:
                target_collection = collection_name
            elif container:
                target_collection = self.get_collection_name(container)
            else:
                target_collection = self.collection_name

            # Perform search with specified vector name or default
            search_params = {
                "collection_name": target_collection,
                "query_vector": query_vector,
                "limit": limit,
                "score_threshold": score_threshold,
                "query_filter": filter_condition,
                "with_payload": True,
                "with_vectors": False
            }
            
            # Add vector name if specified
            if vector_name:
                search_params["query_vector"] = (vector_name, query_vector)
                logger.info(f"Searching with vector name: {vector_name}")
            else:
                logger.info("Searching with default vector")
            
            results = self.client.search(**search_params)
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_result = {
                    "id": str(result.id),
                    "score": float(result.score),
                    "payload": result.payload or {}
                }
                formatted_results.append(formatted_result)
            
            logger.info(f"Vector search completed - Query vector size: {len(query_vector)}, Results: {len(formatted_results)}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise Exception(f"Failed to perform vector search: {e}")
    
    async def hybrid_search(
        self,
        query_vector: List[float],
        text_query: Optional[str] = None,
        limit: int = 10,
        vector_weight: float = 0.7,
        text_weight: float = 0.3,
        score_threshold: float = 0.6,
        filters: Optional[Dict[str, Any]] = None,
        container: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Perform hybrid vector + text search"""
        
        # For now, just perform vector search
        # TODO: Implement actual hybrid search with text matching
        results = await self.vector_search(
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            filters=filters,
            container=container
        )
        
        # Adjust scores based on weights
        for result in results:
            result["score"] = result["score"] * vector_weight
        
        return results
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics (with error handling for config parsing issues)"""
        
        if not self.initialized:
            await self.initialize()
        
        if not self.client:
            raise Exception("Qdrant client not initialized")
        
        try:
            # Get basic count (this always works)
            count = self.client.count(collection_name=self.collection_name)
            
            stats = {
                "collection_name": self.collection_name,
                "points_count": count.count,
                "vector_size": self.vector_size,
                "status": "connected"
            }
            
            # Try to get additional collection info (may fail due to version compatibility)
            try:
                collection_info = self.client.get_collection(self.collection_name)
                
                # Safely extract what we can
                if hasattr(collection_info, 'status'):
                    stats["status"] = collection_info.status.value
                
                if hasattr(collection_info, 'config') and hasattr(collection_info.config, 'params'):
                    vectors_config = collection_info.config.params.vectors
                    if hasattr(vectors_config, 'distance'):
                        stats["distance"] = vectors_config.distance.value
                    if hasattr(vectors_config, 'size'):
                        stats["actual_vector_size"] = vectors_config.size
                        
                if hasattr(collection_info, 'points_count'):
                    stats["indexed_points"] = collection_info.points_count
                    
            except Exception as config_error:
                logger.warning(f"Could not get detailed collection config (version compatibility): {config_error}")
                stats["config_warning"] = "Detailed config unavailable due to Qdrant client version compatibility"
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            raise Exception(f"Failed to get collection statistics: {e}")
    
    async def close(self):
        """Close Qdrant client connection"""
        if self.client:
            try:
                self.client.close()
                logger.info("Qdrant client closed")
            except Exception as e:
                logger.error(f"Error closing Qdrant client: {e}")
            finally:
                self.client = None
                self.initialized = False