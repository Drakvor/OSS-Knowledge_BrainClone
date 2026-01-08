"""
Chunking Strategy Factory
========================

Factory for creating and managing different chunking strategies.
Provides a unified interface for strategy creation and registration.
"""

from typing import Dict, Type, List
from app.strategies.chunking.base import BaseChunkingStrategy, ChunkingConfig, ChunkingStrategyType
from app.strategies.chunking.fixed_size import FixedSizeChunkingStrategy
from app.strategies.chunking.semantic import SemanticChunkingStrategy
from app.strategies.chunking.sliding_window import SlidingWindowChunkingStrategy
from app.strategies.chunking.excel_row import ExcelRowChunkingStrategy
from app.strategies.chunking.excel_column import ExcelColumnChunkingStrategy
from app.strategies.chunking.excel_hybrid import ExcelHybridChunkingStrategy


class ChunkingStrategyFactory:
    """Factory for creating chunking strategies"""
    
    # Registry of available strategies
    _strategies: Dict[ChunkingStrategyType, Type[BaseChunkingStrategy]] = {
        ChunkingStrategyType.FIXED_SIZE: FixedSizeChunkingStrategy,
        ChunkingStrategyType.SEMANTIC: SemanticChunkingStrategy,
        ChunkingStrategyType.SLIDING_WINDOW: SlidingWindowChunkingStrategy,
        ChunkingStrategyType.EXCEL_ROW: ExcelRowChunkingStrategy,
        ChunkingStrategyType.EXCEL_COLUMN: ExcelColumnChunkingStrategy,
        ChunkingStrategyType.EXCEL_HYBRID: ExcelHybridChunkingStrategy,
    }
    
    @classmethod
    def create_strategy(
        self, 
        strategy_type: ChunkingStrategyType, 
        config: ChunkingConfig
    ) -> BaseChunkingStrategy:
        """Create a chunking strategy instance"""
        
        if strategy_type not in self._strategies:
            available = list(self._strategies.keys())
            raise ValueError(
                f"Unknown chunking strategy: {strategy_type}. "
                f"Available strategies: {[s.value for s in available]}"
            )
        
        strategy_class = self._strategies[strategy_type]
        return strategy_class(config)
    
    @classmethod
    def get_available_strategies(self) -> List[ChunkingStrategyType]:
        """Get list of available chunking strategies"""
        return list(self._strategies.keys())
    
    @classmethod
    def register_strategy(
        self, 
        strategy_type: ChunkingStrategyType, 
        strategy_class: Type[BaseChunkingStrategy]
    ):
        """Register a new chunking strategy"""
        if not issubclass(strategy_class, BaseChunkingStrategy):
            raise TypeError(
                f"Strategy class must inherit from BaseChunkingStrategy, "
                f"got {strategy_class}"
            )
        
        self._strategies[strategy_type] = strategy_class
    
    @classmethod
    def create_default_configs(self) -> Dict[ChunkingStrategyType, ChunkingConfig]:
        """Create default configurations for all strategies"""
        
        return {
            ChunkingStrategyType.FIXED_SIZE: ChunkingConfig(
                strategy_type=ChunkingStrategyType.FIXED_SIZE,
                chunk_size=512,
                overlap=50,
                min_chunk_size=50,
                max_chunk_size=1000
            ),
            
            ChunkingStrategyType.SEMANTIC: ChunkingConfig(
                strategy_type=ChunkingStrategyType.SEMANTIC,
                chunk_size=600,
                overlap=0,  # Semantic chunking doesn't use overlap
                min_chunk_size=100,
                max_chunk_size=1200,
                semantic_threshold=0.5
            ),
            
            ChunkingStrategyType.SLIDING_WINDOW: ChunkingConfig(
                strategy_type=ChunkingStrategyType.SLIDING_WINDOW,
                chunk_size=512,
                overlap=128,  # 25% overlap
                min_chunk_size=50,
                max_chunk_size=800
            ),
            
            ChunkingStrategyType.EXCEL_ROW: ChunkingConfig(
                strategy_type=ChunkingStrategyType.EXCEL_ROW,
                chunk_size=1000,  # Not directly used
                overlap=0,
                min_chunk_size=100,
                max_chunk_size=2000,
                custom_params={
                    'rows_per_chunk': 3,
                    'include_headers': True,
                    'preserve_structure': True
                }
            ),
            
            ChunkingStrategyType.EXCEL_COLUMN: ChunkingConfig(
                strategy_type=ChunkingStrategyType.EXCEL_COLUMN,
                chunk_size=1500,
                overlap=0,
                min_chunk_size=200,
                max_chunk_size=3000,
                custom_params={
                    'columns_per_chunk': 2,
                    'include_column_names': True,
                    'sample_rows': 10,
                    'target_columns': ['상세_설명', '문제_유형', '해결_방법']
                }
            ),
            
            ChunkingStrategyType.EXCEL_HYBRID: ChunkingConfig(
                strategy_type=ChunkingStrategyType.EXCEL_HYBRID,
                chunk_size=1200,
                overlap=0,
                min_chunk_size=150,
                max_chunk_size=2500,
                custom_params={
                    'rows_per_chunk': 5,
                    'key_columns': ['문제_유형', '상태', '우선순위'],
                    'chunk_by_similarity': True,
                    'preserve_relationships': True,
                    'min_semantic_similarity': 0.3
                }
            )
        }
    
    @classmethod
    def get_strategy_comparison(self) -> Dict[str, Dict]:
        """Get comparison info for all available strategies"""
        
        comparison = {}
        configs = self.create_default_configs()
        
        for strategy_type in self._strategies:
            config = configs[strategy_type]
            strategy = self.create_strategy(strategy_type, config)
            comparison[strategy_type.value] = strategy.get_strategy_info()
        
        return comparison