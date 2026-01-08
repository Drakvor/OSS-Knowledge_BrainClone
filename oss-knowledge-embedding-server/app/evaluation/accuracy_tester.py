"""
Accuracy Testing Framework
==========================

Comprehensive framework for evaluating chunking and embedding strategy accuracy.
Uses various metrics including semantic similarity, retrieval accuracy, and clustering quality.
"""

import logging
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import asyncio

from app.strategies.orchestrator import StrategyResult

logger = logging.getLogger(__name__)


@dataclass
class AccuracyMetrics:
    """Accuracy evaluation metrics for a strategy"""
    strategy_name: str
    
    # Chunking Quality Metrics
    chunk_coherence_score: float  # 0-1, higher is better
    chunk_size_consistency: float  # 0-1, higher is better
    semantic_boundary_preservation: float  # 0-1, higher is better
    
    # Embedding Quality Metrics
    embedding_coherence: float  # 0-1, higher is better
    cluster_quality: float  # 0-1, higher is better
    semantic_similarity_preservation: float  # 0-1, higher is better
    
    # Retrieval Performance
    retrieval_precision_at_k: Dict[int, float]  # k -> precision
    retrieval_recall_at_k: Dict[int, float]    # k -> recall
    
    # Overall Scores
    overall_accuracy_score: float  # 0-1, weighted combination
    
    # Metadata
    evaluation_metadata: Dict[str, Any]


class AccuracyTester:
    """Comprehensive accuracy testing for strategy combinations"""
    
    def __init__(self):
        self.test_queries = self._generate_test_queries()
        self.ground_truth_mapping = self._create_ground_truth_mapping()
    
    def _generate_test_queries(self) -> List[Dict[str, Any]]:
        """Generate test queries for ITSM evaluation"""
        
        return [
            {
                "query": "서버 성능 모니터링 문제",
                "category": "performance",
                "expected_keywords": ["서버", "성능", "모니터링", "데이터베이스", "응답"],
                "semantic_intent": "server_performance_issues"
            },
            {
                "query": "네트워크 연결 오류",
                "category": "network",
                "expected_keywords": ["네트워크", "연결", "오류", "스위치", "포트"],
                "semantic_intent": "network_connectivity_problems"
            },
            {
                "query": "로그인 인증 실패",
                "category": "authentication",
                "expected_keywords": ["로그인", "인증", "실패", "계정", "권한"],
                "semantic_intent": "authentication_failures"
            },
            {
                "query": "프린터 하드웨어 문제",
                "category": "hardware",
                "expected_keywords": ["프린터", "하드웨어", "용지", "걸림", "점검"],
                "semantic_intent": "printer_hardware_issues"
            },
            {
                "query": "보안 로그 분석",
                "category": "security",
                "expected_keywords": ["보안", "로그", "접근", "시도", "IP"],
                "semantic_intent": "security_log_analysis"
            }
        ]
    
    def _create_ground_truth_mapping(self) -> Dict[str, List[str]]:
        """Create ground truth mappings for evaluation"""
        
        return {
            "server_performance_issues": [
                "데이터베이스 응답 지연",
                "쿼리 실행 시간",
                "서버 연결 오류",
                "성능 모니터링"
            ],
            "network_connectivity_problems": [
                "네트워크 연결 오류",
                "네트워크 스위치",
                "포트 연결",
                "내부 시스템 접근"
            ],
            "authentication_failures": [
                "로그인 실패",
                "인증 실패",
                "계정 권한",
                "사용자 계정"
            ],
            "printer_hardware_issues": [
                "프린터 용지 걸림",
                "프린터 점검",
                "하드웨어 문제",
                "HP LaserJet"
            ],
            "security_log_analysis": [
                "보안 로그",
                "접근 시도",
                "의심스러운 접근",
                "IP 주소"
            ]
        }
    
    async def evaluate_strategy_accuracy(self, result: StrategyResult) -> AccuracyMetrics:
        """Evaluate accuracy metrics for a strategy result"""
        
        logger.info(f"Evaluating accuracy for strategy: {result.combo_name}")
        
        # Chunking Quality Evaluation
        chunk_coherence = self._evaluate_chunk_coherence(result.chunks)
        chunk_consistency = self._evaluate_chunk_size_consistency(result.chunks)
        semantic_preservation = self._evaluate_semantic_boundary_preservation(result.chunks)
        
        # Embedding Quality Evaluation
        embedding_coherence = self._evaluate_embedding_coherence(result.embeddings)
        cluster_quality = self._evaluate_cluster_quality(result.embeddings)
        similarity_preservation = self._evaluate_similarity_preservation(result.chunks, result.embeddings)
        
        # Retrieval Performance
        retrieval_metrics = await self._evaluate_retrieval_performance(result)
        
        # Calculate overall score
        overall_score = self._calculate_overall_accuracy(
            chunk_coherence, chunk_consistency, semantic_preservation,
            embedding_coherence, cluster_quality, similarity_preservation,
            retrieval_metrics
        )
        
        return AccuracyMetrics(
            strategy_name=result.combo_name,
            chunk_coherence_score=chunk_coherence,
            chunk_size_consistency=chunk_consistency,
            semantic_boundary_preservation=semantic_preservation,
            embedding_coherence=embedding_coherence,
            cluster_quality=cluster_quality,
            semantic_similarity_preservation=similarity_preservation,
            retrieval_precision_at_k=retrieval_metrics["precision_at_k"],
            retrieval_recall_at_k=retrieval_metrics["recall_at_k"],
            overall_accuracy_score=overall_score,
            evaluation_metadata={
                "total_chunks": len(result.chunks),
                "total_embeddings": len(result.embeddings),
                "embedding_dimension": result.embedding_dimension,
                "evaluation_time": "real-time",
                "test_queries_used": len(self.test_queries)
            }
        )
    
    def _evaluate_chunk_coherence(self, chunks) -> float:
        """Evaluate how coherent chunks are semantically"""
        
        if not chunks:
            return 0.0
        
        coherence_scores = []
        
        for chunk in chunks:
            # Simple heuristic: evaluate sentence boundary preservation
            content = chunk.content
            sentences = content.split('.')
            
            # Coherence based on sentence completeness
            complete_sentences = sum(1 for s in sentences if s.strip() and len(s.strip()) > 10)
            total_sentences = max(1, len([s for s in sentences if s.strip()]))
            
            coherence = complete_sentences / total_sentences
            coherence_scores.append(coherence)
        
        return sum(coherence_scores) / len(coherence_scores)
    
    def _evaluate_chunk_size_consistency(self, chunks) -> float:
        """Evaluate consistency of chunk sizes"""
        
        if not chunks:
            return 0.0
        
        sizes = [len(chunk.content) for chunk in chunks]
        
        if len(sizes) < 2:
            return 1.0
        
        mean_size = np.mean(sizes)
        std_size = np.std(sizes)
        
        # Consistency score: lower coefficient of variation = higher consistency
        cv = std_size / mean_size if mean_size > 0 else 1.0
        consistency = max(0.0, 1.0 - cv)
        
        return consistency
    
    def _evaluate_semantic_boundary_preservation(self, chunks) -> float:
        """Evaluate how well semantic boundaries are preserved"""
        
        if not chunks:
            return 0.0
        
        boundary_scores = []
        
        for chunk in chunks:
            content = chunk.content.strip()
            
            # Check if chunk starts and ends at reasonable boundaries
            starts_well = (
                content[0].isupper() if content else False or
                content.startswith('■') or
                content.startswith('-') or
                any(content.startswith(prefix) for prefix in ['행 ', '티켓_', '문제_'])
            )
            
            ends_well = (
                content.endswith('.') or
                content.endswith('다') or  # Korean sentence ending
                content.endswith('음') or
                content.endswith('이다')
            )
            
            # Score based on boundary quality
            boundary_score = (int(starts_well) + int(ends_well)) / 2.0
            boundary_scores.append(boundary_score)
        
        return sum(boundary_scores) / len(boundary_scores)
    
    def _evaluate_embedding_coherence(self, embeddings) -> float:
        """Evaluate coherence of embeddings"""
        
        if len(embeddings) < 2:
            return 1.0
        
        try:
            # Convert embeddings to matrix
            embedding_matrix = np.array([emb.embedding for emb in embeddings])
            
            # Calculate pairwise similarities
            similarities = cosine_similarity(embedding_matrix)
            
            # Remove diagonal (self-similarity)
            mask = np.eye(similarities.shape[0], dtype=bool)
            similarities_no_diag = similarities[~mask]
            
            # Coherence based on distribution of similarities
            coherence = np.mean(similarities_no_diag)
            return max(0.0, min(1.0, coherence))
            
        except Exception as e:
            logger.warning(f"Could not evaluate embedding coherence: {e}")
            return 0.5
    
    def _evaluate_cluster_quality(self, embeddings) -> float:
        """Evaluate clustering quality using silhouette score"""
        
        if len(embeddings) < 10:  # Need minimum samples for clustering
            return 0.5
        
        try:
            embedding_matrix = np.array([emb.embedding for emb in embeddings])
            
            # Determine optimal number of clusters (heuristic: sqrt(n/2))
            n_clusters = max(2, min(8, int(np.sqrt(len(embeddings) / 2))))
            
            # Perform clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(embedding_matrix)
            
            # Calculate silhouette score
            silhouette = silhouette_score(embedding_matrix, cluster_labels)
            
            # Normalize to 0-1 (silhouette ranges from -1 to 1)
            normalized_score = (silhouette + 1) / 2
            
            return normalized_score
            
        except Exception as e:
            logger.warning(f"Could not evaluate cluster quality: {e}")
            return 0.5
    
    def _evaluate_similarity_preservation(self, chunks, embeddings) -> float:
        """Evaluate how well embeddings preserve text similarity"""
        
        if len(chunks) < 2 or len(embeddings) < 2:
            return 1.0
        
        try:
            # Sample pairs for efficiency (max 100 pairs)
            n_samples = min(100, len(chunks) * (len(chunks) - 1) // 2)
            
            text_similarities = []
            embedding_similarities = []
            
            # Calculate similarities for sampled pairs
            import random
            pairs = [(i, j) for i in range(len(chunks)) for j in range(i+1, len(chunks))]
            sampled_pairs = random.sample(pairs, min(n_samples, len(pairs)))
            
            for i, j in sampled_pairs:
                # Text similarity (simple Jaccard similarity)
                text1_words = set(chunks[i].content.lower().split())
                text2_words = set(chunks[j].content.lower().split())
                
                intersection = len(text1_words.intersection(text2_words))
                union = len(text1_words.union(text2_words))
                text_sim = intersection / union if union > 0 else 0
                
                # Embedding similarity
                emb1 = np.array(embeddings[i].embedding)
                emb2 = np.array(embeddings[j].embedding)
                emb_sim = cosine_similarity([emb1], [emb2])[0][0]
                
                text_similarities.append(text_sim)
                embedding_similarities.append(emb_sim)
            
            # Correlation between text and embedding similarities
            correlation = np.corrcoef(text_similarities, embedding_similarities)[0, 1]
            
            # Handle NaN correlation
            if np.isnan(correlation):
                correlation = 0.0
            
            # Normalize correlation to 0-1
            preservation_score = (correlation + 1) / 2
            
            return preservation_score
            
        except Exception as e:
            logger.warning(f"Could not evaluate similarity preservation: {e}")
            return 0.5
    
    async def _evaluate_retrieval_performance(self, result: StrategyResult) -> Dict[str, Any]:
        """Evaluate retrieval performance using test queries"""
        
        precision_at_k = {1: 0.0, 3: 0.0, 5: 0.0}
        recall_at_k = {1: 0.0, 3: 0.0, 5: 0.0}
        
        if not result.embeddings:
            return {"precision_at_k": precision_at_k, "recall_at_k": recall_at_k}
        
        try:
            # Create embedding matrix for similarity search
            embedding_matrix = np.array([emb.embedding for emb in result.embeddings])
            
            total_queries = len(self.test_queries)
            
            for query_info in self.test_queries:
                query = query_info["query"]
                expected_keywords = query_info["expected_keywords"]
                semantic_intent = query_info["semantic_intent"]
                
                # Simulate query embedding (use average of embeddings as approximation)
                query_embedding = np.mean(embedding_matrix[:5], axis=0)  # Simple approximation
                
                # Calculate similarities
                similarities = cosine_similarity([query_embedding], embedding_matrix)[0]
                
                # Get top-k results
                for k in [1, 3, 5]:
                    top_k_indices = similarities.argsort()[-k:][::-1]
                    
                    # Count relevant results
                    relevant_count = 0
                    total_relevant = len(self.ground_truth_mapping.get(semantic_intent, []))
                    
                    for idx in top_k_indices:
                        if idx < len(result.chunks):
                            chunk_content = result.chunks[idx].content.lower()
                            
                            # Check if chunk contains expected keywords
                            keyword_matches = sum(1 for kw in expected_keywords if kw in chunk_content)
                            if keyword_matches >= 2:  # At least 2 keyword matches
                                relevant_count += 1
                    
                    # Calculate precision and recall
                    precision_at_k[k] += relevant_count / k if k > 0 else 0
                    recall_at_k[k] += relevant_count / max(1, total_relevant) if total_relevant > 0 else 0
            
            # Average across all queries
            for k in precision_at_k:
                precision_at_k[k] /= max(1, total_queries)
                recall_at_k[k] /= max(1, total_queries)
            
        except Exception as e:
            logger.warning(f"Could not evaluate retrieval performance: {e}")
        
        return {"precision_at_k": precision_at_k, "recall_at_k": recall_at_k}
    
    def _calculate_overall_accuracy(
        self,
        chunk_coherence: float,
        chunk_consistency: float, 
        semantic_preservation: float,
        embedding_coherence: float,
        cluster_quality: float,
        similarity_preservation: float,
        retrieval_metrics: Dict[str, Any]
    ) -> float:
        """Calculate weighted overall accuracy score"""
        
        # Weights for different metrics
        weights = {
            "chunk_coherence": 0.15,
            "chunk_consistency": 0.10,
            "semantic_preservation": 0.15,
            "embedding_coherence": 0.15,
            "cluster_quality": 0.15,
            "similarity_preservation": 0.15,
            "retrieval_precision": 0.15
        }
        
        # Calculate weighted score
        retrieval_score = np.mean(list(retrieval_metrics["precision_at_k"].values()))
        
        overall_score = (
            weights["chunk_coherence"] * chunk_coherence +
            weights["chunk_consistency"] * chunk_consistency +
            weights["semantic_preservation"] * semantic_preservation +
            weights["embedding_coherence"] * embedding_coherence +
            weights["cluster_quality"] * cluster_quality +
            weights["similarity_preservation"] * similarity_preservation +
            weights["retrieval_precision"] * retrieval_score
        )
        
        return max(0.0, min(1.0, overall_score))
    
    async def compare_strategy_accuracy(
        self, 
        results: List[StrategyResult]
    ) -> Dict[str, Any]:
        """Compare accuracy across multiple strategies"""
        
        logger.info(f"Comparing accuracy for {len(results)} strategies")
        
        accuracy_results = []
        for result in results:
            accuracy_metrics = await self.evaluate_strategy_accuracy(result)
            accuracy_results.append(accuracy_metrics)
        
        # Find best performers
        best_overall = max(accuracy_results, key=lambda x: x.overall_accuracy_score)
        best_chunking = max(accuracy_results, key=lambda x: (
            x.chunk_coherence_score + x.chunk_size_consistency + x.semantic_boundary_preservation
        ) / 3)
        best_embedding = max(accuracy_results, key=lambda x: (
            x.embedding_coherence + x.cluster_quality + x.semantic_similarity_preservation
        ) / 3)
        best_retrieval = max(accuracy_results, key=lambda x: np.mean(list(x.retrieval_precision_at_k.values())))
        
        return {
            "summary": {
                "total_strategies_evaluated": len(results),
                "best_overall_strategy": best_overall.strategy_name,
                "best_overall_score": best_overall.overall_accuracy_score,
                "best_chunking_strategy": best_chunking.strategy_name,
                "best_embedding_strategy": best_embedding.strategy_name,
                "best_retrieval_strategy": best_retrieval.strategy_name
            },
            "detailed_results": [
                {
                    "strategy_name": metrics.strategy_name,
                    "overall_score": metrics.overall_accuracy_score,
                    "chunking_scores": {
                        "coherence": metrics.chunk_coherence_score,
                        "consistency": metrics.chunk_size_consistency,
                        "semantic_preservation": metrics.semantic_boundary_preservation
                    },
                    "embedding_scores": {
                        "coherence": metrics.embedding_coherence,
                        "cluster_quality": metrics.cluster_quality,
                        "similarity_preservation": metrics.semantic_similarity_preservation
                    },
                    "retrieval_scores": {
                        "precision_at_1": metrics.retrieval_precision_at_k[1],
                        "precision_at_3": metrics.retrieval_precision_at_k[3],
                        "precision_at_5": metrics.retrieval_precision_at_k[5]
                    }
                }
                for metrics in accuracy_results
            ],
            "accuracy_comparison": accuracy_results
        }