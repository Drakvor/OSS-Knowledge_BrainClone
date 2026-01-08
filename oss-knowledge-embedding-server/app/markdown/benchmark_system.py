"""
Comprehensive Markdown Chunking Strategy Benchmark System
=========================================================

Advanced benchmarking system for evaluating 10 markdown-specific chunking strategies
across multiple dimensions: storage efficiency, search quality, structural preservation,
and operational performance.
"""

import time
import json
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, asdict

import httpx
import neo4j
from sentence_transformers import SentenceTransformer

from app.markdown.base import MarkdownChunkingStrategy, MarkdownProcessingResult
from app.markdown.parser import AdvancedMarkdownParser
from app.markdown.strategies.factory import MarkdownStrategyFactory
from app.markdown.storage_schemas import MarkdownQdrantSchema, MarkdownNeo4jSchema
from app.core.azure_embedding import AzureEmbeddingService

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkConfig:
    """Configuration for benchmark execution."""
    test_data_dir: str = "app/markdown/test_data"
    qdrant_url: str = "http://localhost:6333"
    neo4j_uri: str = "neo4j://127.0.0.1:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    embedding_model: str = "text-embedding-3-large"
    device: str = "mps"
    batch_size: int = 16


@dataclass
class StrategyBenchmarkResult:
    """Results from benchmarking a single strategy."""
    strategy_name: str
    strategy_type: MarkdownChunkingStrategy
    
    # Processing metrics
    processing_time_ms: float
    parsing_time_ms: float
    chunking_time_ms: float
    embedding_time_ms: float
    storage_time_ms: float
    
    # Storage metrics
    chunks_created: int
    relationships_created: int
    avg_chunk_size: int
    storage_efficiency_score: float
    
    # Quality metrics
    structural_preservation_score: float
    semantic_coherence_score: float
    cross_reference_score: float
    
    # Search performance
    search_latency_ms: float
    search_precision: float
    search_recall: float
    search_f1_score: float
    
    # Strategy-specific metrics
    strategy_specific_metrics: Dict[str, Any]
    
    # Error information
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class DocumentBenchmarkResult:
    """Results from benchmarking all strategies on a single document."""
    document_name: str
    document_type: str
    document_size: int
    document_elements: int
    
    strategy_results: List[StrategyBenchmarkResult]
    
    # Overall document metrics
    total_benchmark_time_ms: float
    best_performing_strategy: str
    worst_performing_strategy: str


class MarkdownBenchmarkSystem:
    """Comprehensive benchmarking system for markdown strategies."""
    
    def __init__(self, config: BenchmarkConfig = None):
        self.config = config or BenchmarkConfig()
        
        # Initialize components
        self.parser = AdvancedMarkdownParser()
        self.strategy_factory = MarkdownStrategyFactory()
        self.embedding_service = None
        
        # Storage clients
        self.qdrant_client = None
        self.neo4j_driver = None
        
        # Test queries for search evaluation
        self.test_queries = {
            "structural": [
                "API authentication methods",
                "function definition examples", 
                "table data structures",
                "code implementation details"
            ],
            "semantic": [
                "user authentication workflow",
                "machine learning model training",
                "error handling best practices",
                "performance optimization techniques"
            ],
            "cross_reference": [
                "related documentation links",
                "referenced code examples",
                "cited security guidelines",
                "connected tutorial sections"
            ],
            "code_context": [
                "Python code examples with explanations",
                "API endpoint implementations",
                "testing framework usage",
                "database query optimization"
            ]
        }
    
    async def initialize(self):
        """Initialize all benchmark components."""
        logger.info("Initializing benchmark system...")
        
        # Initialize embedding service
        self.embedding_service = AzureEmbeddingService()
        await self.embedding_service.initialize()
        
        # Initialize storage clients
        await self._initialize_storage()
        
        logger.info("Benchmark system initialized successfully")
    
    async def _initialize_storage(self):
        """Initialize storage clients and create necessary schemas."""
        # Initialize Qdrant client
        self.qdrant_client = httpx.AsyncClient(base_url=self.config.qdrant_url)
        
        # Initialize Neo4j driver (optional)
        try:
            self.neo4j_driver = neo4j.GraphDatabase.driver(
                self.config.neo4j_uri,
                auth=(self.config.neo4j_user, self.config.neo4j_password)
            )
            
            # Test Neo4j connection
            with self.neo4j_driver.session() as session:
                result = session.run("RETURN 1 as test")
                assert result.single()["test"] == 1
            logger.info("Neo4j connection verified")
        except Exception as e:
            logger.warning(f"Neo4j not available: {e}")
            logger.info("Running benchmarks without graph functionality")
            self.neo4j_driver = None
        
        # Verify Qdrant connection  
        try:
            # Test Qdrant connection
            response = await self.qdrant_client.get("/collections")
            logger.info(f"Qdrant connection verified: {response.status_code}")
            
        except Exception as e:
            logger.error(f"Qdrant initialization failed: {e}")
            raise
    
    async def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """Run comprehensive benchmark across all strategies and documents."""
        logger.info("🚀 Starting comprehensive markdown chunking strategy benchmark")
        
        start_time = time.time()
        
        # Load test documents
        test_documents = await self._load_test_documents()
        logger.info(f"Loaded {len(test_documents)} test documents")
        
        # Get all available strategies
        strategies = self.strategy_factory.get_available_strategies()
        logger.info(f"Testing {len(strategies)} chunking strategies")
        
        # Run benchmarks
        document_results = []
        
        for doc_name, doc_content, doc_type in test_documents:
            logger.info(f"\\n📄 Benchmarking document: {doc_name}")
            
            doc_result = await self._benchmark_document(
                doc_name, doc_content, doc_type, strategies
            )
            document_results.append(doc_result)
        
        # Generate comprehensive analysis
        total_time = (time.time() - start_time) * 1000
        analysis = self._generate_comprehensive_analysis(document_results, total_time)
        
        # Save results
        await self._save_benchmark_results(analysis)
        
        logger.info(f"✅ Benchmark completed in {total_time:.1f}ms")
        return analysis
    
    async def _load_test_documents(self) -> List[Tuple[str, str, str]]:
        """Load all test documents from the test data directory."""
        test_data_path = Path(self.config.test_data_dir)
        documents = []
        
        # Document type mapping based on filename
        doc_type_map = {
            "technical_documentation": "technical",
            "tutorial_guide": "tutorial", 
            "knowledge_base": "reference"
        }
        
        for md_file in test_data_path.glob("*.md"):
            try:
                content = md_file.read_text(encoding='utf-8')
                doc_type = doc_type_map.get(md_file.stem, "general")
                documents.append((md_file.stem, content, doc_type))
                logger.info(f"Loaded {md_file.stem} ({len(content)} characters)")
                
            except Exception as e:
                logger.warning(f"Failed to load {md_file}: {e}")
        
        return documents
    
    async def _benchmark_document(
        self, 
        doc_name: str, 
        doc_content: str, 
        doc_type: str, 
        strategies: List[MarkdownChunkingStrategy]
    ) -> DocumentBenchmarkResult:
        """Benchmark all strategies on a single document."""
        
        doc_start_time = time.time()
        
        # Parse document once
        parse_start = time.time()
        elements = self.parser.parse(doc_content)
        parsing_time = (time.time() - parse_start) * 1000
        
        logger.info(f"  📊 Parsed {len(elements)} markdown elements")
        
        # Benchmark each strategy
        strategy_results = []
        
        for strategy_type in strategies:
            try:
                result = await self._benchmark_strategy_on_document(
                    strategy_type, elements, doc_name, doc_type, parsing_time
                )
                strategy_results.append(result)
                
                status = "✅" if result.success else "❌"
                logger.info(f"  {status} {strategy_type.value}: "
                           f"{result.chunks_created} chunks, "
                           f"{result.processing_time_ms:.1f}ms")
                
            except Exception as e:
                logger.error(f"  ❌ {strategy_type.value} failed: {e}")
                strategy_results.append(StrategyBenchmarkResult(
                    strategy_name=strategy_type.value,
                    strategy_type=strategy_type,
                    processing_time_ms=0,
                    parsing_time_ms=parsing_time,
                    chunking_time_ms=0,
                    embedding_time_ms=0,
                    storage_time_ms=0,
                    chunks_created=0,
                    relationships_created=0,
                    avg_chunk_size=0,
                    storage_efficiency_score=0,
                    structural_preservation_score=0,
                    semantic_coherence_score=0,
                    cross_reference_score=0,
                    search_latency_ms=0,
                    search_precision=0,
                    search_recall=0,
                    search_f1_score=0,
                    strategy_specific_metrics={},
                    success=False,
                    error_message=str(e)
                ))
        
        # Calculate document-level metrics
        doc_total_time = (time.time() - doc_start_time) * 1000
        successful_results = [r for r in strategy_results if r.success]
        
        if successful_results:
            best_strategy = min(successful_results, 
                               key=lambda x: x.processing_time_ms).strategy_name
            worst_strategy = max(successful_results, 
                                key=lambda x: x.processing_time_ms).strategy_name
        else:
            best_strategy = worst_strategy = "none"
        
        return DocumentBenchmarkResult(
            document_name=doc_name,
            document_type=doc_type,
            document_size=len(doc_content),
            document_elements=len(elements),
            strategy_results=strategy_results,
            total_benchmark_time_ms=doc_total_time,
            best_performing_strategy=best_strategy,
            worst_performing_strategy=worst_strategy
        )
    
    async def _benchmark_strategy_on_document(
        self,
        strategy_type: MarkdownChunkingStrategy,
        elements: List,
        doc_name: str,
        doc_type: str,
        parsing_time: float
    ) -> StrategyBenchmarkResult:
        """Benchmark a single strategy on parsed document elements."""
        
        strategy_start = time.time()
        
        # Create strategy instance
        strategy = self.strategy_factory.create_strategy(strategy_type)
        
        # Execute chunking
        chunking_start = time.time()
        chunks, relationships = strategy.chunk(elements)
        chunking_time = (time.time() - chunking_start) * 1000
        
        if not chunks:
            raise ValueError(f"Strategy {strategy_type.value} produced no chunks")
        
        # Generate embeddings
        embedding_start = time.time()
        embeddings = await self._generate_embeddings_for_chunks(chunks)
        embedding_time = (time.time() - embedding_start) * 1000
        
        # Store in databases
        storage_start = time.time()
        collection_name = await self._store_chunks_and_relationships(
            chunks, relationships, embeddings, strategy_type, doc_name
        )
        storage_time = (time.time() - storage_start) * 1000
        
        # Evaluate search performance
        search_metrics = await self._evaluate_search_performance(
            collection_name, strategy_type.value, chunks
        )
        
        # Calculate quality metrics
        quality_metrics = self._calculate_quality_metrics(chunks, relationships, elements)
        
        # Calculate storage efficiency
        storage_metrics = self._calculate_storage_efficiency(chunks, relationships)
        
        # Get strategy-specific metrics
        strategy_metrics = self._extract_strategy_specific_metrics(chunks, relationships, strategy_type)
        
        total_time = (time.time() - strategy_start) * 1000
        
        return StrategyBenchmarkResult(
            strategy_name=strategy_type.value,
            strategy_type=strategy_type,
            processing_time_ms=total_time,
            parsing_time_ms=parsing_time,
            chunking_time_ms=chunking_time,
            embedding_time_ms=embedding_time,
            storage_time_ms=storage_time,
            chunks_created=len(chunks),
            relationships_created=len(relationships),
            avg_chunk_size=sum(len(c.content) for c in chunks) // len(chunks),
            storage_efficiency_score=storage_metrics["efficiency_score"],
            structural_preservation_score=quality_metrics["structural_score"],
            semantic_coherence_score=quality_metrics["coherence_score"],
            cross_reference_score=quality_metrics["cross_reference_score"],
            search_latency_ms=search_metrics["avg_latency"],
            search_precision=search_metrics["precision"],
            search_recall=search_metrics["recall"],
            search_f1_score=search_metrics["f1_score"],
            strategy_specific_metrics=strategy_metrics
        )
    
    async def _generate_embeddings_for_chunks(self, chunks) -> List[List[float]]:
        """Generate embeddings for all chunks."""
        texts = [chunk.content for chunk in chunks]
        embeddings = []
        
        # Process in batches
        for i in range(0, len(texts), self.config.batch_size):
            batch_texts = texts[i:i + self.config.batch_size]
            
            batch_embeddings = []
            for text in batch_texts:
                embedding = await self.embedding_service.generate_single_embedding(text)
                batch_embeddings.append(embedding)
            
            embeddings.extend(batch_embeddings)
        
        return embeddings
    
    async def _store_chunks_and_relationships(
        self, 
        chunks, 
        relationships, 
        embeddings: List[List[float]], 
        strategy_type: MarkdownChunkingStrategy,
        doc_name: str
    ) -> str:
        """Store chunks and relationships in both databases."""
        
        # Create collection name
        collection_name = f"benchmark_{strategy_type.value}_{doc_name}_{int(time.time())}"
        
        # Store in Qdrant
        await self._store_in_qdrant(chunks, embeddings, collection_name)
        
        # Store in Neo4j
        await self._store_in_neo4j(chunks, relationships, strategy_type.value)
        
        return collection_name
    
    async def _store_in_qdrant(self, chunks, embeddings: List[List[float]], collection_name: str):
        """Store chunks with embeddings in Qdrant."""
        
        # Create collection
        collection_config = MarkdownQdrantSchema.get_collection_config()
        
        create_response = await self.qdrant_client.put(
            f"/collections/{collection_name}",
            json=collection_config
        )
        
        if create_response.status_code != 200:
            logger.warning(f"Collection creation response: {create_response.status_code}")
        
        # Prepare points
        points = []
        for chunk, embedding in zip(chunks, embeddings):
            point = MarkdownQdrantSchema.chunk_to_point(chunk, embedding)
            points.append(point)
        
        # Upload points
        upload_response = await self.qdrant_client.put(
            f"/collections/{collection_name}/points?wait=true",
            json={"points": points}
        )
        
        if upload_response.status_code != 200:
            raise Exception(f"Failed to upload points: {upload_response.status_code}")
    
    async def _store_in_neo4j(self, chunks, relationships, strategy_name: str):
        """Store chunks and relationships in Neo4j."""
        
        if not self.neo4j_driver:
            logger.info("Skipping Neo4j storage - driver not available")
            return
        
        def store_in_neo4j_session(tx, chunks, relationships, strategy_name):
            # Clear existing data for this strategy
            tx.run("MATCH (n:MarkdownChunk) WHERE n.strategy_used = $strategy DETACH DELETE n", 
                   strategy=strategy_name)
            
            # Create chunk nodes
            for chunk in chunks:
                node_props = MarkdownNeo4jSchema.chunk_to_node(chunk)
                node_props["strategy_used"] = strategy_name
                
                labels_str = ":".join(["MarkdownChunk"] + node_props.pop("labels", []))
                
                tx.run(f"CREATE (n:{labels_str}) SET n = $props", props=node_props)
            
            # Create relationships
            for rel in relationships:
                edge_data = MarkdownNeo4jSchema.relationship_to_edge(rel)
                
                tx.run(f"""
                    MATCH (source:MarkdownChunk {{chunk_id: $source_id, strategy_used: $strategy}})
                    MATCH (target:MarkdownChunk {{chunk_id: $target_id, strategy_used: $strategy}})
                    CREATE (source)-[r:{edge_data['type']}]->(target)
                    SET r = $props
                """, 
                source_id=edge_data['source'],
                target_id=edge_data['target'],
                strategy=strategy_name,
                props=edge_data['properties'])
        
        # Execute in Neo4j session
        with self.neo4j_driver.session() as session:
            session.execute_write(store_in_neo4j_session, chunks, relationships, strategy_name)
    
    async def _evaluate_search_performance(
        self, 
        collection_name: str, 
        strategy_name: str, 
        chunks
    ) -> Dict[str, float]:
        """Evaluate search performance using test queries."""
        
        latencies = []
        precisions = []
        recalls = []
        
        # Test different query types
        all_queries = []
        for query_type, queries in self.test_queries.items():
            all_queries.extend(queries)
        
        for query in all_queries[:8]:  # Limit for performance
            try:
                # Generate query embedding
                query_embedding = await self.embedding_service.generate_single_embedding(query)
                
                # Search in Qdrant
                search_start = time.time()
                
                search_response = await self.qdrant_client.post(
                    f"/collections/{collection_name}/points/search",
                    json={
                        "vector": query_embedding,
                        "limit": 5,
                        "with_payload": True
                    }
                )
                
                latency = (time.time() - search_start) * 1000
                latencies.append(latency)
                
                if search_response.status_code == 200:
                    results = search_response.json().get("result", [])
                    
                    # Calculate precision and recall (simplified)
                    # This is a basic implementation - in practice, you'd have ground truth
                    relevant_results = len([r for r in results if r["score"] > 0.3])
                    precision = relevant_results / max(1, len(results))
                    recall = min(1.0, relevant_results / 3)  # Assume 3 relevant docs exist
                    
                    precisions.append(precision)
                    recalls.append(recall)
                
            except Exception as e:
                logger.warning(f"Search evaluation failed for query '{query}': {e}")
        
        # Calculate metrics
        avg_latency = sum(latencies) / max(1, len(latencies))
        avg_precision = sum(precisions) / max(1, len(precisions))
        avg_recall = sum(recalls) / max(1, len(recalls))
        
        f1_score = 0
        if avg_precision + avg_recall > 0:
            f1_score = 2 * (avg_precision * avg_recall) / (avg_precision + avg_recall)
        
        return {
            "avg_latency": avg_latency,
            "precision": avg_precision,
            "recall": avg_recall,
            "f1_score": f1_score
        }
    
    def _calculate_quality_metrics(self, chunks, relationships, elements) -> Dict[str, float]:
        """Calculate quality metrics for chunking strategy."""
        
        # Structural preservation score
        structural_score = self._calculate_structural_preservation(chunks, elements)
        
        # Semantic coherence score
        coherence_score = self._calculate_semantic_coherence(chunks)
        
        # Cross-reference score
        cross_ref_score = self._calculate_cross_reference_score(chunks, relationships)
        
        return {
            "structural_score": structural_score,
            "coherence_score": coherence_score,
            "cross_reference_score": cross_ref_score
        }
    
    def _calculate_structural_preservation(self, chunks, elements) -> float:
        """Calculate how well the chunking preserves document structure."""
        
        # Check if headers are preserved
        header_elements = [e for e in elements if e.element_type.value == "header"]
        
        header_preservation = 0
        for chunk in chunks:
            chunk_headers = [e for e in chunk.elements if e.element_type.value == "header"]
            if chunk_headers:
                header_preservation += 1
        
        # Normalize by number of chunks
        if chunks:
            structure_score = min(1.0, header_preservation / len(chunks))
        else:
            structure_score = 0
        
        return structure_score
    
    def _calculate_semantic_coherence(self, chunks) -> float:
        """Calculate semantic coherence within chunks."""
        
        coherence_scores = []
        
        for chunk in chunks:
            if hasattr(chunk, 'semantic_metadata') and chunk.semantic_metadata:
                # Use strategy-provided coherence score if available
                coherence = chunk.semantic_metadata.get('coherence_score', 0.5)
                coherence_scores.append(coherence)
            else:
                # Simple heuristic: longer chunks are more coherent
                chunk_length = len(chunk.content.split())
                coherence = min(1.0, chunk_length / 200)  # Normalize by 200 words
                coherence_scores.append(coherence)
        
        return sum(coherence_scores) / max(1, len(coherence_scores))
    
    def _calculate_cross_reference_score(self, chunks, relationships) -> float:
        """Calculate cross-reference preservation score."""
        
        if not chunks:
            return 0
        
        # Count chunks with relationships
        chunks_with_rels = set()
        for rel in relationships:
            chunks_with_rels.add(rel.source_chunk_id)
            chunks_with_rels.add(rel.target_chunk_id)
        
        # Calculate connectivity
        connectivity = len(chunks_with_rels) / len(chunks)
        
        # Bonus for high-quality relationships
        quality_bonus = 0
        if relationships:
            avg_confidence = sum(rel.confidence for rel in relationships) / len(relationships)
            quality_bonus = avg_confidence * 0.2
        
        return min(1.0, connectivity + quality_bonus)
    
    def _calculate_storage_efficiency(self, chunks, relationships) -> Dict[str, float]:
        """Calculate storage efficiency metrics."""
        
        if not chunks:
            return {"efficiency_score": 0}
        
        # Calculate chunk size variance (lower is better)
        chunk_sizes = [len(chunk.content) for chunk in chunks]
        avg_size = sum(chunk_sizes) / len(chunk_sizes)
        size_variance = sum((size - avg_size) ** 2 for size in chunk_sizes) / len(chunk_sizes)
        size_consistency = 1.0 / (1.0 + size_variance / 1000)  # Normalize
        
        # Calculate relationship density
        if len(chunks) > 1:
            max_possible_rels = len(chunks) * (len(chunks) - 1) / 2
            rel_density = len(relationships) / max_possible_rels
        else:
            rel_density = 0
        
        # Overall efficiency score
        efficiency_score = (size_consistency * 0.6 + rel_density * 0.4)
        
        return {"efficiency_score": efficiency_score}
    
    def _extract_strategy_specific_metrics(self, chunks, relationships, strategy_type) -> Dict[str, Any]:
        """Extract strategy-specific metrics."""
        
        metrics = {}
        
        if strategy_type == MarkdownChunkingStrategy.STRUCTURE_AWARE_HIERARCHICAL:
            # Hierarchical-specific metrics
            hierarchy_levels = []
            for chunk in chunks:
                level = chunk.structural_metadata.get("header_level", 0)
                hierarchy_levels.append(level)
            
            metrics.update({
                "max_hierarchy_level": max(hierarchy_levels) if hierarchy_levels else 0,
                "avg_hierarchy_level": sum(hierarchy_levels) / len(hierarchy_levels) if hierarchy_levels else 0,
                "hierarchy_distribution": {str(i): hierarchy_levels.count(i) for i in range(1, 7)}
            })
        
        elif strategy_type == MarkdownChunkingStrategy.CODE_CONTEXT_COUPLING:
            # Code-specific metrics
            code_chunks = [c for c in chunks if c.structural_metadata.get("has_code", False)]
            
            metrics.update({
                "code_chunk_ratio": len(code_chunks) / len(chunks) if chunks else 0,
                "avg_code_complexity": self._calculate_avg_code_complexity(code_chunks),
                "language_distribution": self._get_language_distribution(code_chunks)
            })
        
        elif strategy_type == MarkdownChunkingStrategy.TABLE_AWARE_CONTEXTUAL:
            # Table-specific metrics
            table_chunks = [c for c in chunks if c.structural_metadata.get("has_table", False)]
            
            metrics.update({
                "table_chunk_ratio": len(table_chunks) / len(chunks) if chunks else 0,
                "avg_table_size": self._calculate_avg_table_size(table_chunks)
            })
        
        # Add more strategy-specific metrics as needed
        
        return metrics
    
    def _calculate_avg_code_complexity(self, code_chunks) -> str:
        """Calculate average code complexity for code chunks."""
        if not code_chunks:
            return "none"
        
        complexities = []
        for chunk in code_chunks:
            complexity = chunk.semantic_metadata.get("code_complexity", "simple")
            complexities.append(complexity)
        
        # Simple majority vote
        complexity_counts = {c: complexities.count(c) for c in set(complexities)}
        return max(complexity_counts.items(), key=lambda x: x[1])[0]
    
    def _get_language_distribution(self, code_chunks) -> Dict[str, int]:
        """Get distribution of programming languages in code chunks."""
        languages = []
        for chunk in code_chunks:
            lang = chunk.structural_metadata.get("primary_language", "unknown")
            languages.append(lang)
        
        return {lang: languages.count(lang) for lang in set(languages)}
    
    def _calculate_avg_table_size(self, table_chunks) -> float:
        """Calculate average table size for table chunks."""
        if not table_chunks:
            return 0
        
        sizes = []
        for chunk in table_chunks:
            rows = chunk.structural_metadata.get("table_rows", 0)
            cols = chunk.structural_metadata.get("table_columns", 0)
            sizes.append(rows * cols)
        
        return sum(sizes) / len(sizes)
    
    def _generate_comprehensive_analysis(self, document_results: List[DocumentBenchmarkResult], total_time: float) -> Dict[str, Any]:
        """Generate comprehensive analysis of all benchmark results."""
        
        logger.info("📊 Generating comprehensive analysis...")
        
        # Aggregate strategy performance across all documents
        strategy_aggregates = {}
        
        for doc_result in document_results:
            for strategy_result in doc_result.strategy_results:
                if not strategy_result.success:
                    continue
                
                strategy_name = strategy_result.strategy_name
                if strategy_name not in strategy_aggregates:
                    strategy_aggregates[strategy_name] = {
                        "results": [],
                        "success_rate": 0,
                        "total_attempts": 0
                    }
                
                strategy_aggregates[strategy_name]["results"].append(strategy_result)
                strategy_aggregates[strategy_name]["total_attempts"] += 1
        
        # Calculate success rates
        for doc_result in document_results:
            for strategy_result in doc_result.strategy_results:
                strategy_name = strategy_result.strategy_name
                if strategy_result.success:
                    strategy_aggregates[strategy_name]["success_rate"] += 1
        
        for strategy_name in strategy_aggregates:
            total_attempts = strategy_aggregates[strategy_name]["total_attempts"]
            strategy_aggregates[strategy_name]["success_rate"] /= max(1, total_attempts)
        
        # Generate rankings
        rankings = self._generate_strategy_rankings(strategy_aggregates)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(strategy_aggregates, document_results)
        
        # Compile comprehensive analysis
        analysis = {
            "benchmark_metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_execution_time_ms": total_time,
                "documents_tested": len(document_results),
                "strategies_tested": len(strategy_aggregates),
                "total_test_queries": sum(len(queries) for queries in self.test_queries.values())
            },
            
            "document_results": [asdict(result) for result in document_results],
            
            "strategy_performance_summary": self._create_performance_summary(strategy_aggregates),
            
            "rankings": rankings,
            
            "recommendations": recommendations,
            
            "detailed_analysis": {
                "performance_patterns": self._analyze_performance_patterns(document_results),
                "quality_insights": self._analyze_quality_patterns(strategy_aggregates),
                "efficiency_insights": self._analyze_efficiency_patterns(strategy_aggregates)
            }
        }
        
        return analysis
    
    def _generate_strategy_rankings(self, strategy_aggregates: Dict[str, Any]) -> Dict[str, List[str]]:
        """Generate rankings for different performance metrics."""
        
        def safe_avg(results, key):
            values = [getattr(r, key) for r in results if hasattr(r, key)]
            return sum(values) / len(values) if values else 0
        
        rankings = {}
        
        # Speed ranking (lower processing time is better)
        speed_scores = []
        for strategy_name, data in strategy_aggregates.items():
            if data["results"]:
                avg_time = safe_avg(data["results"], "processing_time_ms")
                speed_scores.append((strategy_name, avg_time))
        
        rankings["speed"] = [name for name, _ in sorted(speed_scores, key=lambda x: x[1])]
        
        # Quality ranking (higher quality scores are better)
        quality_scores = []
        for strategy_name, data in strategy_aggregates.items():
            if data["results"]:
                # Composite quality score
                struct_score = safe_avg(data["results"], "structural_preservation_score")
                coherence_score = safe_avg(data["results"], "semantic_coherence_score")
                cross_ref_score = safe_avg(data["results"], "cross_reference_score")
                
                composite_quality = (struct_score + coherence_score + cross_ref_score) / 3
                quality_scores.append((strategy_name, composite_quality))
        
        rankings["quality"] = [name for name, _ in sorted(quality_scores, key=lambda x: x[1], reverse=True)]
        
        # Search performance ranking
        search_scores = []
        for strategy_name, data in strategy_aggregates.items():
            if data["results"]:
                f1_score = safe_avg(data["results"], "search_f1_score")
                search_scores.append((strategy_name, f1_score))
        
        rankings["search_performance"] = [name for name, _ in sorted(search_scores, key=lambda x: x[1], reverse=True)]
        
        # Storage efficiency ranking
        efficiency_scores = []
        for strategy_name, data in strategy_aggregates.items():
            if data["results"]:
                efficiency = safe_avg(data["results"], "storage_efficiency_score")
                efficiency_scores.append((strategy_name, efficiency))
        
        rankings["storage_efficiency"] = [name for name, _ in sorted(efficiency_scores, key=lambda x: x[1], reverse=True)]
        
        return rankings
    
    def _generate_recommendations(self, strategy_aggregates: Dict[str, Any], document_results: List[DocumentBenchmarkResult]) -> Dict[str, str]:
        """Generate recommendations based on benchmark results."""
        
        recommendations = {}
        
        # Overall best strategy
        best_overall = self._find_best_overall_strategy(strategy_aggregates)
        recommendations["best_overall"] = f"**{best_overall}** shows the best balanced performance across all metrics"
        
        # Use case specific recommendations
        recommendations["for_technical_docs"] = self._recommend_for_document_type("technical", document_results)
        recommendations["for_tutorials"] = self._recommend_for_document_type("tutorial", document_results)
        recommendations["for_reference"] = self._recommend_for_document_type("reference", document_results)
        
        # Performance specific recommendations
        fastest_strategy = self._find_fastest_strategy(strategy_aggregates)
        recommendations["for_speed"] = f"**{fastest_strategy}** provides the fastest processing for time-critical applications"
        
        highest_quality = self._find_highest_quality_strategy(strategy_aggregates)
        recommendations["for_quality"] = f"**{highest_quality}** delivers the highest quality chunking for accuracy-critical applications"
        
        return recommendations
    
    def _find_best_overall_strategy(self, strategy_aggregates: Dict[str, Any]) -> str:
        """Find the best overall performing strategy."""
        
        strategy_scores = {}
        
        for strategy_name, data in strategy_aggregates.items():
            if not data["results"]:
                continue
            
            results = data["results"]
            
            # Normalize and combine metrics (lower is better for time, higher is better for quality)
            avg_time = sum(r.processing_time_ms for r in results) / len(results)
            avg_quality = sum((r.structural_preservation_score + r.semantic_coherence_score + r.cross_reference_score) / 3 for r in results) / len(results)
            avg_search = sum(r.search_f1_score for r in results) / len(results)
            
            # Composite score (normalize time by inverting)
            time_score = 1.0 / (1.0 + avg_time / 1000)  # Normalize time to 0-1
            composite_score = (time_score * 0.3 + avg_quality * 0.4 + avg_search * 0.3)
            
            strategy_scores[strategy_name] = composite_score
        
        if strategy_scores:
            return max(strategy_scores, key=strategy_scores.get)
        return "none"
    
    def _recommend_for_document_type(self, doc_type: str, document_results: List[DocumentBenchmarkResult]) -> str:
        """Recommend best strategy for specific document type."""
        
        type_results = [dr for dr in document_results if dr.document_type == doc_type]
        
        if not type_results:
            return "No data available for this document type"
        
        # Find strategy with best average performance on this document type
        strategy_scores = {}
        
        for doc_result in type_results:
            for strategy_result in doc_result.strategy_results:
                if not strategy_result.success:
                    continue
                
                strategy_name = strategy_result.strategy_name
                if strategy_name not in strategy_scores:
                    strategy_scores[strategy_name] = []
                
                # Use F1 score as primary metric for document type recommendations
                strategy_scores[strategy_name].append(strategy_result.search_f1_score)
        
        # Calculate averages
        avg_scores = {}
        for strategy_name, scores in strategy_scores.items():
            avg_scores[strategy_name] = sum(scores) / len(scores)
        
        if avg_scores:
            best_strategy = max(avg_scores, key=avg_scores.get)
            return f"**{best_strategy}** performs best on {doc_type} documents"
        
        return f"No sufficient data for {doc_type} document recommendations"
    
    def _find_fastest_strategy(self, strategy_aggregates: Dict[str, Any]) -> str:
        """Find the fastest strategy."""
        
        strategy_times = {}
        
        for strategy_name, data in strategy_aggregates.items():
            if data["results"]:
                avg_time = sum(r.processing_time_ms for r in data["results"]) / len(data["results"])
                strategy_times[strategy_name] = avg_time
        
        if strategy_times:
            return min(strategy_times, key=strategy_times.get)
        return "none"
    
    def _find_highest_quality_strategy(self, strategy_aggregates: Dict[str, Any]) -> str:
        """Find the highest quality strategy."""
        
        strategy_quality = {}
        
        for strategy_name, data in strategy_aggregates.items():
            if data["results"]:
                qualities = []
                for r in data["results"]:
                    quality = (r.structural_preservation_score + r.semantic_coherence_score + r.cross_reference_score) / 3
                    qualities.append(quality)
                strategy_quality[strategy_name] = sum(qualities) / len(qualities)
        
        if strategy_quality:
            return max(strategy_quality, key=strategy_quality.get)
        return "none"
    
    def _create_performance_summary(self, strategy_aggregates: Dict[str, Any]) -> Dict[str, Any]:
        """Create performance summary for each strategy."""
        
        summary = {}
        
        for strategy_name, data in strategy_aggregates.items():
            if not data["results"]:
                summary[strategy_name] = {
                    "success_rate": 0,
                    "avg_processing_time_ms": 0,
                    "avg_chunks_created": 0,
                    "avg_quality_score": 0,
                    "avg_search_performance": 0
                }
                continue
            
            results = data["results"]
            
            summary[strategy_name] = {
                "success_rate": data["success_rate"],
                "avg_processing_time_ms": sum(r.processing_time_ms for r in results) / len(results),
                "avg_chunks_created": sum(r.chunks_created for r in results) / len(results),
                "avg_relationships_created": sum(r.relationships_created for r in results) / len(results),
                "avg_quality_score": sum((r.structural_preservation_score + r.semantic_coherence_score + r.cross_reference_score) / 3 for r in results) / len(results),
                "avg_search_performance": sum(r.search_f1_score for r in results) / len(results),
                "avg_storage_efficiency": sum(r.storage_efficiency_score for r in results) / len(results)
            }
        
        return summary
    
    def _analyze_performance_patterns(self, document_results: List[DocumentBenchmarkResult]) -> List[str]:
        """Analyze patterns in performance across different documents."""
        
        patterns = []
        
        # Document type performance patterns
        type_performance = {}
        for doc_result in document_results:
            doc_type = doc_result.document_type
            if doc_type not in type_performance:
                type_performance[doc_type] = []
            
            successful_strategies = [sr for sr in doc_result.strategy_results if sr.success]
            if successful_strategies:
                avg_time = sum(sr.processing_time_ms for sr in successful_strategies) / len(successful_strategies)
                type_performance[doc_type].append(avg_time)
        
        for doc_type, times in type_performance.items():
            avg_time = sum(times) / len(times)
            patterns.append(f"{doc_type.title()} documents average {avg_time:.1f}ms processing time")
        
        return patterns
    
    def _analyze_quality_patterns(self, strategy_aggregates: Dict[str, Any]) -> List[str]:
        """Analyze quality patterns across strategies."""
        
        patterns = []
        
        # Find strategies that excel in specific quality dimensions
        struct_leaders = []
        coherence_leaders = []
        cross_ref_leaders = []
        
        for strategy_name, data in strategy_aggregates.items():
            if not data["results"]:
                continue
            
            results = data["results"]
            avg_struct = sum(r.structural_preservation_score for r in results) / len(results)
            avg_coherence = sum(r.semantic_coherence_score for r in results) / len(results)
            avg_cross_ref = sum(r.cross_reference_score for r in results) / len(results)
            
            if avg_struct > 0.8:
                struct_leaders.append(strategy_name)
            if avg_coherence > 0.7:
                coherence_leaders.append(strategy_name)
            if avg_cross_ref > 0.6:
                cross_ref_leaders.append(strategy_name)
        
        if struct_leaders:
            patterns.append(f"Best structural preservation: {', '.join(struct_leaders)}")
        if coherence_leaders:
            patterns.append(f"Best semantic coherence: {', '.join(coherence_leaders)}")
        if cross_ref_leaders:
            patterns.append(f"Best cross-reference handling: {', '.join(cross_ref_leaders)}")
        
        return patterns
    
    def _analyze_efficiency_patterns(self, strategy_aggregates: Dict[str, Any]) -> List[str]:
        """Analyze efficiency patterns across strategies."""
        
        patterns = []
        
        # Chunk size patterns
        chunk_size_patterns = {}
        
        for strategy_name, data in strategy_aggregates.items():
            if not data["results"]:
                continue
            
            results = data["results"]
            avg_chunk_size = sum(r.avg_chunk_size for r in results) / len(results)
            avg_chunks = sum(r.chunks_created for r in results) / len(results)
            
            chunk_size_patterns[strategy_name] = {
                "avg_size": avg_chunk_size,
                "avg_count": avg_chunks
            }
        
        # Find patterns
        large_chunk_strategies = [name for name, data in chunk_size_patterns.items() if data["avg_size"] > 800]
        small_chunk_strategies = [name for name, data in chunk_size_patterns.items() if data["avg_size"] < 300]
        
        if large_chunk_strategies:
            patterns.append(f"Large chunk strategies (>800 chars): {', '.join(large_chunk_strategies)}")
        if small_chunk_strategies:
            patterns.append(f"Small chunk strategies (<300 chars): {', '.join(small_chunk_strategies)}")
        
        return patterns
    
    async def _save_benchmark_results(self, analysis: Dict[str, Any]):
        """Save benchmark results to file."""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"docs/markdown_benchmark_results_{timestamp}.json"
        
        # Ensure docs directory exists
        Path("docs").mkdir(exist_ok=True)
        
        # Save results
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, default=str)
        
        logger.info(f"💾 Benchmark results saved to: {filename}")
    
    async def shutdown(self):
        """Cleanup resources."""
        if self.embedding_service:
            await self.embedding_service.shutdown()
        
        if self.qdrant_client:
            await self.qdrant_client.aclose()
        
        if self.neo4j_driver:
            self.neo4j_driver.close()
        
        logger.info("Benchmark system shutdown complete")


# Standalone execution
async def main():
    """Main execution function for running the benchmark."""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    config = BenchmarkConfig()
    benchmark_system = MarkdownBenchmarkSystem(config)
    
    try:
        await benchmark_system.initialize()
        results = await benchmark_system.run_comprehensive_benchmark()
        
        print("\\n🎯 MARKDOWN CHUNKING STRATEGY BENCHMARK COMPLETE")
        print("=" * 60)
        print(f"📊 Tested {len(results['strategy_performance_summary'])} strategies")
        print(f"📄 Processed {results['benchmark_metadata']['documents_tested']} documents")
        print(f"⏱️  Total execution time: {results['benchmark_metadata']['total_execution_time_ms']:.1f}ms")
        
        print("\\n🏆 TOP PERFORMERS:")
        rankings = results['rankings']
        print(f"🚀 Fastest: {rankings['speed'][0] if rankings['speed'] else 'N/A'}")
        print(f"🎯 Highest Quality: {rankings['quality'][0] if rankings['quality'] else 'N/A'}")
        print(f"🔍 Best Search: {rankings['search_performance'][0] if rankings['search_performance'] else 'N/A'}")
        
        print("\\n💡 RECOMMENDATIONS:")
        for use_case, recommendation in results['recommendations'].items():
            print(f"  {use_case}: {recommendation}")
        
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        raise
    
    finally:
        await benchmark_system.shutdown()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())