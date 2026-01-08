"""
Base Models for File Processing
Common models shared across all processor types
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod
from enum import Enum


# ===== ENUMS =====

class ChunkingStrategy(str, Enum):
    """Available chunking strategies"""
    SEMANTIC = "semantic"
    FIXED = "fixed"
    ADAPTIVE = "adaptive"


class ProcessingStatusEnum(str, Enum):
    """Processing job status"""
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class StorageType(str, Enum):
    """Storage destination types"""
    VECTOR_DB = "vector_db"
    GRAPH_DB = "graph_db"
    DOCUMENT_STORE = "document_store"


# ===== CORE PROCESSING MODELS =====

class ProcessedChunk(BaseModel):
    """A single processed chunk of content"""
    chunk_id: str
    content: str
    chunk_type: str  # "schema", "data", "metadata", "relationship"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Position information
    source_file: str
    source_section: Optional[str] = None
    start_position: Optional[int] = None
    end_position: Optional[int] = None
    
    # Semantic information
    semantic_type: Optional[str] = None
    domain: Optional[str] = None
    confidence: Optional[float] = None
    
    # Container/Domain specification
    container: str = Field(default="general", description="Container or domain this chunk belongs to")
    
    # Relationships
    related_chunks: List[str] = Field(default_factory=list)
    parent_chunk: Optional[str] = None
    child_chunks: List[str] = Field(default_factory=list)


class ChunkEmbedding(BaseModel):
    """Embedding information for a chunk"""
    model_config = {"protected_namespaces": ()}

    chunk_id: str
    embedding: List[float]
    model_used: str
    embedding_dimension: int
    created_at: datetime = Field(default_factory=datetime.now)


class ChunkRelationship(BaseModel):
    """Relationship between chunks"""
    relationship_id: str
    from_chunk_id: str
    to_chunk_id: str
    relationship_type: str  # "references", "contains", "similar_to", "follows"
    confidence: float
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FileRecord(BaseModel):
    """Metadata record for processed file"""
    file_id: str
    original_filename: str
    file_type: str
    file_size: int
    processed_at: datetime
    processing_options: Dict[str, Any]
    
    # Processing results
    total_chunks: int
    total_embeddings: int
    total_relationships: int
    domains_detected: List[str] = Field(default_factory=list)
    
    # Storage information
    stored_in: List[StorageType] = Field(default_factory=list)
    storage_metadata: Dict[str, Any] = Field(default_factory=dict)


class ProcessingStatus(BaseModel):
    """Status of a processing job"""
    job_id: str
    status: ProcessingStatusEnum
    progress: int = Field(ge=0, le=100)  # 0-100
    current_step: str
    message: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    
    # Results (populated when completed)
    chunks_created: Optional[int] = None
    embeddings_generated: Optional[int] = None
    relationships_detected: Optional[int] = None
    storage_operations: Optional[Dict[str, Any]] = None


class ProcessingResult(BaseModel):
    """Complete processing result"""
    job_id: str
    file_record: FileRecord
    chunks: List[ProcessedChunk]
    embeddings: List[ChunkEmbedding]
    relationships: List[ChunkRelationship]
    processing_status: ProcessingStatus
    
    # Analysis results
    semantic_analysis: Optional[Dict[str, Any]] = None
    quality_metrics: Optional[Dict[str, Any]] = None
    domain_analysis: Optional[Dict[str, Any]] = None


# ===== BASE PROCESSING OPTIONS =====

class BaseProcessingOptions(BaseModel):
    """Base class for format-specific processing options"""
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.SEMANTIC
    chunk_size: int = Field(default=2000, ge=100, le=10000)
    chunk_overlap: int = Field(default=200, ge=0, le=1000)
    generate_embeddings: bool = True
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    # Graph processing options (now optional and default off)
    create_graph: bool = Field(default=False, description="Create Neo4j graph relationships (default: False)")
    detect_relationships: bool = Field(default=False, description="Detect complex relationships between chunks (default: False)")
    store_to: List[StorageType] = Field(default_factory=lambda: [StorageType.VECTOR_DB])
    # Container/Domain specification
    container: str = Field(default="general", description="Container or domain to store the document (e.g., 'general', 'pcp', 'hr', 'finance')")
    domain: Optional[str] = Field(default=None, description="Alias for container field for backward compatibility")


# ===== STORAGE INTERFACE MODELS =====

class StorageOperation(BaseModel):
    """Result of a storage operation"""
    storage_type: StorageType
    operation: str  # "store_chunks", "store_embeddings", "store_relationships"
    success: bool
    records_processed: int
    error_message: Optional[str] = None
    storage_id: Optional[str] = None  # ID assigned by storage system


class StorageResult(BaseModel):
    """Complete storage operation result"""
    job_id: str
    operations: List[StorageOperation]
    total_success: int
    total_failed: int
    completed_at: datetime = Field(default_factory=datetime.now)


# ===== ANALYSIS MODELS =====

class SemanticAnalysis(BaseModel):
    """Results of semantic analysis"""
    domain: str
    confidence: float
    semantic_types: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    business_rules: List[str] = Field(default_factory=list)
    analysis_method: str = "langchain"


class QualityMetrics(BaseModel):
    """Data quality assessment results"""
    completeness: float = Field(ge=0.0, le=1.0)
    consistency: float = Field(ge=0.0, le=1.0)
    validity: float = Field(ge=0.0, le=1.0)
    accuracy: float = Field(ge=0.0, le=1.0)
    overall_score: float = Field(ge=0.0, le=1.0)
    issues_found: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class DomainAnalysis(BaseModel):
    """Domain classification results"""
    primary_domain: str
    confidence: float
    alternative_domains: List[Dict[str, float]] = Field(default_factory=list)
    domain_patterns: List[str] = Field(default_factory=list)
    business_context: Optional[str] = None