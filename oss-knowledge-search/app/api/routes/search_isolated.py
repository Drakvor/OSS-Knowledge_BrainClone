"""
Isolated search endpoint - no external dependencies
"""
import time
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

class IsolatedSearchQuery(BaseModel):
    query: str
    collection: str = "general"
    limit: int = 1

class IsolatedSearchResult(BaseModel):
    id: str
    content: str
    score: float

class IsolatedSearchResponse(BaseModel):
    query: str
    results: List[IsolatedSearchResult]
    total_results: int
    processing_time_ms: float
    status: str

@router.post("/search/isolated", response_model=IsolatedSearchResponse)
async def isolated_search(
    query: IsolatedSearchQuery,
    request: Request
) -> IsolatedSearchResponse:
    """Isolated search that doesn't use any external services"""
    
    start_time = time.time()
    logger.info(f"Isolated search request: '{query.query}' in collection '{query.collection}'")
    
    try:
        # Simulate search results without any external calls
        mock_results = [
            IsolatedSearchResult(
                id=f"result-{i}",
                content=f"Search result {i} for query: {query.query}",
                score=0.9 - (i * 0.1)
            )
            for i in range(min(query.limit, 3))
        ]
        
        processing_time = (time.time() - start_time) * 1000
        logger.info(f"Isolated search completed: {len(mock_results)} results in {processing_time:.2f}ms")
        
        return IsolatedSearchResponse(
            query=query.query,
            results=mock_results,
            total_results=len(mock_results),
            processing_time_ms=processing_time,
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Isolated search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/search/isolated/test")
async def test_isolated_search():
    """Test endpoint"""
    return {"message": "Isolated search endpoint is working"}

