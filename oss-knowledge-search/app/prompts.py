"""
Centralized prompt strings and helpers for LLM interactions.
"""

from typing import List, Dict, Any, Optional

# Hints / notices
MULTI_DEPT_HINT = (
    "참고: 본 답변은 다음 부서의 자료를 함께 고려합니다: {collections}. "
    "질문의 주된 목적을 우선하여 가장 관련 있는 부서 정보를 중심으로 정리하세요."
)

ATTACHMENTS_HINT = (
    "지침: 첨부 자료는 참고용입니다. 현재 사용자 질문에 우선 직접 답변하세요. "
    "첨부 내용이 도움이 될 때만 요점 위주로 반영하고, 관련성이 약하면 과감히 무시하세요."
)


# System prompt (single source of truth)
SYSTEM_PROMPT = """당신은 친근하고 도움이 되는 AI 어시스턴트입니다. 모든 응답은 한국어로 자연스럽게 해주세요.

응답 방식:
1. 현재 사용자 메시지를 가장 우선으로 직접적으로 답하세요
2. 이전 대화 맥락은 보조 컨텍스트로만 사용하세요 (필요 시)
3. 검색 결과가 사용자 질문과 관련이 있는지 먼저 판단하세요
4. 관련성이 있다면 검색 결과를 바탕으로 도움이 되는 설명을 제공하세요
5. 관련성이 없다면 검색 결과를 무시하고 자연스럽게 대화하세요
6. 인사나 일반 대화에는 따뜻하고 친근하게 응답하세요
7. 기술적 질문에는 명확하고 이해하기 쉽게 설명하세요
8. 원시 데이터를 그대로 붙여넣지 말고 사용자가 이해할 수 있도록 설명하세요
9. 검색 결과가 비어 있거나 불명확하면 \"관련 자료를 찾지 못했다\"고 먼저 알리고, 추측하거나 임의로 만들어내지 마세요
10. 질문이 검색 범위와 무관한 소소한 대화일 경우 검색을 사용하지 말고 짧고 친근하게 응답하세요

중요: 
- 사용자의 실제 질문에 먼저 집중하세요. 검색 결과와 이전 대화는 참고용입니다.
- 인사나 일반 대화에는 검색 결과를 사용하지 마세요.
- 사용자가 원하는 것이 무엇인지 먼저 파악하세요."""


# Instruction blocks
INSTRUCTION_CONTEXT_DEP = (
    "작업: 사용자의 현재 메시지는 이전 대화를 참조하는 맥락 의존적 질문입니다. "
    "반드시 위의 대화 히스토리를 확인하여 이전에 논의된 내용을 파악하세요. "
    "'그것', '저것', '그거', '어떻게 해야되는데', '3번' 등의 표현은 이전 대화를 가리킵니다. "
    "가장 최근 어시스턴트 응답과 사용자 질문을 참조하여 일관성 있는 답변을 제공하세요. "
    "이전 대화 맥락 없이는 답변할 수 없는 질문이므로, 반드시 대화 히스토리를 활용하세요. "
    "검색 결과가 사용자 질문과 관련 있고 도움이 된다면 그것을 바탕으로 답변하세요. "
    "관련성이 낮거나 검색 결과가 비어 있다면 이전 대화 내용을 바탕으로 답변하세요."
)

INSTRUCTION_DEFAULT = (
    "작업: 사용자의 메시지에 자연스럽고 친근하게 응답하세요. 이전 대화 맥락을 고려하여 일관성 있는 답변을 제공하세요. "
    "검색 결과가 사용자 질문과 관련 있고 도움이 된다면 그것을 바탕으로 답변하세요. 관련성이 낮거나 검색 결과가 비어 있다면 "
    "사용자가 이해할 수 있도록 솔직하게 부족한 점을 설명하고 필요한 후속 질문을 던지세요."
)


def build_user_prompt(
    query: str,
    context_summary: str = "",
    chat_history_text: str = "",
    most_recent_assistant: Optional[str] = None,
    search_context: str = "",
    attachments_text: Optional[List[Dict[str, str]]] = None,
    is_context_dependent: bool = False,
    searched_collections: Optional[List[str]] = None,
) -> str:
    """
    Assemble a user prompt from provided parts in a consistent order.
    The caller is responsible for pre-trimming long fields.
    """
    parts: List[str] = []
    parts.append(f"사용자 메시지: {query}")

    # Attached text/code snippets - placed immediately after user message for clarity
    if attachments_text:
        attached_blocks: List[str] = []
        file_names = []
        for att in attachments_text[:5]:
            try:
                name = att.get("name", "attachment")
                snippet = att.get("snippet", "")
                if snippet:
                    file_names.append(name)
                    attached_blocks.append(f"[파일: {name}]\n{snippet[:2000]}")
            except Exception:
                continue
        if attached_blocks:
            files_str = ", ".join(file_names)
            parts.append(f"\n사용자가 다음 파일을 첨부했습니다: {files_str}")
            parts.append("\n첨부된 파일 내용:\n" + "\n\n".join(attached_blocks))
            parts.append("\n" + ATTACHMENTS_HINT)

    if context_summary:
        parts.append(f"\n이전 대화 요약:\n{context_summary}")

    if chat_history_text:
        parts.append(f"\n최근 대화:\n{chat_history_text}")
        if is_context_dependent and most_recent_assistant:
            topic_preview = most_recent_assistant[:100].replace("\n", " ").strip()
            parts.append(
                f"\n중요 참고: 이전 대화에서 가장 최근에 언급한 주제는 '{topic_preview}...' 입니다. "
                f"'그것', '저것', '그거' 등의 표현은 이 주제를 가리킵니다."
            )

    # Multi-dept hint
    if searched_collections and len(searched_collections) > 1:
        parts.append("\n" + MULTI_DEPT_HINT.format(collections=", ".join(searched_collections)))

    if search_context:
        parts.append(f"\n지식베이스 검색 결과 (관련성이 있을 수도 없을 수도 있음):\n{search_context}")

    # Instruction block
    parts.append("\n" + (INSTRUCTION_CONTEXT_DEP if is_context_dependent else INSTRUCTION_DEFAULT))

    return "\n".join(parts)


