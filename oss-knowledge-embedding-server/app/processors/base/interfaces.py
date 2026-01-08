"""
Storage Interfaces for External Database Integration
Abstract interfaces for vector DBs, graph DBs, and document stores
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.processors.base.base_models import (
    ProcessedChunk, ChunkEmbedding, ChunkRelationship, 
    FileRecord, StorageOperation, StorageResult
)


# ===== STORAGE INTERFACES =====

class StorageInterface(ABC):
    """Abstract base class for all storage operations"""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize storage connection"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if storage is accessible"""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close storage connection"""
        pass


class VectorStorageInterface(StorageInterface):
    """Interface for vector database operations"""
    
    @abstractmethod
    async def store_embeddings(
        self, 
        job_id: str,
        embeddings: List[ChunkEmbedding]
    ) -> StorageOperation:
        """Store chunk embeddings in vector database"""
        pass
    
    @abstractmethod
    async def store_chunks_with_vectors(
        self,
        job_id: str, 
        chunks: List[ProcessedChunk],
        embeddings: List[ChunkEmbedding]
    ) -> StorageOperation:
        """Store chunks along with their vector embeddings"""
        pass
    
    @abstractmethod
    async def create_collection(
        self,
        collection_name: str,
        dimension: int,
        metadata_schema: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Create a new collection for embeddings"""
        pass


class GraphStorageInterface(StorageInterface):
    """Interface for graph database operations"""
    
    @abstractmethod
    async def store_relationships(
        self,
        job_id: str,
        relationships: List[ChunkRelationship]
    ) -> StorageOperation:
        """Store chunk relationships in graph database"""
        pass
    
    @abstractmethod
    async def store_chunks_as_nodes(
        self,
        job_id: str,
        chunks: List[ProcessedChunk]
    ) -> StorageOperation:
        """Store chunks as nodes in graph database"""
        pass
    
    @abstractmethod
    async def create_relationship_graph(
        self,
        job_id: str,
        chunks: List[ProcessedChunk],
        relationships: List[ChunkRelationship]
    ) -> StorageOperation:
        """Create complete relationship graph"""
        pass

    @abstractmethod
    async def create_simple_document_graph(
        self,
        job_id: str,
        file_record: FileRecord,
        container: str
    ) -> StorageOperation:
        """Create simple document node connected to department/container"""
        pass


class DocumentStorageInterface(StorageInterface):
    """Interface for document store operations"""
    
    @abstractmethod
    async def store_file_metadata(
        self,
        job_id: str,
        file_record: FileRecord
    ) -> StorageOperation:
        """Store file metadata in document store"""
        pass
    
    @abstractmethod
    async def store_processing_results(
        self,
        job_id: str,
        chunks: List[ProcessedChunk],
        analysis_results: Dict[str, Any]
    ) -> StorageOperation:
        """Store complete processing results"""
        pass
    
    @abstractmethod
    async def update_job_status(
        self,
        job_id: str,
        status_data: Dict[str, Any]
    ) -> bool:
        """Update job processing status"""
        pass


# ===== PROCESSOR INTERFACE =====

class FileProcessorInterface(ABC):
    """Abstract interface for format-specific processors"""
    
    @abstractmethod
    async def process_file(
        self,
        file_path: str,
        options: Any,  # Format-specific options
        job_id: str
    ) -> Dict[str, Any]:
        """
        Process file and return structured results
        
        Returns:
            Dictionary containing:
            - chunks: List[ProcessedChunk]
            - embeddings: List[ChunkEmbedding] (if enabled)
            - relationships: List[ChunkRelationship] (if enabled)
            - semantic_analysis: Dict[str, Any] (if enabled)
            - quality_metrics: Dict[str, Any] (if enabled)
        """
        pass
    
    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions"""
        pass
    
    @abstractmethod
    def validate_options(self, options: Any) -> bool:
        """Validate format-specific processing options"""
        pass


# ===== CHUNKING INTERFACE =====

class ChunkingInterface(ABC):
    """Abstract interface for chunking strategies"""
    
    @abstractmethod
    async def create_chunks(
        self,
        content: Any,  # Format-specific content structure
        options: Dict[str, Any]
    ) -> List[ProcessedChunk]:
        """Create chunks from content using specific strategy"""
        pass
    
    @abstractmethod
    def estimate_chunk_count(
        self,
        content_size: int,
        options: Dict[str, Any]
    ) -> int:
        """Estimate number of chunks that will be created"""
        pass


# ===== EMBEDDING INTERFACE =====

class EmbeddingInterface(ABC):
    """Abstract interface for embedding generation"""
    
    @abstractmethod
    async def generate_embeddings(
        self,
        chunks: List[ProcessedChunk],
        model_name: str
    ) -> List[ChunkEmbedding]:
        """Generate embeddings for chunks"""
        pass
    
    @abstractmethod
    def get_embedding_dimension(self, model_name: str) -> int:
        """Get embedding dimension for model"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available embedding models"""
        pass


# ===== RELATIONSHIP DETECTOR INTERFACE =====

class RelationshipDetectorInterface(ABC):
    """Abstract interface for relationship detection"""
    
    @abstractmethod
    async def detect_relationships(
        self,
        chunks: List[ProcessedChunk],
        semantic_analysis: Optional[Dict[str, Any]] = None
    ) -> List[ChunkRelationship]:
        """Detect relationships between chunks"""
        pass
    
    @abstractmethod
    def get_supported_relationship_types(self) -> List[str]:
        """Get list of supported relationship types"""
        pass