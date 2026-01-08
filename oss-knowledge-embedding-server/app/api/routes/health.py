"""
Health Check Endpoints
System health monitoring for file processing service
"""

import logging
import time
import os
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.config import settings
from app.dependencies import check_system_health, check_storage_health

logger = logging.getLogger(__name__)
router = APIRouter()

# Track application start time
_start_time = time.time()


class HealthResponse(BaseModel):
    """Basic health check response"""
    status: str
    timestamp: datetime
    uptime_seconds: float


class DetailedHealthResponse(BaseModel):
    """Detailed health check response"""
    status: str
    timestamp: datetime
    uptime_seconds: float
    system_info: Dict[str, Any]
    storage_health: Dict[str, Any]
    configuration: Dict[str, Any]


@router.get("/", response_model=HealthResponse)
async def basic_health_check():
    """Basic health check - always returns 200 if service is running"""
    
    uptime = time.time() - _start_time
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        uptime_seconds=uptime
    )


@router.get("/live", response_model=HealthResponse)
async def liveness_check():
    """Kubernetes liveness probe - checks if service is alive"""
    
    uptime = time.time() - _start_time
    
    return HealthResponse(
        status="alive",
        timestamp=datetime.now(),
        uptime_seconds=uptime
    )


@router.get("/ready")
async def readiness_check(system_health: Dict[str, Any] = Depends(check_system_health)):
    """Kubernetes readiness probe - checks if service is ready to handle requests"""
    
    # Service is ready if storage and file system are accessible
    storage_ready = system_health.get("storage") == "healthy"
    filesystem_ready = system_health.get("file_system") == "healthy"
    
    ready = storage_ready and filesystem_ready
    status_code = 200 if ready else 503
    
    return {
        "ready": ready,
        "checks": system_health,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check(
    system_health: Dict[str, Any] = Depends(check_system_health),
    storage_health: Dict[str, Any] = Depends(check_storage_health)
):
    """Comprehensive health check with detailed system information"""
    
    uptime = time.time() - _start_time
    
    # System information
    system_info = {
        "service_name": settings.APP_NAME,
        "uptime_seconds": uptime,
        "debug_mode": settings.DEBUG,
        "temp_directory": settings.TEMP_DIR,
        "max_file_size_mb": settings.MAX_FILE_SIZE / (1024 * 1024),
        "max_concurrent_jobs": settings.MAX_CONCURRENT_JOBS,
        "job_timeout_seconds": settings.JOB_TIMEOUT_SECONDS
    }
    
    # Configuration info (excluding sensitive data)
    configuration = {
        "supported_formats": {
            "excel": {
                "status": "available",
                "extensions": [".xlsx", ".xls"]
            },
            "pdf": {
                "status": "planned", 
                "extensions": [".pdf"]
            },
            "markdown": {
                "status": "planned",
                "extensions": [".md", ".markdown"]
            }
        },
        "embedding_models": {
            "default": settings.EMBEDDING_MODEL,
            "device": settings.EMBEDDING_DEVICE
        },
        "storage_configured": {
            "qdrant": settings.ENABLE_QDRANT,
            "neo4j": settings.ENABLE_NEO4J
        },
        "langchain_configured": bool(settings.OPENAI_API_KEY)
    }
    
    # Determine overall status
    overall_status = "healthy"
    if system_health.get("storage") != "healthy":
        overall_status = "degraded"
    if system_health.get("file_system") != "healthy":
        overall_status = "unhealthy"
    
    return DetailedHealthResponse(
        status=overall_status,
        timestamp=datetime.now(),
        uptime_seconds=uptime,
        system_info=system_info,
        storage_health=storage_health,
        configuration=configuration
    )