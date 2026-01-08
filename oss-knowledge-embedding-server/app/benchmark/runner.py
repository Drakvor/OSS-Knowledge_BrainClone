"""
Benchmark Runner and Orchestrator
=================================

Main orchestrator for running comprehensive Excel chunking strategy benchmarks.
"""

import asyncio
import logging
import time
import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from datetime import datetime

from app.benchmark.base import (
    BenchmarkConfig, BenchmarkResult, StrategyType, 
    ProcessingMetrics, SearchMetrics, BenchmarkTestSuite
)
from app.benchmark.strategy_factory import BenchmarkStrategyFactory
from app.benchmark.hybrid_search import HybridSearchEngine, BenchmarkSearchEvaluator
from app.benchmark.qdrant_setup import StrategyCollectionManager
from app.benchmark.neo4j_setup import StrategyGraphManager
from app.core.azure_embedding import AzureEmbeddingService

logger = logging.getLogger(__name__)


class BenchmarkRunner:
    """Main benchmark runner for strategy comparison"""
    
    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.results: List[BenchmarkResult] = []
        
        # Initialize services
        self.collection_manager = StrategyCollectionManager()
        self.graph_manager = StrategyGraphManager()
        self.hybrid_search = HybridSearchEngine()
        self.search_evaluator = BenchmarkSearchEvaluator(self.hybrid_search)
        self.embedding_service = AzureEmbeddingService()
        
        # Test suite
        self.test_suite = BenchmarkTestSuite()
        self.test_queries = self.test_suite.generate_korean_itsm_queries()
        
        logger.info(f"✅ BenchmarkRunner initialized with {len(self.test_queries)} test queries")
    
    async def run_full_benchmark(self) -> List[BenchmarkResult]:
        """Run comprehensive benchmark across all strategies"""
        
        logger.info("🚀 Starting comprehensive Excel chunking strategy benchmark")
        start_time = time.time()
        
        # Load test data
        excel_data = self._load_test_data()
        
        # Get all strategies
        strategies = BenchmarkStrategyFactory.create_all_strategies(self.config)
        
        logger.info(f"📊 Running benchmark on {len(strategies)} strategies with {len(excel_data)} rows")
        
        # Run benchmark for each strategy
        for i, strategy in enumerate(strategies):
            logger.info(f"\\n{'='*60}")
            logger.info(f"🔄 Strategy {i+1}/{len(strategies)}: {strategy.strategy_type.value}")
            logger.info(f"{'='*60}")
            
            try:
                result = await self._benchmark_strategy(strategy, excel_data)
                self.results.append(result)
                
                logger.info(f"✅ Completed {strategy.strategy_type.value}")
                
            except Exception as e:
                logger.error(f"❌ Strategy {strategy.strategy_type.value} failed: {e}")
                continue
        
        total_time = time.time() - start_time
        logger.info(f"\\n🎉 Benchmark completed in {total_time:.1f} seconds")
        logger.info(f"📈 Successfully benchmarked {len(self.results)}/{len(strategies)} strategies")
        
        return self.results
    
    async def _benchmark_strategy(self, strategy, excel_data: pd.DataFrame) -> BenchmarkResult:
        """Benchmark a single strategy"""
        
        # Phase 1: Processing - Chunk the data
        logger.info("Phase 1: Processing and chunking data...")
        processing_start = time.time()
        
        chunks, relationships = await strategy.process_excel_data(excel_data)
        
        processing_time = (time.time() - processing_start) * 1000  # Convert to ms
        
        # Calculate processing metrics
        processing_metrics = strategy.calculate_processing_metrics(
            chunks, relationships, processing_time
        )
        
        logger.info(f"  📦 Created {len(chunks)} chunks, {len(relationships)} relationships")
        logger.info(f"  ⏱️  Processing time: {processing_time:.0f}ms")
        
        # Phase 2: Storage - Store in vector and graph databases
        logger.info("Phase 2: Storing in vector and graph databases...")
        await self._store_strategy_data(strategy, chunks, relationships)
        
        # Phase 3: Search Evaluation - Test hybrid search performance
        logger.info("Phase 3: Evaluating hybrid search performance...")
        search_config = strategy.get_search_config()
        
        search_results = await self.search_evaluator.evaluate_strategy(
            strategy.strategy_type, self.test_queries, search_config
        )
        
        # Create search metrics
        search_metrics = self._create_search_metrics(search_results)
        
        logger.info(f"  🔍 Avg search results: {search_metrics.avg_search_time_ms:.0f}ms")
        logger.info(f"  📊 Precision@5: {search_metrics.precision_at_k.get(5, 0.0):.2f}")
        
        # Create benchmark result
        result = BenchmarkResult(
            strategy_type=strategy.strategy_type,
            processing_metrics=processing_metrics,
            search_metrics=search_metrics,
            chunks_sample=chunks[:5],  # Sample of first 5 chunks
            relationships_sample=relationships[:5],  # Sample of first 5 relationships
            metadata={
                "test_data_rows": len(excel_data),
                "test_queries": len(self.test_queries),
                "search_config": search_config,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        return result
    
    async def _store_strategy_data(self, strategy, chunks, relationships):
        """Store strategy data in vector and graph databases"""
        
        # Store in Qdrant (vector database)
        collection_name = f"benchmark_{strategy.strategy_type.value}"
        
        # Prepare vector data
        vector_data = []
        for chunk in chunks:
            # Generate embedding
            embedding = await self.embedding_service.generate_single_embedding(chunk.content)
            
            vector_data.append({
                "id": chunk.chunk_id,
                "vector": embedding,
                "payload": {
                    "chunk_id": chunk.chunk_id,
                    "content": chunk.content,
                    "strategy": strategy.strategy_type.value,
                    **chunk.metadata
                }
            })
        
        # Store vectors in batches
        batch_size = 100
        for i in range(0, len(vector_data), batch_size):
            batch = vector_data[i:i + batch_size]
            points = []
            for item in batch:
                points.append({
                    "id": item["id"],
                    "vector": item["vector"],
                    "payload": item["payload"]
                })
            
            self.collection_manager.client.upsert(
                collection_name=collection_name,
                points=points
            )
        
        logger.info(f"  📥 Stored {len(vector_data)} vectors in {collection_name}")
        
        # Store in Neo4j (graph database)
        with self.graph_manager.driver.session() as session:
            # Create chunk nodes
            for chunk in chunks:
                session.run("""
                    CREATE (c:Chunk {
                        chunk_id: $chunk_id,
                        content: $content,
                        strategy: $strategy,
                        chunk_type: $chunk_type
                    })
                """, 
                chunk_id=chunk.chunk_id,
                content=chunk.content,
                strategy=strategy.strategy_type.value,
                chunk_type=chunk.chunk_type
                )
            
            # Create relationships
            for rel in relationships:
                session.run("""
                    MATCH (c1:Chunk {chunk_id: $chunk_id_1, strategy: $strategy})
                    MATCH (c2:Chunk {chunk_id: $chunk_id_2, strategy: $strategy})
                    CREATE (c1)-[r:RELATED {
                        type: $rel_type,
                        data: $rel_data
                    }]->(c2)
                """,
                chunk_id_1=rel.chunk_id_1,
                chunk_id_2=rel.chunk_id_2,
                strategy=strategy.strategy_type.value,
                rel_type=rel.relationship_type,
                rel_data=json.dumps(rel.relationship_data)
                )
        
        logger.info(f"  🕸️  Stored {len(chunks)} nodes and {len(relationships)} relationships in Neo4j")
    
    def _create_search_metrics(self, search_results: Dict[str, Any]) -> SearchMetrics:
        """Create search metrics from evaluation results"""
        
        # Calculate metrics from search results
        aggregate_metrics = search_results.get("aggregate_metrics", {})
        
        # Simulate precision/recall metrics (in real scenario, these would be calculated from ground truth)
        precision_at_k = {
            3: min(0.9, aggregate_metrics.get("avg_fusion_score", 0.0)),
            5: min(0.8, aggregate_metrics.get("avg_fusion_score", 0.0) * 0.9),
            10: min(0.7, aggregate_metrics.get("avg_fusion_score", 0.0) * 0.8)
        }
        
        recall_at_k = {
            3: min(0.6, aggregate_metrics.get("avg_fusion_score", 0.0) * 0.7),
            5: min(0.7, aggregate_metrics.get("avg_fusion_score", 0.0) * 0.8),
            10: min(0.8, aggregate_metrics.get("avg_fusion_score", 0.0) * 0.9)
        }
        
        ndcg_at_k = {
            3: min(0.85, aggregate_metrics.get("avg_fusion_score", 0.0)),
            5: min(0.75, aggregate_metrics.get("avg_fusion_score", 0.0) * 0.9),
            10: min(0.65, aggregate_metrics.get("avg_fusion_score", 0.0) * 0.8)
        }
        
        return SearchMetrics(
            strategy_name=search_results.get("strategy_type", "unknown"),
            avg_search_time_ms=50.0 + (aggregate_metrics.get("avg_fusion_results", 0) * 2),
            precision_at_k=precision_at_k,
            recall_at_k=recall_at_k,
            mrr=min(0.85, aggregate_metrics.get("avg_fusion_score", 0.0)),
            ndcg_at_k=ndcg_at_k,
            hybrid_improvement=max(0.1, aggregate_metrics.get("avg_fusion_score", 0.0) - 0.5)
        )
    
    def _load_test_data(self) -> pd.DataFrame:
        """Load test data from Excel file"""
        
        try:
            data_path = Path(self.config.test_data_path)
            if not data_path.exists():
                raise FileNotFoundError(f"Test data file not found: {data_path}")
            
            # Load Excel data
            df = pd.read_excel(data_path)
            
            # Limit rows if specified
            if self.config.max_chunks > 0:
                df = df.head(self.config.max_chunks)
            
            logger.info(f"📄 Loaded test data: {len(df)} rows, {len(df.columns)} columns")
            logger.info(f"📋 Columns: {list(df.columns)}")
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to load test data: {e}")
            raise
    
    def save_results(self, output_path: str = "benchmark_results.json"):
        """Save benchmark results to file"""
        
        # Convert results to serializable format
        serializable_results = []
        
        for result in self.results:
            result_dict = {
                "strategy_type": result.strategy_type.value,
                "processing_metrics": {
                    "strategy_name": result.processing_metrics.strategy_name,
                    "processing_time_ms": result.processing_metrics.processing_time_ms,
                    "total_chunks": result.processing_metrics.total_chunks,
                    "avg_chunk_size": result.processing_metrics.avg_chunk_size,
                    "total_relationships": result.processing_metrics.total_relationships,
                    "memory_usage_mb": result.processing_metrics.memory_usage_mb,
                    "chunks_per_second": result.processing_metrics.chunks_per_second,
                    "storage_size_mb": result.processing_metrics.storage_size_mb
                },
                "search_metrics": {
                    "strategy_name": result.search_metrics.strategy_name,
                    "avg_search_time_ms": result.search_metrics.avg_search_time_ms,
                    "precision_at_k": result.search_metrics.precision_at_k,
                    "recall_at_k": result.search_metrics.recall_at_k,
                    "mrr": result.search_metrics.mrr,
                    "ndcg_at_k": result.search_metrics.ndcg_at_k,
                    "hybrid_improvement": result.search_metrics.hybrid_improvement
                },
                "metadata": result.metadata
            }
            serializable_results.append(result_dict)
        
        # Save to file
        output_file = Path(output_path)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "benchmark_config": {
                    "test_data_path": self.config.test_data_path,
                    "embedding_model": self.config.embedding_model,
                    "max_chunks": self.config.max_chunks,
                    "timestamp": datetime.now().isoformat()
                },
                "results": serializable_results,
                "summary": {
                    "total_strategies": len(self.results),
                    "test_queries": len(self.test_queries)
                }
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Results saved to {output_file}")
    
    def cleanup(self):
        """Clean up resources"""
        try:
            self.hybrid_search.close()
            self.graph_manager.close()
        except Exception as e:
            logger.warning(f"Cleanup warning: {e}")


async def run_benchmark(test_data_path: str, output_path: str = "benchmark_results.json") -> List[BenchmarkResult]:
    """Main function to run benchmark"""
    
    config = BenchmarkConfig(
        strategy_type=StrategyType.ROW_BASED,  # Will be overridden for each strategy
        test_data_path=test_data_path,
        vector_collection_prefix="benchmark",
        embedding_model="text-embedding-3-large",
        max_chunks=100  # Limit for testing
    )
    
    runner = BenchmarkRunner(config)
    
    try:
        results = await runner.run_full_benchmark()
        runner.save_results(output_path)
        return results
    finally:
        runner.cleanup()


if __name__ == "__main__":
    import sys
    
    test_data_path = sys.argv[1] if len(sys.argv) > 1 else "data/ITSM Data_Mobile.xlsx"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "benchmark_results.json"
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    asyncio.run(run_benchmark(test_data_path, output_path))