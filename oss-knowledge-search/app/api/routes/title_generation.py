"""
채팅 제목 생성 API 라우터
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import structlog

from app.core.azure_llm import AzureLLMService

logger = structlog.get_logger(__name__)
router = APIRouter()

class TitleGenerationRequest(BaseModel):
    message: str
    language: str = "ko"

class TitleGenerationResponse(BaseModel):
    title: str
    success: bool
    error_message: Optional[str] = None

@router.post("/search/generate-title", response_model=TitleGenerationResponse)
async def generate_chat_title(request: TitleGenerationRequest):
    """
    LLM을 사용하여 채팅 제목을 생성합니다.
    """
    try:
        logger.info("🎯 [TitleGeneration] Starting title generation", 
                   message=request.message[:50] + "...",
                   language=request.language)
        
        # Azure LLM 서비스 인스턴스 생성
        llm_service = AzureLLMService()
        await llm_service.initialize()
        logger.info("🤖 [TitleGeneration] LLM service initialized")
        
        # 제목 생성 프롬프트
        prompt = f"""
다음 사용자 메시지를 바탕으로 간단하고 명확한 채팅방 제목을 생성해주세요.

사용자 메시지: "{request.message}"

요구사항:
- 20자 이내로 간결하게 작성
- 메시지의 핵심 주제를 반영
- 한국어로 작성
- 불필요한 수식어나 인사말 제외
- 질문의 핵심만 추출

제목만 출력하고 다른 설명은 포함하지 마세요.
 
추가 규칙:
- 입력 전처리: 앞뒤 공백과 불필요한 특수문자(예: ~, !, ?, 이모지)를 제거한 텍스트를 기준으로 판단하세요.
- 길이 규칙:
  - 처리 기준 텍스트 길이가 5자 이하이면: 제목 = 처리 기준 텍스트 + " 채팅방"
    예: "안녕" -> "안녕 채팅방", "반가워요~" -> "반가워요 채팅방"
  - 처리 기준 텍스트 길이가 6자 이상이면: 원문을 그대로 쓰지 말고, 핵심 주제로 간단히 변환한 제목으로 작성하세요. 원문과 동일하거나 거의 동일한 표현 금지.
- 공통 규칙:
  - 12자 이내
  - 한국어
  - 불필요한 수식어·인사말 제외
  - 제목만 출력(따옴표·부가설명 금지)

예시:
- 입력: "안녕" -> 출력: 안녕 채팅방
- 입력: "반가워요~" -> 출력: 반가워요 채팅방
- 입력: "오늘 회의 아젠다 정리 부탁해" -> 출력: 회의 아젠다
- 입력: "마우스는 무슨 역할을 하나요?" -> 출력: 마우스의 역할
"""
        
        logger.info("📝 [TitleGeneration] Calling LLM with prompt", prompt_length=len(prompt))
        
        # LLM 호출 (제목 생성 전용 메서드 사용)
        response = await llm_service.generate_title(
            message=request.message,
            max_tokens=50,
            temperature=0.3
        )
        
        logger.info("🤖 [TitleGeneration] LLM response received", 
                   response_length=len(response) if response else 0,
                   response_preview=response[:100] if response else "None")
        
        if response and response.strip():
            title = response.strip()
            
            logger.info("✅ [TitleGeneration] Chat title generated successfully", 
                       original_message=request.message[:50], 
                       generated_title=title)
            
            return TitleGenerationResponse(
                title=title,
                success=True
            )
        else:
            logger.warning("⚠️ [TitleGeneration] Empty response from LLM for title generation")
            return TitleGenerationResponse(
                title="새 대화",
                success=False,
                error_message="제목 생성에 실패했습니다."
            )
            
    except Exception as e:
        logger.error("❌ [TitleGeneration] Error generating chat title", error=str(e))
        return TitleGenerationResponse(
            title="새 대화",
            success=False,
            error_message=f"제목 생성 중 오류가 발생했습니다: {str(e)}"
        )
