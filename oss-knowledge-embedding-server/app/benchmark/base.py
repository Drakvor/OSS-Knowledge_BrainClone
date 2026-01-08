"""
Base Classes and Interfaces for Benchmarking Framework
=====================================================

Common interfaces and utilities for strategy benchmarking.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import time
import pandas as pd

from app.processors.base.base_models import ProcessedChunk, ChunkRelationship


class StrategyType(Enum):
    """Available chunking strategy types"""
    ROW_BASED = "row_based"
    HIERARCHICAL = "hierarchical"
    COLUMN_SEMANTIC = "column_semantic"
    ADAPTIVE_SMART = "adaptive_smart"
    ENTITY_CENTRIC = "entity_centric"
    SLIDING_WINDOW = "sliding_window"
    TOPIC_CLUSTERING = "topic_clustering"


@dataclass
class BenchmarkConfig:
    """Configuration for benchmark testing"""
    strategy_type: StrategyType
    test_data_path: str
    vector_collection_prefix: str = "benchmark"
    graph_database: str = "neo4j"
    embedding_model: str = "text-embedding-3-large"
    batch_size: int = 16
    max_chunks: int = 1000
    enable_hybrid_search: bool = True


@dataclass
class ProcessingMetrics:
    """Metrics from processing phase"""
    strategy_name: str
    processing_time_ms: float
    total_chunks: int
    avg_chunk_size: float
    total_relationships: int
    memory_usage_mb: float
    chunks_per_second: float
    storage_size_mb: float


@dataclass
class SearchMetrics:
    """Metrics from search evaluation"""
    strategy_name: str
    avg_search_time_ms: float
    precision_at_k: Dict[int, float]  # k -> precision
    recall_at_k: Dict[int, float]     # k -> recall
    mrr: float  # Mean reciprocal rank
    ndcg_at_k: Dict[int, float]       # k -> NDCG
    hybrid_improvement: float         # % improvement over vector-only


@dataclass
class BenchmarkResult:
    """Complete benchmark results for a strategy"""
    strategy_type: StrategyType
    processing_metrics: ProcessingMetrics
    search_metrics: SearchMetrics
    chunks_sample: List[ProcessedChunk]  # Sample chunks for analysis
    relationships_sample: List[ChunkRelationship]  # Sample relationships
    metadata: Dict[str, Any]


class BenchmarkStrategy(ABC):
    """Abstract base class for benchmarking strategies"""
    
    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.strategy_type = config.strategy_type
    
    @abstractmethod
    async def process_excel_data(self, excel_data: pd.DataFrame) -> Tuple[List[ProcessedChunk], List[ChunkRelationship]]:
        """Process Excel data and return chunks + relationships"""
        pass
    
    @abstractmethod
    def get_search_config(self) -> Dict[str, Any]:
        """Get strategy-specific search configuration"""
        pass
    
    @abstractmethod
    def get_strategy_description(self) -> str:
        """Get human-readable strategy description"""
        pass
    
    def create_chunk_id(self, base_id: str, chunk_index: int) -> str:
        """Create unique chunk identifier"""
        return f"benchmark_{self.strategy_type.value}_{base_id}_{chunk_index}"
    
    def calculate_processing_metrics(
        self, 
        chunks: List[ProcessedChunk], 
        relationships: List[ChunkRelationship],
        processing_time_ms: float,
        memory_usage_mb: float = 0.0
    ) -> ProcessingMetrics:
        """Calculate processing performance metrics"""
        
        total_chunks = len(chunks)
        avg_chunk_size = sum(len(chunk.content) for chunk in chunks) / total_chunks if total_chunks > 0 else 0
        chunks_per_second = (total_chunks / processing_time_ms) * 1000 if processing_time_ms > 0 else 0
        
        return ProcessingMetrics(
            strategy_name=self.strategy_type.value,
            processing_time_ms=processing_time_ms,
            total_chunks=total_chunks,
            avg_chunk_size=avg_chunk_size,
            total_relationships=len(relationships),
            memory_usage_mb=memory_usage_mb,
            chunks_per_second=chunks_per_second,
            storage_size_mb=self._estimate_storage_size(chunks, relationships)
        )
    
    def _estimate_storage_size(self, chunks: List[ProcessedChunk], relationships: List[ChunkRelationship]) -> float:
        """Estimate storage size in MB"""
        
        # Rough estimation based on content + metadata
        chunk_size = sum(len(str(chunk.content)) + len(str(chunk.metadata)) for chunk in chunks)
        relationship_size = sum(len(str(rel.relationship_data)) for rel in relationships)
        
        return (chunk_size + relationship_size) / (1024 * 1024)  # Convert to MB


@dataclass
class TestQuery:
    """Test query for evaluation"""
    query_id: str
    query_text: str
    query_type: str  # specific_entity, thematic, analytical, cross_sheet
    expected_chunks: Optional[List[str]] = None  # Expected chunk IDs for evaluation
    relevance_threshold: float = 0.7


class BenchmarkTestSuite:
    """Test suite for comprehensive strategy evaluation"""
    
    def __init__(self):
        self.test_queries: List[TestQuery] = []
        self.ground_truth: Dict[str, List[str]] = {}  # query_id -> relevant_chunk_ids
    
    def add_test_query(self, query: TestQuery):
        """Add test query to the suite"""
        self.test_queries.append(query)
    
    def generate_korean_itsm_queries(self) -> List[TestQuery]:
        """Generate comprehensive Korean ITSM test queries"""
        
        queries = [
            # Specific Entity Queries
            TestQuery("entity_001", "ITSM-001 티켓 정보", "specific_entity"),
            TestQuery("entity_002", "김철수 담당자 모든 티켓", "specific_entity"),
            TestQuery("entity_003", "SERVER-01 관련 자산 정보", "specific_entity"),
            
            # Thematic Queries
            TestQuery("theme_001", "네트워크 연결 문제", "thematic"),
            TestQuery("theme_002", "서버 성능 저하 이슈", "thematic"),
            TestQuery("theme_003", "하드웨어 장애 패턴", "thematic"),
            TestQuery("theme_004", "보안 접근 제어 문제", "thematic"),
            
            # Analytical Queries  
            TestQuery("analysis_001", "해결 시간이 긴 문제 유형", "analytical"),
            TestQuery("analysis_002", "반복 발생하는 장애", "analytical"),
            TestQuery("analysis_003", "부서별 요청 패턴", "analytical"),
            
            # Cross-Sheet Queries
            TestQuery("cross_001", "티켓과 연관된 자산", "cross_sheet"),
            TestQuery("cross_002", "사용자 요청과 IT 티켓 관계", "cross_sheet"),
            TestQuery("cross_003", "자산별 장애 이력", "cross_sheet"),
        ]
        
        self.test_queries.extend(queries)
        return queries