"""
Azure OpenAI LLM Service for Search Response Generation
"""

import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime

import os
import sys

# Set comprehensive Pydantic compatibility mode before importing OpenAI
os.environ.setdefault('PYDANTIC_V1_COMPAT', '1')
os.environ.setdefault('PYDANTIC_V1', '1')

# Suppress Pydantic warnings globally
import warnings
warnings.filterwarnings("ignore", message="Field .* has conflict with protected namespace")
warnings.filterwarnings("ignore", message="Fields must not use names with leading underscores")

from openai import AzureOpenAI

from app.config import settings
from app.prompts import (
    MULTI_DEPT_HINT,
    SYSTEM_PROMPT,
    ATTACHMENTS_HINT,
    INSTRUCTION_CONTEXT_DEP,
    INSTRUCTION_DEFAULT,
)
from app.core.mem0_client import Mem0Service

logger = logging.getLogger(__name__)


class AzureLLMService:
    """Azure OpenAI LLM service for generating responses from search results"""
    
    def __init__(self):
        self.client: Optional[AzureOpenAI] = None
        self.deployment_name = "gpt-4.1-mini"
        self.model_name = "gpt-4.1-mini"
        self.initialized = False
        
        self.mem0_service: Optional[Mem0Service] = None
        if settings.MEM0_ENABLED:
            try:
                self.mem0_service = Mem0Service(base_url=settings.MEM0_BASE_URL)
            except Exception as e:
                logger.warning(f"Failed to initialize Mem0 service: {e}")
                self.mem0_service = None
    
    async def initialize(self) -> bool:
        """Initialize Azure OpenAI client"""
        
        if self.initialized:
            return True
        
        try:
            import warnings
            warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

            self.client = AzureOpenAI(
                api_key=settings.OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
            )

            test_response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )

            if test_response.choices and len(test_response.choices) > 0:
                self.initialized = True
                return True
            else:
                raise Exception("No completion data returned from test")

        except Exception as e:
            logger.error(f"Failed to initialize Azure LLM service: {e}")
            if "pydantic" in str(e).lower() or "__pydantic" in str(e):
                try:
                    os.environ['PYDANTIC_V1'] = '1'
                    import importlib
                    import openai
                    importlib.reload(openai)

                    self.client = AzureOpenAI(
                        api_key=settings.OPENAI_API_KEY,
                        api_version=settings.AZURE_OPENAI_API_VERSION,
                        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
                    )

                    test_response = self.client.chat.completions.create(
                        model=self.deployment_name,
                        messages=[{"role": "user", "content": "Hello"}],
                        max_tokens=10
                    )

                    if test_response.choices and len(test_response.choices) > 0:
                        self.initialized = True
                        return True
                except Exception as fallback_error:
                    logger.error(f"Fallback approach also failed: {fallback_error}")

            raise Exception(f"Azure LLM initialization failed: {e}")
    
    def _is_context_dependent_question(self, query: str) -> bool:
        """Check if the query is context-dependent (refers to previous conversation)"""
        query_lower = query.lower().strip()
        
        context_patterns = [
            # Pronouns
            "그거", "그것", "그게", "그건", "그건가", "저거", "저것", "이거", "이것",
            # Temporal references
            "방금", "이전에", "전에", "아까", "조금 전", "앞에서",
            # Question patterns
            "어떻게", "어떻게 해야", "어떻게 해야되는데", "어떻게 해야 하는데",
            "뭐물어봤", "뭐물어봤더라", "뭐물어봤지", "뭐물어봤어",
            "뭐했", "뭐했더라", "뭐했지", "뭐했어",
            "뭐말했", "뭐말했더라", "뭐말했지", "뭐말했어",
            "뭐대화했", "뭐대화했더라", "뭐대화했지", "뭐대화했어",
            # References
            "그 질문", "그 답변", "그 내용", "그 정보",
            # Numbered references
            "번", "첫 번째", "두 번째", "세 번째", "마지막",
            # Repetition
            "다시", "다시 말해", "다시 설명", "다시 알려",
            # Memory issues
            "잊었", "기억 안나", "기억이 안나", "모르겠",
            "뭐였", "뭐였더라", "뭐였지", "뭐였어"
        ]
        
        return any(pattern in query_lower for pattern in context_patterns)

    async def generate_response_with_context(
        self, 
        query: str, 
        search_results: List[Dict[str, Any]], 
        chat_context: Optional[Dict[str, Any]] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        searched_collections: Optional[List[str]] = None,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        active_collection: Optional[str] = None
    ) -> str:
        """Generate a response based on search results, user query, and chat context"""


        if not self.initialized:
            logger.info("Initializing Azure LLM service...")
            init_result = await self.initialize()
            logger.info(f"Initialization result: {init_result}")

        if not query.strip():
            logger.warning("Empty query provided")
            return "질문을 해주셔야 답변을 드릴 수 있습니다."

        try:
            memory_context = ""
            if self.mem0_service and user_id and session_id:
                try:
                    combined_memories = await self.mem0_service.search_combined_memories(
                        query=query,
                        user_id=user_id,
                        session_id=session_id,
                        user_limit=settings.MEM0_USER_MEMORY_LIMIT,
                        session_limit=settings.MEM0_SESSION_MEMORY_LIMIT
                    )
                    
                    if combined_memories.get("user_memories"):
                        user_memories_list = []
                        for memory in combined_memories["user_memories"]:
                            if isinstance(memory, dict):
                                memory_text = memory.get("memory", "")
                                if memory_text:
                                    user_memories_list.append(f"- {memory_text}")
                        
                        if user_memories_list:
                            memory_context += f"\n\n📝 사용자 개인 정보 (장기 기억):\n" + "\n".join(user_memories_list)
                    
                    if combined_memories.get("session_memories"):
                        session_memories_list = []
                        for memory in combined_memories["session_memories"]:
                            if isinstance(memory, dict):
                                memory_text = memory.get("memory", "")
                                if memory_text:
                                    session_memories_list.append(f"- {memory_text}")
                        
                        if session_memories_list:
                            memory_context += f"\n\n💭 이번 대화 맥락 (단기 기억):\n" + "\n".join(session_memories_list)
                        
                except Exception as e:
                    logger.warning(f"Failed to search Mem0 memories: {e}")
                    memory_context = ""
            
            # Prepare context from search results
            context_parts = []
            has_search_results = search_results and len(search_results) > 0
            
            if has_search_results:
                for i, result in enumerate(search_results[:5], 1):  # Limit to top 5 results
                    content = result.get('content', '')
                    source = result.get('source_file', 'Unknown source')
                    score = result.get('score', 0.0)
                    
                    context_parts.append(f"Source {i} (from {source}, relevance: {score:.2f}):\n{content}\n")

            search_context = "\n".join(context_parts) if context_parts else ""

            chat_history = []
            context_summary = ""
            current_department = None
            
            if chat_context:
                chat_history_raw = chat_context.get("chat_history", [])
                if chat_history_raw and isinstance(chat_history_raw, list):
                    # Limit to exactly 3 turns (6 messages: 3 user + 3 assistant)
                    # Take the last 6 messages to ensure we have the most recent context
                    limited_history = chat_history_raw[-6:] if len(chat_history_raw) > 6 else chat_history_raw
                    for msg in limited_history:
                        if isinstance(msg, dict) and "role" in msg and "content" in msg:
                            chat_history.append({
                                "role": msg["role"],
                                "content": msg["content"]
                            })
                
                context_summary = chat_context.get("context_summary", "")
                current_department = chat_context.get("current_department")

            system_prompt = SYSTEM_PROMPT
            is_context_dependent = self._is_context_dependent_question(query)
            
            # Build user prompt with context
            user_prompt_parts = [f"사용자 메시지: {query}"]
            
            # 첨부된 텍스트/코드 스니펫이 있으면 사용자 메시지 바로 다음에 포함 (명확성을 위해)
            attachments_text = []
            if chat_context:
                try:
                    attachments_text = chat_context.get("attachments_text", []) or []
                    logger.info(f"Found attachments_text in chat_context: {len(attachments_text)} items")
                except Exception as e:
                    logger.warning(f"Failed to extract attachments_text from chat_context: {e}")
                    attachments_text = []

            if attachments_text:
                try:
                    # Build a concise attached context block
                    attached_parts = []
                    file_names = []
                    for att in attachments_text[:5]:
                        name = att.get('name', 'attachment') if isinstance(att, dict) else 'attachment'
                        snippet = att.get('snippet', '') if isinstance(att, dict) else ''
                        if snippet:
                            file_names.append(name)
                            attached_parts.append(f"[파일: {name}]\n{snippet[:2000]}")
                    if attached_parts:
                        files_str = ", ".join(file_names)
                        user_prompt_parts.append(f"\n사용자가 다음 파일을 첨부했습니다: {files_str}")
                        user_prompt_parts.append("\n첨부된 파일 내용:\n" + "\n\n".join(attached_parts))
                        user_prompt_parts.append("\n" + ATTACHMENTS_HINT)
                except Exception:
                    pass
            
            if context_summary:
                user_prompt_parts.append(f"\n이전 대화 요약:\n{context_summary}")
            
            # Add memory context from Mem0 (user preferences and session memories)
            if memory_context:
                user_prompt_parts.append(memory_context)
            
            # For context-dependent questions, rely on mem0 session memories for context
            # Mem0 session memories should contain recent conversation context
            if is_context_dependent and current_department:
                user_prompt_parts.append(f"\n중요 참고: 현재 질문은 {current_department} 컬렉션에 대한 것입니다. '그것', '저것', '그거' 등의 표현은 이 컬렉션의 내용을 가리킵니다.")

            if search_context:
                user_prompt_parts.append(f"\n지식베이스 검색 결과 (관련성이 있을 수도 없을 수도 있음):\n{search_context}")
            elif active_collection:
                user_prompt_parts.append(
                    "\n지식베이스 검색 결과: 해당 컬렉션에서 관련 정보를 찾지 못했습니다. "
                    "응답을 '관련 정보를 찾지 못했습니다'라는 문장으로 시작하고, 필요한 경우 후속 질문이나 다음 단계만 제안하세요."
                )
            
            # Add multi-department hint if multiple collections were searched
            if searched_collections and len(searched_collections) > 1:
                collections_str = ", ".join(searched_collections)
                user_prompt_parts.append(f"\n{MULTI_DEPT_HINT.format(collections=collections_str)}")
            
            # Enhanced instruction for context-dependent questions
            instruction_block = INSTRUCTION_CONTEXT_DEP if is_context_dependent else INSTRUCTION_DEFAULT
            user_prompt_parts.append("\n" + instruction_block)

            user_prompt = "\n".join(user_prompt_parts)

            # Build messages array with sliding window chat history
            messages = [{"role": "system", "content": system_prompt}]
            
            if chat_history:
                messages.extend(chat_history)
            
            messages.append({"role": "user", "content": user_prompt})
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )

            if response.choices and len(response.choices) > 0:
                generated_text = response.choices[0].message.content
                
                if self.mem0_service and user_id and session_id and generated_text:
                    try:
                        response_len_check = len(generated_text) > 200
                        keyword_check = any(keyword in query.lower() for keyword in ['좋아', '싫어', '선호', '취향', '습관'])
                        auto_save_check = settings.MEM0_AUTO_SAVE_IMPORTANT
                        
                        is_important = (
                            response_len_check or
                            keyword_check or
                            auto_save_check
                        )
                        
                        await self.mem0_service.add_conversation_memory(
                            query=query,
                            response=generated_text,
                            user_id=user_id,
                            session_id=session_id,
                            is_important=is_important
                        )
                    except Exception as e:
                        logger.warning(f"Failed to save conversation to memory: {e}")
                
                return generated_text
            else:
                logger.error("No completion data returned from Azure")
                raise Exception("No completion data returned")

        except Exception as e:
            logger.error(f"Response generation with context failed: {e}")
            # Safe fallback on Azure content filter or Responsible AI violations
            err = str(e).lower()
            if "content_filter" in err or "responsibleaipolicyviolation" in err:
                try:
                    logger.warning("Content filter triggered. Retrying with safe minimal prompt...")
                    safe_system = "당신은 한국어 어시스턴트입니다. 안전하고 존중하는 표현으로 간단히 안내합니다."
                    safe_user = (
                        f"사용자 메시지: {query}\n\n"
                        "작업: 현재 메시지에 대해 간단하고 안전한 범위에서 답변하세요."
                    )
                    safe_resp = self.client.chat.completions.create(
                        model=self.deployment_name,
                        messages=[
                            {"role": "system", "content": safe_system},
                            {"role": "user", "content": safe_user},
                        ],
                        max_tokens=min(400, max_tokens),
                        temperature=min(0.4, max(0.2, temperature)),
                    )
                    if safe_resp.choices and len(safe_resp.choices) > 0:
                        return safe_resp.choices[0].message.content
                except Exception as safe_ex:
                    logger.error(f"Safe retry failed: {safe_ex}")
                return "죄송합니다. 해당 요청이 정책에 의해 제한되었습니다. 다른 표현으로 다시 시도해 주세요."
            raise Exception(f"Failed to generate response: {e}")

    async def generate_streaming_response_with_context(
        self, 
        query: str, 
        context_results: List[Any], 
        chat_context: Optional[Dict[str, Any]] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        searched_collections: Optional[List[str]] = None,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response based on search results, user query, and chat context"""

        if not self.initialized:
            await self.initialize()

        if not query.strip():
            logger.warning("Empty query provided")
            yield "질문을 해주셔야 답변을 드릴 수 있습니다."
            return
        
        if not context_results:
            logger.warning("No search results provided")
            yield "죄송합니다. 질문에 대한 관련 정보를 찾을 수 없습니다."
            return
        
        try:
            memory_context = ""
            if self.mem0_service and user_id and session_id:
                try:
                    combined_memories = await self.mem0_service.search_combined_memories(
                        query=query,
                        user_id=user_id,
                        session_id=session_id,
                        user_limit=settings.MEM0_USER_MEMORY_LIMIT,
                        session_limit=settings.MEM0_SESSION_MEMORY_LIMIT
                    )
                    
                    if combined_memories.get("user_memories"):
                        user_memories_list = []
                        for memory in combined_memories["user_memories"]:
                            if isinstance(memory, dict):
                                memory_text = memory.get("memory", "")
                                if memory_text:
                                    user_memories_list.append(f"- {memory_text}")
                        
                        if user_memories_list:
                            memory_context += f"\n\n📝 사용자 개인 정보 (장기 기억):\n" + "\n".join(user_memories_list)
                    
                    if combined_memories.get("session_memories"):
                        session_memories_list = []
                        for memory in combined_memories["session_memories"]:
                            if isinstance(memory, dict):
                                memory_text = memory.get("memory", "")
                                if memory_text:
                                    session_memories_list.append(f"- {memory_text}")
                        
                        if session_memories_list:
                            memory_context += f"\n\n💭 이번 대화 맥락 (단기 기억):\n" + "\n".join(session_memories_list)
                        
                except Exception as e:
                    logger.warning(f"Failed to search Mem0 memories: {e}")
                    memory_context = ""
            
            # Prepare context from search results
            context_parts = []
            for i, result in enumerate(context_results):
                if hasattr(result, 'content'):
                    content = result.content
                    source = getattr(result, 'source_file', f'Result {i+1}')
                    context_parts.append(f"[Source: {source}]\n{content}")
                elif isinstance(result, dict):
                    content = result.get('content', '')
                    source = result.get('source_file', f'Result {i+1}')
                    context_parts.append(f"[Source: {source}]\n{content}")
                else:
                    context_parts.append(f"[Result {i+1}]\n{str(result)}")

            search_context = "\n".join(context_parts)

            # Extract chat history for sliding window context
            chat_history = []
            context_summary = ""
            current_department = None
            
            if chat_context:
                chat_history_raw = chat_context.get("chat_history", [])
                if chat_history_raw and isinstance(chat_history_raw, list):
                    # Limit to exactly 3 turns (6 messages: 3 user + 3 assistant)
                    # Take the last 6 messages to ensure we have the most recent context
                    limited_history = chat_history_raw[-6:] if len(chat_history_raw) > 6 else chat_history_raw
                    for msg in limited_history:
                        if isinstance(msg, dict) and "role" in msg and "content" in msg:
                            chat_history.append({
                                "role": msg["role"],
                                "content": msg["content"]
                            })
                
                context_summary = chat_context.get("context_summary", "")
                current_department = chat_context.get("current_department")

            # Create the enhanced prompt
            system_prompt = """당신은 친근하고 도움이 되는 AI 어시스턴트입니다. 모든 응답은 한국어로 자연스럽게 해주세요.

응답 방식:
1. 현재 사용자 메시지를 가장 우선으로 직접적으로 답하세요
2. 이전 대화 맥락은 보조 컨텍스트로만 사용하세요 (필요 시)
3. 검색 결과가 사용자 질문과 관련이 있는지 먼저 판단하세요
4. 관련성이 있다면 검색 결과를 바탕으로 도움이 되는 설명을 제공하세요
5. 관련성이 없다면 검색 결과를 무시하고 자연스럽게 대화하세요
6. 인사나 일반 대화에는 따뜻하고 친근하게 응답하세요
7. 기술적 질문에는 명확하고 이해하기 쉽게 설명하세요
8. 원시 데이터를 그대로 붙여넣지 말고 사용자가 이해할 수 있도록 설명하세요

중요: 
- 사용자의 실제 질문에 먼저 집중하세요. 검색 결과와 이전 대화는 참고용입니다.
- 인사나 일반 대화에는 검색 결과를 사용하지 마세요.
- 사용자가 원하는 것이 무엇인지 먼저 파악하세요."""

            # Check if query is context-dependent
            is_context_dependent = self._is_context_dependent_question(query)
            
            # Build user prompt with context
            user_prompt_parts = [f"사용자 메시지: {query}"]
            
            # 첨부된 텍스트/코드 스니펫이 있으면 사용자 메시지 바로 다음에 포함 (명확성을 위해)
            attachments_text = []
            if chat_context:
                try:
                    attachments_text = chat_context.get("attachments_text", []) or []
                    logger.info(f"Found attachments_text in chat_context: {len(attachments_text)} items")
                except Exception as e:
                    logger.warning(f"Failed to extract attachments_text from chat_context: {e}")
                    attachments_text = []

            if attachments_text:
                try:
                    attached_parts = []
                    file_names = []
                    for att in attachments_text[:5]:
                        name = att.get('name', 'attachment') if isinstance(att, dict) else 'attachment'
                        snippet = att.get('snippet', '') if isinstance(att, dict) else ''
                        if snippet:
                            file_names.append(name)
                            attached_parts.append(f"[파일: {name}]\n{snippet[:2000]}")
                    if attached_parts:
                        files_str = ", ".join(file_names)
                        user_prompt_parts.append(f"\n사용자가 다음 파일을 첨부했습니다: {files_str}")
                        user_prompt_parts.append("\n첨부된 파일 내용:\n" + "\n\n".join(attached_parts))
                        user_prompt_parts.append("\n지침: 첨부 자료는 참고용입니다. 현재 사용자 질문에 우선 직접 답변하세요. 첨부 내용이 도움이 될 때만 요점 위주로 반영하고, 관련성이 약하면 과감히 무시하세요.")
                except Exception:
                    pass
            
            if context_summary:
                user_prompt_parts.append(f"\n이전 대화 요약:\n{context_summary}")
            
            # Add memory context from Mem0 (user preferences and session memories)
            if memory_context:
                user_prompt_parts.append(memory_context)
            
            # For context-dependent questions, rely on mem0 session memories for context
            # Mem0 session memories should contain recent conversation context
            if is_context_dependent and current_department:
                user_prompt_parts.append(f"\n중요 참고: 현재 질문은 {current_department} 컬렉션에 대한 것입니다. '그것', '저것', '그거' 등의 표현은 이 컬렉션의 내용을 가리킵니다.")

            if search_context:
                user_prompt_parts.append(f"\n지식베이스 검색 결과 (관련성이 있을 수도 없을 수도 있음):\n{search_context}")
            
            # Add multi-department hint if multiple collections were searched
            if searched_collections and len(searched_collections) > 1:
                collections_str = ", ".join(searched_collections)
                user_prompt_parts.append(f"\n{MULTI_DEPT_HINT.format(collections=collections_str)}")
            
            # Enhanced instruction for context-dependent questions
            instruction_block = INSTRUCTION_CONTEXT_DEP if is_context_dependent else INSTRUCTION_DEFAULT
            user_prompt_parts.append("\n" + instruction_block)

            user_prompt = "\n".join(user_prompt_parts)

            # Build messages array with sliding window chat history
            messages = [{"role": "system", "content": system_prompt}]
            
            if chat_history:
                messages.extend(chat_history)
            
            messages.append({"role": "user", "content": user_prompt})
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True
            )

            # Stream the response chunks
            async for chunk in response:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        yield delta.content
            
            # Note: Memory saving is handled in the route handler after streaming completes
            # to avoid blocking the streaming response or sending data after connection closes
            # The route handler accumulates the full response and saves it in a background task

        except Exception as e:
            logger.error(f"Streaming response generation with context failed: {e}")
            yield f"죄송합니다. 응답 생성 중 오류가 발생했습니다: {str(e)}"

    async def generate_response(
        self, 
        query: str, 
        search_results: List[Dict[str, Any]], 
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """Generate a response based on search results and user query"""

        logger.info(f"generate_response called with query: '{query}', results_count: {len(search_results)}, initialized: {self.initialized}")

        if not self.initialized:
            logger.info("Initializing Azure LLM service...")
            init_result = await self.initialize()
            logger.info(f"Initialization result: {init_result}")

        if not query.strip():
            logger.warning("Empty query provided")
            return "질문을 해주셔야 답변을 드릴 수 있습니다."

        try:
            # Prepare context from search results
            context_parts = []
            has_search_results = search_results and len(search_results) > 0
            
            if has_search_results:
                for i, result in enumerate(search_results[:5], 1):  # Limit to top 5 results
                    content = result.get('content', '')
                    source = result.get('source_file', 'Unknown source')
                    score = result.get('score', 0.0)
                    
                    context_parts.append(f"Source {i} (from {source}, relevance: {score:.2f}):\n{content}\n")

            context = "\n".join(context_parts) if context_parts else ""

            # Create the prompt with different messages based on search results
            if not has_search_results:
                # No search results - pure conversational mode
                system_prompt = """당신은 친근하고 도움이 되는 AI 어시스턴트입니다. 모든 응답은 한국어로 자연스럽게 해주세요.

응답 방식:
1. 사용자의 의도를 정확히 파악하세요
2. 인사나 일반 대화에는 따뜻하고 친근하게 응답하세요
3. 기술적 질문에는 명확하고 이해하기 쉽게 설명하세요
4. 특정 기술 문서나 데이터베이스에 접근할 수 없는 경우, 일반적인 지식을 바탕으로 답변하세요

중요: 
- 자연스럽고 친근한 대화를 유지하세요.
- 사용자가 원하는 것이 무엇인지 먼저 파악하고 도움을 제공하세요."""

                user_prompt = f"""사용자 메시지: {query}

작업: 사용자의 메시지에 자연스럽고 친근하게 응답하세요. 대화하듯이 따뜻하고 도움이 되도록 응답하세요."""
            else:
                # Has search results - RAG mode
                system_prompt = """당신은 도움이 되는 AI 어시스턴트입니다. 모든 응답은 한국어로 해주세요.

응답 방식:
1. 사용자의 질문을 정확히 이해하세요
2. 검색 결과가 관련성이 있는지 확인하세요
3. 관련성이 있다면 검색 결과를 바탕으로 명확한 설명을 제공하세요
4. 관련성이 없다면 (인사, 일반 대화 등) 자연스럽게 응답하세요
5. 자연스러운 대화처럼 직접적으로 답변하세요
6. 원시 데이터를 그대로 붙여넣지 말고 이해하기 쉬운 용어로 설명하세요
7. 실제로 사용한 정보에 대해서만 출처를 인용하세요

중요: 검색 결과가 항상 사용자의 메시지와 관련이 있는 것은 아닙니다. 판단력을 사용하여 관련 없는 정보를 억지로 응답에 포함시키지 마세요."""

                user_prompt = f"""사용자 메시지: {query}

지식베이스 검색 결과 (참고용):

{context}

작업: 사용자의 메시지에 자연스럽고 친근하게 응답하세요. 검색 결과가 사용자 질문과 관련 있고 도움이 된다면 그것을 바탕으로 답변하세요. 관련이 없다면 (예: 인사, 일반 대화) 검색 결과를 무시하고 사용자가 원하는 대로 응답하세요. 대화하듯이 따뜻하고 도움이 되도록 응답하세요."""

            logger.info(f"Creating completion with model: {self.deployment_name}")
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )

            if response.choices and len(response.choices) > 0:
                generated_text = response.choices[0].message.content
                return generated_text
            else:
                logger.error("No completion data returned from Azure")
                raise Exception("No completion data returned")

        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            raise Exception(f"Failed to generate response: {e}")
    
    async def generate_streaming_response(
        self, 
        query: str, 
        context_results: List[Any], 
        max_tokens: int = 1000,
        temperature: float = 0.7
    ):
        """Generate a streaming response based on search results and user query"""
        
        if not self.initialized:
            await self.initialize()
        
        if not query.strip():
            logger.warning("Empty query provided")
            yield "질문을 해주셔야 답변을 드릴 수 있습니다."
            return
        
        if not context_results:
            logger.warning("No search results provided")
            yield "죄송합니다. 질문에 대한 관련 정보를 찾을 수 없습니다."
            return
        
        try:
            # Prepare context from search results
            context_parts = []
            for i, result in enumerate(context_results):
                if hasattr(result, 'content'):
                    content = result.content
                    source = getattr(result, 'source_file', f'Result {i+1}')
                    context_parts.append(f"[Source: {source}]\n{content}")
                elif isinstance(result, dict):
                    content = result.get('content', '')
                    source = result.get('source_file', f'Result {i+1}')
                    context_parts.append(f"[Source: {source}]\n{content}")
            
            context = "\n\n".join(context_parts)
            
            # Create system prompt
            system_prompt = """당신은 친근하고 도움이 되는 AI 어시스턴트입니다. 모든 응답은 한국어로 자연스럽게 해주세요.
            사용자의 질문에 맞는 답변을 제공하세요.
            주어진 맥락이 관련이 있다면 그것을 바탕으로 설명하세요.
            맥락이 관련이 없다면 자연스럽게 대화하세요.
            따뜻하고 친근한 톤으로 응답하세요."""
            
            # Create user prompt
            user_prompt = f"""참고 맥락:
{context}

질문: {query}

위의 맥락이 질문과 관련이 있다면 그것을 바탕으로 도움이 되는 답변을 제공해 주세요. 관련이 없다면 자연스럽게 대화해 주세요."""
            
            logger.info(f"Creating streaming completion with model: {self.deployment_name}")
            
            # Create streaming completion
            stream = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True
            )
            
            # Stream the response
            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        yield delta.content
            
            logger.info("Streaming response completed successfully")
            
        except Exception as e:
            logger.error(f"Streaming response generation failed: {e}")
            yield f"죄송합니다. 응답 생성 중 오류가 발생했습니다: {str(e)}"
    
    async def generate_title(self, message: str, max_tokens: int = 50, temperature: float = 0.3) -> str:
        """Generate a chat title from user message"""
        
        if not self.initialized or not self.client:
            raise Exception("Azure LLM service not initialized")
        
        try:
            logger.info(f"Generating title for message: {message[:50]}...")
            
            # 제목 생성 프롬프트
            prompt = f"""
다음 사용자 메시지를 바탕으로 간단하고 명확한 채팅방 제목을 생성해주세요.

사용자 메시지: "{message}"

요구사항:
- 12자 이내로 간결하게 작성
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
            
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            if response.choices and len(response.choices) > 0:
                title = response.choices[0].message.content.strip()
                
                # 제목 길이 제한 (12자) - 단어 경계에서 자르기
                if len(title) > 12:
                    # 12자 이내에서 마지막 공백 찾기
                    lastSpaceIndex = title.rfind(' ', 0, 12)
                    if lastSpaceIndex > 0:
                        title = title[:lastSpaceIndex]
                    else:
                        # 공백이 없으면 12자로 자르기
                        title = title[:12]
                
                logger.info(f"Title generated successfully: {title}")
                return title
            else:
                logger.warning("No response from LLM for title generation")
                return "새 대화"
                
        except Exception as e:
            logger.error(f"Title generation failed: {e}")
            return "새 대화"
    
    async def close(self):
        """Clean up resources"""
        if self.client:
            # Azure OpenAI client doesn't need explicit cleanup
            self.client = None
            self.initialized = False
            logger.info("Azure LLM service closed")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "service": "azure_openai",
            "deployment": self.deployment_name,
            "model": self.model_name,
            "initialized": self.initialized
        }


