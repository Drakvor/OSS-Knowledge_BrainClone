"""
Minimal search endpoint - bypasses all complex logic
"""
import time
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

class MinimalSearchQuery(BaseModel):
    query: str
    collection: str = "general"
    limit: int = 1

class MinimalSearchResult(BaseModel):
    id: str
    content: str
    score: float

class MinimalSearchResponse(BaseModel):
    query: str
    results: List[MinimalSearchResult]
    total_results: int
    processing_time_ms: float
    status: str

@router.post("/search/minimal", response_model=MinimalSearchResponse)
async def minimal_search(
    query: MinimalSearchQuery,
    request: Request
) -> MinimalSearchResponse:
    """Minimal search with real embedding and Qdrant logic"""
    
    start_time = time.time()
    logger.info(f"Minimal search request: '{query.query}' in collection '{query.collection}'")
    
    try:
        # Step 1: Get services (with proper error handling)
        logger.info("Getting services...")
        qdrant_service = request.app.state.qdrant_service
        embedding_service = request.app.state.embedding_service
        
        if not qdrant_service:
            logger.error("Qdrant service not available")
            raise HTTPException(status_code=503, detail="Qdrant service not available")
        if not embedding_service:
            logger.error("Embedding service not available")
            raise HTTPException(status_code=503, detail="Embedding service not available")
        
        logger.info("Services available, proceeding with search...")
        
        # Step 2: Generate embedding (with timeout protection)
        logger.info("Generating embedding...")
        try:
            import asyncio
            # Add timeout to prevent hanging
            query_vector = await asyncio.wait_for(
                embedding_service.embed_query(query.query),
                timeout=10.0  # 10 second timeout
            )
            if not query_vector:
                logger.warning("Empty embedding generated")
                return MinimalSearchResponse(
                    query=query.query,
                    results=[],
                    total_results=0,
                    processing_time_ms=(time.time() - start_time) * 1000,
                    status="no_embedding"
                )
            logger.info(f"Generated embedding with {len(query_vector)} dimensions")
        except asyncio.TimeoutError:
            logger.error("Embedding generation timed out")
            raise HTTPException(status_code=504, detail="Embedding generation timed out")
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")
        
        # Step 3: Perform vector search (with timeout protection)
        logger.info("Performing vector search...")
        try:
            raw_results = await asyncio.wait_for(
                qdrant_service.vector_search(
                    query_vector=query_vector,
                    limit=query.limit,
                    score_threshold=0.7,
                    container=query.collection
                ),
                timeout=10.0  # 10 second timeout
            )
            logger.info(f"Qdrant returned {len(raw_results) if raw_results else 0} results")
        except asyncio.TimeoutError:
            logger.error("Vector search timed out")
            raise HTTPException(status_code=504, detail="Vector search timed out")
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise HTTPException(status_code=500, detail=f"Vector search failed: {str(e)}")
        
        # Step 4: Convert results
        results = []
        for raw_result in raw_results:
            payload = raw_result.get("payload", {})
            result = MinimalSearchResult(
                id=raw_result.get("id", ""),
                content=payload.get("content", ""),
                score=raw_result.get("score", 0.0)
            )
            results.append(result)
        
        processing_time = (time.time() - start_time) * 1000
        logger.info(f"Minimal search completed: {len(results)} results in {processing_time:.2f}ms")
        
        return MinimalSearchResponse(
            query=query.query,
            results=results,
            total_results=len(results),
            processing_time_ms=processing_time,
            status="success"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Minimal search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/search/minimal/test")
async def test_minimal_search():
    """Test endpoint"""
    return {"message": "Minimal search endpoint is working"}
