"""
FastAPI Middleware
Custom middleware for logging, timing, and request processing
"""

import time
import logging
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class TimingMiddleware(BaseHTTPMiddleware):
    """Middleware to log request timing"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log slow requests
        if process_time > 5.0:  # Log requests taking more than 5 seconds
            logger.warning(
                f"Slow request: {request.method} {request.url.path} took {process_time:.2f}s"
            )
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log requests and add request IDs"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())[:8]
        
        # Log request
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} - "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        try:
            response = await call_next(request)
            
            # Log response
            logger.info(
                f"[{request_id}] Response: {response.status_code}"
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            logger.error(
                f"[{request_id}] Request failed: {str(e)}"
            )
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY" 
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to limit request size"""
    
    def __init__(self, app, max_size: int = 50 * 1024 * 1024):  # 50MB default
        super().__init__(app)
        self.max_size = max_size
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_size:
            logger.warning(
                f"Request too large: {content_length} bytes (max: {self.max_size})"
            )
            return Response(
                content="Request entity too large",
                status_code=413
            )
        
        return await call_next(request)