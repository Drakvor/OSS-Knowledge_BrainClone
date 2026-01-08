"""
Search Performance Comparison Across Chunking Strategies
========================================================

This script runs the complete pipeline for each strategy:
1. Chunk the Excel data
2. Store chunks in Qdrant + relationships in Neo4j  
3. Run hybrid search queries
4. Compare search accuracy and performance
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


class SearchPerformanceComparator:
    """Compare search performance across different chunking strategies"""
    
    def __init__(self):
        self.collection_manager = StrategyCollectionManager()
        self.graph_manager = StrategyGraphManager()
        self.embedding_service = AzureEmbeddingService()
        self.hybrid_search = HybridSearchEngine()
        
        # Korean ITSM test queries for comparison
        self.test_queries = [
            TestQuery("q1", "서비스 요청 처리", "specific_entity"),
            TestQuery("q2", "네트워크 연결 문제", "thematic"),
            TestQuery("q3", "시스템 장애 복구", "thematic"), 
            TestQuery("q4", "사용자 계정 문제", "analytical"),
            TestQuery("q5", "하드웨어 교체 요청", "specific_entity"),
            TestQuery("q6", "데이터베이스 백업", "thematic"),
            TestQuery("q7", "보안 업데이트", "thematic")
        ]
    
    async def run_full_comparison(self, excel_file_path: str, max_rows: int = 50):
        """Run complete chunking + search comparison"""
        
        logger.info(f"🚀 Starting search performance comparison")
        logger.info(f"📄 Data: {excel_file_path} (max {max_rows} rows)")
        logger.info(f"🔍 Queries: {len(self.test_queries)} Korean ITSM tests")
        
        # Load test data
        excel_data = pd.read_excel(excel_file_path).head(max_rows)
        logger.info(f"📊 Loaded {len(excel_data)} rows × {len(excel_data.columns)} columns")
        
        # Initialize embedding service
        await self.embedding_service.initialize()
        
        # Test all 7 chunking strategies
        strategies_to_test = [
            StrategyType.ROW_BASED,
            StrategyType.HIERARCHICAL,
            StrategyType.COLUMN_SEMANTIC,
            StrategyType.ADAPTIVE_SMART,
            StrategyType.ENTITY_CENTRIC,
            StrategyType.SLIDING_WINDOW,
            StrategyType.TOPIC_CLUSTERING
        ]
        
        comparison_results = {}
        
        for strategy_type in strategies_to_test:
            logger.info(f"\\n{'='*60}")
            logger.info(f"🔄 Testing Strategy: {strategy_type.value}")
            logger.info(f"{'='*60}")
            
            try:
                result = await self._test_strategy_search_performance(
                    strategy_type, excel_data, excel_file_path
                )
                comparison_results[strategy_type.value] = result
                
                logger.info(f"✅ {strategy_type.value} completed successfully")
                
            except Exception as e:
                logger.error(f"❌ {strategy_type.value} failed: {e}")
                comparison_results[strategy_type.value] = {"error": str(e)}
        
        # Generate comparison report
        self._generate_search_comparison_report(comparison_results)
        
        return comparison_results
    
    async def _test_strategy_search_performance(self, strategy_type: StrategyType, 
                                              excel_data: pd.DataFrame, file_path: str) -> Dict[str, Any]:
        """Test search performance for a single strategy"""
        
        # Step 1: Create strategy and chunk data
        config = BenchmarkConfig(
            strategy_type=strategy_type,
            test_data_path=file_path,
            vector_collection_prefix="search_test",
            max_chunks=100
        )
        
        strategy = BenchmarkStrategyFactory.create_strategy(config)
        
        chunk_start = time.time()
        chunks, relationships = await strategy.process_excel_data(excel_data)
        chunk_time = time.time() - chunk_start
        
        logger.info(f"📦 Created {len(chunks)} chunks, {len(relationships)} relationships in {chunk_time:.2f}s")
        
        # Step 2: Store in databases
        store_start = time.time()
        await self._store_chunks_and_relationships(strategy_type, chunks, relationships)
        store_time = time.time() - store_start
        
        logger.info(f"💾 Stored data in {store_time:.2f}s")
        
        # Step 3: Run search queries and measure performance
        search_results = await self._run_search_queries(strategy_type, strategy.get_search_config())
        
        return {
            "strategy_type": strategy_type.value,
            "chunking_metrics": {
                "chunks_created": len(chunks),
                "relationships_created": len(relationships),
                "chunking_time": chunk_time,
                "storage_time": store_time
            },
            "search_performance": search_results,
            "chunks_sample": [
                {"id": c.chunk_id, "content": c.content[:100] + "..."} 
                for c in chunks[:3]
            ]
        }
    
    async def _store_chunks_and_relationships(self, strategy_type: StrategyType, chunks, relationships):
        """Store chunks in Qdrant and relationships in Neo4j"""
        
        collection_name = f"search_test_{strategy_type.value}"
        
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
        
        # Store chunks with embeddings
        for i, chunk in enumerate(chunks):
            # Generate embedding
            embedding = await self.embedding_service.generate_single_embedding(chunk.content)
            
            # Convert chunk ID to integer for Qdrant (hash of string chunk ID)
            chunk_id_int = abs(hash(chunk.chunk_id)) % (2**31)  # Convert to positive 31-bit integer
            
            # Store in Qdrant
            self.collection_manager.client.upsert(
                collection_name=collection_name,
                points=[{
                    "id": chunk_id_int,
                    "vector": embedding,
                    "payload": {
                        "chunk_id": chunk.chunk_id,  # Keep original ID in payload
                        "content": chunk.content,
                        "strategy": strategy_type.value,
                        **chunk.metadata
                    }
                }]
            )
        
        # Store relationships in Neo4j
        with self.graph_manager.driver.session() as session:
            # Clean existing data for this strategy
            session.run("""
                MATCH (n:Chunk {strategy: $strategy}) 
                DETACH DELETE n
            """, strategy=strategy_type.value)
            
            # Create chunk nodes
            for chunk in chunks:
                session.run("""
                    CREATE (c:Chunk {
                        chunk_id: $chunk_id,
                        content: $content,
                        strategy: $strategy
                    })
                """, 
                chunk_id=chunk.chunk_id,
                content=chunk.content[:500],  # Limit content size
                strategy=strategy_type.value
                )
            
            # Create relationships (if any were created successfully)
            if relationships:
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
            "hybrid_effectiveness": 0.0
        }
        
        total_latency = 0.0
        total_precision = 0.0
        total_score = 0.0
        
        for query in self.test_queries:
            query_start = time.time()
            
            try:
                # Run hybrid search
                results = await self.hybrid_search.search(query, strategy_type, search_config)
                
                query_latency = (time.time() - query_start) * 1000
                total_latency += query_latency
                
                # Calculate metrics
                top_5_results = results.results[:5]
                precision_at_5 = len([r for r in top_5_results if r.fusion_score > 0.6]) / 5.0
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
                    "top_result_score": top_5_results[0].fusion_score if top_5_results else 0.0,
                    "vector_results": results.search_metrics.get("vector_results_count", 0),
                    "graph_results": results.search_metrics.get("graph_results_count", 0)
                }
                
                search_results["queries"].append(query_result)
                
                logger.info(f"  🔍 '{query.query_text}': {query_latency:.1f}ms, P@5={precision_at_5:.2f}, Score={avg_score:.3f}")
                
            except Exception as e:
                logger.error(f"  ❌ Query '{query.query_text}' failed: {e}")
                query_result = {
                    "query": query.query_text,
                    "error": str(e)
                }
                search_results["queries"].append(query_result)
        
        # Calculate averages
        successful_queries = [q for q in search_results["queries"] if "error" not in q]
        if successful_queries:
            search_results["avg_latency_ms"] = total_latency / len(successful_queries)
            search_results["avg_precision_at_5"] = total_precision / len(successful_queries)
            search_results["avg_score"] = total_score / len(successful_queries)
            search_results["successful_queries"] = len(successful_queries)
            search_results["failed_queries"] = len(search_results["queries"]) - len(successful_queries)
        
        return search_results
    
    def _generate_search_comparison_report(self, results: Dict[str, Any]):
        """Generate comparison report"""
        
        print("\\n🎯 CHUNKING STRATEGY SEARCH PERFORMANCE COMPARISON")
        print("=" * 80)
        
        # Create comparison table
        print("\\nStrategy             | Chunks | Relations | Search Latency | Precision@5 | Avg Score")
        print("-" * 80)
        
        for strategy_name, result in results.items():
            if "error" in result:
                print(f"{strategy_name:20} | ERROR: {result['error'][:50]}")
                continue
                
            chunking = result.get("chunking_metrics", {})
            search = result.get("search_performance", {})
            
            chunks = chunking.get("chunks_created", 0)
            relations = chunking.get("relationships_created", 0) 
            latency = search.get("avg_latency_ms", 0)
            precision = search.get("avg_precision_at_5", 0)
            score = search.get("avg_score", 0)
            
            print(f"{strategy_name:20} | {chunks:6d} | {relations:9d} | {latency:11.1f}ms | {precision:10.2f} | {score:8.3f}")
        
        print("\\n🔍 DETAILED SEARCH RESULTS:")
        print("-" * 50)
        
        for strategy_name, result in results.items():
            if "error" in result:
                continue
                
            search_perf = result.get("search_performance", {})
            successful = search_perf.get("successful_queries", 0)
            failed = search_perf.get("failed_queries", 0)
            
            print(f"\\n{strategy_name.upper()} STRATEGY:")
            print(f"  ✅ Successful queries: {successful}/{successful + failed}")
            print(f"  📊 Average latency: {search_perf.get('avg_latency_ms', 0):.1f}ms")
            print(f"  🎯 Average precision@5: {search_perf.get('avg_precision_at_5', 0):.2f}")
            print(f"  ⭐ Average relevance score: {search_perf.get('avg_score', 0):.3f}")
        
        # Save detailed results
        output_file = f"docs/search_comparison_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\\n💾 Detailed results saved to: {output_file}")


async def main():
    comparator = SearchPerformanceComparator()
    results = await comparator.run_full_comparison("data/ITSM Data_Mobile.xlsx", max_rows=30)
    return results


if __name__ == "__main__":
    asyncio.run(main())