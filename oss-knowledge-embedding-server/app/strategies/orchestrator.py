"""
Strategy Orchestrator
====================

Orchestrates and coordinates different chunking and embedding strategies.
Provides a unified interface for running multiple strategy combinations.
"""

import time
import logging
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

from app.strategies.chunking.base import ChunkingConfig, ChunkingStrategyType
from app.strategies.chunking.factory import ChunkingStrategyFactory
from app.strategies.embedding.base import EmbeddingConfig, EmbeddingStrategyType
from app.strategies.embedding.factory import EmbeddingStrategyFactory
from app.processors.base.base_models import ProcessedChunk, ChunkEmbedding

logger = logging.getLogger(__name__)


@dataclass
class StrategyCombo:
    """Configuration for a chunking + embedding strategy combination"""
    name: str
    chunking_config: ChunkingConfig
    embedding_config: EmbeddingConfig
    description: str = ""


@dataclass 
class StrategyResult:
    """Result from processing with a strategy combination"""
    combo_name: str
    chunking_strategy: ChunkingStrategyType
    embedding_strategy: EmbeddingStrategyType
    chunks: List[ProcessedChunk]
    embeddings: List[ChunkEmbedding]
    processing_time_ms: float
    chunking_time_ms: float
    embedding_time_ms: float
    total_chunks: int
    avg_chunk_size: float
    embedding_dimension: int
    metadata: Dict[str, Any]


class StrategyOrchestrator:
    """Orchestrates multiple strategy combinations for comparison"""
    
    def __init__(self):
        self.chunking_factory = ChunkingStrategyFactory()
        self.embedding_factory = EmbeddingStrategyFactory()
        self.results: List[StrategyResult] = []
    
    def create_default_combos(self) -> List[StrategyCombo]:
        """Create default strategy combinations for testing"""
        
        return [
            StrategyCombo(
                name="Fast Processing",
                chunking_config=ChunkingConfig(
                    strategy_type=ChunkingStrategyType.FIXED_SIZE,
                    chunk_size=512,
                    overlap=50
                ),
                embedding_config=EmbeddingConfig(
                    strategy_type=EmbeddingStrategyType.SENTENCE_BERT,
                    model_name="sentence-transformers/all-MiniLM-L6-v2",
                    batch_size=32
                ),
                description="Fast processing with fixed-size chunks and lightweight embeddings"
            ),
            
            StrategyCombo(
                name="Korean Optimized",
                chunking_config=ChunkingConfig(
                    strategy_type=ChunkingStrategyType.SEMANTIC,
                    chunk_size=600,
                    max_chunk_size=1200
                ),
                embedding_config=EmbeddingConfig(
                    strategy_type=EmbeddingStrategyType.SENTENCE_BERT,
                    model_name="sentence-transformers/all-MiniLM-L6-v2",
                    batch_size=16
                ),
                description="Korean-optimized with semantic chunking and Azure OpenAI embeddings"
            ),
            
            StrategyCombo(
                name="Context Preservation",
                chunking_config=ChunkingConfig(
                    strategy_type=ChunkingStrategyType.SLIDING_WINDOW,
                    chunk_size=512,
                    overlap=128
                ),
                embedding_config=EmbeddingConfig(
                    strategy_type=EmbeddingStrategyType.SENTENCE_BERT,
                    model_name="sentence-transformers/all-MiniLM-L6-v2",
                    batch_size=16
                ),
                description="Context preservation with sliding window and Azure OpenAI embeddings"
            ),
            
            StrategyCombo(
                name="Balanced Performance",
                chunking_config=ChunkingConfig(
                    strategy_type=ChunkingStrategyType.SEMANTIC,
                    chunk_size=512,
                    max_chunk_size=1000
                ),
                embedding_config=EmbeddingConfig(
                    strategy_type=EmbeddingStrategyType.SENTENCE_BERT,
                    model_name="sentence-transformers/all-mpnet-base-v2",
                    batch_size=24
                ),
                description="Balanced approach with semantic chunking and high-quality English embeddings"
            )
        ]
    
    async def process_with_combo(
        self,
        text: str,
        combo: StrategyCombo,
        source_metadata: Dict[str, Any] = None
    ) -> StrategyResult:
        """Process text with a specific strategy combination"""
        
        start_time = time.time()
        source_metadata = source_metadata or {}
        
        logger.info(f"Processing with combo: {combo.name}")
        
        # Step 1: Chunking
        chunking_start = time.time()
        chunking_strategy = self.chunking_factory.create_strategy(
            combo.chunking_config.strategy_type,
            combo.chunking_config
        )
        
        chunking_result = await chunking_strategy.chunk_text(text, source_metadata)
        chunking_time = (time.time() - chunking_start) * 1000
        
        # Step 2: Embedding
        embedding_start = time.time()
        embedding_strategy = self.embedding_factory.create_strategy(
            combo.embedding_config.strategy_type,
            combo.embedding_config
        )
        
        embedding_result = await embedding_strategy.generate_embeddings(
            chunking_result.chunks, show_progress=False
        )
        embedding_time = (time.time() - embedding_start) * 1000
        
        # Create result
        total_time = (time.time() - start_time) * 1000
        
        result = StrategyResult(
            combo_name=combo.name,
            chunking_strategy=combo.chunking_config.strategy_type,
            embedding_strategy=combo.embedding_config.strategy_type,
            chunks=chunking_result.chunks,
            embeddings=embedding_result.embeddings,
            processing_time_ms=total_time,
            chunking_time_ms=chunking_time,
            embedding_time_ms=embedding_time,
            total_chunks=len(chunking_result.chunks),
            avg_chunk_size=chunking_result.avg_chunk_size,
            embedding_dimension=embedding_strategy.get_embedding_dimension(),
            metadata={
                "combo_config": {
                    "chunking": chunking_strategy.get_strategy_info(),
                    "embedding": embedding_strategy.get_strategy_info()
                },
                "chunking_result": {
                    "processing_time_ms": chunking_result.processing_time_ms,
                    "metadata": chunking_result.metadata
                },
                "embedding_result": {
                    "processing_time_ms": embedding_result.processing_time_ms,
                    "model_info": embedding_result.model_info
                }
            }
        )
        
        # Cleanup embedding strategy
        await embedding_strategy.shutdown()
        
        logger.info(f"Combo '{combo.name}' completed in {total_time:.1f}ms")
        return result
    
    async def compare_strategies(
        self,
        text: str,
        combos: List[StrategyCombo] = None,
        source_metadata: Dict[str, Any] = None
    ) -> List[StrategyResult]:
        """Compare multiple strategy combinations"""
        
        if combos is None:
            combos = self.create_default_combos()
        
        logger.info(f"Comparing {len(combos)} strategy combinations")
        
        results = []
        for combo in combos:
            try:
                result = await self.process_with_combo(text, combo, source_metadata)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process combo '{combo.name}': {e}")
        
        self.results.extend(results)
        return results
    
    def get_performance_comparison(self, results: List[StrategyResult]) -> Dict[str, Any]:
        """Analyze performance across strategy combinations"""
        
        if not results:
            return {"error": "No results to compare"}
        
        # Performance metrics
        performance_data = []
        for result in results:
            performance_data.append({
                "combo_name": result.combo_name,
                "total_time_ms": result.processing_time_ms,
                "chunking_time_ms": result.chunking_time_ms,
                "embedding_time_ms": result.embedding_time_ms,
                "total_chunks": result.total_chunks,
                "avg_chunk_size": result.avg_chunk_size,
                "embedding_dimension": result.embedding_dimension,
                "chunks_per_second": result.total_chunks / (result.processing_time_ms / 1000),
                "efficiency_score": result.total_chunks / result.processing_time_ms * 1000
            })
        
        # Rankings
        fastest_combo = min(performance_data, key=lambda x: x["total_time_ms"])
        most_chunks = max(performance_data, key=lambda x: x["total_chunks"])
        most_efficient = max(performance_data, key=lambda x: x["efficiency_score"])
        
        return {
            "comparison_summary": {
                "total_combinations": len(results),
                "fastest_combo": fastest_combo["combo_name"],
                "fastest_time_ms": fastest_combo["total_time_ms"],
                "most_chunks_combo": most_chunks["combo_name"],
                "max_chunks": most_chunks["total_chunks"],
                "most_efficient_combo": most_efficient["combo_name"],
                "max_efficiency": most_efficient["efficiency_score"]
            },
            "detailed_performance": performance_data,
            "avg_metrics": {
                "avg_total_time_ms": sum(p["total_time_ms"] for p in performance_data) / len(performance_data),
                "avg_chunking_time_ms": sum(p["chunking_time_ms"] for p in performance_data) / len(performance_data),
                "avg_embedding_time_ms": sum(p["embedding_time_ms"] for p in performance_data) / len(performance_data),
                "avg_chunks": sum(p["total_chunks"] for p in performance_data) / len(performance_data),
                "avg_chunk_size": sum(p["avg_chunk_size"] for p in performance_data) / len(performance_data)
            }
        }
    
    def get_strategy_recommendations(
        self, 
        results: List[StrategyResult],
        use_case: str = "general"
    ) -> Dict[str, Any]:
        """Get strategy recommendations based on use case"""
        
        recommendations = {
            "speed": min(results, key=lambda r: r.processing_time_ms),
            "quality": max(results, key=lambda r: r.embedding_dimension),  # Higher dimension often means better quality
            "context": max(results, key=lambda r: r.avg_chunk_size),
            "efficiency": max(results, key=lambda r: r.total_chunks / r.processing_time_ms)
        }
        
        use_case_mapping = {
            "itsm": "Korean Optimized",
            "speed": recommendations["speed"].combo_name,
            "quality": recommendations["quality"].combo_name,
            "context": recommendations["context"].combo_name,
            "general": "Balanced Performance"
        }
        
        recommended_combo = use_case_mapping.get(use_case, "Balanced Performance")
        
        return {
            "use_case": use_case,
            "recommended_combo": recommended_combo,
            "reasoning": self._get_recommendation_reasoning(recommended_combo, results),
            "alternatives": {
                "for_speed": recommendations["speed"].combo_name,
                "for_quality": recommendations["quality"].combo_name,
                "for_context": recommendations["context"].combo_name,
                "for_efficiency": recommendations["efficiency"].combo_name
            },
            "performance_tradeoffs": self._analyze_tradeoffs(results)
        }
    
    def _get_recommendation_reasoning(self, combo_name: str, results: List[StrategyResult]) -> str:
        """Get reasoning for recommendation"""
        
        combo_result = next((r for r in results if r.combo_name == combo_name), None)
        if not combo_result:
            return "Combo not found in results"
        
        reasoning_map = {
            "Fast Processing": "Optimized for speed with lightweight models and simple chunking",
            "Korean Optimized": "Best for Korean text with semantic awareness and language-specific embeddings",
            "Context Preservation": "Maintains context across chunk boundaries with overlapping windows",
            "Balanced Performance": "Good balance of speed, quality, and resource usage"
        }
        
        return reasoning_map.get(combo_name, "Custom strategy combination")
    
    def _analyze_tradeoffs(self, results: List[StrategyResult]) -> Dict[str, str]:
        """Analyze tradeoffs between strategies"""
        
        return {
            "speed_vs_quality": "Faster strategies often use smaller models with lower dimensional embeddings",
            "chunk_size_vs_context": "Larger chunks preserve more context but may dilute semantic focus",
            "overlap_vs_storage": "Overlapping chunks improve context but increase storage requirements",
            "model_size_vs_accuracy": "Larger models (BGE-M3) provide better accuracy but slower processing"
        }