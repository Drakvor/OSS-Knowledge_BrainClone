"""
Simple, robust search endpoint implementation
"""
import time
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.core.qdrant_client import QdrantService
from app.core.azure_embedding import AzureEmbeddingService

logger = logging.getLogger(__name__)

router = APIRouter()

class SimpleSearchQuery(BaseModel):
    query: str
    collection: str = "general"
    limit: int = 10
    threshold: float = 0.7

class SimpleSearchResult(BaseModel):
    id: str
    content: str
    score: float
    source_file: str = "unknown"
    chunk_type: str = "text"
    metadata: Dict[str, Any] = {}

class SimpleSearchResponse(BaseModel):
    query: str
    results: List[SimpleSearchResult]
    total_results: int
    processing_time_ms: float
    collection: str

def get_simple_services(request: Request) -> tuple[QdrantService, AzureEmbeddingService]:
    """Get services directly from app state"""
    qdrant_service = request.app.state.qdrant_service
    embedding_service = request.app.state.embedding_service
    
    if not qdrant_service:
        raise HTTPException(status_code=503, detail="Qdrant service not available")
    if not embedding_service:
        raise HTTPException(status_code=503, detail="Embedding service not available")
    
    return qdrant_service, embedding_service

@router.post("/search/vector", response_model=SimpleSearchResponse)
async def simple_vector_search(
    query: SimpleSearchQuery,
    request: Request
) -> SimpleSearchResponse:
    """Simple, robust vector similarity search"""
    
    start_time = time.time()
    logger.info(f"Simple search request: '{query.query}' in collection '{query.collection}'")
    
    try:
        # Get services
        qdrant_service, embedding_service = get_simple_services(request)
        
        # Generate embedding
        logger.info("Generating embedding...")
        query_vector = await embedding_service.embed_query(query.query)
        if not query_vector:
            logger.warning("Empty embedding generated")
            return SimpleSearchResponse(
                query=query.query,
                results=[],
                total_results=0,
                processing_time_ms=(time.time() - start_time) * 1000,
                collection=query.collection
            )
        
        # Perform vector search
        logger.info("Performing vector search...")
        raw_results = await qdrant_service.vector_search(
            query_vector=query_vector,
            limit=query.limit,
            score_threshold=query.threshold,
            container=query.collection
        )
        
        # Convert results
        results = []
        for raw_result in raw_results:
            payload = raw_result.get("payload", {})
            result = SimpleSearchResult(
                id=raw_result.get("id", ""),
                content=payload.get("content", ""),
                score=raw_result.get("score", 0.0),
                source_file=payload.get("source_file", "unknown"),
                chunk_type=payload.get("chunk_type", "text"),
                metadata=payload
            )
            results.append(result)
        
        processing_time = (time.time() - start_time) * 1000
        logger.info(f"Search completed: {len(results)} results in {processing_time:.2f}ms")
        
        return SimpleSearchResponse(
            query=query.query,
            results=results,
            total_results=len(results),
            processing_time_ms=processing_time,
            collection=query.collection
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/search/test")
async def test_simple_search():
    """Test endpoint"""
    return {"message": "Simple search endpoint is working"}
