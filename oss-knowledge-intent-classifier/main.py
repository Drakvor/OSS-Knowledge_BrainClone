from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import httpx
from datetime import datetime
from intent_classifier import intent_classifier, IntentType
from typing import Optional, Dict, Any
from app.routing import IntentRouter
from app.fallback_llm import FallbackLLM

# Request/Response models
class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    user_id: str = "default"
    session_id: str = None  # 세션ID 추가
    chat_history: list[ChatMessage] = []
    collection: Optional[str] = None  # 선택된 부서/컬렉션 (null이면 RAG 검색 건너뛰기)
    chat_context: Optional[dict] = None  # 채팅 컨텍스트 (Backend에서 전달)

class ClassifyRequest(BaseModel):
    message: str
    chat_context: Optional[Dict[str, Any]] = None

class ClassifyResponse(BaseModel):
    intent: IntentType
    reasoning: str
    timestamp: str

class ChatResponse(BaseModel):
    response: str
    intent: IntentType
    timestamp: str
    sources: Optional[list] = None  # Source files with download links

# Search client for connecting to search server
class SearchClient:
    def __init__(self, base_url: str = None):
        import os
        self.base_url = base_url or os.getenv("SEARCH_SERVER_URL", "http://localhost:8002")
    
    async def search_and_generate_response(self, query: str, collection: str = "general", session_id: str = None, chat_context: dict = None) -> dict:
        """Call the search server's /search/response endpoint and return full response with sources"""
        try:
            async with httpx.AsyncClient() as client:
                request_data = {
                    "query": query,
                    "collection": collection,
                    "limit": 5,
                    "threshold": 0.55,
                    "include_metadata": True,
                    "include_content": True,
                    "max_tokens": 1000,
                    "temperature": 0.7
                }
                
                if session_id:
                    request_data["session_id"] = session_id
                
                if chat_context:
                    request_data["chat_context"] = chat_context
                    if "chat_history" in chat_context:
                        request_data["chat_history"] = chat_context["chat_history"]
                
                response = await client.post(
                    f"{self.base_url}/search/response",
                    json=request_data,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                # Return full response dict with sources
                return {
                    "response": data.get("response", "No response generated"),
                    "sources": data.get("sources", [])
                }
        except Exception as e:
            print(f"Error calling search server: {e}")
            return {
                "response": f"I'm sorry, I encountered an error while searching for information: {str(e)}",
                "sources": []
            }
    
    async def search_and_generate_response_direct(self, query: str, session_id: str = None, chat_context: dict = None) -> dict:
        """Call LLM directly without RAG search (for general chat)"""
        try:
            async with httpx.AsyncClient() as client:
                request_data = {
                    "query": query,
                    "collection": "general",
                    "limit": 5,
                    "threshold": 0.4,
                    "include_metadata": True,
                    "include_content": True,
                    "max_tokens": 1000,
                    "temperature": 0.7
                }
                
                if session_id:
                    request_data["session_id"] = session_id
                
                if chat_context:
                    request_data["chat_context"] = chat_context
                    if "chat_history" in chat_context:
                        request_data["chat_history"] = chat_context["chat_history"]
                
                response = await client.post(
                    f"{self.base_url}/search/response",
                    json=request_data,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                # Return full response dict with sources
                return {
                    "response": data.get("response", "No response generated"),
                    "sources": data.get("sources", [])
                }
        except Exception as e:
            print(f"Error calling LLM directly: {e}")
            return {
                "response": f"I'm sorry, I encountered an error while generating a response: {str(e)}",
                "sources": []
            }

# Initialize search client
search_client = SearchClient()

# Initialize fallback LLM and router
fallback_llm = FallbackLLM()
intent_router = IntentRouter(fallback_llm)

app = FastAPI(
    title="OSS Knowledge Intent Classifier",
    description="Intent classification service for OSS Knowledge system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify service is running
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "oss-knowledge-intent-classifier"
    }

@app.get("/")
async def root():
    """
    Root endpoint with basic service information
    """
    return {
        "message": "OSS Knowledge Intent Classifier Service",
        "version": "1.0.0",
        "status": "running"
    }

async def route_to_agent(intent: str, message: str, collection: str, session_id: str, chat_context: dict = None) -> dict:
    """
    Agent Router: intent에 따라 적절한 에이전트로 라우팅
    
    현재 지원 intent:
    - GREETING: 간단한 인사 응답
    - RAG_QUERY: Search-Back 호출 (기본값)
    - CONTEXT_QUERY: Search-Back 호출 (맥락 처리)
    - OTHER: Search-Back 호출 (기본 응답)
    
    향후 확장 계획:
    - CODE_GENERATION → CodeAgent
    - DATA_ANALYSIS → DataAgent  
    - DOCUMENT_SUMMARY → SummaryAgent
    - MEMORY_UPDATE → MemoryAgent
    """
    if intent == "GREETING":
        return {
            "response": "안녕하세요! OSS 지식베이스 어시스턴트입니다. 질문에 도움을 드릴 수 있습니다. 무엇을 도와드릴까요?",
            "sources": []
        }
    
    try:
        if collection is None or collection == "":
            result = await search_client.search_and_generate_response_direct(
                message,
                session_id=session_id,
                chat_context=chat_context
            )
        else:
            result = await search_client.search_and_generate_response(
                message,
                collection=collection,
                session_id=session_id,
                chat_context=chat_context
            )
        return result
    except Exception as e:
        print(f"ERROR: Search-Back 호출 실패: {e}")
        # Search-Back 호출 실패 시 기본 응답 생성
        fallback_response = intent_classifier.generate_response(message)
        return {
            "response": fallback_response,
            "sources": []
        }

@app.post("/classify", response_model=ClassifyResponse)
async def classify(request: ClassifyRequest):
    """
    Intent classification endpoint using EXAONE
    """
    try:
        # Classify intent using EXAONE
        result = await intent_classifier.classify_intent_async(
            request.message,
            request.chat_context
        )
        
        return ClassifyResponse(
            intent=result.get("intent", "UNKNOWN"),
            reasoning=result.get("reasoning", "No reasoning provided"),
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception as e:
        print(f"ERROR: Classification failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Classification error: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint with intent classification and routing
    Maintains backward compatibility with old /chat endpoint
    """
    try:
        # Debug: Log request information
        print(f"DEBUG: User message: '{request.message}'")
        print(f"DEBUG: Session ID: '{request.session_id}'")
        print(f"DEBUG: User ID: '{request.user_id}'")
        print(f"DEBUG: Collection: '{request.collection}'")
        
        # Classify intent using EXAONE (async)
        classification_result = await intent_classifier.classify_intent_async(
            request.message,
            request.chat_context
        )
        intent = classification_result.get("intent", "UNKNOWN")
        
        # Route based on intent
        routing_result = await intent_router.route(
            intent=intent,
            message=request.message,
            collection=request.collection,
            chat_context=request.chat_context
        )
        
        # Handle routing
        if routing_result.get("response"):
            # CASUAL or UNKNOWN - direct response
            return ChatResponse(
                response=routing_result["response"],
                intent=intent,
                timestamp=datetime.utcnow().isoformat(),
                sources=None
            )
        else:
            # COMPLEX or CONTEXT - route to appropriate service
            # For now, maintain backward compatibility with Search Server for COMPLEX
            route_to = routing_result.get("route_to")
            
            if intent == "COMPLEX":
                # Route to Search Server (orchestrator will decide whether to use task planner)
                agent_result = await route_to_agent("RAG_QUERY", request.message, request.collection, request.session_id, request.chat_context)
                response_text = agent_result.get("response", "") if isinstance(agent_result, dict) else str(agent_result)
                sources = agent_result.get("sources", []) if isinstance(agent_result, dict) else []
                
                return ChatResponse(
                    response=response_text,
                    intent=intent,
                    timestamp=datetime.utcnow().isoformat(),
                    sources=sources if sources else None
                )
            else:
                # CONTEXT - for now, return placeholder
                return ChatResponse(
                    response=f"Intent '{intent}' requires {route_to} service (not yet implemented)",
                    intent=intent,
                    timestamp=datetime.utcnow().isoformat(),
                    sources=None
                )
        
    except Exception as e:
        print(f"ERROR: Chat request failed: {e}")
        import traceback
        traceback.print_exc()
        
        # 에러 상세 정보 포함
        error_detail = f"Error processing chat request: {str(e)}"
        raise HTTPException(status_code=500, detail=error_detail)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )
