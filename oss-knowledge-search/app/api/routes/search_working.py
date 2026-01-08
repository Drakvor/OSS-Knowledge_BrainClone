"""
Working search endpoint - uses real embedding but mock Qdrant results
"""
import time
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

class WorkingSearchQuery(BaseModel):
    query: str
    collection: str = "general"
    limit: int = 10
    threshold: float = 0.7

class WorkingSearchResult(BaseModel):
    id: str
    content: str
    score: float
    source_file: str = "mock_file.txt"
    chunk_type: str = "text"
    metadata: Dict[str, Any] = {}

class WorkingSearchResponse(BaseModel):
    query: str
    search_type: str = "vector"
    results: List[WorkingSearchResult]
    total_results: int
    processing_time_ms: float
    threshold_used: float

@router.post("/search/working", response_model=WorkingSearchResponse)
async def working_search(
    query: WorkingSearchQuery,
    request: Request
) -> WorkingSearchResponse:
    """Working search that uses real embedding but mock Qdrant results"""
    
    start_time = time.time()
    logger.info(f"Working search request: '{query.query}' in collection '{query.collection}'")
    
    try:
        # Step 1: Get embedding service
        embedding_service = request.app.state.embedding_service
        
        if not embedding_service:
            logger.error("Embedding service not available")
            raise HTTPException(status_code=503, detail="Embedding service not available")
        
        # Step 2: Generate embedding with timeout
        logger.info("Generating embedding...")
        try:
            import asyncio
            query_vector = await asyncio.wait_for(
                embedding_service.embed_query(query.query),
                timeout=10.0  # 10 second timeout
            )
            if not query_vector:
                logger.warning("Empty embedding generated")
                return WorkingSearchResponse(
                    query=query.query,
                    results=[],
                    total_results=0,
                    processing_time_ms=(time.time() - start_time) * 1000,
                    threshold_used=query.threshold
                )
            logger.info(f"Generated embedding with {len(query_vector)} dimensions")
        except asyncio.TimeoutError:
            logger.error("Embedding generation timed out")
            raise HTTPException(status_code=504, detail="Embedding generation timed out")
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")
        
        # Step 3: Generate mock Qdrant results (bypassing the problematic Qdrant call)
        logger.info("Generating mock search results...")
        
        # Create realistic mock results based on the query
        mock_results = []
        for i in range(min(query.limit, 5)):  # Limit to 5 results max
            score = 0.95 - (i * 0.1)  # Decreasing scores
            if score < query.threshold:
                break
                
            result = WorkingSearchResult(
                id=f"mock-result-{i+1}",
                content=f"Mock search result {i+1} for query '{query.query}'. This is a simulated result that would normally come from Qdrant vector search.",
                score=score,
                source_file=f"mock_document_{i+1}.txt",
                chunk_type="text",
                metadata={
                    "source_file": f"mock_document_{i+1}.txt",
                    "chunk_type": "text",
                    "container": query.collection,
                    "created_at": "2025-01-01T00:00:00Z",
                    "embedding_dimensions": len(query_vector)
                }
            )
            mock_results.append(result)
        
        processing_time = (time.time() - start_time) * 1000
        logger.info(f"Working search completed: {len(mock_results)} results in {processing_time:.2f}ms")
        
        return WorkingSearchResponse(
            query=query.query,
            results=mock_results,
            total_results=len(mock_results),
            processing_time_ms=processing_time,
            threshold_used=query.threshold
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Working search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/search/working/test")
async def test_working_search():
    """Test endpoint"""
    return {"message": "Working search endpoint is ready"}

