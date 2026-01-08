"""
Focused Comparison: Hierarchical vs Sliding Window Strategies
===========================================================

Test the two best-performing strategies with larger dataset:
- Hierarchical (best quality)
- Sliding Window (best speed)
"""

import asyncio
import time
import logging
import pandas as pd
from typing import List, Dict, Any
import json
from datetime import datetime

from app.benchmark.base import BenchmarkConfig, StrategyType, TestQuery
from app.benchmark.strategy_factory import BenchmarkStrategyFactory
from app.benchmark.hybrid_search import HybridSearchEngine
from app.core.azure_embedding import AzureEmbeddingService
from app.benchmark.qdrant_setup import StrategyCollectionManager
from app.benchmark.neo4j_setup import StrategyGraphManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FocusedStrategyComparator:
    """Compare top 2 strategies on larger dataset"""
    
    def __init__(self):
        self.collection_manager = StrategyCollectionManager()
        self.graph_manager = StrategyGraphManager()
        self.embedding_service = AzureEmbeddingService()
        self.hybrid_search = HybridSearchEngine()
        
        # Korean ITSM test queries
        self.test_queries = [
            TestQuery("q1", "서비스 요청 처리", "specific_entity"),
            TestQuery("q2", "네트워크 연결 문제", "thematic"),
            TestQuery("q3", "시스템 장애 복구", "thematic"), 
            TestQuery("q4", "사용자 계정 문제", "analytical"),
            TestQuery("q5", "하드웨어 교체 요청", "specific_entity"),
            TestQuery("q6", "데이터베이스 백업", "thematic"),
            TestQuery("q7", "보안 업데이트", "thematic"),
            TestQuery("q8", "모바일 앱 오류", "specific_entity"),
            TestQuery("q9", "서버 성능 모니터링", "analytical"),
            TestQuery("q10", "사용자 권한 관리", "thematic")
        ]
    
    async def run_focused_comparison(self, excel_file_path: str, max_rows: int = None):
        """Run focused comparison on larger dataset"""
        
        logger.info(f"🚀 FOCUSED COMPARISON: Hierarchical vs Sliding Window")
        logger.info(f"📄 Data: {excel_file_path}")
        
        # Load test data (use more rows for larger test)
        excel_data = pd.read_excel(excel_file_path)
        if max_rows:
            excel_data = excel_data.head(max_rows)
        
        logger.info(f"📊 Dataset: {len(excel_data)} rows × {len(excel_data.columns)} columns")
        logger.info(f"🔍 Test Queries: {len(self.test_queries)} Korean ITSM scenarios")
        
        # Initialize embedding service
        await self.embedding_service.initialize()
        
        # Test only the top 2 strategies
        strategies_to_test = [
            StrategyType.HIERARCHICAL,
            StrategyType.SLIDING_WINDOW
        ]
        
        comparison_results = {}
        
        for strategy_type in strategies_to_test:
            logger.info(f"\n{'='*60}")
            logger.info(f"🔄 Testing Strategy: {strategy_type.value.upper()}")
            logger.info(f"{'='*60}")
            
            try:
                result = await self._test_strategy_performance(
                    strategy_type, excel_data, excel_file_path
                )
                comparison_results[strategy_type.value] = result
                
                logger.info(f"✅ {strategy_type.value} completed successfully")
                
                # Print immediate results
                self._print_strategy_summary(strategy_type.value, result)
                
            except Exception as e:
                logger.error(f"❌ {strategy_type.value} failed: {e}")
                comparison_results[strategy_type.value] = {"error": str(e)}
        
        # Generate comparison report
        self._generate_focused_report(comparison_results, len(excel_data))
        
        return comparison_results
    
    async def _test_strategy_performance(self, strategy_type: StrategyType, 
                                       excel_data: pd.DataFrame, file_path: str) -> Dict[str, Any]:
        """Test performance for a single strategy"""
        
        # Step 1: Create strategy and chunk data
        config = BenchmarkConfig(
            strategy_type=strategy_type,
            test_data_path=file_path,
            vector_collection_prefix="focused_test",
            max_chunks=200  # Allow more chunks for larger dataset
        )
        
        strategy = BenchmarkStrategyFactory.create_strategy(config)
        
        chunk_start = time.time()
        chunks, relationships = await strategy.process_excel_data(excel_data)
        chunk_time = time.time() - chunk_start
        
        logger.info(f"📦 Created {len(chunks)} chunks, {len(relationships)} relationships in {chunk_time:.2f}s")
        
        # Step 2: Store in databases
        store_start = time.time()
        await self._store_data(strategy_type, chunks, relationships)
        store_time = time.time() - store_start
        
        logger.info(f"💾 Stored data in {store_time:.2f}s")
        
        # Step 3: Run search queries and measure performance
        search_results = await self._run_search_queries(strategy_type, strategy.get_search_config())
        
        return {
            "strategy_type": strategy_type.value,
            "dataset_size": len(excel_data),
            "chunking_metrics": {
                "chunks_created": len(chunks),
                "relationships_created": len(relationships),
                "chunking_time": chunk_time,
                "storage_time": store_time,
                "total_processing_time": chunk_time + store_time
            },
            "search_performance": search_results,
            "chunks_sample": [
                {"id": c.chunk_id, "content": c.content[:150] + "..."} 
                for c in chunks[:5]
            ]
        }
    
    async def _store_data(self, strategy_type: StrategyType, chunks, relationships):
        """Store chunks and relationships efficiently"""
        
        collection_name = f"focused_test_{strategy_type.value}"
        
        # Clean up existing data
        try:
            self.collection_manager.client.delete_collection(collection_name)
        except:
            pass
        
        # Create fresh collection
        from qdrant_client.http.models import Distance, VectorParams
        self.collection_manager.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=3072, distance=Distance.COSINE)
        )
        
        # Store chunks with embeddings (batch process)
        logger.info("Generating embeddings and storing chunks...")
        for i, chunk in enumerate(chunks):
            if i % 10 == 0:
                logger.info(f"Processing chunk {i+1}/{len(chunks)}")
                
            embedding = await self.embedding_service.generate_single_embedding(chunk.content)
            chunk_id_int = abs(hash(chunk.chunk_id)) % (2**31)
            
            self.collection_manager.client.upsert(
                collection_name=collection_name,
                points=[{
                    "id": chunk_id_int,
                    "vector": embedding,
                    "payload": {
                        "chunk_id": chunk.chunk_id,
                        "content": chunk.content,
                        "strategy": strategy_type.value,
                        **chunk.metadata
                    }
                }]
            )
        
        # Store relationships in Neo4j
        with self.graph_manager.driver.session() as session:
            # Clean existing data
            session.run("""
                MATCH (n:Chunk {strategy: $strategy}) 
                DETACH DELETE n
            """, strategy=strategy_type.value)
            
            # Create chunk nodes (batch process)
            logger.info("Creating chunk nodes in Neo4j...")
            for chunk in chunks:
                session.run("""
                    CREATE (c:Chunk {
                        chunk_id: $chunk_id,
                        content: $content,
                        strategy: $strategy
                    })
                """, 
                chunk_id=chunk.chunk_id,
                content=chunk.content[:500],
                strategy=strategy_type.value
                )
            
            # Create relationships
            logger.info(f"Creating {len(relationships)} relationships...")
            for rel in relationships:
                try:
                    session.run("""
                        MATCH (c1:Chunk {chunk_id: $from_id, strategy: $strategy})
                        MATCH (c2:Chunk {chunk_id: $to_id, strategy: $strategy})
                        CREATE (c1)-[r:RELATED {
                            type: $rel_type,
                            confidence: $confidence
                        }]->(c2)
                    """,
                    from_id=rel.from_chunk_id,
                    to_id=rel.to_chunk_id,
                    strategy=strategy_type.value,
                    rel_type=rel.relationship_type,
                    confidence=rel.confidence
                    )
                except Exception as e:
                    logger.warning(f"Failed to create relationship: {e}")
    
    async def _run_search_queries(self, strategy_type: StrategyType, search_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run search queries and measure performance"""
        
        search_results = {
            "queries": [],
            "avg_latency_ms": 0.0,
            "avg_precision_at_5": 0.0,
            "avg_score": 0.0,
            "successful_queries": 0,
            "failed_queries": 0
        }
        
        total_latency = 0.0
        total_precision = 0.0
        total_score = 0.0
        
        logger.info(f"Running {len(self.test_queries)} search queries...")
        
        for i, query in enumerate(self.test_queries):
            logger.info(f"  Query {i+1}/{len(self.test_queries)}: '{query.query_text}'")
            query_start = time.time()
            
            try:
                results = await self.hybrid_search.search(query, strategy_type, search_config)
                
                query_latency = (time.time() - query_start) * 1000
                total_latency += query_latency
                
                # Calculate metrics
                top_5_results = results.results[:5]
                precision_at_5 = len([r for r in top_5_results if r.fusion_score > 0.5]) / 5.0
                avg_score = sum(r.fusion_score for r in top_5_results) / len(top_5_results) if top_5_results else 0.0
                
                total_precision += precision_at_5
                total_score += avg_score
                
                query_result = {
                    "query": query.query_text,
                    "query_type": query.query_type,
                    "latency_ms": query_latency,
                    "results_count": len(results.results),
                    "precision_at_5": precision_at_5,
                    "avg_score": avg_score,
                    "top_result_score": top_5_results[0].fusion_score if top_5_results else 0.0
                }
                
                search_results["queries"].append(query_result)
                logger.info(f"    ✅ {query_latency:.1f}ms, P@5={precision_at_5:.2f}, Score={avg_score:.3f}")
                
            except Exception as e:
                logger.error(f"    ❌ Query failed: {e}")
                search_results["queries"].append({
                    "query": query.query_text,
                    "error": str(e)
                })
        
        # Calculate averages
        successful_queries = [q for q in search_results["queries"] if "error" not in q]
        if successful_queries:
            search_results["avg_latency_ms"] = total_latency / len(successful_queries)
            search_results["avg_precision_at_5"] = total_precision / len(successful_queries)
            search_results["avg_score"] = total_score / len(successful_queries)
            search_results["successful_queries"] = len(successful_queries)
            search_results["failed_queries"] = len(search_results["queries"]) - len(successful_queries)
        
        return search_results
    
    def _print_strategy_summary(self, strategy_name: str, result: Dict[str, Any]):
        """Print immediate strategy results"""
        
        if "error" in result:
            print(f"\n❌ {strategy_name.upper()} FAILED: {result['error']}")
            return
        
        chunking = result.get("chunking_metrics", {})
        search = result.get("search_performance", {})
        
        print(f"\n🎯 {strategy_name.upper()} RESULTS:")
        print(f"  📦 Chunks: {chunking.get('chunks_created', 0)}")
        print(f"  🔗 Relationships: {chunking.get('relationships_created', 0)}")
        print(f"  ⏱️  Processing: {chunking.get('total_processing_time', 0):.1f}s")
        print(f"  🔍 Search Latency: {search.get('avg_latency_ms', 0):.1f}ms")
        print(f"  ⭐ Avg Score: {search.get('avg_score', 0):.3f}")
        print(f"  ✅ Success Rate: {search.get('successful_queries', 0)}/{len(self.test_queries)}")
    
    def _generate_focused_report(self, results: Dict[str, Any], dataset_size: int):
        """Generate focused comparison report"""
        
        print(f"\n🏆 FOCUSED STRATEGY COMPARISON")
        print("=" * 80)
        print(f"Dataset: {dataset_size} rows")
        print(f"Queries: {len(self.test_queries)} Korean ITSM scenarios")
        
        print(f"\n{'Strategy':<15} | {'Chunks':<7} | {'Relations':<9} | {'Process':<8} | {'Search':<8} | {'Score':<6}")
        print("-" * 80)
        
        for strategy_name, result in results.items():
            if "error" in result:
                print(f"{strategy_name:<15} | ERROR: {result['error'][:50]}")
                continue
            
            chunking = result.get("chunking_metrics", {})
            search = result.get("search_performance", {})
            
            chunks = chunking.get("chunks_created", 0)
            relations = chunking.get("relationships_created", 0)
            process_time = chunking.get("total_processing_time", 0)
            search_time = search.get("avg_latency_ms", 0)
            score = search.get("avg_score", 0)
            
            print(f"{strategy_name:<15} | {chunks:<7d} | {relations:<9d} | {process_time:<7.1f}s | {search_time:<7.1f}ms | {score:<6.3f}")
        
        # Save detailed results
        output_file = f"docs/focused_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "test_info": {
                    "dataset_size": dataset_size,
                    "strategies_tested": list(results.keys()),
                    "queries_count": len(self.test_queries),
                    "test_timestamp": datetime.now().isoformat()
                },
                "results": results
            }, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 Detailed results saved to: {output_file}")


async def main():
    """Run focused comparison"""
    comparator = FocusedStrategyComparator()
    
    # Test with more rows from the larger dataset
    results = await comparator.run_focused_comparison(
        "data/ITSM Data_Mobile.xlsx", 
        max_rows=100  # Use 100 rows instead of 30
    )
    
    return results


if __name__ == "__main__":
    asyncio.run(main())