"""
File Processing Service - FastAPI Main Application
Pure processing pipeline for file ingestion and storage
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.routes import process, health, collections
from app.api.middleware import TimingMiddleware, RequestLoggingMiddleware
from app.core.exceptions import ProcessingException
from fastapi.responses import JSONResponse

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info(f"Starting {settings.APP_NAME}")
    logger.info(f"Processing service ready - Focus: File ingestion and storage")
    
    # Initialize storage interfaces (removed hardcoded 'general' initialization)
    # Storage services will be created per-request based on container parameter
    
    yield
    
    # Shutdown
    logger.info("Shutting down file processing service")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="""
    **File Processing Service** - Pure ingestion pipeline for intelligent file processing.
    
    **Core Purpose:**
    - 📁 **Input**: Files with format-specific processing options
    - ⚙️ **Processing**: Parse → Chunk → Embed → Analyze → Store
    - 📤 **Output**: Job status tracking and storage confirmation
    - 🏗️ **Architecture**: Microservice for orchestrated file processing
    
    **Key Features:**
    - Format-specific processors (Excel, PDF, Markdown)
    - Intelligent chunking with relationship detection
    - LangChain semantic analysis
    - External storage interfaces (Vector DB, Graph DB)
    - Background processing with status tracking
    
    **Not included:** Search, retrieval, or query endpoints (handled by separate search service)
    """,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    # Use origin patterns compatible with credentials instead of wildcard
    allow_origin_regex=r"^https?://localhost(:\d+)?$|^https?://.*\.4\.230\.158\.187\.nip\.io$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TimingMiddleware)
app.add_middleware(RequestLoggingMiddleware)


# Exception handlers
@app.exception_handler(ProcessingException)
async def processing_exception_handler(request, exc: ProcessingException):
    """Handle processing exceptions"""
    logger.error(f"Processing error: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "Processing Error",
            "message": exc.message,
            "details": exc.details
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred" if not settings.DEBUG else str(exc)
        }
    )


# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(process.router, prefix="", tags=["File Processing"])
app.include_router(collections.router, prefix="/qdrant", tags=["Collection Management"])


@app.get("/")
async def root():
    """Service information"""
    return {
        "service": settings.APP_NAME,
        "version": "1.0.0",
        "purpose": "Pure file processing pipeline",
        "features": [
            "Format-specific processing (Excel, PDF, Markdown)",
            "Intelligent chunking with semantic analysis", 
            "LangChain integration for domain detection",
            "Container-isolated storage with external databases",
            "Azure OpenAI text-embedding-3-large embeddings generation",
            "Background processing with status tracking"
        ],
        "endpoints": {
            "processing": "/process/*",
            "collections": "/qdrant/collections/*",
            "health": "/health",
            "docs": "/docs" if settings.DEBUG else "disabled"
        }
    }