"""
Adaptive Smart Excel Chunking Strategy
======================================

Strategy 4: Intelligent adaptive chunking with content-aware sizing.
Uses data analysis to determine optimal chunk boundaries dynamically.
"""

import pandas as pd
from typing import List, Tuple, Dict, Any, Optional
import logging
import numpy as np
from collections import Counter
import re

from app.benchmark.base import BenchmarkStrategy, BenchmarkConfig, StrategyType
from app.processors.base.base_models import ProcessedChunk, ChunkRelationship

logger = logging.getLogger(__name__)


class AdaptiveSmartStrategy(BenchmarkStrategy):
    """Adaptive smart chunking strategy implementation"""
    
    def __init__(self, config: BenchmarkConfig):
        super().__init__(config)
        self.base_chunk_size = 5
        self.min_chunk_size = 2
        self.max_chunk_size = 12
        self.content_similarity_threshold = 0.7
        self.semantic_break_patterns = [
            '새로운', '다른', '변경', '문제', '완료', '시작', '종료',
            'new', 'different', 'change', 'issue', 'complete', 'start', 'end'
        ]
    
    async def process_excel_data(self, excel_data: pd.DataFrame) -> Tuple[List[ProcessedChunk], List[ChunkRelationship]]:
        """Process Excel data using adaptive smart chunking"""
        
        chunks = []
        relationships = []
        
        headers = list(excel_data.columns)
        total_rows = len(excel_data)
        
        logger.info(f"Processing {total_rows} rows with adaptive smart chunking")
        
        # Step 1: Analyze data patterns for adaptive chunking
        data_analysis = self._analyze_data_patterns(excel_data, headers)
        
        # Step 2: Determine adaptive chunk boundaries
        chunk_boundaries = self._determine_adaptive_boundaries(excel_data, data_analysis)
        
        # Step 3: Create adaptive chunks
        for i, (start_idx, end_idx, chunk_type, adaptation_rules) in enumerate(chunk_boundaries):
            chunk_data = excel_data.iloc[start_idx:end_idx]
            
            chunk_content = self._create_adaptive_chunk_content(
                chunk_data, headers, start_idx, end_idx, chunk_type, adaptation_rules
            )
            
            chunk_id = self.create_chunk_id("adaptive", i)
            
            metadata = {
                "strategy": self.strategy_type.value,
                "chunk_type": "adaptive_smart",
                "adaptive_type": chunk_type,
                "row_start": start_idx,
                "row_end": end_idx - 1,
                "row_count": len(chunk_data),
                "columns": headers,
                "adaptation_rules": adaptation_rules,
                "content_density": self._calculate_content_density(chunk_data),
                "semantic_coherence": adaptation_rules.get("coherence_score", 0.0)
            }
            
            processed_chunk = ProcessedChunk(
                chunk_id=chunk_id,
                content=chunk_content,
                chunk_type="adaptive_smart",
                metadata=metadata,
                source_file=self.config.test_data_path,
                processing_metadata={"strategy": "adaptive_smart"}
            )
            
            chunks.append(processed_chunk)
            
            # Create adaptive relationships
            if i > 0:
                prev_chunk = chunks[i - 1]
                relationship_type = self._determine_relationship_type(prev_chunk, processed_chunk)
                
                relationship = ChunkRelationship(relationship_id=f"rel_{chunk_id_1}_{chunk_id_2}", from_chunk_id=chunk_id_1, to_chunk_id=chunk_id_2, confidence=0.8, 
                    chunk_id_1=prev_chunk.chunk_id,
                    chunk_id_2=chunk_id,
                    relationship_type=relationship_type,
                    relationship_data={
                        "connection_type": "adaptive_sequence",
                        "relationship_strength": adaptation_rules.get("relationship_strength", 0.5),
                        "content_similarity": adaptation_rules.get("content_similarity", 0.0),
                        "boundary_type": adaptation_rules.get("boundary_reason", "content_change")
                    }
                )
                relationships.append(relationship)
        
        # Create smart cross-references
        cross_refs = self._create_smart_cross_references(chunks)
        relationships.extend(cross_refs)
        
        logger.info(f"Created {len(chunks)} adaptive chunks with {len(relationships)} relationships")
        return chunks, relationships
    
    def _analyze_data_patterns(self, data: pd.DataFrame, headers: List[str]) -> Dict[str, Any]:
        """Analyze data patterns for adaptive chunking decisions"""
        
        analysis = {
            "content_length_stats": {},
            "value_patterns": {},
            "semantic_breaks": [],
            "data_density": {},
            "column_correlations": {}
        }
        
        # Analyze content length patterns
        for col in headers:
            if data[col].dtype == 'object':  # Text columns
                lengths = data[col].astype(str).str.len()
                analysis["content_length_stats"][col] = {
                    "mean": lengths.mean(),
                    "std": lengths.std(),
                    "median": lengths.median(),
                    "max": lengths.max()
                }
        
        # Detect semantic break points
        for idx in range(1, len(data)):
            semantic_score = self._calculate_semantic_break_score(data.iloc[idx-1], data.iloc[idx], headers)
            if semantic_score > self.content_similarity_threshold:
                analysis["semantic_breaks"].append({
                    "row_index": idx,
                    "break_score": semantic_score,
                    "break_type": self._classify_break_type(data.iloc[idx-1], data.iloc[idx], headers)
                })
        
        # Analyze data density
        for col in headers:
            non_null_ratio = data[col].notna().mean()
            unique_ratio = data[col].nunique() / len(data)
            analysis["data_density"][col] = {
                "completeness": non_null_ratio,
                "uniqueness": unique_ratio,
                "information_density": non_null_ratio * unique_ratio
            }
        
        return analysis
    
    def _determine_adaptive_boundaries(self, data: pd.DataFrame, analysis: Dict[str, Any]) -> List[Tuple[int, int, str, Dict[str, Any]]]:
        """Determine adaptive chunk boundaries based on data analysis"""
        
        boundaries = []
        current_start = 0
        
        while current_start < len(data):
            # Calculate adaptive chunk size
            adaptive_size = self._calculate_adaptive_chunk_size(data, current_start, analysis)
            current_end = min(current_start + adaptive_size, len(data))
            
            # Check for semantic breaks within the proposed chunk
            semantic_breaks = [br for br in analysis["semantic_breaks"] 
                             if current_start < br["row_index"] <= current_end]
            
            if semantic_breaks:
                # Adjust boundary to semantic break
                break_point = semantic_breaks[0]["row_index"]
                if break_point - current_start >= self.min_chunk_size:
                    current_end = break_point
            
            # Determine chunk type and adaptation rules
            chunk_type, adaptation_rules = self._determine_chunk_type_and_rules(
                data.iloc[current_start:current_end], analysis, current_start, current_end
            )
            
            boundaries.append((current_start, current_end, chunk_type, adaptation_rules))
            current_start = current_end
        
        return boundaries
    
    def _calculate_adaptive_chunk_size(self, data: pd.DataFrame, start_idx: int, analysis: Dict[str, Any]) -> int:
        """Calculate adaptive chunk size based on content characteristics"""
        
        # Base size adjustment factors
        size_factors = []
        
        # Factor 1: Content density
        remaining_data = data.iloc[start_idx:]
        avg_density = np.mean([analysis["data_density"][col]["information_density"] 
                              for col in analysis["data_density"]])
        
        if avg_density > 0.8:  # High density
            size_factors.append(0.7)  # Smaller chunks
        elif avg_density > 0.5:  # Medium density
            size_factors.append(1.0)  # Normal chunks
        else:  # Low density
            size_factors.append(1.3)  # Larger chunks
        
        # Factor 2: Content length
        if analysis["content_length_stats"]:
            avg_content_length = np.mean([stats["mean"] for stats in analysis["content_length_stats"].values()])
            if avg_content_length > 500:
                size_factors.append(0.8)
            elif avg_content_length > 200:
                size_factors.append(1.0)
            else:
                size_factors.append(1.2)
        
        # Factor 3: Upcoming semantic breaks
        next_breaks = [br for br in analysis["semantic_breaks"] 
                      if br["row_index"] > start_idx]
        if next_breaks:
            next_break = next_breaks[0]["row_index"] - start_idx
            if next_break < self.base_chunk_size:
                size_factors.append(0.6)
        
        # Calculate final adaptive size
        final_factor = np.mean(size_factors)
        adaptive_size = int(self.base_chunk_size * final_factor)
        
        return max(self.min_chunk_size, min(adaptive_size, self.max_chunk_size))
    
    def _calculate_semantic_break_score(self, row1: pd.Series, row2: pd.Series, headers: List[str]) -> float:
        """Calculate semantic break score between two consecutive rows"""
        
        break_score = 0.0
        
        for col in headers:
            if pd.isna(row1[col]) or pd.isna(row2[col]):
                continue
                
            val1, val2 = str(row1[col]).lower(), str(row2[col]).lower()
            
            # Check for semantic break patterns
            for pattern in self.semantic_break_patterns:
                if pattern in val2 and pattern not in val1:
                    break_score += 0.3
            
            # Check for significant content change
            if len(val1) > 0 and len(val2) > 0:
                # Simple content similarity check
                common_words = set(val1.split()) & set(val2.split())
                total_words = set(val1.split()) | set(val2.split())
                
                if total_words:
                    similarity = len(common_words) / len(total_words)
                    if similarity < 0.3:  # Low similarity indicates break
                        break_score += 0.4
        
        return min(break_score, 1.0)
    
    def _classify_break_type(self, row1: pd.Series, row2: pd.Series, headers: List[str]) -> str:
        """Classify the type of semantic break"""
        
        # Check status changes
        status_cols = [col for col in headers if any(term in col.lower() for term in ['상태', 'status', '단계'])]
        if status_cols:
            for col in status_cols:
                if not pd.isna(row1[col]) and not pd.isna(row2[col]) and row1[col] != row2[col]:
                    return "status_change"
        
        # Check category changes
        category_cols = [col for col in headers if any(term in col.lower() for term in ['유형', 'type', '분류'])]
        if category_cols:
            for col in category_cols:
                if not pd.isna(row1[col]) and not pd.isna(row2[col]) and row1[col] != row2[col]:
                    return "category_change"
        
        # Check for new incidents/tickets
        id_cols = [col for col in headers if any(term in col.lower() for term in ['id', '번호', '아이디'])]
        if id_cols:
            for col in id_cols:
                if not pd.isna(row1[col]) and not pd.isna(row2[col]):
                    val1, val2 = str(row1[col]), str(row2[col])
                    if val1 != val2:
                        return "entity_change"
        
        return "content_change"
    
    def _determine_chunk_type_and_rules(self, chunk_data: pd.DataFrame, analysis: Dict[str, Any], 
                                      start_idx: int, end_idx: int) -> Tuple[str, Dict[str, Any]]:
        """Determine chunk type and adaptation rules"""
        
        # Analyze chunk characteristics
        chunk_size = len(chunk_data)
        
        # Calculate content coherence
        coherence_score = self._calculate_chunk_coherence(chunk_data)
        
        # Determine chunk type
        if chunk_size <= 3:
            chunk_type = "focused_detail"
        elif chunk_size >= 8:
            chunk_type = "comprehensive_context"
        elif coherence_score > 0.8:
            chunk_type = "coherent_group"
        else:
            chunk_type = "adaptive_mixed"
        
        # Define adaptation rules
        adaptation_rules = {
            "coherence_score": coherence_score,
            "size_optimization": "adaptive",
            "content_focus": self._determine_content_focus(chunk_data),
            "relationship_strength": min(coherence_score + 0.2, 1.0),
            "boundary_reason": "adaptive_analysis",
            "content_similarity": coherence_score
        }
        
        return chunk_type, adaptation_rules
    
    def _calculate_chunk_coherence(self, chunk_data: pd.DataFrame) -> float:
        """Calculate content coherence within chunk"""
        
        if len(chunk_data) <= 1:
            return 1.0
        
        coherence_scores = []
        
        # Check text column coherence
        text_cols = [col for col in chunk_data.columns if chunk_data[col].dtype == 'object']
        
        for col in text_cols:
            values = chunk_data[col].dropna().astype(str)
            if len(values) <= 1:
                continue
            
            # Simple word overlap analysis
            all_words = []
            for val in values:
                all_words.extend(val.lower().split())
            
            if all_words:
                word_counts = Counter(all_words)
                common_words = [word for word, count in word_counts.items() if count > 1]
                coherence = len(common_words) / len(set(all_words))
                coherence_scores.append(coherence)
        
        return np.mean(coherence_scores) if coherence_scores else 0.5
    
    def _determine_content_focus(self, chunk_data: pd.DataFrame) -> str:
        """Determine the main content focus of the chunk"""
        
        # Analyze column content to determine focus
        text_cols = [col for col in chunk_data.columns if chunk_data[col].dtype == 'object']
        
        focus_keywords = {
            "문제해결": ["문제", "오류", "장애", "해결", "수리", "problem", "error", "issue"],
            "요청처리": ["요청", "신청", "처리", "승인", "request", "process", "approve"],
            "상태변경": ["상태", "진행", "완료", "대기", "status", "progress", "complete"],
            "정보조회": ["조회", "확인", "검색", "정보", "view", "check", "search", "info"]
        }
        
        focus_scores = {focus: 0 for focus in focus_keywords}
        
        for col in text_cols:
            col_text = " ".join(chunk_data[col].dropna().astype(str)).lower()
            
            for focus, keywords in focus_keywords.items():
                for keyword in keywords:
                    focus_scores[focus] += col_text.count(keyword)
        
        # Return focus with highest score
        if max(focus_scores.values()) > 0:
            return max(focus_scores, key=focus_scores.get)
        else:
            return "일반정보"
    
    def _calculate_content_density(self, chunk_data: pd.DataFrame) -> float:
        """Calculate content density of chunk"""
        
        total_cells = len(chunk_data) * len(chunk_data.columns)
        non_empty_cells = chunk_data.notna().sum().sum()
        
        return non_empty_cells / total_cells if total_cells > 0 else 0.0
    
    def _determine_relationship_type(self, chunk1: ProcessedChunk, chunk2: ProcessedChunk) -> str:
        """Determine relationship type between two chunks"""
        
        # Get adaptation rules from metadata
        rules1 = chunk1.metadata.get("adaptation_rules", {})
        rules2 = chunk2.metadata.get("adaptation_rules", {})
        
        similarity = rules2.get("content_similarity", 0.0)
        
        if similarity > 0.8:
            return "high_coherence"
        elif similarity > 0.5:
            return "moderate_coherence"
        else:
            return "adaptive_sequence"
    
    def _create_smart_cross_references(self, chunks: List[ProcessedChunk]) -> List[ChunkRelationship]:
        """Create intelligent cross-references between chunks"""
        
        relationships = []
        
        # Group chunks by content focus
        focus_groups = {}
        for chunk in chunks:
            focus = chunk.metadata.get("adaptation_rules", {}).get("content_focus", "일반정보")
            if focus not in focus_groups:
                focus_groups[focus] = []
            focus_groups[focus].append(chunk)
        
        # Create cross-references within focus groups
        for focus, group_chunks in focus_groups.items():
            if len(group_chunks) <= 1:
                continue
            
            for i, chunk1 in enumerate(group_chunks):
                for chunk2 in group_chunks[i + 1:]:
                    # Skip if chunks are adjacent (already have sequence relationship)
                    if abs(chunk1.metadata["row_start"] - chunk2.metadata["row_start"]) <= 1:
                        continue
                    
                    relationship = ChunkRelationship(relationship_id=f"rel_{chunk_id_1}_{chunk_id_2}", from_chunk_id=chunk_id_1, to_chunk_id=chunk_id_2, confidence=0.8, 
                        chunk_id_1=chunk1.chunk_id,
                        chunk_id_2=chunk2.chunk_id,
                        relationship_type="thematic_similarity",
                        relationship_data={
                            "connection_type": "content_focus_similarity",
                            "shared_focus": focus,
                            "coherence_score": (chunk1.metadata["semantic_coherence"] + 
                                              chunk2.metadata["semantic_coherence"]) / 2
                        }
                    )
                    relationships.append(relationship)
        
        return relationships
    
    def _create_adaptive_chunk_content(self, chunk_data: pd.DataFrame, headers: List[str], 
                                     start_idx: int, end_idx: int, chunk_type: str, 
                                     adaptation_rules: Dict[str, Any]) -> str:
        """Create content for adaptive chunk"""
        
        content_lines = [
            f"적응형 청크 ({chunk_type})",
            f"행 범위: {start_idx + 1}-{end_idx}",
            f"일관성 점수: {adaptation_rules.get('coherence_score', 0.0):.2f}",
            f"내용 초점: {adaptation_rules.get('content_focus', '일반정보')}",
            "=" * 50
        ]
        
        # Add adaptive analysis
        content_lines.append("\\n적응형 분석:")
        content_lines.append(f"- 청크 유형: {chunk_type}")
        content_lines.append(f"- 크기 최적화: {adaptation_rules.get('size_optimization', 'unknown')}")
        content_lines.append(f"- 내용 밀도: {self._calculate_content_density(chunk_data):.2f}")
        
        content_lines.append("\\n데이터:")
        
        # Add chunk data with adaptive formatting
        for idx, (_, row) in enumerate(chunk_data.iterrows()):
            row_values = []
            for header in headers:
                value = str(row[header]) if pd.notna(row[header]) else "[비어있음]"
                row_values.append(f"{header}: {value}")
            
            content_lines.append(f"행 {start_idx + idx + 1}: " + " | ".join(row_values))
        
        return "\\n".join(content_lines)
    
    def get_search_config(self) -> Dict[str, Any]:
        """Get adaptive smart search configuration"""
        return {
            "strategy_name": "adaptive_smart",
            "search_type": "adaptive_semantic",
            "embedding_fields": ["content"],
            "boost_fields": {
                "adaptive_analysis": 1.3,
                "content_focus": 1.5,
                "coherent_content": 1.2,
                "data_content": 1.0
            },
            "filter_metadata": {
                "strategy": self.strategy_type.value,
                "chunk_type": "adaptive_smart"
            },
            "adaptive_weights": {
                "focused_detail": 1.4,
                "comprehensive_context": 1.0,
                "coherent_group": 1.2,
                "adaptive_mixed": 1.1
            },
            "coherence_boost": True,
            "relationship_traversal": {
                "enabled": True,
                "max_depth": 3,
                "relationship_types": ["high_coherence", "moderate_coherence", "thematic_similarity"],
                "coherence_weighted": True
            }
        }
    
    def get_strategy_description(self) -> str:
        """Get strategy description"""
        return (
            f"Adaptive Smart Chunking: Intelligent content-aware chunking with dynamic sizing. "
            f"Size range: {self.min_chunk_size}-{self.max_chunk_size} rows based on content analysis. "
            f"Uses semantic break detection and coherence scoring for optimal boundaries."
        )