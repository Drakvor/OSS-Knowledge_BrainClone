"""
Main FastAPI application for OSS Knowledge Search Server
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
import uvicorn

from app.config import settings
from app.api.routes import search, health, admin, title_generation
from app.core.qdrant_client import QdrantService
from app.core.azure_embedding import AzureEmbeddingService
from app.core.azure_llm import AzureLLMService
# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Global service instances
qdrant_service: QdrantService = None
embedding_service: AzureEmbeddingService = None
llm_service: AzureLLMService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global qdrant_service, embedding_service, llm_service
    
    logger.info("Starting OSS Knowledge Search Server", version="1.0.0")
    
    try:
        # Initialize services
        logger.info("Initializing services...")
        
        # Initialize Qdrant service
        qdrant_service = QdrantService()
        await qdrant_service.initialize()
        logger.info("Qdrant service initialized")
        
        # Initialize Azure embedding service
        embedding_service = None
        try:
            embedding_service = AzureEmbeddingService()
            await embedding_service.initialize()
            logger.info("Azure embedding service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Azure embedding service: {e}")
            logger.warning("Search functionality will be limited without embedding service")
        
        # Initialize Azure LLM service
        llm_service = None
        try:
            llm_service = AzureLLMService()
            await llm_service.initialize()
            logger.info("Azure LLM service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Azure LLM service: {e}")
            logger.warning("LLM functionality will be limited without LLM service")
        
        # Store services in app state
        app.state.qdrant_service = qdrant_service
        app.state.embedding_service = embedding_service
        app.state.llm_service = llm_service
        
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize services", error=str(e))
        raise
    
    yield
    
    # Cleanup
    logger.info("Shutting down services...")
    
    try:
        if llm_service:
            await llm_service.close()
            logger.info("Azure LLM service closed")
            
        if embedding_service:
            await embedding_service.close()
            logger.info("Azure embedding service closed")
            
        if qdrant_service:
            await qdrant_service.close()
            logger.info("Qdrant service closed")
            
    except Exception as e:
        logger.error("Error during service cleanup", error=str(e))
    
    logger.info("OSS Knowledge Search Server shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="A dedicated search service for the OSS Knowledge platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(search.router, prefix="", tags=["Search"])
app.include_router(admin.router, prefix="", tags=["Admin"])
app.include_router(title_generation.router, prefix="", tags=["Title Generation"])


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error("Unhandled exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )