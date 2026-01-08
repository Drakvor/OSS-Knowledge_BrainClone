"""
Health check endpoints
"""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any
import asyncio
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    services: Dict[str, str]


async def check_qdrant_health(qdrant_service) -> str:
    """Check Qdrant service health"""
    try:
        if qdrant_service and qdrant_service.client:
            # Try to get collections info as a health check
            collections = qdrant_service.client.get_collections()
            if collections:
                return "healthy"
            else:
                return "unhealthy"
        else:
            return "not_initialized"
    except Exception as e:
        logger.error(f"Qdrant health check failed: {e}")
        return "unhealthy"


async def check_azure_embedding_health(embedding_service) -> str:
    """Check Azure Embedding service health"""
    try:
        if embedding_service and hasattr(embedding_service, 'client'):
            # Try a simple embedding test
            test_text = "health check"
            await embedding_service.embed_query(test_text)
            return "healthy"
        else:
            return "not_initialized"
    except Exception as e:
        logger.error(f"Azure Embedding health check failed: {e}")
        return "unhealthy"


async def check_azure_llm_health(llm_service) -> str:
    """Check Azure LLM service health"""
    try:
        if llm_service and hasattr(llm_service, 'client') and llm_service.initialized:
            # Just check if the service is initialized and has a client
            return "healthy"
        else:
            return "not_initialized"
    except Exception as e:
        logger.error(f"Azure LLM health check failed: {e}")
        return "unhealthy"


async def check_database_health(chat_context_service) -> str:
    """Check database connection health"""
    try:
        if chat_context_service and chat_context_service.conn_pool:
            # Try to get a connection from the pool
            async with chat_context_service.conn_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return "healthy"
        else:
            return "not_initialized"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return "unhealthy"


@router.get("/health")
async def health_check(request: Request) -> HealthResponse:
    """Comprehensive health check with actual service verification"""
    
    # Get services from app state
    qdrant_service = getattr(request.app.state, 'qdrant_service', None)
    embedding_service = getattr(request.app.state, 'embedding_service', None)
    llm_service = getattr(request.app.state, 'llm_service', None)
    chat_context_service = getattr(request.app.state, 'chat_context_service', None)
    
    # Check all services concurrently
    health_checks = await asyncio.gather(
        check_qdrant_health(qdrant_service),
        check_azure_embedding_health(embedding_service),
        check_azure_llm_health(llm_service),
        check_database_health(chat_context_service),
        return_exceptions=True
    )
    
    # Extract results
    qdrant_status = health_checks[0] if not isinstance(health_checks[0], Exception) else "error"
    embedding_status = health_checks[1] if not isinstance(health_checks[1], Exception) else "error"
    llm_status = health_checks[2] if not isinstance(health_checks[2], Exception) else "error"
    database_status = health_checks[3] if not isinstance(health_checks[3], Exception) else "error"
    
    # Determine overall status
    all_healthy = all(status == "healthy" for status in [qdrant_status, embedding_status, llm_status, database_status])
    overall_status = "healthy" if all_healthy else "degraded"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now(),
        version="1.0.0",
        services={
            "api": "healthy",
            "qdrant": qdrant_status,
            "azure_embedding": embedding_status,
            "azure_llm": llm_status,
            "database": database_status
        }
    )


@router.get("/ready")
async def readiness_check(request: Request) -> HealthResponse:
    """Readiness check - ensures all services are available"""
    
    # Get services from app state
    qdrant_service = getattr(request.app.state, 'qdrant_service', None)
    embedding_service = getattr(request.app.state, 'embedding_service', None)
    llm_service = getattr(request.app.state, 'llm_service', None)
    chat_context_service = getattr(request.app.state, 'chat_context_service', None)
    
    # Check all services concurrently
    health_checks = await asyncio.gather(
        check_qdrant_health(qdrant_service),
        check_azure_embedding_health(embedding_service),
        check_azure_llm_health(llm_service),
        check_database_health(chat_context_service),
        return_exceptions=True
    )
    
    # Extract results
    qdrant_status = health_checks[0] if not isinstance(health_checks[0], Exception) else "error"
    embedding_status = health_checks[1] if not isinstance(health_checks[1], Exception) else "error"
    llm_status = health_checks[2] if not isinstance(health_checks[2], Exception) else "error"
    database_status = health_checks[3] if not isinstance(health_checks[3], Exception) else "error"
    
    # For readiness, we need all services to be healthy
    all_ready = all(status == "healthy" for status in [qdrant_status, embedding_status, llm_status, database_status])
    overall_status = "ready" if all_ready else "not_ready"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now(),
        version="1.0.0",
        services={
            "api": "ready",
            "qdrant": qdrant_status,
            "azure_embedding": embedding_status,
            "azure_llm": llm_status,
            "database": database_status
        }
    )


@router.get("/live")
async def liveness_check() -> Dict[str, Any]:
    """Liveness check for Kubernetes"""
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat()
    }