"""
Qdrant Vector Storage Implementation
Production-ready vector storage with rich metadata
"""

import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

from app.config import settings
from app.processors.base.interfaces import VectorStorageInterface
from app.processors.base.base_models import (
    ProcessedChunk, ChunkEmbedding, StorageOperation, StorageType
)
from app.core.exceptions import StorageError

logger = logging.getLogger(__name__)


class QdrantVectorStorage(VectorStorageInterface):
    """Production Qdrant vector storage with rich metadata and container isolation"""
    
    def __init__(self, container: str = "general"):
        self.client: Optional[QdrantClient] = None
        self.container = container
        self.collection_name = self._get_collection_name(container)
        self.vector_size = 3072  # OpenAI text-embedding-3-large dimension
        self.similarity_function = settings.SIMILARITY_FUNCTION
        self.connected = False

        # Initialize Qdrant client immediately
        self._initialize_client()

        logger.info(f"Qdrant storage initialized - Container: {container}, Collection: {self.collection_name}")

    def _initialize_client(self):
        """Initialize Qdrant client synchronously"""
        try:
            if settings.QDRANT_API_KEY:
                self.client = QdrantClient(
                    host=settings.QDRANT_HOST,
                    port=settings.QDRANT_PORT,
                    api_key=settings.QDRANT_API_KEY,
                    https=settings.QDRANT_HTTPS
                )
            else:
                self.client = QdrantClient(
                    host=settings.QDRANT_HOST,
                    port=settings.QDRANT_PORT
                )
            
            # Test connection
            collections = self.client.get_collections()
            self.connected = True
            logger.info(f"Qdrant client initialized successfully - Connected to {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {str(e)}")
            self.connected = False
            raise StorageError(f"Qdrant client initialization failed: {str(e)}", "qdrant")

    def _get_collection_name(self, container: str) -> str:
        """Get collection name for a specific container"""
        try:
            # Import here to avoid circular imports
            from app.services.container_validation_service import ContainerValidationService

            validator = ContainerValidationService()
            collection_name = validator.get_container_collection_name(container)
            logger.info(f"Mapped container '{container}' to collection '{collection_name}'")
            return collection_name
        except Exception as e:
            logger.error(f"Failed to get collection name for container '{container}': {e}")
            # Fallback to container name for backward compatibility (preserve case)
            return container.replace(' ', '_')
    
    async def initialize(self) -> bool:
        """Initialize Qdrant client and collection"""
        
        if self.connected:
            return True
        
        try:
            # Initialize Qdrant client
            if settings.QDRANT_API_KEY:
                self.client = QdrantClient(
                    host=settings.QDRANT_HOST,
                    port=settings.QDRANT_PORT,
                    api_key=settings.QDRANT_API_KEY,
                    https=settings.QDRANT_HTTPS
                )
            else:
                self.client = QdrantClient(
                    host=settings.QDRANT_HOST,
                    port=settings.QDRANT_PORT
                )
            
            # Test connection
            collections = self.client.get_collections()
            logger.info(f"Connected to Qdrant - Available collections: {len(collections.collections)}")
            
            # Create collection if it doesn't exist
            await self._ensure_collection_exists()
            
            self.connected = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant storage: {str(e)}")
            raise StorageError(f"Qdrant initialization failed: {str(e)}", "qdrant")
    
    async def _ensure_collection_exists(self):
        """Ensure collection exists with proper configuration"""
        
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"Creating Qdrant collection: {self.collection_name}")
                
                # Define vector configuration
                vector_config = models.VectorParams(
                    size=self.vector_size,
                    distance=models.Distance.COSINE if self.similarity_function == "cosine" else models.Distance.DOT
                )
                
                # Create collection with rich metadata schema (simplified config for compatibility)
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=vector_config
                )
                
                logger.info(f"Created Qdrant collection: {self.collection_name}")
            else:
                logger.info(f"Qdrant collection already exists: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"Failed to ensure collection exists: {str(e)}")
            raise StorageError(f"Collection creation failed: {str(e)}", "qdrant")
    
    async def health_check(self) -> bool:
        """Check Qdrant health"""
        
        try:
            if not self.client:
                return False
            
            # Test with a simple collection info request
            info = self.client.get_collection(self.collection_name)
            return info is not None
            
        except Exception:
            return False
    
    async def close(self) -> None:
        """Close Qdrant connection"""
        
        if self.client:
            try:
                self.client.close()
            except Exception as e:
                logger.warning(f"Error closing Qdrant client: {e}")
        
        self.connected = False
        logger.info("Qdrant storage connection closed")
    
    async def store_embeddings(
        self, 
        job_id: str,
        embeddings: List[ChunkEmbedding]
    ) -> StorageOperation:
        """Store embeddings in Qdrant with rich metadata"""
        
        if not self.connected:
            await self.initialize()
        
        try:
            logger.info(f"Storing {len(embeddings)} embeddings in Qdrant for job {job_id}")
            
            # Check collection configuration to determine vector format
            collection_info = self.client.get_collection(self.collection_name)
            vectors_config = collection_info.config.params.vectors
            
            # Determine if collection uses named vectors
            use_named_vectors = isinstance(vectors_config, dict) and "embedding" in vectors_config
            
            # Prepare points for batch upsert
            points = []
            
            for embedding in embeddings:
                # Create rich metadata payload
                payload = {
                    "chunk_id": embedding.chunk_id,
                    "job_id": job_id,
                    "container": self.container,
                    "collection": self.collection_name,
                    "model_used": embedding.model_used,
                    "embedding_dimension": embedding.embedding_dimension,
                    "created_at": embedding.created_at.isoformat(),
                    "storage_type": "embedding_only"
                }
                
                # Create point with appropriate vector format
                if use_named_vectors:
                    vector_data = {"embedding": embedding.embedding}
                else:
                    vector_data = embedding.embedding
                
                point = models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector_data,
                    payload=payload
                )
                points.append(point)
            
            # Batch upsert embeddings
            batch_size = settings.BATCH_SIZE
            total_stored = 0
            
            logger.info(f"Attempting to store {len(points)} embeddings in collection '{self.collection_name}'")
            logger.info(f"First point vector dimension: {len(points[0].vector) if points else 'No points'}")
            logger.info(f"First point vector type: {type(points[0].vector) if points else 'No points'}")
            
            for i in range(0, len(points), batch_size):
                batch_points = points[i:i + batch_size]
                
                try:
                    logger.info(f"Storing batch {i//batch_size + 1} with {len(batch_points)} points")
                    operation_info = self.client.upsert(
                        collection_name=self.collection_name,
                        points=batch_points,
                        wait=True
                    )
                    
                    total_stored += len(batch_points)
                    logger.info(f"Successfully stored batch {i//batch_size + 1}: {len(batch_points)} embeddings")
                    logger.info(f"Operation info: {operation_info}")
                    
                except Exception as batch_error:
                    logger.error(f"Failed to store batch {i//batch_size + 1}: {str(batch_error)}")
                    logger.error(f"Batch error type: {type(batch_error)}")
                    raise batch_error
            
            logger.info(f"Successfully stored {total_stored} embeddings in Qdrant")
            
            return StorageOperation(
                storage_type=StorageType.VECTOR_DB,
                operation="store_embeddings",
                success=True,
                records_processed=total_stored,
                storage_id=f"qdrant_{job_id}_embeddings"
            )
            
        except Exception as e:
            logger.error(f"Failed to store embeddings in Qdrant: {str(e)}")
            return StorageOperation(
                storage_type=StorageType.VECTOR_DB,
                operation="store_embeddings",
                success=False,
                records_processed=0,
                error_message=str(e)
            )
    
    async def store_chunks_with_vectors(
        self,
        job_id: str, 
        chunks: List[ProcessedChunk],
        embeddings: List[ChunkEmbedding]
    ) -> StorageOperation:
        """Store chunks with embeddings and rich metadata"""
        
        if not self.connected:
            await self.initialize()
        
        try:
            logger.info(f"Storing {len(chunks)} chunks with vectors in Qdrant for job {job_id}")
            
            # Check collection configuration to determine vector format
            collection_info = self.client.get_collection(self.collection_name)
            vectors_config = collection_info.config.params.vectors
            
            # Determine if collection uses named vectors
            use_named_vectors = isinstance(vectors_config, dict) and "embedding" in vectors_config
            
            # Create embedding lookup
            embedding_map = {emb.chunk_id: emb for emb in embeddings}
            
            # Prepare points for batch upsert
            points = []
            
            for chunk in chunks:
                embedding = embedding_map.get(chunk.chunk_id)
                if not embedding:
                    logger.warning(f"No embedding found for chunk {chunk.chunk_id}")
                    continue
                
                # Create comprehensive metadata payload
                payload = {
                    # Chunk metadata
                    "chunk_id": chunk.chunk_id,
                    "job_id": job_id,
                    "content": chunk.content,
                    "chunk_type": chunk.chunk_type,
                    "source_file": chunk.source_file,
                    "source_section": chunk.source_section,
                    "start_position": chunk.start_position,
                    "end_position": chunk.end_position,
                    
                    # Container and domain metadata
                    "container": self.container,
                    "collection": self.collection_name,
                    "semantic_type": chunk.semantic_type,
                    "domain": chunk.domain,
                    "confidence": chunk.confidence,
                    
                    # Relationship metadata
                    "related_chunks": chunk.related_chunks,
                    "parent_chunk": chunk.parent_chunk,
                    "child_chunks": chunk.child_chunks,
                    
                    # Embedding metadata
                    "model_used": embedding.model_used,
                    "embedding_dimension": embedding.embedding_dimension,
                    "created_at": embedding.created_at.isoformat(),
                    
                    # Additional searchable metadata
                    "storage_type": "chunk_with_vector",
                    "metadata": chunk.metadata
                }
                
                # Create point with appropriate vector format
                if use_named_vectors:
                    vector_data = {"embedding": embedding.embedding}
                else:
                    vector_data = embedding.embedding
                
                point = models.PointStruct(
                    id=str(uuid.uuid4()),  # Generate UUID for Qdrant
                    vector=vector_data,
                    payload=payload
                )
                points.append(point)
            
            # Batch upsert chunks with vectors
            batch_size = settings.BATCH_SIZE
            total_stored = 0
            
            logger.info(f"Attempting to store {len(points)} chunks with vectors in collection '{self.collection_name}'")
            logger.info(f"First point vector dimension: {len(points[0].vector) if points else 'No points'}")
            logger.info(f"First point vector type: {type(points[0].vector) if points else 'No points'}")
            
            for i in range(0, len(points), batch_size):
                batch_points = points[i:i + batch_size]
                
                try:
                    logger.info(f"Storing batch {i//batch_size + 1} with {len(batch_points)} chunks")
                    operation_info = self.client.upsert(
                        collection_name=self.collection_name,
                        points=batch_points,
                        wait=True
                    )
                    
                    total_stored += len(batch_points)
                    logger.info(f"Successfully stored batch {i//batch_size + 1}: {len(batch_points)} chunks with vectors")
                    logger.info(f"Operation info: {operation_info}")
                    
                except Exception as batch_error:
                    logger.error(f"Failed to store batch {i//batch_size + 1}: {str(batch_error)}")
                    logger.error(f"Batch error type: {type(batch_error)}")
                    raise batch_error
            
            logger.info(f"Successfully stored {total_stored} chunks with vectors in Qdrant")
            
            return StorageOperation(
                storage_type=StorageType.VECTOR_DB,
                operation="store_chunks_with_vectors",
                success=True,
                records_processed=total_stored,
                storage_id=f"qdrant_{job_id}_chunks"
            )
            
        except Exception as e:
            logger.error(f"Failed to store chunks with vectors in Qdrant: {str(e)}")
            return StorageOperation(
                storage_type=StorageType.VECTOR_DB,
                operation="store_chunks_with_vectors",
                success=False,
                records_processed=0,
                error_message=str(e)
            )
    
    async def create_collection(
        self,
        collection_name: str,
        dimension: int,
        metadata_schema: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Create a new collection with specified configuration"""
        
        if not self.connected:
            await self.initialize()
        
        try:
            # Create named vector configuration
            vector_config = {
                "embedding": models.VectorParams(
                    size=dimension,
                    distance=models.Distance.COSINE
                )
            }
            
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=vector_config
            )
            
            logger.info(f"Created Qdrant collection: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {str(e)}")
            return False
    
    async def search_similar_chunks(
        self,
        query_embedding: List[float],
        limit: int = 10,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar chunks using vector similarity"""
        
        if not self.connected:
            await self.initialize()
        
        try:
            # Build filter if provided
            query_filter = None
            if filter_conditions:
                query_filter = models.Filter(
                    must=[
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value)
                        ) for key, value in filter_conditions.items()
                    ]
                )
            
            # Search for similar vectors
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=query_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            
            # Format results
            results = []
            for scored_point in search_result:
                result = {
                    "chunk_id": scored_point.payload.get("chunk_id"),
                    "score": scored_point.score,
                    "content": scored_point.payload.get("content"),
                    "metadata": scored_point.payload
                }
                results.append(result)
            
            logger.info(f"Found {len(results)} similar chunks")
            return results
            
        except Exception as e:
            logger.error(f"Vector search failed: {str(e)}")
            return []
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """Get collection information for monitoring"""
        
        if not self.connected:
            await self.initialize()
        
        try:
            info = self.client.get_collection(self.collection_name)
            
            return {
                "collection_name": self.collection_name,
                "vectors_count": info.vectors_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "points_count": info.points_count,
                "segments_count": info.segments_count,
                "status": info.status.value,
                "optimizer_status": info.optimizer_status.ok,
                "disk_data_size": info.disk_data_size,
                "ram_data_size": info.ram_data_size,
                "config": {
                    "vector_size": info.config.params.vectors.size,
                    "distance": info.config.params.vectors.distance.value
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection info: {str(e)}")
            return {"error": str(e)}