"""
Benchmark Strategy Factory
=========================

Factory for creating and managing benchmark chunking strategies.
"""

from typing import Dict, Type, List
from app.benchmark.base import BenchmarkStrategy, BenchmarkConfig, StrategyType
from app.benchmark.strategies import (
    RowBasedStrategy,
    HierarchicalStrategy,
    ColumnSemanticStrategy,
    AdaptiveSmartStrategy,
    EntityCentricStrategy,
    SlidingWindowStrategy,
    TopicClusteringStrategy
)


class BenchmarkStrategyFactory:
    """Factory for creating benchmark strategies"""
    
    _strategies: Dict[StrategyType, Type[BenchmarkStrategy]] = {
        StrategyType.ROW_BASED: RowBasedStrategy,
        StrategyType.HIERARCHICAL: HierarchicalStrategy,
        StrategyType.COLUMN_SEMANTIC: ColumnSemanticStrategy,
        StrategyType.ADAPTIVE_SMART: AdaptiveSmartStrategy,
        StrategyType.ENTITY_CENTRIC: EntityCentricStrategy,
        StrategyType.SLIDING_WINDOW: SlidingWindowStrategy,
        StrategyType.TOPIC_CLUSTERING: TopicClusteringStrategy,
    }
    
    @classmethod
    def create_strategy(cls, config: BenchmarkConfig) -> BenchmarkStrategy:
        """Create a strategy instance from config"""
        
        strategy_type = config.strategy_type
        
        if strategy_type not in cls._strategies:
            raise ValueError(f"Unknown strategy type: {strategy_type}")
        
        strategy_class = cls._strategies[strategy_type]
        return strategy_class(config)
    
    @classmethod
    def get_available_strategies(cls) -> List[StrategyType]:
        """Get list of available strategy types"""
        return list(cls._strategies.keys())
    
    @classmethod
    def get_strategy_description(cls, strategy_type: StrategyType) -> str:
        """Get description for a strategy type"""
        
        if strategy_type not in cls._strategies:
            return f"Unknown strategy: {strategy_type}"
        
        # Create temporary config to get description
        temp_config = BenchmarkConfig(
            strategy_type=strategy_type,
            test_data_path="temp",
            vector_collection_prefix="temp"
        )
        
        strategy = cls._strategies[strategy_type](temp_config)
        return strategy.get_strategy_description()
    
    @classmethod
    def create_all_strategies(cls, base_config: BenchmarkConfig) -> List[BenchmarkStrategy]:
        """Create instances of all available strategies"""
        
        strategies = []
        
        for strategy_type in cls._strategies:
            # Create config for this strategy
            strategy_config = BenchmarkConfig(
                strategy_type=strategy_type,
                test_data_path=base_config.test_data_path,
                vector_collection_prefix=f"{base_config.vector_collection_prefix}_{strategy_type.value}",
                graph_database=base_config.graph_database,
                embedding_model=base_config.embedding_model,
                batch_size=base_config.batch_size,
                max_chunks=base_config.max_chunks,
                enable_hybrid_search=base_config.enable_hybrid_search
            )
            
            strategy = cls.create_strategy(strategy_config)
            strategies.append(strategy)
        
        return strategies