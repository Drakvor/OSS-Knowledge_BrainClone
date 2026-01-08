"""
FastAPI Dependencies
Dependency injection for services and validation
"""

import os
from typing import List
from functools import lru_cache
from fastapi import HTTPException, UploadFile

from app.config import settings
from app.services.processing_service import ProcessingService
from app.services.storage_service import StorageService
from app.core.exceptions import FileValidationError, UnsupportedFormatError


# ===== SERVICE DEPENDENCIES =====

@lru_cache()
def get_processing_service() -> ProcessingService:
    """Get processing service instance (cached)"""
    return ProcessingService()


@lru_cache()
def get_storage_service() -> StorageService:
    """Get storage service instance (cached)"""
    return StorageService()


# ===== FILE VALIDATION =====

async def validate_file(file: UploadFile, allowed_extensions: List[str]) -> UploadFile:
    """Validate uploaded file"""
    
    # Check if file is provided
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Check filename
    if not file.filename:
        raise HTTPException(status_code=400, detail="File must have a name")
    
    # Check file extension
    file_ext = os.path.splitext(file.filename.lower())[1]
    if file_ext not in allowed_extensions:
        raise UnsupportedFormatError(
            f"Unsupported file type: {file_ext}. Allowed: {', '.join(allowed_extensions)}",
            format=file_ext
        )
    
    # Check file size
    if file.size and file.size > settings.MAX_FILE_SIZE:
        raise FileValidationError(
            f"File too large: {file.size} bytes. Maximum: {settings.MAX_FILE_SIZE} bytes",
            file.filename
        )
    
    # Reset file pointer
    await file.seek(0)
    return file


# ===== HEALTH CHECK DEPENDENCIES =====

async def check_storage_health() -> dict:
    """Check health of storage services"""
    
    storage_service = get_storage_service()
    
    # Initialize if not already done
    if not storage_service.initialized:
        await storage_service.initialize()
    
    return await storage_service.health_check()


async def check_system_health() -> dict:
    """Check overall system health"""
    
    health_status = {
        "storage": "unknown",
        "file_system": "unknown",
        "temp_directory": "unknown"
    }
    
    try:
        # Check storage
        storage_health = await check_storage_health()
        health_status["storage"] = "healthy" if any(storage_health.values()) else "unhealthy"
    except Exception as e:
        health_status["storage"] = f"error: {str(e)}"
    
    try:
        # Check file system access
        os.makedirs(settings.TEMP_DIR, exist_ok=True)
        health_status["file_system"] = "healthy"
        health_status["temp_directory"] = "accessible"
    except Exception as e:
        health_status["file_system"] = f"error: {str(e)}"
        health_status["temp_directory"] = "inaccessible"
    
    return health_status