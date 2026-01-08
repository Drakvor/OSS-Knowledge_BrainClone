"""
Storage Service
Manages external storage operations for vector DBs, graph DBs, and document stores
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.config import settings
from app.processors.base.interfaces import (
    VectorStorageInterface, GraphStorageInterface, DocumentStorageInterface
)
from app.processors.base.base_models import (
    ProcessedChunk, ChunkEmbedding, ChunkRelationship, 
    FileRecord, StorageOperation, StorageResult, StorageType
)
from app.core.exceptions import ProcessingException
from app.core.qdrant_storage import QdrantVectorStorage
from app.core.neo4j_storage import Neo4jGraphStorage

logger = logging.getLogger(__name__)


# ===== CONCRETE STORAGE IMPLEMENTATIONS =====

class MockVectorStorage(VectorStorageInterface):
    """Mock vector storage for development/testing"""
    
    def __init__(self, connection_url: str):
        self.connection_url = connection_url
        self.connected = False
    
    async def initialize(self) -> bool:
        """Initialize mock vector storage"""
        logger.info(f"Initializing mock vector storage: {self.connection_url}")
        self.connected = True
        return True
    
    async def health_check(self) -> bool:
        """Check vector storage health"""
        return self.connected
    
    async def close(self) -> None:
        """Close vector storage connection"""
        self.connected = False
    
    async def store_embeddings(
        self, 
        job_id: str,
        embeddings: List[ChunkEmbedding]
    ) -> StorageOperation:
        """Store embeddings in mock vector database"""
        
        logger.info(f"Storing {len(embeddings)} embeddings for job {job_id}")
        
        # Simulate storage operation
        return StorageOperation(
            storage_type=StorageType.VECTOR_DB,
            operation="store_embeddings",
            success=True,
            records_processed=len(embeddings),
            storage_id=f"vector_{job_id}"
        )
    
    async def store_chunks_with_vectors(
        self,
        job_id: str, 
        chunks: List[ProcessedChunk],
        embeddings: List[ChunkEmbedding]
    ) -> StorageOperation:
        """Store chunks with vectors in mock database"""
        
        logger.info(f"Storing {len(chunks)} chunks with vectors for job {job_id}")
        
        return StorageOperation(
            storage_type=StorageType.VECTOR_DB,
            operation="store_chunks_with_vectors",
            success=True,
            records_processed=len(chunks),
            storage_id=f"chunks_vector_{job_id}"
        )
    
    async def create_collection(
        self,
        collection_name: str,
        dimension: int,
        metadata_schema: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Create collection in mock vector database"""
        
        logger.info(f"Creating collection: {collection_name} (dim: {dimension})")
        return True


class MockGraphStorage(GraphStorageInterface):
    """Mock graph storage for development/testing"""
    
    def __init__(self, connection_url: str):
        self.connection_url = connection_url
        self.connected = False
    
    async def initialize(self) -> bool:
        """Initialize mock graph storage"""
        logger.info(f"Initializing mock graph storage: {self.connection_url}")
        self.connected = True
        return True
    
    async def health_check(self) -> bool:
        """Check graph storage health"""
        return self.connected
    
    async def close(self) -> None:
        """Close graph storage connection"""
        self.connected = False
    
    async def store_relationships(
        self,
        job_id: str,
        relationships: List[ChunkRelationship]
    ) -> StorageOperation:
        """Store relationships in mock graph database"""
        
        logger.info(f"Storing {len(relationships)} relationships for job {job_id}")
        
        return StorageOperation(
            storage_type=StorageType.GRAPH_DB,
            operation="store_relationships",
            success=True,
            records_processed=len(relationships),
            storage_id=f"graph_{job_id}"
        )
    
    async def store_chunks_as_nodes(
        self,
        job_id: str,
        chunks: List[ProcessedChunk]
    ) -> StorageOperation:
        """Store chunks as nodes in mock graph database"""
        
        logger.info(f"Storing {len(chunks)} chunks as nodes for job {job_id}")
        
        return StorageOperation(
            storage_type=StorageType.GRAPH_DB,
            operation="store_chunks_as_nodes",
            success=True,
            records_processed=len(chunks),
            storage_id=f"nodes_{job_id}"
        )
    
    async def create_relationship_graph(
        self,
        job_id: str,
        chunks: List[ProcessedChunk],
        relationships: List[ChunkRelationship]
    ) -> StorageOperation:
        """Create complete relationship graph"""

        logger.info(f"Creating relationship graph for job {job_id}")

        return StorageOperation(
            storage_type=StorageType.GRAPH_DB,
            operation="create_relationship_graph",
            success=True,
            records_processed=len(chunks) + len(relationships),
            storage_id=f"graph_complete_{job_id}"
        )

    async def create_simple_document_graph(
        self,
        job_id: str,
        file_record: FileRecord,
        container: str
    ) -> StorageOperation:
        """Create simple document node connected to department/container"""

        logger.info(f"Creating simple document graph for {file_record.original_filename} in container {container}")

        return StorageOperation(
            storage_type=StorageType.GRAPH_DB,
            operation="create_simple_document_graph",
            success=True,
            records_processed=2,  # Document node + relationship to department
            storage_id=f"simple_graph_{job_id}"
        )


class MockDocumentStorage(DocumentStorageInterface):
    """Mock document storage for development/testing"""
    
    def __init__(self, connection_url: str):
        self.connection_url = connection_url
        self.connected = False
        self.job_statuses = {}  # In-memory job status tracking
    
    async def initialize(self) -> bool:
        """Initialize mock document storage"""
        logger.info(f"Initializing mock document storage: {self.connection_url}")
        self.connected = True
        return True
    
    async def health_check(self) -> bool:
        """Check document storage health"""
        return self.connected
    
    async def close(self) -> None:
        """Close document storage connection"""
        self.connected = False
    
    async def store_file_metadata(
        self,
        job_id: str,
        file_record: FileRecord
    ) -> StorageOperation:
        """Store file metadata in mock document store"""
        
        logger.info(f"Storing file metadata for job {job_id}: {file_record.original_filename}")
        
        return StorageOperation(
            storage_type=StorageType.DOCUMENT_STORE,
            operation="store_file_metadata",
            success=True,
            records_processed=1,
            storage_id=f"doc_{job_id}"
        )
    
    async def store_processing_results(
        self,
        job_id: str,
        chunks: List[ProcessedChunk],
        analysis_results: Dict[str, Any]
    ) -> StorageOperation:
        """Store complete processing results"""
        
        logger.info(f"Storing processing results for job {job_id}")
        
        return StorageOperation(
            storage_type=StorageType.DOCUMENT_STORE,
            operation="store_processing_results",
            success=True,
            records_processed=len(chunks),
            storage_id=f"results_{job_id}"
        )
    
    async def update_job_status(
        self,
        job_id: str,
        status_data: Dict[str, Any]
    ) -> bool:
        """Update job processing status"""
        
        self.job_statuses[job_id] = status_data
        logger.info(f"Updated job status for {job_id}: {status_data.get('status')}")
        return True
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status (helper method for testing)"""
        return self.job_statuses.get(job_id)


# ===== MAIN STORAGE SERVICE =====

class StorageService:
    """Main storage service coordinating all storage operations with container isolation"""
    
    def __init__(self, container: str = "general"):
        self.container = container
        self.vector_storage: Optional[VectorStorageInterface] = None
        self.graph_storage: Optional[GraphStorageInterface] = None
        self.document_storage: Optional[DocumentStorageInterface] = None
        self.initialized = False
        
        logger.info(f"Storage service initialized for container: {container}")
    
    async def initialize(self):
        """Initialize all configured storage interfaces with container isolation"""
        
        if self.initialized:
            return
        
        try:
            # Initialize Qdrant Vector Storage with container-specific collection
            if settings.ENABLE_QDRANT:
                self.vector_storage = QdrantVectorStorage(container=self.container)
                await self.vector_storage.initialize()
                logger.info(f"Qdrant vector storage initialized for container: {self.container}")
            
            # Initialize Neo4j Graph Storage with container-specific database
            if settings.ENABLE_NEO4J:
                self.graph_storage = Neo4jGraphStorage(container=self.container)
                await self.graph_storage.initialize()
                logger.info(f"Neo4j graph storage initialized for container: {self.container}")
            
            # Initialize Document Storage (keep mock for now - can be replaced with MongoDB/PostgreSQL later)
            if not self.document_storage:
                self.document_storage = MockDocumentStorage("mock://localhost")
                await self.document_storage.initialize()
                logger.info("Mock document storage initialized for job tracking")
            
            self.initialized = True
            logger.info("Storage service initialization complete")
            
        except Exception as e:
            logger.error(f"Storage service initialization failed: {str(e)}")
            raise ProcessingException(f"Storage initialization failed: {str(e)}")
    
    async def store_processing_results(
        self,
        job_id: str,
        chunks: List[ProcessedChunk],
        embeddings: List[ChunkEmbedding],
        relationships: List[ChunkRelationship],
        file_record: FileRecord,
        create_graph: bool = False
    ) -> StorageResult:
        """Store complete processing results across all configured storage systems"""
        
        operations = []
        
        try:
            # Store in Vector Database
            if self.vector_storage and embeddings:
                logger.info(f"Storing {len(embeddings)} embeddings and {len(chunks)} chunks in vector database")
                logger.info(f"Vector storage type: {type(self.vector_storage)}")
                logger.info(f"Collection name: {getattr(self.vector_storage, 'collection_name', 'Unknown')}")
                
                # Store embeddings
                logger.info("Calling store_embeddings...")
                embedding_op = await self.vector_storage.store_embeddings(job_id, embeddings)
                logger.info(f"Embedding operation result: success={embedding_op.success}, records={embedding_op.records_processed}")
                operations.append(embedding_op)
                
                # Store chunks with vectors
                logger.info("Calling store_chunks_with_vectors...")
                chunks_op = await self.vector_storage.store_chunks_with_vectors(
                    job_id, chunks, embeddings
                )
                logger.info(f"Chunks operation result: success={chunks_op.success}, records={chunks_op.records_processed}")
                operations.append(chunks_op)
            else:
                logger.warning(f"Vector storage not available: vector_storage={self.vector_storage}, embeddings={len(embeddings) if embeddings else 0}")
            
            # Store in Graph Database (simplified or full based on create_graph flag)
            if self.graph_storage and create_graph:
                if relationships:
                    # Full graph mode: store chunks as nodes and all relationships
                    nodes_op = await self.graph_storage.store_chunks_as_nodes(job_id, chunks)
                    operations.append(nodes_op)

                    # Store relationships
                    rels_op = await self.graph_storage.store_relationships(job_id, relationships)
                    operations.append(rels_op)

                    # Create complete graph
                    graph_op = await self.graph_storage.create_relationship_graph(
                        job_id, chunks, relationships
                    )
                    operations.append(graph_op)
                else:
                    # Simple mode: just create document node and connect to department
                    simple_graph_op = await self.graph_storage.create_simple_document_graph(
                        job_id, file_record, self.container
                    )
                    operations.append(simple_graph_op)
            elif self.graph_storage:
                # Default: simple document->department relationship only
                simple_graph_op = await self.graph_storage.create_simple_document_graph(
                    job_id, file_record, self.container
                )
                operations.append(simple_graph_op)
            
            # Store in Document Store
            if self.document_storage:
                # Store file metadata
                file_op = await self.document_storage.store_file_metadata(job_id, file_record)
                operations.append(file_op)
                
                # Store processing results
                results_op = await self.document_storage.store_processing_results(
                    job_id, chunks, {"embeddings": len(embeddings), "relationships": len(relationships)}
                )
                operations.append(results_op)
            
            # Calculate results
            successful_ops = [op for op in operations if op.success]
            failed_ops = [op for op in operations if not op.success]
            
            result = StorageResult(
                job_id=job_id,
                operations=operations,
                total_success=len(successful_ops),
                total_failed=len(failed_ops)
            )
            
            logger.info(f"Storage complete for job {job_id}: {len(successful_ops)} success, {len(failed_ops)} failed")
            return result
            
        except Exception as e:
            logger.error(f"Storage operation failed for job {job_id}: {str(e)}")
            
            # Create error result
            error_op = StorageOperation(
                storage_type=StorageType.DOCUMENT_STORE,
                operation="store_all",
                success=False,
                records_processed=0,
                error_message=str(e)
            )
            
            return StorageResult(
                job_id=job_id,
                operations=[error_op],
                total_success=0,
                total_failed=1
            )
    
    async def update_job_status(self, job_id: str, status_data: Dict[str, Any]) -> bool:
        """Update job processing status"""
        
        if self.document_storage:
            return await self.document_storage.update_job_status(job_id, status_data)
        return False
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job processing status"""
        
        if isinstance(self.document_storage, MockDocumentStorage):
            return self.document_storage.get_job_status(job_id)
        return None
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all storage systems"""
        
        health_status = {}
        
        if self.vector_storage:
            try:
                health_status["vector_storage"] = await self.vector_storage.health_check()
            except Exception:
                health_status["vector_storage"] = False
        
        if self.graph_storage:
            try:
                health_status["graph_storage"] = await self.graph_storage.health_check()
            except Exception:
                health_status["graph_storage"] = False
        
        if self.document_storage:
            try:
                health_status["document_storage"] = await self.document_storage.health_check()
            except Exception:
                health_status["document_storage"] = False
        
        return health_status
    
    async def close(self):
        """Close all storage connections"""
        
        if self.vector_storage:
            await self.vector_storage.close()
        
        if self.graph_storage:
            await self.graph_storage.close()
        
        if self.document_storage:
            await self.document_storage.close()
        
        self.initialized = False
        logger.info("Storage service closed")