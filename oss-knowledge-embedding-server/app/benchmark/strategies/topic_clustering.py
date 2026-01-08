"""
Topic Clustering Excel Chunking Strategy
========================================

Strategy 7: Topic-based clustering using semantic similarity.
Groups semantically similar rows into topic-coherent chunks.
"""

import pandas as pd
from typing import List, Tuple, Dict, Any, Optional
import logging
import numpy as np
from collections import defaultdict, Counter
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity

from app.benchmark.base import BenchmarkStrategy, BenchmarkConfig, StrategyType
from app.processors.base.base_models import ProcessedChunk, ChunkRelationship

logger = logging.getLogger(__name__)


class TopicClusteringStrategy(BenchmarkStrategy):
    """Topic clustering chunking strategy implementation"""
    
    def __init__(self, config: BenchmarkConfig):
        super().__init__(config)
        self.target_clusters = 5  # Target number of topic clusters
        self.min_chunk_size = 2
        self.max_chunk_size = 10
        self.similarity_threshold = 0.3
        self.korean_stopwords = [
            '이', '그', '저', '것', '수', '등', '및', '또는', '그리고', '하지만', '그러나', 
            '때문에', '이다', '있다', '없다', '한다', '된다', '같다', '다른'
        ]
    
    async def process_excel_data(self, excel_data: pd.DataFrame) -> Tuple[List[ProcessedChunk], List[ChunkRelationship]]:
        """Process Excel data using topic clustering"""
        
        chunks = []
        relationships = []
        
        headers = list(excel_data.columns)
        total_rows = len(excel_data)
        
        logger.info(f"Processing {total_rows} rows with topic clustering (target clusters: {self.target_clusters})")
        
        # Step 1: Extract text features from all rows
        row_features = self._extract_row_features(excel_data, headers)
        
        # Step 2: Perform topic clustering
        cluster_assignments, cluster_info = self._perform_topic_clustering(row_features, total_rows)
        
        # Step 3: Create topic-based chunks
        topic_chunks = []
        
        for cluster_id, cluster_data in cluster_info.items():
            if not cluster_data["row_indices"]:
                continue
            
            # Split large clusters into multiple chunks
            cluster_chunks = self._create_cluster_chunks(
                excel_data, headers, cluster_id, cluster_data, len(topic_chunks)
            )
            
            topic_chunks.extend(cluster_chunks)
        
        chunks.extend(topic_chunks)
        
        # Step 4: Create topic relationships
        topic_relationships = self._create_topic_relationships(chunks, cluster_info)
        relationships.extend(topic_relationships)
        
        # Step 5: Handle outlier rows (if any)
        outlier_chunks = self._handle_outlier_rows(excel_data, headers, cluster_assignments, len(chunks))
        chunks.extend(outlier_chunks)
        
        logger.info(f"Created {len(chunks)} topic-clustered chunks with {len(relationships)} relationships")
        logger.info(f"Topic distribution: {[len(cluster_data['row_indices']) for cluster_data in cluster_info.values()]}")
        
        return chunks, relationships
    
    def _extract_row_features(self, data: pd.DataFrame, headers: List[str]) -> List[str]:
        """Extract text features from each row for clustering"""
        
        row_features = []
        
        for _, row in data.iterrows():
            # Combine all text from the row
            row_text_parts = []
            
            for col in headers:
                if pd.notna(row[col]):
                    cell_value = str(row[col]).strip()
                    if cell_value:
                        row_text_parts.append(cell_value)
            
            # Create combined text for this row
            combined_text = " ".join(row_text_parts)
            
            # Clean and preprocess text
            cleaned_text = self._preprocess_text(combined_text)
            row_features.append(cleaned_text)
        
        return row_features
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for clustering"""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep Korean characters
        text = re.sub(r'[^\w\s가-힣]', ' ', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove Korean stopwords
        words = text.split()
        filtered_words = [word for word in words if word not in self.korean_stopwords]
        
        return ' '.join(filtered_words)
    
    def _perform_topic_clustering(self, row_features: List[str], total_rows: int) -> Tuple[List[int], Dict[int, Dict[str, Any]]]:
        """Perform topic clustering on row features"""
        
        # Create TF-IDF vectors
        vectorizer = TfidfVectorizer(
            max_features=1000,
            min_df=1,
            max_df=0.8,
            ngram_range=(1, 2),
            stop_words=None  # We already removed Korean stopwords
        )
        
        try:
            tfidf_matrix = vectorizer.fit_transform(row_features)
        except ValueError:
            # Fallback if TF-IDF fails
            logger.warning("TF-IDF failed, using simple word counting")
            return self._fallback_clustering(row_features, total_rows)
        
        # Adjust number of clusters based on data size
        n_clusters = min(self.target_clusters, max(2, total_rows // 4))
        
        # Perform K-means clustering
        try:
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(tfidf_matrix)
        except Exception as e:
            logger.warning(f"K-means clustering failed: {e}, using fallback")
            return self._fallback_clustering(row_features, total_rows)
        
        # Analyze clusters
        cluster_info = self._analyze_clusters(
            cluster_labels, row_features, tfidf_matrix, vectorizer, kmeans
        )
        
        return cluster_labels.tolist(), cluster_info
    
    def _fallback_clustering(self, row_features: List[str], total_rows: int) -> Tuple[List[int], Dict[int, Dict[str, Any]]]:
        """Fallback clustering method when TF-IDF fails"""
        
        logger.info("Using fallback clustering based on text similarity")
        
        # Simple clustering based on text length and common words
        cluster_assignments = []
        cluster_info = defaultdict(lambda: {
            "row_indices": [],
            "topic_keywords": [],
            "cluster_centroid": None,
            "coherence_score": 0.5,
            "topic_description": "일반 내용"
        })
        
        # Group by text length ranges
        for i, text in enumerate(row_features):
            text_length = len(text)
            
            if text_length < 50:
                cluster_id = 0  # Short text
            elif text_length < 150:
                cluster_id = 1  # Medium text
            else:
                cluster_id = 2  # Long text
            
            cluster_assignments.append(cluster_id)
            cluster_info[cluster_id]["row_indices"].append(i)
        
        # Set topic descriptions
        cluster_info[0]["topic_description"] = "짧은 내용"
        cluster_info[1]["topic_description"] = "중간 길이 내용"  
        cluster_info[2]["topic_description"] = "긴 내용"
        
        return cluster_assignments, dict(cluster_info)
    
    def _analyze_clusters(self, cluster_labels: np.ndarray, row_features: List[str], 
                         tfidf_matrix, vectorizer, kmeans) -> Dict[int, Dict[str, Any]]:
        """Analyze clusters to extract topic information"""
        
        cluster_info = {}
        feature_names = vectorizer.get_feature_names_out()
        
        for cluster_id in range(max(cluster_labels) + 1):
            cluster_indices = np.where(cluster_labels == cluster_id)[0]
            
            if len(cluster_indices) == 0:
                continue
            
            # Get cluster centroid
            cluster_centroid = kmeans.cluster_centers_[cluster_id]
            
            # Find top keywords for this cluster
            top_indices = cluster_centroid.argsort()[-10:][::-1]  # Top 10 keywords
            topic_keywords = [feature_names[i] for i in top_indices if cluster_centroid[i] > 0]
            
            # Calculate cluster coherence
            cluster_tfidf = tfidf_matrix[cluster_indices]
            if cluster_tfidf.shape[0] > 1:
                coherence_score = self._calculate_cluster_coherence(cluster_tfidf)
            else:
                coherence_score = 1.0
            
            # Generate topic description
            topic_description = self._generate_topic_description(topic_keywords, cluster_indices, row_features)
            
            cluster_info[cluster_id] = {
                "row_indices": cluster_indices.tolist(),
                "topic_keywords": topic_keywords,
                "cluster_centroid": cluster_centroid,
                "coherence_score": coherence_score,
                "topic_description": topic_description,
                "cluster_size": len(cluster_indices)
            }
        
        return cluster_info
    
    def _calculate_cluster_coherence(self, cluster_tfidf) -> float:
        """Calculate coherence score for a cluster"""
        
        # Calculate pairwise cosine similarity
        similarity_matrix = cosine_similarity(cluster_tfidf)
        
        # Get average similarity (excluding diagonal)
        n_docs = similarity_matrix.shape[0]
        if n_docs <= 1:
            return 1.0
        
        total_similarity = similarity_matrix.sum() - np.trace(similarity_matrix)
        avg_similarity = total_similarity / (n_docs * (n_docs - 1))
        
        return max(0.0, avg_similarity)
    
    def _generate_topic_description(self, topic_keywords: List[str], cluster_indices: np.ndarray, 
                                   row_features: List[str]) -> str:
        """Generate human-readable topic description"""
        
        if not topic_keywords:
            return "기타 주제"
        
        # Check for ITSM-specific patterns
        itsm_patterns = {
            "네트워크 문제": ["네트워크", "연결", "인터넷", "network", "connection"],
            "서버 이슈": ["서버", "server", "시스템", "system", "성능"],
            "사용자 요청": ["사용자", "요청", "신청", "user", "request"],
            "하드웨어 장애": ["하드웨어", "장비", "hardware", "equipment", "고장"],
            "소프트웨어 문제": ["소프트웨어", "프로그램", "software", "application", "앱"],
            "보안 문제": ["보안", "security", "접근", "권한", "password"]
        }
        
        # Check if keywords match ITSM patterns
        for pattern_name, pattern_keywords in itsm_patterns.items():
            if any(keyword in topic_keywords for keyword in pattern_keywords):
                return pattern_name
        
        # Default to most frequent keywords
        return f"{' + '.join(topic_keywords[:3])}" if topic_keywords else "일반 주제"
    
    def _create_cluster_chunks(self, data: pd.DataFrame, headers: List[str], cluster_id: int, 
                             cluster_data: Dict[str, Any], base_chunk_id: int) -> List[ProcessedChunk]:
        """Create chunks for a topic cluster"""
        
        chunks = []
        row_indices = cluster_data["row_indices"]
        
        # Split large clusters into multiple chunks
        for chunk_start in range(0, len(row_indices), self.max_chunk_size):
            chunk_end = min(chunk_start + self.max_chunk_size, len(row_indices))
            chunk_indices = row_indices[chunk_start:chunk_end]
            
            chunk_data = data.iloc[chunk_indices]
            
            # Create topic chunk content
            chunk_content = self._create_topic_chunk_content(
                chunk_data, headers, cluster_id, cluster_data, chunk_indices, len(chunks)
            )
            
            chunk_id = self.create_chunk_id(f"topic_c{cluster_id}", base_chunk_id + len(chunks))
            
            metadata = {
                "strategy": self.strategy_type.value,
                "chunk_type": "topic_cluster",
                "cluster_id": cluster_id,
                "topic_description": cluster_data["topic_description"],
                "topic_keywords": cluster_data["topic_keywords"],
                "coherence_score": cluster_data["coherence_score"],
                "row_indices": chunk_indices,
                "row_count": len(chunk_data),
                "columns": headers,
                "cluster_size": cluster_data["cluster_size"],
                "chunk_in_cluster": len(chunks) + 1
            }
            
            processed_chunk = ProcessedChunk(
                chunk_id=chunk_id,
                content=chunk_content,
                chunk_type="topic_clustering",
                metadata=metadata,
                source_file=self.config.test_data_path,
                processing_metadata={"strategy": "topic_clustering"}
            )
            
            chunks.append(processed_chunk)
        
        return chunks
    
    def _create_topic_chunk_content(self, chunk_data: pd.DataFrame, headers: List[str], 
                                  cluster_id: int, cluster_data: Dict[str, Any], 
                                  chunk_indices: List[int], chunk_in_cluster: int) -> str:
        """Create content for topic cluster chunk"""
        
        content_lines = [
            f"주제 클러스터 청크 (클러스터 {cluster_id})",
            f"주제: {cluster_data['topic_description']}",
            f"일관성 점수: {cluster_data['coherence_score']:.2f}",
            f"클러스터 내 청크: {chunk_in_cluster + 1}",
            f"포함 행: {len(chunk_data)}개",
            "=" * 50
        ]
        
        # Add topic analysis
        content_lines.append("\\n주제 분석:")
        content_lines.append(f"- 클러스터 ID: {cluster_id}")
        content_lines.append(f"- 주제 설명: {cluster_data['topic_description']}")
        content_lines.append(f"- 핵심 키워드: {', '.join(cluster_data['topic_keywords'][:5])}")
        content_lines.append(f"- 전체 클러스터 크기: {cluster_data['cluster_size']}행")
        content_lines.append(f"- 주제 일관성: {cluster_data['coherence_score']:.2f}")
        
        content_lines.append("\\n클러스터 데이터:")
        
        # Add chunk data with topic highlighting
        for i, (original_idx, row) in enumerate(chunk_data.iterrows()):
            row_values = []
            for header in headers:
                value = str(row[header]) if pd.notna(row[header]) else "[비어있음]"
                
                # Highlight topic keywords in content
                for keyword in cluster_data["topic_keywords"][:3]:
                    if keyword and keyword.lower() in value.lower():
                        value = value.replace(keyword, f"**{keyword}**")
                
                row_values.append(f"{header}: {value}")
            
            content_lines.append(f"행 {original_idx + 1}: " + " | ".join(row_values))
        
        return "\\n".join(content_lines)
    
    def _create_topic_relationships(self, chunks: List[ProcessedChunk], 
                                  cluster_info: Dict[int, Dict[str, Any]]) -> List[ChunkRelationship]:
        """Create relationships between topic chunks"""
        
        relationships = []
        
        # Group chunks by cluster
        clusters_chunks = defaultdict(list)
        for chunk in chunks:
            if chunk.metadata.get("cluster_id") is not None:
                cluster_id = chunk.metadata["cluster_id"]
                clusters_chunks[cluster_id].append(chunk)
        
        # Create intra-cluster relationships
        for cluster_id, cluster_chunks in clusters_chunks.items():
            if len(cluster_chunks) <= 1:
                continue
            
            # Create sequential relationships within cluster
            for i in range(len(cluster_chunks) - 1):
                relationship = ChunkRelationship(relationship_id=f"rel_{chunk_id_1}_{chunk_id_2}", from_chunk_id=chunk_id_1, to_chunk_id=chunk_id_2, confidence=0.8, 
                    chunk_id_1=cluster_chunks[i].chunk_id,
                    chunk_id_2=cluster_chunks[i + 1].chunk_id,
                    relationship_type="topic_sequence",
                    relationship_data={
                        "connection_type": "same_topic_cluster",
                        "cluster_id": cluster_id,
                        "coherence_score": cluster_info[cluster_id]["coherence_score"],
                        "topic_description": cluster_info[cluster_id]["topic_description"]
                    }
                )
                relationships.append(relationship)
        
        # Create inter-cluster relationships based on topic similarity
        cluster_ids = list(clusters_chunks.keys())
        for i, cluster_id1 in enumerate(cluster_ids):
            for cluster_id2 in cluster_ids[i + 1:]:
                topic_similarity = self._calculate_topic_similarity(
                    cluster_info[cluster_id1], cluster_info[cluster_id2]
                )
                
                if topic_similarity > self.similarity_threshold:
                    # Create relationship between representative chunks
                    chunk1 = clusters_chunks[cluster_id1][0]
                    chunk2 = clusters_chunks[cluster_id2][0]
                    
                    relationship = ChunkRelationship(relationship_id=f"rel_{chunk_id_1}_{chunk_id_2}", from_chunk_id=chunk_id_1, to_chunk_id=chunk_id_2, confidence=0.8, 
                        chunk_id_1=chunk1.chunk_id,
                        chunk_id_2=chunk2.chunk_id,
                        relationship_type="topic_similarity",
                        relationship_data={
                            "connection_type": "similar_topics",
                            "cluster_id1": cluster_id1,
                            "cluster_id2": cluster_id2,
                            "topic_similarity": topic_similarity,
                            "shared_keywords": self._find_shared_keywords(
                                cluster_info[cluster_id1]["topic_keywords"],
                                cluster_info[cluster_id2]["topic_keywords"]
                            )
                        }
                    )
                    relationships.append(relationship)
        
        return relationships
    
    def _calculate_topic_similarity(self, cluster1: Dict[str, Any], cluster2: Dict[str, Any]) -> float:
        """Calculate similarity between two topic clusters"""
        
        keywords1 = set(cluster1["topic_keywords"])
        keywords2 = set(cluster2["topic_keywords"])
        
        if not keywords1 or not keywords2:
            return 0.0
        
        # Jaccard similarity
        intersection = len(keywords1 & keywords2)
        union = len(keywords1 | keywords2)
        
        jaccard_sim = intersection / union if union > 0 else 0.0
        
        # Adjust based on coherence scores
        avg_coherence = (cluster1["coherence_score"] + cluster2["coherence_score"]) / 2
        
        return jaccard_sim * avg_coherence
    
    def _find_shared_keywords(self, keywords1: List[str], keywords2: List[str]) -> List[str]:
        """Find shared keywords between two clusters"""
        return list(set(keywords1) & set(keywords2))
    
    def _handle_outlier_rows(self, data: pd.DataFrame, headers: List[str], 
                           cluster_assignments: List[int], base_chunk_id: int) -> List[ProcessedChunk]:
        """Handle rows that don't fit well into any cluster"""
        
        # For now, we assume all rows are assigned to clusters
        # This could be extended to handle outliers from clustering
        return []
    
    def get_search_config(self) -> Dict[str, Any]:
        """Get topic clustering search configuration"""
        return {
            "strategy_name": "topic_clustering",
            "search_type": "topic_aware_semantic",
            "embedding_fields": ["content"],
            "boost_fields": {
                "topic_analysis": 1.5,
                "topic_keywords": 1.8,
                "cluster_data": 1.0,
                "coherent_content": 1.3
            },
            "filter_metadata": {
                "strategy": self.strategy_type.value,
                "chunk_type": "topic_cluster"
            },
            "topic_weights": {
                "네트워크 문제": 1.3,
                "서버 이슈": 1.2,
                "사용자 요청": 1.1,
                "하드웨어 장애": 1.2,
                "소프트웨어 문제": 1.1,
                "보안 문제": 1.4
            },
            "coherence_boost": True,
            "relationship_traversal": {
                "enabled": True,
                "max_depth": 2,
                "relationship_types": ["topic_sequence", "topic_similarity"],
                "topic_boost": True,
                "traverse_similar_topics": True
            }
        }
    
    def get_strategy_description(self) -> str:
        """Get strategy description"""
        return (
            f"Topic Clustering: Groups semantically similar rows using TF-IDF + K-means clustering. "
            f"Target clusters: {self.target_clusters}, chunk size: {self.min_chunk_size}-{self.max_chunk_size} rows. "
            f"Creates topic-based relationships with Korean ITSM domain awareness."
        )