"""
Search request and response models
"""

from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum


class SearchType(str, Enum):
    """Available search types"""
    VECTOR = "vector"
    GRAPH = "graph"
    HYBRID = "hybrid"
    COMPREHENSIVE = "comprehensive"


class SortOrder(str, Enum):
    """Sort order options"""
    RELEVANCE = "relevance"
    DATE = "date"
    SCORE = "score"


class SearchQuery(BaseModel):
    """Base search query model"""
    query: str = Field(..., description="Search query text")
    collection: str = Field(..., description="Collection/container to search within")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of results")
    offset: int = Field(default=0, ge=0, description="Number of results to skip")
    threshold: float = Field(default=0.55, ge=0.0, le=1.0, description="Similarity threshold")


class VectorSearchQuery(SearchQuery):
    """Vector similarity search query"""
    search_type: SearchType = Field(default=SearchType.VECTOR)
    include_metadata: bool = Field(default=True, description="Include chunk metadata")
    include_content: bool = Field(default=True, description="Include chunk content")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Additional filters")


class GraphSearchQuery(SearchQuery):
    """Graph traversal search query"""
    search_type: SearchType = Field(default=SearchType.GRAPH)
    max_depth: int = Field(default=3, ge=1, le=10, description="Maximum traversal depth")
    relationship_types: Optional[List[str]] = Field(default=None, description="Filter by relationship types")
    node_types: Optional[List[str]] = Field(default=None, description="Filter by node types")


class HybridSearchQuery(SearchQuery):
    """Hybrid vector + graph search query"""
    search_type: SearchType = Field(default=SearchType.HYBRID)
    vector_weight: float = Field(default=0.7, ge=0.0, le=1.0, description="Weight for vector search")
    graph_weight: float = Field(default=0.3, ge=0.0, le=1.0, description="Weight for graph search")
    max_depth: int = Field(default=2, ge=1, le=5, description="Graph traversal depth")
    include_metadata: bool = Field(default=True)
    include_content: bool = Field(default=True)


class ComprehensiveSearchQuery(SearchQuery):
    """Advanced comprehensive search query"""
    search_type: SearchType = Field(default=SearchType.COMPREHENSIVE)
    search_modes: List[SearchType] = Field(default=[SearchType.VECTOR, SearchType.GRAPH])
    vector_weight: float = Field(default=0.6, ge=0.0, le=1.0)
    graph_weight: float = Field(default=0.4, ge=0.0, le=1.0)
    max_depth: int = Field(default=3, ge=1, le=10)
    sort_by: SortOrder = Field(default=SortOrder.RELEVANCE)
    include_analytics: bool = Field(default=False, description="Include search analytics")
    filters: Optional[Dict[str, Any]] = Field(default=None)


class SearchResult(BaseModel):
    """Individual search result"""
    id: str = Field(..., description="Unique result identifier")
    content: str = Field(..., description="Result content")
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    source_file: str = Field(..., description="Source file name")
    chunk_type: str = Field(..., description="Type of content chunk")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class GraphResult(BaseModel):
    """Graph search result with relationship info"""
    id: str = Field(..., description="Node identifier")
    content: str = Field(..., description="Node content")
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    node_type: str = Field(..., description="Type of graph node")
    relationships: List[Dict[str, Any]] = Field(default_factory=list, description="Connected relationships")
    depth: int = Field(..., ge=0, description="Depth from search origin")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    """Search response model"""
    query: str = Field(..., description="Original search query")
    search_type: SearchType = Field(..., description="Type of search performed")
    results: List[Union[SearchResult, GraphResult]] = Field(default_factory=list)
    total_results: int = Field(..., ge=0, description="Total number of results found")
    processing_time_ms: float = Field(..., ge=0, description="Search processing time")
    threshold_used: float = Field(..., ge=0.0, le=1.0, description="Similarity threshold applied")
    
    # Optional analytics
    analytics: Optional[Dict[str, Any]] = Field(default=None, description="Search analytics data")
    suggestions: Optional[List[str]] = Field(default=None, description="Search suggestions")


class BatchSearchQuery(BaseModel):
    """Batch search request"""
    queries: List[Union[VectorSearchQuery, GraphSearchQuery, HybridSearchQuery]] = Field(
        ..., min_items=1, max_items=10, description="List of search queries"
    )
    parallel: bool = Field(default=True, description="Execute searches in parallel")


class BatchSearchResponse(BaseModel):
    """Batch search response"""
    results: List[SearchResponse] = Field(..., description="Results for each query")
    total_processing_time_ms: float = Field(..., ge=0, description="Total processing time")
    successful_queries: int = Field(..., ge=0, description="Number of successful queries")
    failed_queries: int = Field(default=0, ge=0, description="Number of failed queries")


class SearchAnalytics(BaseModel):
    """Search analytics and metrics"""
    total_searches: int = Field(..., ge=0)
    avg_response_time_ms: float = Field(..., ge=0)
    popular_queries: List[str] = Field(default_factory=list)
    search_type_distribution: Dict[SearchType, int] = Field(default_factory=dict)
    success_rate: float = Field(..., ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.now)


class SearchSuggestion(BaseModel):
    """Search suggestion model"""
    suggestion: str = Field(..., description="Suggested search query")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    category: Optional[str] = Field(default=None, description="Suggestion category")


class SearchSuggestionsResponse(BaseModel):
    """Search suggestions response"""
    query: str = Field(..., description="Original partial query")
    suggestions: List[SearchSuggestion] = Field(default_factory=list)
    processing_time_ms: float = Field(..., ge=0)


class SearchResponseQuery(BaseModel):
    """Request model for search + response generation (combines search and LLM)"""
    query: str = Field(..., description="Search query text")
    collection: str = Field(default="general", description="Collection/container to search within")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of search results")
    threshold: float = Field(default=0.55, ge=0.0, le=1.0, description="Similarity threshold")
    include_metadata: bool = Field(default=True, description="Include chunk metadata")
    include_content: bool = Field(default=True, description="Include chunk content")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Additional filters")
    max_tokens: int = Field(default=1000, ge=100, le=4000, description="Maximum tokens for response")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperature for response generation")
    session_id: Optional[str] = Field(default=None, description="Chat session ID for conversation context")
    user_id: Optional[int] = Field(default=None, description="User ID for memory management")
    chat_context: Optional[Dict[str, Any]] = Field(default=None, description="Chat context including history and summary")


class SourceInfo(BaseModel):
    """Source file information with download link"""
    filename: str = Field(..., description="Source file name")
    download_url: Optional[str] = Field(default=None, description="Download URL if available")
    upload_status: str = Field(default="unknown", description="Upload status: completed, failed, unknown")


class SearchResponseResponse(BaseModel):
    """Response model for LLM-generated search response"""
    model_config = {"protected_namespaces": ()}
    
    query: str = Field(..., description="Original search query")
    response: str = Field(..., description="LLM-generated response")
    search_results: List[Union[SearchResult, GraphResult]] = Field(default_factory=list, description="Search results used")
    search_results_count: int = Field(..., ge=0, description="Number of search results found")
    search_processing_time_ms: float = Field(..., ge=0, description="Search processing time")
    response_processing_time_ms: float = Field(..., ge=0, description="Response generation time")
    total_processing_time_ms: float = Field(..., ge=0, description="Total processing time")
    threshold_used: float = Field(..., ge=0.0, le=1.0, description="Similarity threshold applied")
    model_info: Dict[str, Any] = Field(..., description="Information about the LLM model used")
    sources: List[SourceInfo] = Field(default_factory=list, description="Source files with download links")