"""
Debug search endpoint - tests each step individually
"""
import time
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

class DebugSearchQuery(BaseModel):
    query: str
    collection: str = "general"
    limit: int = 1

class DebugSearchResponse(BaseModel):
    query: str
    step: str
    status: str
    message: str
    processing_time_ms: float

@router.post("/search/debug", response_model=DebugSearchResponse)
async def debug_search(
    query: DebugSearchQuery,
    request: Request
) -> DebugSearchResponse:
    """Debug search that tests each step individually"""
    
    start_time = time.time()
    logger.info(f"Debug search request: '{query.query}' in collection '{query.collection}'")
    
    try:
        # Step 1: Test service availability
        logger.info("=== STEP 1: Testing service availability ===")
        qdrant_service = request.app.state.qdrant_service
        embedding_service = request.app.state.embedding_service
        
        if not qdrant_service:
            return DebugSearchResponse(
                query=query.query,
                step="service_check",
                status="error",
                message="Qdrant service not available",
                processing_time_ms=(time.time() - start_time) * 1000
            )
        
        if not embedding_service:
            return DebugSearchResponse(
                query=query.query,
                step="service_check",
                status="error",
                message="Embedding service not available",
                processing_time_ms=(time.time() - start_time) * 1000
            )
        
        logger.info("Services are available")
        
        # Step 2: Test embedding service call with timeout
        logger.info("=== STEP 2: Testing embedding service call ===")
        try:
            import asyncio
            # Test actual embedding call with timeout
            query_vector = await asyncio.wait_for(
                embedding_service.embed_query(query.query),
                timeout=5.0  # 5 second timeout
            )
            logger.info(f"Embedding successful: {len(query_vector)} dimensions")
        except asyncio.TimeoutError:
            logger.error("Embedding service timed out")
            return DebugSearchResponse(
                query=query.query,
                step="embedding_test",
                status="timeout",
                message="Embedding service timed out after 5 seconds",
                processing_time_ms=(time.time() - start_time) * 1000
            )
        except Exception as e:
            logger.error(f"Embedding service failed: {e}")
            return DebugSearchResponse(
                query=query.query,
                step="embedding_test",
                status="error",
                message=f"Embedding service failed: {str(e)}",
                processing_time_ms=(time.time() - start_time) * 1000
            )
        
        # Step 3: Test Qdrant service call with timeout
        logger.info("=== STEP 3: Testing Qdrant service call ===")
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
            logger.info(f"Qdrant successful: {len(raw_results) if raw_results else 0} results")
            return DebugSearchResponse(
                query=query.query,
                step="qdrant_test",
                status="success",
                message=f"Qdrant successful: {len(raw_results) if raw_results else 0} results",
                processing_time_ms=(time.time() - start_time) * 1000
            )
        except asyncio.TimeoutError:
            logger.error("Qdrant service timed out")
            return DebugSearchResponse(
                query=query.query,
                step="qdrant_test",
                status="timeout",
                message="Qdrant service timed out after 10 seconds",
                processing_time_ms=(time.time() - start_time) * 1000
            )
        except Exception as e:
            logger.error(f"Qdrant service failed: {e}")
            return DebugSearchResponse(
                query=query.query,
                step="qdrant_test",
                status="error",
                message=f"Qdrant service failed: {str(e)}",
                processing_time_ms=(time.time() - start_time) * 1000
            )
        
    except Exception as e:
        logger.error(f"Debug search failed: {e}")
        return DebugSearchResponse(
            query=query.query,
            step="error",
            status="error",
            message=f"Debug search failed: {str(e)}",
            processing_time_ms=(time.time() - start_time) * 1000
        )

@router.get("/search/debug/test")
async def test_debug_search():
    """Test endpoint"""
    return {"message": "Debug search endpoint is working"}
