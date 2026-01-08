import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from mem0 import Memory
from dotenv import load_dotenv

load_dotenv() # take environment variables from .env.

app = FastAPI(title="MEM0 Azure API", version="1.0.0")

# MEM0 설정
config = {
    "graph_store": {
        "provider": "neo4j",
        "config": {
            "url": os.getenv("NEO4J_URL"),
            "username": os.getenv("NEO4J_USERNAME"),
            "password": os.getenv("NEO4J_PASSWORD")
        }
    },
    "llm": {
        "provider": "azure_openai",
        "config": {
            "model": os.getenv("AZURE_DEPLOYMENT", "gpt-4.1-mini"),
            "temperature": 0.2,
            "max_tokens": 1500,
            "azure_kwargs": {
                "api_key": os.getenv("AZURE_API_KEY"),
                "azure_endpoint": os.getenv("AZURE_ENDPOINT"),
                "api_version": os.getenv("AZURE_API_VERSION", "2024-02-15-preview"),
                "azure_deployment": os.getenv("AZURE_DEPLOYMENT", "gpt-4.1-mini"),
            }
        }
    },
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "mem0_collection",
            "host": os.getenv("QDRANT_HOST", "20.249.165.27"),
            "port": int(os.getenv("QDRANT_PORT", 6333)),
            "embedding_model_dims": 1536,  # text-embedding-3-small dimension
        }
    },
    "embedder": {
        "provider": "azure_openai",
        "config": {
            # Use AZURE_EMBEDDING_SMALL_MODEL if available, otherwise fallback to AZURE_EMBEDDING_DEPLOYMENT
            "model": os.getenv("AZURE_EMBEDDING_SMALL_MODEL") or os.getenv("AZURE_EMBEDDING_DEPLOYMENT"),
            "embedding_dims": 1536,  # text-embedding-3-small dimension
            "azure_kwargs": {
                "api_key": os.getenv("AZURE_API_KEY"),
                "azure_endpoint": os.getenv("AZURE_ENDPOINT"),
                "api_version": os.getenv("AZURE_API_VERSION", "2024-02-15-preview"),
                # Use AZURE_EMBEDDING_SMALL_MODEL if available, otherwise fallback to AZURE_EMBEDDING_DEPLOYMENT
                "azure_deployment": os.getenv("AZURE_EMBEDDING_SMALL_MODEL") or os.getenv("AZURE_EMBEDDING_DEPLOYMENT"),
            }
        }
    }
}

# MEM0 메모리 인스턴스
print(f"DEBUG: AZURE_API_KEY from env: {os.getenv('AZURE_API_KEY')}")
try:
    print("Initializing memory with config...")
    memory = Memory.from_config(config)
    print("Memory initialized successfully!")
except Exception as e:
    print(f"Memory initialization failed: {e}")
    import traceback
    traceback.print_exc()
    memory = None

class MemoryRequest(BaseModel):
    message: str
    user_id: str
    metadata: dict = {}

class MemoryResponse(BaseModel):
    success: bool
    result: dict = {}
    error: str = ""

@app.get("/")
async def root():
    return {
        "message": "MEM0 Azure API is running",
        "status": "healthy",
        "version": "1.0.0"
    }

@app.get("/health")
async def health():
    memory_status = "available" if memory else "unavailable"
    return {
        "status": "healthy",
        "service": "mem0-azure-api",
        "memory_engine": memory_status
    }

@app.post("/memory/add", response_model=MemoryResponse)
async def add_memory(request: MemoryRequest):
    if not memory:
        raise HTTPException(status_code=500, detail="Memory engine not available")
    
    try:
        result = memory.add(
            messages=request.message,
            user_id=request.user_id,
            metadata=request.metadata
        )
        return MemoryResponse(success=True, result=result)
    except Exception as e:
        return MemoryResponse(success=False, error=str(e))

@app.get("/memory/get/{user_id}")
async def get_memories(user_id: str):
    if not memory:
        raise HTTPException(status_code=500, detail="Memory engine not available")
    
    try:
        result = memory.get_all(user_id=user_id)
        return {"success": True, "memories": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/memory/search")
async def search_memories(request: dict):
    if not memory:
        raise HTTPException(status_code=500, detail="Memory engine not available")
    
    try:
        query = request.get("query", "")
        user_id = request.get("user_id", "")
        
        result = memory.search(query=query, user_id=user_id)
        return {"success": True, "results": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
