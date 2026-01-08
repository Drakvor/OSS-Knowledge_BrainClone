"""
OSS Knowledge Context Manager Service
Handles chat context building, mem0 integration, and memory management.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.context_manager import ContextManager

# Setup logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Request/Response models
class BuildContextRequest(BaseModel):
    session_id: str
    user_id: Optional[int] = None
    current_query: Optional[str] = None
    attachments: Optional[list] = None

class AddMemoryRequest(BaseModel):
    query: str
    response: str
    user_id: int
    session_id: str
    is_important: Optional[bool] = None

class SearchMemoryRequest(BaseModel):
    query: str
    user_id: int
    session_id: str
    user_limit: Optional[int] = 3
    session_limit: Optional[int] = 5

context_manager_service: Optional[ContextManager] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global context_manager_service
    # Startup
    logger.info("Starting OSS Knowledge Context Manager Service")
    context_manager_service = ContextManager()
    logger.info("Context Manager service ready - Port 8005")
    yield
    # Shutdown
    logger.info("Shutting down Context Manager service")

app = FastAPI(
    title="OSS Knowledge Context Manager Service",
    description="Handles chat context building, mem0 integration, and memory management.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "context-manager",
        "version": "1.0.0",
        "port": 8005
    }

@app.get("/")
async def root():
    """Root endpoint with basic service information"""
    return {
        "message": "OSS Knowledge Context Manager Service",
        "version": "1.0.0",
        "status": "running"
    }

@app.post("/context/build")
async def build_context(request: BuildContextRequest):
    """Build complete chat context with sliding window, mem0 memories, and attachments"""
    if context_manager_service is None:
        raise HTTPException(status_code=503, detail="Context Manager service not initialized")
    
    try:
        context = await context_manager_service.build_context(
            session_id=request.session_id,
            user_id=request.user_id,
            current_query=request.current_query,
            attachments=request.attachments
        )
        return context
    except Exception as e:
        logger.error(f"Error building context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memory/add")
async def add_memory(request: AddMemoryRequest):
    """Add conversation to mem0 with importance detection"""
    if context_manager_service is None:
        raise HTTPException(status_code=503, detail="Context Manager service not initialized")
    
    try:
        result = await context_manager_service.add_conversation_memory(
            query=request.query,
            response=request.response,
            user_id=request.user_id,
            session_id=request.session_id,
            is_important=request.is_important
        )
        return {"success": result}
    except Exception as e:
        logger.error(f"Error adding memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memory/search")
async def search_memory(request: SearchMemoryRequest):
    """Search mem0 memories (user + session)"""
    if context_manager_service is None:
        raise HTTPException(status_code=503, detail="Context Manager service not initialized")
    
    try:
        memories = await context_manager_service.search_memories(
            query=request.query,
            user_id=request.user_id,
            session_id=request.session_id,
            user_limit=request.user_limit,
            session_limit=request.session_limit
        )
        return memories
    except Exception as e:
        logger.error(f"Error searching memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8005,
        reload=True
    )

