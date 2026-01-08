"""
Markdown Processing Models
Pydantic models for markdown processing configuration and results
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class MarkdownProcessingOptions(BaseModel):
    """Configuration options for markdown processing"""
    
    # Container/Domain specification
    container: str = Field(default="general", description="Target container for storage")
    domain: Optional[str] = Field(default=None, description="Alias for container (backward compatibility)")
    
    # Markdown-specific processing options
    chunking_strategy: str = Field(default="structure_aware_hierarchical", description="Chunking strategy to use")
    create_graph: bool = Field(default=False, description="Create Neo4j graph relationships (default: False)")
    detect_relationships: bool = Field(default=False, description="Enable complex relationship detection (default: False)")
    detect_domains: bool = Field(default=False, description="Enable domain classification (default: False)")
    generate_embeddings: bool = Field(default=True, description="Generate vector embeddings")
    embedding_model: str = Field(description="Embedding model to use")
    
    # Additional metadata
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional processing metadata")
    
    class Config:
        """Pydantic config"""
        extra = "allow"
        json_schema_extra = {
            "example": {
                "container": "general",
                "chunking_strategy": "structure_aware_hierarchical",
                "detect_relationships": True,
                "detect_domains": True,
                "generate_embeddings": True,
                "embedding_model": "text-embedding-3-large"
            }
        }


class MarkdownProcessingResult(BaseModel):
    """Result of markdown processing operation"""

    job_id: str
    filename: str
    processing_options: MarkdownProcessingOptions

    # Processing results
    chunks_created: int = Field(default=0, description="Number of chunks created")
    embeddings_generated: int = Field(default=0, description="Number of embeddings generated")
    relationships_detected: int = Field(default=0, description="Number of relationships detected")

    # Processing metadata
    content_length: int = Field(default=0, description="Original content length in characters")
    processing_time_seconds: float = Field(default=0.0, description="Total processing time")

    # Storage information
    storage_operations: Optional[Dict[str, Any]] = Field(default=None, description="Storage operation results")

    class Config:
        """Pydantic config"""
        extra = "allow"


# ===== INTERACTIVE CHUNKING MODELS =====

class ChunkPreview(BaseModel):
    """Preview of a chunk for user review"""

    chunk_id: str = Field(description="Unique identifier for this chunk")
    content: str = Field(description="The chunk content")
    chunk_type: str = Field(description="Type of chunk (header, paragraph, code, etc.)")
    start_position: int = Field(description="Start position in original document")
    end_position: int = Field(description="End position in original document")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional chunk metadata")

    class Config:
        """Pydantic config"""
        extra = "allow"


class ChunkingStrategy(BaseModel):
    """Information about the recommended chunking strategy"""

    strategy_name: str = Field(description="Name of the chunking strategy")
    reason: str = Field(description="Explanation of why this strategy was chosen")
    parameters: Dict[str, Any] = Field(description="Strategy parameters used")

    class Config:
        """Pydantic config"""
        extra = "allow"


class MarkdownChunkingPreview(BaseModel):
    """Preview of markdown chunking for user review"""

    filename: str = Field(description="Original filename")
    content_length: int = Field(description="Original content length in characters")

    # Strategy information
    recommended_strategy: ChunkingStrategy = Field(description="Recommended chunking strategy")

    # Chunk previews
    chunks: List[ChunkPreview] = Field(description="Preview of all chunks")
    total_chunks: int = Field(description="Total number of chunks")

    # Metadata
    processing_time_seconds: float = Field(default=0.0, description="Time to generate preview")

    class Config:
        """Pydantic config"""
        extra = "allow"


class UserEditedChunk(BaseModel):
    """User-edited chunk for final processing"""

    chunk_id: str = Field(description="Unique identifier for this chunk")
    content: str = Field(description="User-edited chunk content")
    chunk_type: str = Field(default="text", description="Type of chunk")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional chunk metadata")

    class Config:
        """Pydantic config"""
        extra = "allow"


class MarkdownInteractiveProcessing(BaseModel):
    """Request for processing user-edited markdown chunks"""

    filename: str = Field(description="Original filename")
    container: str = Field(default="general", description="Target container for storage")

    # User-edited chunks
    chunks: List[UserEditedChunk] = Field(description="User-edited chunks to process")

    # Processing options (same as MarkdownProcessingOptions but simplified)
    create_graph: bool = Field(default=False, description="Create Neo4j graph relationships")
    detect_relationships: bool = Field(default=False, description="Enable relationship detection")
    detect_domains: bool = Field(default=False, description="Enable domain classification")
    generate_embeddings: bool = Field(default=True, description="Generate vector embeddings")
    embedding_model: str = Field(description="Embedding model to use")

    # Additional metadata
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional processing metadata")

    class Config:
        """Pydantic config"""
        extra = "allow"


class LLMChunkSuggestion(BaseModel):
    """Individual chunk suggestion from LLM"""
    start_position: int = Field(description="Start character position in document")
    end_position: int = Field(description="End character position in document")
    content: str = Field(description="Chunk content text")
    reasoning: str = Field(description="Reasoning for this chunk boundary")
    semantic_score: float = Field(default=0.9, description="Semantic coherence score")


class LLMChunkingResponse(BaseModel):
    """Response from LLM chunking suggestion endpoint"""
    filename: str = Field(description="Original filename")
    content_length: int = Field(description="Total document length in characters")
    file_size_mb: float = Field(description="File size in MB")
    llm_model_used: str = Field(description="LLM model used for analysis")
    suggested_chunks: List[LLMChunkSuggestion] = Field(description="List of suggested chunks")
    total_chunks: int = Field(description="Total number of suggested chunks")
    processing_time_seconds: float = Field(description="Processing time in seconds")
    token_usage: Dict[str, int] = Field(description="Token usage statistics")