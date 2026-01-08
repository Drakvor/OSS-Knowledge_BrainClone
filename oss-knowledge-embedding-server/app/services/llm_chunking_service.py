"""
LLM Chunking Service
Service for using Azure OpenAI to suggest optimal chunk boundaries for markdown documents
"""

import json
import logging
import time
from typing import List, Dict, Any
from openai import AzureOpenAI
from app.config import settings
from app.processors.markdown.markdown_models import LLMChunkSuggestion
from app.prompts.chunking_prompts import MARKDOWN_CHUNKING_SYSTEM_PROMPT, MARKDOWN_CHUNKING_USER_PROMPT

logger = logging.getLogger(__name__)


class LLMChunkingService:
    """Service for LLM-based chunking suggestions"""
    
    def __init__(self):
        """Initialize the LLM chunking service with Azure OpenAI client"""
        self.client = AzureOpenAI(
            api_key=settings.OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.temperature = settings.OPENAI_TEMPERATURE
        self._last_raw_response = None  # For debugging failed responses
    
    async def suggest_chunks(self, markdown_content: str) -> List[LLMChunkSuggestion]:
        """
        Get LLM suggestions for chunk boundaries
        
        Args:
            markdown_content: The markdown document content to analyze
            
        Returns:
            List of LLMChunkSuggestion objects with suggested chunk boundaries
            
        Raises:
            Exception: If LLM API call fails or response is invalid
        """
        try:
            # Adaptive content sampling based on size
            processed_content = self._prepare_content_for_llm(markdown_content)
            
            # Prepare the prompt with document length
            document_length = len(markdown_content)  # Original document length, not processed
            user_prompt = MARKDOWN_CHUNKING_USER_PROMPT.format(
                document_length=document_length,
                document_content=processed_content
            )
            
            # Calculate dynamic max_tokens based on content size
            input_tokens = len(user_prompt) // 4  # Rough token estimation
            
            # Very generous tokens for GPT-4.1-mini (128K context window)
            if len(processed_content) > 50000:  # Large content
                response_tokens = 32000  # Very generous
            elif len(processed_content) > 20000:  # Medium content  
                response_tokens = 24000  # Very generous
            else:  # Small content
                response_tokens = 16000  # Very generous for small files
            
            # Use higher limit for GPT-4.1-mini
            max_tokens_to_use = min(32000, response_tokens)  # Much higher limit
            logger.info(f"LLM 청킹 시작: 문서 {len(processed_content)}자, max_tokens: {max_tokens_to_use}")
            
            # Call Azure OpenAI with enhanced parameters
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": MARKDOWN_CHUNKING_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=max_tokens_to_use,
                temperature=self.temperature,
                response_format={"type": "json_object"}  # Force JSON response
            )
            
            # Extract response content
            response_content = response.choices[0].message.content
            
            # Check if response looks truncated
            is_truncated = not response_content.strip().endswith('}')
            if is_truncated:
                logger.error(f"⚠️ LLM 응답 잘림 감지 (길이: {len(response_content)}자, max_tokens: {max_tokens_to_use})")
            
            # Save full response for debugging when errors occur
            self._last_raw_response = response_content
            
            # Parse JSON response - enhanced parsing logic
            response_data = self._parse_llm_response(response_content)
            
            # Validate response structure
            if "chunks" not in response_data:
                raise Exception("LLM 응답에 'chunks' 필드가 없습니다.")
            
            chunks_data = response_data["chunks"]
            if not isinstance(chunks_data, list):
                raise Exception("LLM 응답의 'chunks' 필드가 배열이 아닙니다.")
            
            # Convert to LLMChunkSuggestion objects (LLM already returns cleaned content)
            suggestions = []
            for i, chunk_data in enumerate(chunks_data):
                try:
                    suggestion = LLMChunkSuggestion(
                        start_position=chunk_data.get("start_char", 0),
                        end_position=chunk_data.get("end_char", 0),
                        content=chunk_data.get("content", ""),  # LLM-cleaned content
                        reasoning=chunk_data.get("reasoning", "LLM 제안"),
                        semantic_score=0.9  # Default score
                    )
                    suggestions.append(suggestion)
                except Exception as e:
                    logger.warning(f"Failed to parse chunk {i}: {e}")
                    continue
            
            # Validate chunk boundaries
            self._validate_chunk_boundaries(suggestions, markdown_content)
            
            logger.info(f"✅ LLM 청킹 완료: {len(suggestions)}개 청크 생성")
            return suggestions
            
        except Exception as e:
            logger.error(f"LLM chunking service error: {str(e)}")
            raise Exception(f"LLM 청킹 제안 생성 중 오류가 발생했습니다: {str(e)}")
    
    def _parse_llm_response(self, response_content: str) -> Dict[str, Any]:
        """
        Parse LLM response with enhanced error handling and multiple parsing strategies
        
        Args:
            response_content: Raw LLM response content
            
        Returns:
            Parsed JSON data as dictionary
            
        Raises:
            Exception: If parsing fails after all attempts
        """
        import re
        
        # Parse JSON with minimal logging
        
        # Strategy 1: Try to parse as raw JSON
        try:
            return json.loads(response_content)
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Extract JSON from markdown code blocks
        try:
            json_match = re.search(r'```json\s*\n(.*?)\n```', response_content, re.DOTALL)
            if json_match:
                json_content = json_match.group(1).strip()
                return json.loads(json_content)
        except json.JSONDecodeError:
            pass
        
        # Strategy 3: Find first complete JSON object
        try:
            # Look for balanced braces
            start_idx = response_content.find('{')
            if start_idx != -1:
                brace_count = 0
                end_idx = start_idx
                
                for i, char in enumerate(response_content[start_idx:], start_idx):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i + 1
                            break
                
                if brace_count == 0:
                    json_content = response_content[start_idx:end_idx]
                    return json.loads(json_content)
        except json.JSONDecodeError:
            pass
        
        # Strategy 4: Try to extract partial JSON and complete it
        try:
            # Look for chunks array start
            chunks_match = re.search(r'"chunks"\s*:\s*\[(.*)', response_content, re.DOTALL)
            if chunks_match:
                chunks_content = chunks_match.group(1)
                # Try to find the end of the array
                array_end = self._find_array_end(chunks_content)
                if array_end:
                    json_str = '{"chunks": [' + array_end + ']'
                    return json.loads(json_str)
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # All parsing strategies failed
        logger.error(f"❌ JSON 파싱 실패 (응답 길이: {len(response_content)}자)")
        
        # Save failed response for debugging
        import time
        failed_response_file = f"/tmp/llm_failed_response_{int(time.time())}.txt"
        try:
            with open(failed_response_file, 'w', encoding='utf-8') as f:
                f.write(response_content)
            logger.error(f"실패한 응답을 저장했습니다: {failed_response_file}")
        except Exception:
            pass
        
        raise Exception("LLM 응답을 파싱할 수 없습니다. JSON 형식이 올바르지 않습니다.")
    
    def _find_array_end(self, content: str) -> str:
        """
        Try to find a valid end for a JSON array that might be truncated
        
        Args:
            content: Partial array content
            
        Returns:
            Valid array content or None
        """
        try:
            # Count brackets and braces to find balanced point
            bracket_count = 0
            brace_count = 0
            last_valid_pos = 0
            
            for i, char in enumerate(content):
                if char == '[':
                    bracket_count += 1
                elif char == ']':
                    bracket_count -= 1
                    if bracket_count == -1:  # Found array end
                        return content[:i]
                elif char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0 and bracket_count >= 0:
                        last_valid_pos = i + 1
            
            # If we didn't find a proper end, try to use the last valid object
            if last_valid_pos > 0:
                return content[:last_valid_pos]
                
        except Exception:
            pass
        
        return None
    
    # 텍스트 정제는 LLM이 직접 수행 - 더 지능적이고 컨텍스트 인식
    
    def _prepare_content_for_llm(self, markdown_content: str) -> str:
        """
        Adaptive content preparation based on file size
        
        Args:
            markdown_content: Original markdown content
            
        Returns:
            Processed content optimized for LLM analysis
        """
        content_length = len(markdown_content)
        
        # Level 1: Small files (< 50KB) - send full content  
        if content_length < 50 * 1024:  # 50KB
            return markdown_content
        
        # Level 2: Medium files (50KB-200KB) - structure-based sampling
        elif content_length < 200 * 1024:  # 200KB
            logger.info(f"📄 중간 파일 샘플링 적용 ({content_length}자)")
            return self._structure_based_sampling(markdown_content)
        
        # Level 3: Large files (> 200KB) - hierarchical sampling
        else:
            logger.info(f"📄 대용량 파일 샘플링 적용 ({content_length}자)")
            return self._hierarchical_sampling(markdown_content)
    
    def _structure_based_sampling(self, content: str) -> str:
        """
        Structure-based sampling for medium files (1-5MB)
        Uses simple position-based sampling with content analysis
        """
        # Simple 3-part sampling: beginning, middle, end
        content_length = len(content)
        
        # Calculate sample sizes (aim for ~15KB total to reduce token usage)
        target_size = 15 * 1024  # 15KB target
        part_size = target_size // 3
        
        # Beginning part
        beginning = content[:part_size]
        
        # Middle part  
        middle_start = (content_length // 2) - (part_size // 2)
        middle_end = middle_start + part_size
        middle = content[middle_start:middle_end]
        
        # End part
        end = content[-part_size:]
        
        # Combine with separators
        sampled_content = f"""=== 문서 시작 부분 ===
{beginning}

=== 문서 중간 부분 ===
{middle}

=== 문서 끝 부분 ===
{end}"""
        
        return sampled_content
    
    def _hierarchical_sampling(self, content: str) -> str:
        """
        Hierarchical sampling for large files (> 5MB)
        Uses multi-point sampling with summary approach
        """
        content_length = len(content)
        
        # For very large files, sample 5 points across the document
        target_size = 20 * 1024  # 20KB target to reduce token usage
        sample_size = target_size // 5  # ~4KB per sample
        
        samples = []
        positions = [0, 0.25, 0.5, 0.75, 0.9]  # Start, quarter, middle, three-quarter, near-end
        
        for i, pos in enumerate(positions):
            start_pos = int(content_length * pos)
            end_pos = min(start_pos + sample_size, content_length)
            
            sample = content[start_pos:end_pos]
            samples.append(f"=== 샘플 {i+1} (위치: {pos*100:.0f}%) ===\n{sample}")
        
        result = "\n\n".join(samples)
        return result
    
    def _validate_chunk_boundaries(self, suggestions: List[LLMChunkSuggestion], content: str) -> None:
        """
        Validate that chunk boundaries are valid and cover the entire document
        
        Args:
            suggestions: List of chunk suggestions
            content: Original document content
            
        Raises:
            Exception: If validation fails
        """
        if not suggestions:
            raise Exception("제안된 청크가 없습니다.")
        
        content_length = len(content)
        
        # Check basic chunk validity
        for i, chunk in enumerate(suggestions):
            if chunk.start_position < 0 or chunk.end_position > content_length:
                raise Exception(f"청크 {i}의 경계가 문서 범위를 벗어났습니다.")
            
            if chunk.start_position >= chunk.end_position:
                raise Exception(f"청크 {i}의 시작 위치가 끝 위치보다 크거나 같습니다.")
        
        # Sort chunks by start position
        sorted_chunks = sorted(suggestions, key=lambda x: x.start_position)
        
        # STRICT VALIDATION: Require complete coverage
        first_chunk_start = sorted_chunks[0].start_position
        last_chunk_end = sorted_chunks[-1].end_position
        
        # Must start from 0
        if first_chunk_start != 0:
            raise Exception(f"첫 번째 청크가 문서 시작(0)에서 시작하지 않습니다. 시작 위치: {first_chunk_start}")
        
        # Must end at document end
        if last_chunk_end != content_length:
            raise Exception(f"마지막 청크가 문서 끝({content_length})에서 끝나지 않습니다. 끝 위치: {last_chunk_end}")
        
        # Check for gaps or overlaps between consecutive chunks
        for i in range(len(sorted_chunks) - 1):
            current_end = sorted_chunks[i].end_position
            next_start = sorted_chunks[i + 1].start_position
            
            if current_end > next_start:
                raise Exception(f"청크 {i}와 {i+1}이 겹칩니다. 청크 {i} 끝: {current_end}, 청크 {i+1} 시작: {next_start}")
            elif current_end < next_start:
                gap_size = next_start - current_end
                if gap_size > 5:  # Allow small gaps (like single spaces) but not large ones
                    raise Exception(f"청크 {i}와 {i+1} 사이에 {gap_size}자 간격이 있습니다. 연속적이어야 합니다.")
                else:
                    logger.warning(f"청크 {i}와 {i+1} 사이에 {gap_size}자 간격이 있습니다.")
        
        logger.info(f"✅ 청크 검증 성공: {len(suggestions)}개 청크가 문서 전체를 완전히 커버합니다.")
    
    def get_token_usage(self, response) -> Dict[str, int]:
        """
        Extract token usage from OpenAI response
        
        Args:
            response: OpenAI chat completion response
            
        Returns:
            Dictionary with token usage statistics
        """
        usage = response.usage
        return {
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens
        }
