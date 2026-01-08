"""
Qdrant Collection Setup for Strategy Benchmarking
================================================

Creates strategy-specific collections for isolated testing.
"""

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, CreateCollection
from typing import List, Dict
import logging

from app.benchmark.base import StrategyType

logger = logging.getLogger(__name__)


class StrategyCollectionManager:
    """Manages strategy-specific Qdrant collections"""
    
    def __init__(self, qdrant_host: str = "localhost", qdrant_port: int = 6333):
        self.client = QdrantClient(host=qdrant_host, port=qdrant_port)
        self.vector_size = 3072  # OpenAI text-embedding-3-large embedding size
        self.distance = Distance.COSINE
        
    def create_strategy_collections(self, strategies: List[StrategyType]) -> Dict[str, str]:
        """Create separate collections for each strategy
        
        Returns:
            Dict mapping strategy_type -> collection_name
        """
        collection_mapping = {}
        
        for strategy in strategies:
            collection_name = f"benchmark_{strategy.value}"
            
            try:
                # Delete existing collection if it exists
                collections = self.client.get_collections()
                if collection_name in [col.name for col in collections.collections]:
                    self.client.delete_collection(collection_name)
                    logger.info(f"Deleted existing collection: {collection_name}")
                
                # Create new collection
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=self.distance
                    )
                )
                
                collection_mapping[strategy.value] = collection_name
                logger.info(f"Created collection: {collection_name}")
                
            except Exception as e:
                logger.error(f"Failed to create collection {collection_name}: {e}")
                raise
        
        return collection_mapping
    
    def get_collection_info(self, collection_name: str) -> Dict:
        """Get collection information and stats"""
        try:
            info = self.client.get_collection(collection_name)
            return {
                "name": collection_name,
                "vectors_count": info.vectors_count,
                "status": info.status,
                "config": {
                    "vector_size": info.config.params.vectors.size,
                    "distance": info.config.params.vectors.distance
                }
            }
        except Exception as e:
            logger.error(f"Failed to get collection info for {collection_name}: {e}")
            return {}
    
    def cleanup_strategy_collections(self, strategies: List[StrategyType]) -> None:
        """Clean up all strategy collections"""
        for strategy in strategies:
            collection_name = f"benchmark_{strategy.value}"
            try:
                self.client.delete_collection(collection_name)
                logger.info(f"Deleted collection: {collection_name}")
            except Exception as e:
                logger.warning(f"Could not delete collection {collection_name}: {e}")


def setup_benchmark_collections() -> Dict[str, str]:
    """Setup all benchmark collections
    
    Returns:
        Dict mapping strategy names to collection names
    """
    strategies = list(StrategyType)
    manager = StrategyCollectionManager()
    
    collection_mapping = manager.create_strategy_collections(strategies)
    
    # Verify all collections were created
    for strategy_name, collection_name in collection_mapping.items():
        info = manager.get_collection_info(collection_name)
        if info:
            logger.info(f"✅ {strategy_name}: {collection_name} ({info['status']})")
        else:
            logger.error(f"❌ {strategy_name}: Failed to verify collection")
    
    return collection_mapping


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Setting up strategy-specific Qdrant collections...")
    collections = setup_benchmark_collections()
    
    print(f"\nCreated {len(collections)} collections:")
    for strategy, collection in collections.items():
        print(f"  {strategy} -> {collection}")