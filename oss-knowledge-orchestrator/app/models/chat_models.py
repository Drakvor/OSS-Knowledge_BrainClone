"""
Pydantic models for chat requests and responses
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator

class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str = Field(..., min_length=1, description="User message")
    session_id: str = Field(..., min_length=1, description="Chat session identifier")
    user_id: str = Field(..., min_length=1, description="User identifier")
    collection: Optional[str] = "general"
    attachments: Optional[List[Dict[str, Any]]] = None
    
    @validator('session_id')
    def validate_session_id(cls, v):
        if not v or not v.strip():
            raise ValueError('session_id cannot be empty')
        return v.strip()
    
    @validator('user_id')
    def validate_user_id(cls, v):
        if not v or not v.strip():
            raise ValueError('user_id cannot be empty')
        return v.strip()
    
    @validator('message')
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError('message cannot be empty')
        return v.strip()

class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    response: str
    intent: str
    reasoning: Optional[str] = None
    sources: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None

