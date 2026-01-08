"""
Code-Context Coupling Strategy
==============================

Pairs code blocks with their surrounding explanatory text. Creates chunks that 
include code plus preceding and following documentation, maintains language-specific 
metadata, and establishes explanation-to-implementation relationships.
"""

import uuid
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from app.markdown.base import (
    MarkdownElement, MarkdownElementType, MarkdownChunk, 
    MarkdownRelationship, MarkdownChunkingStrategy
)

logger = logging.getLogger(__name__)


class CodeContextCouplingChunker:
    """Creates chunks by coupling code blocks with explanatory context."""
    
    def __init__(self, min_chunk_size: int = 200, max_chunk_size: int = 2000, context_window: int = 3):
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.context_window = context_window  # Number of elements to consider before/after code
        self.strategy = MarkdownChunkingStrategy.CODE_CONTEXT_COUPLING
        
        # Language-specific processing hints
        self.language_categories = {
            'python': 'scripting',
            'javascript': 'scripting', 
            'typescript': 'scripting',
            'java': 'compiled',
            'c++': 'compiled',
            'c': 'compiled',
            'go': 'compiled',
            'rust': 'compiled',
            'bash': 'shell',
            'shell': 'shell',
            'sql': 'query',
            'yaml': 'config',
            'json': 'config',
            'xml': 'markup',
            'html': 'markup',
            'css': 'styling'
        }
    
    def chunk(self, elements: List[MarkdownElement]) -> tuple[List[MarkdownChunk], List[MarkdownRelationship]]:
        """Create chunks by coupling code blocks with their context."""
        chunks = []
        relationships = []
        
        if not elements:
            return chunks, relationships
        
        # Find all code blocks and their contexts
        code_contexts = self._identify_code_contexts(elements)
        
        # Create code-context chunks
        processed_indices = set()
        
        for code_context in code_contexts:
            chunk = self._create_code_context_chunk(code_context)
            if chunk:
                chunks.append(chunk)
                
                # Mark elements as processed
                for elem_idx in code_context['element_indices']:
                    processed_indices.add(elem_idx)
        
        # Handle remaining elements (non-code content)
        remaining_chunks = self._process_remaining_elements(elements, processed_indices)
        chunks.extend(remaining_chunks)
        
        # Create relationships
        relationships = self._create_code_relationships(chunks)
        
        logger.info(f"Created {len(chunks)} code-context chunks with {len(relationships)} relationships")
        return chunks, relationships
    
    def _identify_code_contexts(self, elements: List[MarkdownElement]) -> List[Dict[str, Any]]:
        """Identify code blocks and their surrounding context."""
        code_contexts = []
        
        for i, element in enumerate(elements):
            if element.element_type == MarkdownElementType.CODE_BLOCK:
                context = self._extract_code_context(elements, i)
                if context:
                    code_contexts.append(context)
        
        return code_contexts
    
    def _extract_code_context(self, elements: List[MarkdownElement], code_index: int) -> Dict[str, Any]:
        """Extract context around a code block."""
        code_element = elements[code_index]
        
        # Find preceding context (explanatory text)
        preceding_context = []
        for i in range(max(0, code_index - self.context_window), code_index):
            elem = elements[i]
            if self._is_explanatory_for_code(elem, code_element):
                preceding_context.append((i, elem))
        
        # Find following context (results, explanations, examples)
        following_context = []
        for i in range(code_index + 1, min(len(elements), code_index + 1 + self.context_window)):
            elem = elements[i]
            if self._is_related_to_code(elem, code_element):
                following_context.append((i, elem))
            elif elem.element_type == MarkdownElementType.CODE_BLOCK:
                # Stop at next code block unless it's very similar
                if not self._are_code_blocks_related(code_element, elem):
                    break
                following_context.append((i, elem))
        
        # Build context structure
        context_elements = []
        element_indices = []
        
        # Add preceding context
        for idx, elem in preceding_context:
            context_elements.append(elem)
            element_indices.append(idx)
        
        # Add the code block itself
        context_elements.append(code_element)
        element_indices.append(code_index)
        
        # Add following context
        for idx, elem in following_context:
            context_elements.append(elem)
            element_indices.append(idx)
        
        return {
            'code_element': code_element,
            'code_index': code_index,
            'context_elements': context_elements,
            'element_indices': element_indices,
            'preceding_count': len(preceding_context),
            'following_count': len(following_context),
            'language': code_element.language or 'text'
        }
    
    def _is_explanatory_for_code(self, element: MarkdownElement, code_element: MarkdownElement) -> bool:
        """Check if element explains the code block."""
        if element.element_type not in {MarkdownElementType.PARAGRAPH, MarkdownElementType.HEADER}:
            return False
        
        content_lower = element.content.lower()
        code_content = code_element.content.lower()
        
        # Look for explanatory keywords
        explanatory_keywords = {
            'example', 'following', 'code', 'function', 'method', 'class',
            'implementation', 'usage', 'how to', 'to do this', 'script',
            'program', 'algorithm', 'snippet'
        }
        
        has_explanatory = any(keyword in content_lower for keyword in explanatory_keywords)
        
        # Look for technical terms that appear in the code
        code_words = set(word for word in code_content.split() if len(word) > 3)
        content_words = set(content_lower.split())
        shared_technical_terms = len(code_words & content_words)
        
        # Look for language mentions
        language_mentioned = (code_element.language and 
                            code_element.language.lower() in content_lower)
        
        return has_explanatory or shared_technical_terms > 2 or language_mentioned
    
    def _is_related_to_code(self, element: MarkdownElement, code_element: MarkdownElement) -> bool:
        """Check if element is related to the code block (results, explanation, etc.)."""
        if element.element_type in {MarkdownElementType.PARAGRAPH, MarkdownElementType.LIST}:
            content_lower = element.content.lower()
            
            # Look for result/output keywords
            result_keywords = {
                'output', 'result', 'returns', 'produces', 'prints',
                'displays', 'shows', 'generates', 'creates'
            }
            
            has_result_keywords = any(keyword in content_lower for keyword in result_keywords)
            
            # Look for continuation keywords
            continuation_keywords = {
                'also', 'additionally', 'furthermore', 'next', 'then',
                'alternatively', 'similarly', 'note that'
            }
            
            has_continuation = any(keyword in content_lower for keyword in continuation_keywords)
            
            return has_result_keywords or has_continuation
        
        return False
    
    def _are_code_blocks_related(self, code1: MarkdownElement, code2: MarkdownElement) -> bool:
        """Check if two code blocks are related (same language, similar content)."""
        # Same language
        if code1.language == code2.language and code1.language:
            # Look for similar function names, variable names, etc.
            content1_words = set(code1.content.split())
            content2_words = set(code2.content.split())
            
            shared_words = content1_words & content2_words
            # Filter out common programming keywords
            common_keywords = {'def', 'function', 'var', 'let', 'const', 'if', 'else', 'for', 'while'}
            meaningful_shared = shared_words - common_keywords
            
            return len(meaningful_shared) > 2
        
        return False
    
    def _create_code_context_chunk(self, code_context: Dict[str, Any]) -> Optional[MarkdownChunk]:
        """Create a chunk from a code context."""
        elements = code_context['context_elements']
        if not elements:
            return None
        
        # Build content
        content_parts = []
        for element in elements:
            if element.element_type == MarkdownElementType.CODE_BLOCK:
                # Format code blocks specially
                lang = element.language or 'text'
                content_parts.append(f"```{lang}\n{element.content}\n```")
            else:
                content_parts.append(element.content)
        
        content = '\n\n'.join(content_parts)
        
        # Skip if too small
        if len(content) < self.min_chunk_size:
            return None
        
        # Truncate if too large
        if len(content) > self.max_chunk_size:
            content = content[:self.max_chunk_size] + "..."
        
        code_element = code_context['code_element']
        language = code_element.language or 'text'
        
        chunk_id = f"md_codecontext_{uuid.uuid4().hex[:8]}"
        
        return MarkdownChunk(
            chunk_id=chunk_id,
            content=content,
            elements=elements,
            chunk_type=f"code_context_{language}",
            structural_metadata={
                "has_code": True,
                "primary_language": language,
                "language_category": self.language_categories.get(language, 'other'),
                "code_lines": len(code_element.content.split('\n')),
                "context_elements": len(elements),
                "preceding_context": code_context['preceding_count'],
                "following_context": code_context['following_count']
            },
            semantic_metadata={
                "code_complexity": self._assess_code_complexity(code_element),
                "has_explanation": code_context['preceding_count'] > 0,
                "has_results": code_context['following_count'] > 0,
                "code_purpose": self._infer_code_purpose(code_element, elements),
                "technical_concepts": self._extract_technical_concepts(elements)
            },
            position_start=elements[0].position,
            position_end=elements[-1].position,
            word_count=len(content.split())
        )
    
    def _assess_code_complexity(self, code_element: MarkdownElement) -> str:
        """Assess the complexity of a code block."""
        code = code_element.content
        lines = len(code.split('\n'))
        
        # Count complexity indicators
        complexity_indicators = {
            'functions': len([line for line in code.split('\n') if 'def ' in line or 'function ' in line]),
            'conditionals': len([line for line in code.split('\n') if ' if ' in line or 'if(' in line]),
            'loops': len([line for line in code.split('\n') if 'for ' in line or 'while ' in line]),
            'classes': len([line for line in code.split('\n') if 'class ' in line])
        }
        
        total_complexity = sum(complexity_indicators.values())
        
        if lines < 5 and total_complexity == 0:
            return 'simple'
        elif lines < 20 and total_complexity < 3:
            return 'moderate'
        else:
            return 'complex'
    
    def _infer_code_purpose(self, code_element: MarkdownElement, context_elements: List[MarkdownElement]) -> str:
        """Infer the purpose of the code from context."""
        code = code_element.content.lower()
        
        # Check context for purpose keywords
        context_text = ' '.join(elem.content.lower() for elem in context_elements 
                               if elem.element_type == MarkdownElementType.PARAGRAPH)
        
        purpose_patterns = {
            'example': ['example', 'for example', 'demonstrates', 'shows how'],
            'tutorial': ['step', 'tutorial', 'guide', 'how to', 'first', 'then'],
            'api_usage': ['api', 'endpoint', 'request', 'response', 'call'],
            'configuration': ['config', 'setup', 'configure', 'settings'],
            'test': ['test', 'testing', 'assert', 'expect', 'should'],
            'utility': ['utility', 'helper', 'function', 'tool']
        }
        
        for purpose, keywords in purpose_patterns.items():
            if any(keyword in context_text for keyword in keywords):
                return purpose
        
        # Infer from code content
        if 'test' in code or 'assert' in code:
            return 'test'
        elif 'main' in code and 'if __name__' in code:
            return 'script'
        elif 'class' in code:
            return 'class_definition'
        elif 'def' in code or 'function' in code:
            return 'function_definition'
        else:
            return 'snippet'
    
    def _extract_technical_concepts(self, elements: List[MarkdownElement]) -> List[str]:
        """Extract technical concepts from the context."""
        concepts = set()
        
        for element in elements:
            content = element.content.lower()
            
            # Programming concepts
            prog_concepts = [
                'variable', 'function', 'method', 'class', 'object',
                'array', 'list', 'dictionary', 'loop', 'condition',
                'algorithm', 'data structure', 'api', 'database',
                'authentication', 'authorization', 'encryption'
            ]
            
            for concept in prog_concepts:
                if concept in content:
                    concepts.add(concept)
        
        return list(concepts)
    
    def _process_remaining_elements(self, elements: List[MarkdownElement], 
                                   processed_indices: set) -> List[MarkdownChunk]:
        """Process elements that weren't part of code contexts."""
        chunks = []
        current_group = []
        current_size = 0
        
        for i, element in enumerate(elements):
            if i in processed_indices:
                # Finish current group if it exists
                if current_group:
                    chunk = self._create_non_code_chunk(current_group)
                    if chunk:
                        chunks.append(chunk)
                    current_group = []
                    current_size = 0
                continue
            
            element_size = len(element.content)
            
            # Check if adding this element would exceed max size
            if current_size + element_size > self.max_chunk_size and current_group:
                # Finish current group
                chunk = self._create_non_code_chunk(current_group)
                if chunk:
                    chunks.append(chunk)
                current_group = [element]
                current_size = element_size
            else:
                current_group.append(element)
                current_size += element_size
        
        # Process final group
        if current_group:
            chunk = self._create_non_code_chunk(current_group)
            if chunk:
                chunks.append(chunk)
        
        return chunks
    
    def _create_non_code_chunk(self, elements: List[MarkdownElement]) -> Optional[MarkdownChunk]:
        """Create a chunk from non-code elements."""
        if not elements:
            return None
        
        content = '\n\n'.join(elem.content for elem in elements)
        
        if len(content) < self.min_chunk_size:
            return None
        
        chunk_id = f"md_noncode_{uuid.uuid4().hex[:8]}"
        
        return MarkdownChunk(
            chunk_id=chunk_id,
            content=content,
            elements=elements,
            chunk_type="contextual_content",
            structural_metadata={
                "has_code": False,
                "element_count": len(elements),
                "element_types": list(set(elem.element_type.value for elem in elements))
            },
            semantic_metadata={
                "content_type": "documentation",
                "technical_concepts": self._extract_technical_concepts(elements)
            },
            position_start=elements[0].position,
            position_end=elements[-1].position,
            word_count=len(content.split())
        )
    
    def _create_code_relationships(self, chunks: List[MarkdownChunk]) -> List[MarkdownRelationship]:
        """Create relationships between code and context chunks."""
        relationships = []
        
        # Group chunks by type
        code_chunks = [c for c in chunks if c.structural_metadata.get('has_code', False)]
        non_code_chunks = [c for c in chunks if not c.structural_metadata.get('has_code', False)]
        
        # Create explanation-implementation relationships
        for code_chunk in code_chunks:
            # Find nearby non-code chunks that might explain this code
            for non_code_chunk in non_code_chunks:
                if self._chunks_are_contextually_related(non_code_chunk, code_chunk):
                    relationships.append(MarkdownRelationship(
                        source_chunk_id=non_code_chunk.chunk_id,
                        target_chunk_id=code_chunk.chunk_id,
                        relationship_type="explanation_implementation",
                        relationship_metadata={
                            "language": code_chunk.structural_metadata.get('primary_language'),
                            "code_purpose": code_chunk.semantic_metadata.get('code_purpose')
                        }
                    ))
        
        # Create language-based relationships
        language_groups = {}
        for chunk in code_chunks:
            lang = chunk.structural_metadata.get('primary_language', 'unknown')
            if lang not in language_groups:
                language_groups[lang] = []
            language_groups[lang].append(chunk)
        
        for lang, lang_chunks in language_groups.items():
            for i, chunk1 in enumerate(lang_chunks):
                for chunk2 in lang_chunks[i + 1:]:
                    relationships.append(MarkdownRelationship(
                        source_chunk_id=chunk1.chunk_id,
                        target_chunk_id=chunk2.chunk_id,
                        relationship_type="same_language",
                        relationship_metadata={
                            "language": lang,
                            "language_category": self.language_categories.get(lang, 'other')
                        },
                        confidence=0.7
                    ))
        
        return relationships
    
    def _chunks_are_contextually_related(self, non_code_chunk: MarkdownChunk, code_chunk: MarkdownChunk) -> bool:
        """Check if a non-code chunk is contextually related to a code chunk."""
        # Position-based proximity
        non_code_end = non_code_chunk.position_end
        code_start = code_chunk.position_start
        
        # Must be reasonably close in the document
        if abs(code_start - non_code_end) > 1000:  # Arbitrary distance threshold
            return False
        
        # Content-based relationship
        non_code_concepts = set(non_code_chunk.semantic_metadata.get('technical_concepts', []))
        code_concepts = set(code_chunk.semantic_metadata.get('technical_concepts', []))
        
        shared_concepts = non_code_concepts & code_concepts
        return len(shared_concepts) > 0