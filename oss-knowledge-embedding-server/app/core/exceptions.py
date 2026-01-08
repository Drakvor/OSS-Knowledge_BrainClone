"""
Custom Exceptions for File Processing Service
Focused exception handling for processing pipeline
"""

from typing import Any, Dict, Optional


class ProcessingException(Exception):
    """Base exception for file processing errors"""
    
    def __init__(
        self, 
        message: str, 
        status_code: int = 500, 
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class FileValidationError(ProcessingException):
    """Raised when file validation fails"""
    
    def __init__(self, message: str, filename: str = None):
        super().__init__(
            message, 
            status_code=400,
            details={"filename": filename, "error_type": "file_validation"}
        )


class UnsupportedFormatError(ProcessingException):
    """Raised when file format is not supported"""
    
    def __init__(self, message: str, format: str = None):
        super().__init__(
            message,
            status_code=415,
            details={"format": format, "error_type": "unsupported_format"}
        )


class ProcessorError(ProcessingException):
    """Raised when format-specific processor fails"""
    
    def __init__(self, message: str, processor_type: str = None):
        super().__init__(
            message,
            status_code=422,
            details={"processor_type": processor_type, "error_type": "processor_error"}
        )


class StorageError(ProcessingException):
    """Raised when storage operations fail"""
    
    def __init__(self, message: str, storage_type: str = None):
        super().__init__(
            message,
            status_code=500,
            details={"storage_type": storage_type, "error_type": "storage_error"}
        )


class EmbeddingError(ProcessingException):
    """Raised when embedding generation fails"""
    
    def __init__(self, message: str, model_name: str = None):
        super().__init__(
            message,
            status_code=500,
            details={"model_name": model_name, "error_type": "embedding_error"}
        )


class JobNotFoundError(ProcessingException):
    """Raised when job is not found"""
    
    def __init__(self, job_id: str):
        super().__init__(
            f"Job not found: {job_id}",
            status_code=404,
            details={"job_id": job_id, "error_type": "job_not_found"}
        )


class JobTimeoutError(ProcessingException):
    """Raised when job times out"""
    
    def __init__(self, job_id: str, timeout_seconds: int):
        super().__init__(
            f"Job timed out: {job_id}",
            status_code=408,
            details={
                "job_id": job_id, 
                "timeout_seconds": timeout_seconds,
                "error_type": "job_timeout"
            }
        )