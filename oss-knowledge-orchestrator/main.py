"""
OSS Knowledge Orchestrator Service
Main coordination service for agentic RAG system
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
from typing import Optional
import logging
import json

from app.orchestrator import Orchestrator
from app.models.chat_models import ChatRequest, ChatResponse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global orchestrator instance
orchestrator_service: Optional[Orchestrator] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global orchestrator_service
    # Startup
    logger.info("Starting OSS Knowledge Orchestrator Service")
    orchestrator_service = Orchestrator()
    logger.info("Orchestrator service ready - Port 8000")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Orchestrator service")


# Create FastAPI application
app = FastAPI(
    title="OSS Knowledge Orchestrator",
    version="1.0.0",
    description="""
    **Orchestrator Service** - Central coordination service for agentic RAG system.
    
    **Core Purpose:**
    - Coordinates between Intent Classifier, Task Planner, Search Server, and Backend
    - Manages chat context and streaming
    - Routes requests based on intent classification
    
    **Architecture:**
    - Port 8000
    - Coordinates: Intent Classifier (8001), Task Planner (8004), Search Server (8002), Backend (8080)
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://localhost(:\d+)?$|^https?://.*\.4\.230\.158\.187\.nip\.io$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "orchestrator",
        "version": "1.0.0",
        "port": 8000
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "OSS Knowledge Orchestrator",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "chat": "/chat"
        }
    }

@app.post("/chat")
async def chat(request: dict):
    """Chat endpoint - main orchestration endpoint"""
    if orchestrator_service is None:
        raise HTTPException(status_code=503, detail="Orchestrator service not initialized")
    
    try:
        # Parse request
        chat_request = ChatRequest(**request)
        
        # Orchestrate chat
        result = await orchestrator_service.orchestrate_chat(
            message=chat_request.message,
            session_id=chat_request.session_id,
            user_id=chat_request.user_id,
            collection=chat_request.collection,
            attachments=chat_request.attachments
        )
        
        return ChatResponse(**result)
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/stream")
async def chat_stream(request: dict):
    """Chat endpoint with SSE streaming"""
    if orchestrator_service is None:
        raise HTTPException(status_code=503, detail="Orchestrator service not initialized")
    
    async def generate_stream():
        try:
            chat_request = ChatRequest(**request)
            
            # Use streaming orchestration method
            async for event in orchestrator_service.orchestrate_chat_stream(
                message=chat_request.message,
                session_id=chat_request.session_id,
                user_id=chat_request.user_id,
                collection=chat_request.collection,
                attachments=chat_request.attachments
            ):
                # Format as SSE: data: {json}\n\n
                yield f"data: {json.dumps(event)}\n\n"
            
        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'data': {'error': str(e)}})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

