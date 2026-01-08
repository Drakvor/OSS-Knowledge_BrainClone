"""
Advanced Markdown Parser
========================

Comprehensive markdown parsing with structural and semantic analysis.
"""

import re
import logging
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass

from app.markdown.base import MarkdownElement, MarkdownElementType

logger = logging.getLogger(__name__)


class AdvancedMarkdownParser:
    """Advanced markdown parser with comprehensive element extraction."""
    
    def __init__(self):
        self.header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        self.code_block_pattern = re.compile(r'```(\w+)?\n(.*?)```', re.DOTALL)
        self.inline_code_pattern = re.compile(r'`([^`]+)`')
        self.link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
        self.image_pattern = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
        self.bold_pattern = re.compile(r'\*\*([^*]+)\*\*|__([^_]+)__')
        self.italic_pattern = re.compile(r'\*([^*]+)\*|_([^_]+)_')
        self.list_pattern = re.compile(r'^(\s*)([*+-]|\d+\.)\s+(.+)$', re.MULTILINE)
        self.table_pattern = re.compile(r'^\|.*\|$', re.MULTILINE)
        self.blockquote_pattern = re.compile(r'^>\s*(.+)$', re.MULTILINE)
        self.horizontal_rule_pattern = re.compile(r'^(---+|\*\*\*+|___+)$', re.MULTILINE)
    
    def parse(self, markdown_text: str) -> List[MarkdownElement]:
        """Parse markdown text into structured elements."""
        elements = []
        position = 0
        
        # Track processed ranges to avoid overlaps
        processed_ranges = []
        
        # Parse headers
        for match in self.header_pattern.finditer(markdown_text):
            start, end = match.span()
            if not self._is_processed(start, end, processed_ranges):
                level = len(match.group(1))
                content = match.group(2).strip()
                elements.append(MarkdownElement(
                    element_type=MarkdownElementType.HEADER,
                    content=content,
                    metadata={
                        "raw_content": match.group(0),
                        "marker": match.group(1)
                    },
                    position=start,
                    level=level
                ))
                processed_ranges.append((start, end))
        
        # Parse code blocks
        for match in self.code_block_pattern.finditer(markdown_text):
            start, end = match.span()
            if not self._is_processed(start, end, processed_ranges):
                language = match.group(1) or "text"
                code_content = match.group(2).strip()
                elements.append(MarkdownElement(
                    element_type=MarkdownElementType.CODE_BLOCK,
                    content=code_content,
                    metadata={
                        "raw_content": match.group(0),
                        "line_count": len(code_content.split('\n'))
                    },
                    position=start,
                    language=language
                ))
                processed_ranges.append((start, end))
        
        # Parse tables
        table_blocks = self._extract_table_blocks(markdown_text)
        for table_block in table_blocks:
            start = markdown_text.index(table_block["content"])
            end = start + len(table_block["content"])
            if not self._is_processed(start, end, processed_ranges):
                elements.append(MarkdownElement(
                    element_type=MarkdownElementType.TABLE,
                    content=table_block["content"],
                    metadata={
                        "rows": table_block["rows"],
                        "columns": table_block["columns"],
                        "headers": table_block["headers"]
                    },
                    position=start
                ))
                processed_ranges.append((start, end))
        
        # Parse lists
        list_blocks = self._extract_list_blocks(markdown_text)
        for list_block in list_blocks:
            start = markdown_text.index(list_block["content"])
            end = start + len(list_block["content"])
            if not self._is_processed(start, end, processed_ranges):
                elements.append(MarkdownElement(
                    element_type=MarkdownElementType.LIST,
                    content=list_block["content"],
                    metadata={
                        "items": list_block["items"],
                        "nested_levels": list_block["nested_levels"]
                    },
                    position=start,
                    list_type=list_block["list_type"]
                ))
                processed_ranges.append((start, end))
        
        # Parse links and images
        for match in self.link_pattern.finditer(markdown_text):
            start, end = match.span()
            if not self._is_processed(start, end, processed_ranges):
                elements.append(MarkdownElement(
                    element_type=MarkdownElementType.LINK,
                    content=match.group(1),
                    metadata={
                        "raw_content": match.group(0),
                        "is_internal": self._is_internal_link(match.group(2))
                    },
                    position=start,
                    url=match.group(2)
                ))
        
        for match in self.image_pattern.finditer(markdown_text):
            start, end = match.span()
            if not self._is_processed(start, end, processed_ranges):
                elements.append(MarkdownElement(
                    element_type=MarkdownElementType.IMAGE,
                    content=match.group(2),
                    metadata={
                        "raw_content": match.group(0)
                    },
                    position=start,
                    url=match.group(2),
                    alt_text=match.group(1)
                ))
        
        # Parse remaining text as paragraphs
        paragraph_blocks = self._extract_paragraphs(markdown_text, processed_ranges)
        for para in paragraph_blocks:
            elements.append(MarkdownElement(
                element_type=MarkdownElementType.PARAGRAPH,
                content=para["content"].strip(),
                metadata={
                    "word_count": len(para["content"].split()),
                    "has_formatting": self._has_formatting(para["content"])
                },
                position=para["position"]
            ))
        
        # Sort elements by position
        elements.sort(key=lambda x: x.position)
        
        logger.info(f"Parsed {len(elements)} markdown elements")
        return elements
    
    def _is_processed(self, start: int, end: int, processed_ranges: List[Tuple[int, int]]) -> bool:
        """Check if a range overlaps with processed ranges."""
        for p_start, p_end in processed_ranges:
            if (start < p_end and end > p_start):
                return True
        return False
    
    def _extract_table_blocks(self, text: str) -> List[Dict[str, Any]]:
        """Extract table blocks with metadata."""
        tables = []
        lines = text.split('\n')
        
        i = 0
        while i < len(lines):
            if '|' in lines[i] and lines[i].strip().startswith('|'):
                # Found start of table
                table_lines = []
                start_line = i
                
                while i < len(lines) and '|' in lines[i]:
                    table_lines.append(lines[i])
                    i += 1
                
                if len(table_lines) >= 2:  # Must have header and separator
                    headers = [h.strip() for h in table_lines[0].split('|')[1:-1]]
                    rows = len(table_lines) - 2  # Exclude header and separator
                    
                    tables.append({
                        "content": '\n'.join(table_lines),
                        "headers": headers,
                        "rows": rows,
                        "columns": len(headers)
                    })
            else:
                i += 1
        
        return tables
    
    def _extract_list_blocks(self, text: str) -> List[Dict[str, Any]]:
        """Extract list blocks with nesting information."""
        lists = []
        lines = text.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if re.match(r'^(\s*)([*+-]|\d+\.)\s+', line):
                # Found start of list
                list_lines = []
                start_line = i
                items = []
                nested_levels = set()
                
                while i < len(lines):
                    line = lines[i]
                    list_match = re.match(r'^(\s*)([*+-]|\d+\.)\s+(.+)$', line)
                    if list_match:
                        indent_level = len(list_match.group(1)) // 2
                        nested_levels.add(indent_level)
                        items.append({
                            "content": list_match.group(3),
                            "level": indent_level,
                            "marker": list_match.group(2)
                        })
                        list_lines.append(line)
                    elif line.strip() == "":
                        # Empty line in list
                        list_lines.append(line)
                    else:
                        break
                    i += 1
                
                if items:
                    list_type = "ordered" if any(item["marker"].endswith('.') for item in items) else "unordered"
                    lists.append({
                        "content": '\n'.join(list_lines),
                        "items": items,
                        "nested_levels": list(nested_levels),
                        "list_type": list_type
                    })
            else:
                i += 1
        
        return lists
    
    def _extract_paragraphs(self, text: str, processed_ranges: List[Tuple[int, int]]) -> List[Dict[str, Any]]:
        """Extract paragraphs from unprocessed text."""
        paragraphs = []
        lines = text.split('\n')
        
        current_para = []
        current_position = 0
        line_position = 0
        
        for line in lines:
            line_start = line_position
            line_end = line_position + len(line)
            
            # Check if this line is in a processed range
            if not any(start <= line_start < end or start < line_end <= end 
                      for start, end in processed_ranges):
                
                if line.strip():
                    if not current_para:
                        current_position = line_start
                    current_para.append(line.strip())
                else:
                    if current_para:
                        paragraphs.append({
                            "content": ' '.join(current_para),
                            "position": current_position
                        })
                        current_para = []
            else:
                # Line is processed, finish current paragraph if exists
                if current_para:
                    paragraphs.append({
                        "content": ' '.join(current_para),
                        "position": current_position
                    })
                    current_para = []
            
            line_position = line_end + 1  # +1 for newline
        
        # Add final paragraph if exists
        if current_para:
            paragraphs.append({
                "content": ' '.join(current_para),
                "position": current_position
            })
        
        return paragraphs
    
    def _is_internal_link(self, url: str) -> bool:
        """Check if a link is internal (relative)."""
        return not url.startswith(('http://', 'https://', 'ftp://'))
    
    def _has_formatting(self, text: str) -> bool:
        """Check if text contains markdown formatting."""
        return any(pattern.search(text) for pattern in [
            self.bold_pattern, self.italic_pattern, self.inline_code_pattern
        ])