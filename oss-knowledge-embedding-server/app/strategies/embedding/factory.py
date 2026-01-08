"""
Embedding Strategy Factory
=========================

Factory for creating and managing different embedding strategies.
Provides a unified interface for strategy creation and registration.
"""

from typing import Dict, Type, List
from app.strategies.embedding.base import BaseEmbeddingStrategy, EmbeddingConfig, EmbeddingStrategyType
# BGE strategy removed - using Azure OpenAI instead
from app.strategies.embedding.sentence_bert import SentenceBERTEmbeddingStrategy


class EmbeddingStrategyFactory:
    """Factory for creating embedding strategies"""
    
    # Registry of available strategies
    _strategies: Dict[EmbeddingStrategyType, Type[BaseEmbeddingStrategy]] = {
        EmbeddingStrategyType.SENTENCE_BERT: SentenceBERTEmbeddingStrategy,
    }
    
    @classmethod
    def create_strategy(
        cls, 
        strategy_type: EmbeddingStrategyType, 
        config: EmbeddingConfig
    ) -> BaseEmbeddingStrategy:
        """Create an embedding strategy instance"""
        
        if strategy_type not in cls._strategies:
            available = list(cls._strategies.keys())
            raise ValueError(
                f"Unknown embedding strategy: {strategy_type}. "
                f"Available strategies: {[s.value for s in available]}"
            )
        
        strategy_class = cls._strategies[strategy_type]
        return strategy_class(config)
    
    @classmethod
    def get_available_strategies(cls) -> List[EmbeddingStrategyType]:
        """Get list of available embedding strategies"""
        return list(cls._strategies.keys())
    
    @classmethod
    def register_strategy(
        cls, 
        strategy_type: EmbeddingStrategyType, 
        strategy_class: Type[BaseEmbeddingStrategy]
    ):
        """Register a new embedding strategy"""
        if not issubclass(strategy_class, BaseEmbeddingStrategy):
            raise TypeError(
                f"Strategy class must inherit from BaseEmbeddingStrategy, "
                f"got {strategy_class}"
            )
        
        cls._strategies[strategy_type] = strategy_class
    
    @classmethod
    def create_default_configs(cls) -> Dict[EmbeddingStrategyType, EmbeddingConfig]:
        """Create default configurations for all strategies"""
        
        return {
            EmbeddingStrategyType.SENTENCE_BERT: EmbeddingConfig(
                strategy_type=EmbeddingStrategyType.SENTENCE_BERT,
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                device="auto", 
                batch_size=32,
                max_sequence_length=512,
                normalize_embeddings=True
            )
        }
    
    @classmethod
    def get_strategy_comparison(cls) -> Dict[str, Dict]:
        """Get comparison info for all available strategies"""
        
        comparison = {}
        configs = cls.create_default_configs()
        
        for strategy_type in cls._strategies:
            config = configs[strategy_type]
            strategy = cls.create_strategy(strategy_type, config)
            comparison[strategy_type.value] = strategy.get_strategy_info()
        
        return comparison
    
    @classmethod
    def get_recommended_strategy(cls, use_case: str, language: str = "korean") -> EmbeddingStrategyType:
        """Get recommended strategy for specific use case"""
        
        recommendations = {
            ("english", "general"): EmbeddingStrategyType.SENTENCE_BERT,
            ("fast", "english"): EmbeddingStrategyType.SENTENCE_BERT,
        }
        
        key = (language.lower(), use_case.lower())
        return recommendations.get(key, EmbeddingStrategyType.SENTENCE_BERT)