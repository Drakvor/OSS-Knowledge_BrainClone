"""
Search Service - Main orchestration layer for all search operations
"""

import logging
import asyncio
import time
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from app.models.search import (
    SearchType, SortOrder, SearchResult, GraphResult, SearchAnalytics, 
    SearchSuggestion, VectorSearchQuery, GraphSearchQuery, HybridSearchQuery,
    SearchResponse
)
from app.core.qdrant_client import QdrantService
from app.core.azure_embedding import AzureEmbeddingService
from app.core.azure_llm import AzureLLMService
# Container validation is now handled by the Qdrant client

logger = logging.getLogger(__name__)


class SearchService:
    """Main search service orchestrator"""
    
    def __init__(
        self,
        qdrant_service: QdrantService,
        embedding_service: AzureEmbeddingService,
        llm_service: AzureLLMService
    ):
        logger.info("Creating search service...")
        self.qdrant_service = qdrant_service
        self.embedding_service = embedding_service
        self.llm_service = llm_service
        
        # Simple in-memory analytics (in production, use Redis or database)
        self.search_count = 0
        self.search_times = []
        self.popular_queries = []
        
        logger.info("Search service initialized successfully")
    
    async def vector_search(
        self,
        query: str,
        collection: str,
        limit: int = 10,
        threshold: float = 0.7,
        include_metadata: bool = True,
        include_content: bool = True,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Perform vector similarity search"""

        logger.info("=== SEARCH SERVICE VECTOR_SEARCH START ===")
        logger.info(f"Query: '{query}'")
        logger.info(f"Collection: '{collection}'")
        logger.info(f"Limit: {limit}")
        logger.info(f"Threshold: {threshold}")
        logger.info(f"Include metadata: {include_metadata}")
        logger.info(f"Include content: {include_content}")
        logger.info(f"Filters: {filters}")
        self._track_search_metrics(query)

        # If collection is empty or None, skip search entirely for direct chat
        if not collection or collection.strip() == "":
            logger.info("Empty collection provided - skipping vector search for direct conversational chat")
            return []  # Return empty results to trigger direct LLM response

        # Container validation is now handled by the Qdrant client's get_collection_name method
        # No need to validate here - just proceed with search

        try:
            # Check if embedding service is available
            logger.info("Checking embedding service availability...")
            if self.embedding_service is None:
                logger.error("Embedding service is None!")
                raise ValueError("Embedding service is not available. Azure OpenAI service may not be properly configured.")
            else:
                logger.info("Embedding service is available")
            
            # Generate query embedding
            logger.info(f"About to generate embedding for query: '{query}'")
            logger.info("Calling embedding_service.embed_query...")
            query_vector = await self.embedding_service.embed_query(query)
            logger.info(f"Generated query vector with {len(query_vector) if query_vector else 0} dimensions")

            if not query_vector:
                logger.warning("Empty query vector generated")
                return []

            # Check if Qdrant service is available
            logger.info("Checking Qdrant service availability...")
            if self.qdrant_service is None:
                logger.error("Qdrant service is None!")
                raise ValueError("Qdrant service is not available. Vector database may not be properly configured.")
            else:
                logger.info("Qdrant service is available")
            
            # Note: Collection filter removed as data doesn't have collection field in payload
            # The container parameter is passed to Qdrant service for collection selection

            # Perform vector search
            logger.info("Calling qdrant_service.vector_search...")
            logger.info(f"Search parameters: limit={limit}, threshold={threshold}, container={collection}")
            
            # For 'general' department, search both 'embedding' and 'sparse' collections
            if collection == "general":
                logger.info("General department detected - searching both embedding and sparse collections")
                raw_results = []
                
                # Search embedding vector in general collection
                try:
                    embedding_results = await self.qdrant_service.vector_search(
                        query_vector=query_vector,
                        limit=limit,
                        score_threshold=threshold,
                        filters=filters,
                        collection_name="general",
                        vector_name="embedding"
                    )
                    if embedding_results:
                        raw_results.extend(embedding_results)
                        logger.info(f"Embedding vector returned {len(embedding_results)} results")
                except Exception as e:
                    logger.warning(f"Failed to search embedding vector: {e}")
                
                # Search sparse vector in general collection
                try:
                    sparse_results = await self.qdrant_service.vector_search(
                        query_vector=query_vector,
                        limit=limit,
                        score_threshold=threshold,
                        filters=filters,
                        collection_name="general",
                        vector_name="sparse"
                    )
                    if sparse_results:
                        raw_results.extend(sparse_results)
                        logger.info(f"Sparse vector returned {len(sparse_results)} results")
                except Exception as e:
                    logger.warning(f"Failed to search sparse vector: {e}")
                
                logger.info(f"Total results from both collections: {len(raw_results)}")
                
                # Remove duplicates and sort by score for general department
                if raw_results:
                    # Remove duplicates based on ID
                    seen_ids = set()
                    unique_results = []
                    for result in raw_results:
                        result_id = result.get("id", "")
                        if result_id not in seen_ids:
                            seen_ids.add(result_id)
                            unique_results.append(result)
                    
                    # Sort by score (descending)
                    unique_results.sort(key=lambda x: x.get("score", 0.0), reverse=True)
                    
                    # Limit results
                    raw_results = unique_results[:limit]
                    logger.info(f"After deduplication and sorting: {len(raw_results)} results")
            else:
                # For other departments, try with vector_name first (most collections have named vectors)
                try:
                    raw_results = await self.qdrant_service.vector_search(
                        query_vector=query_vector,
                        limit=limit,
                        score_threshold=threshold,
                        filters=filters,
                        container=collection,
                        vector_name="embedding"
                    )
                    logger.info(f"Qdrant returned {len(raw_results) if raw_results else 0} raw results with vector_name='embedding'")
                except Exception as e:
                    # Fallback: try without vector_name for collections without named vectors
                    logger.warning(f"Search with vector_name='embedding' failed for {collection}: {e}, trying without vector_name")
                    try:
                        raw_results = await self.qdrant_service.vector_search(
                            query_vector=query_vector,
                            limit=limit,
                            score_threshold=threshold,
                            filters=filters,
                            container=collection
                            # No vector_name for collections without named vectors
                        )
                        logger.info(f"Qdrant returned {len(raw_results) if raw_results else 0} raw results without vector_name")
                    except Exception as e2:
                        logger.error(f"Vector search failed for {collection} with and without vector_name: {e2}")
                        raise
            
            # Convert to SearchResult objects
            results = []
            for raw_result in raw_results:
                payload = raw_result.get("payload", {})
                
                result = SearchResult(
                    id=raw_result["id"],
                    content=payload.get("content", "") if include_content else "",
                    score=raw_result["score"],
                    source_file=payload.get("source_file", "unknown"),
                    chunk_type=payload.get("chunk_type", "text"),
                    metadata=payload if include_metadata else {}
                )
                results.append(result)
            
            # 유사도 측정 주석
            # Log similarity scores for each result
            logger.info(f"Vector search completed: {len(results)} results")
            # if results:
            #     scores = [result.score for result in results]
            #     print(f"[SEARCH] Similarity scores - min={min(scores):.4f}, max={max(scores):.4f}, avg={sum(scores)/len(scores):.4f}")
            #     for i, result in enumerate(results[:5], 1):  # Log top 5
            #         print(f"[SEARCH]   Result {i}: score={result.score:.4f}, source={result.source_file[:50]}")
            logger.info("=== SEARCH SERVICE VECTOR_SEARCH END ===")
            return results
            
        except Exception as e:
            logger.error("=== SEARCH SERVICE VECTOR_SEARCH ERROR ===")
            logger.error(f"Vector search failed: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error details: {repr(e)}")
            logger.error("=== SEARCH SERVICE VECTOR_SEARCH END (ERROR) ===")
            raise Exception(f"Vector search failed: {e}")
    
    
    
    async def comprehensive_search(
        self,
        query: str,
        collection: str,
        search_modes: List[SearchType],
        limit: int = 10,
        threshold: float = 0.6,
        vector_weight: float = 0.6,
        graph_weight: float = 0.4,
        max_depth: int = 3,
        sort_by: SortOrder = SortOrder.RELEVANCE,
        include_analytics: bool = False,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform comprehensive multi-modal search"""
        
        logger.info(f"Comprehensive search: {query} in collection: {collection} with modes: {search_modes}")
        self._track_search_metrics(query)

        # Validate collection first
        try:
            if not container_validator.validate_container(collection):
                validation_result = container_validator.validate_container_with_suggestions(collection)
                raise ValueError(f"Invalid collection: {validation_result['error']}. Available containers: {validation_result['available_containers']}")
        except ContainerValidationError as e:
            logger.error(f"Container validation failed: {e}")
            raise ValueError(f"Container validation failed: {e}")

        try:
            all_results = []
            analytics_data = {}
            
            # Execute different search modes
            if SearchType.VECTOR in search_modes:
                vector_results = await self.vector_search(
                    query=query,
                    collection=collection,
                    limit=limit,
                    threshold=threshold,
                    filters=filters
                )
                all_results.extend(vector_results)
                analytics_data["vector_results"] = len(vector_results)

            # Note: Graph and hybrid search modes removed as Neo4j dependency was removed
            # Only vector search is supported now
            
            # Remove duplicates while preserving order and best scores
            seen_ids = {}
            unique_results = []
            
            for result in all_results:
                if result.id in seen_ids:
                    # Keep the result with higher score
                    if result.score > seen_ids[result.id].score:
                        # Replace the existing result
                        for i, existing in enumerate(unique_results):
                            if existing.id == result.id:
                                unique_results[i] = result
                                seen_ids[result.id] = result
                                break
                else:
                    seen_ids[result.id] = result
                    unique_results.append(result)
            
            # Sort results
            if sort_by == SortOrder.RELEVANCE:
                unique_results.sort(key=lambda x: x.score, reverse=True)
            elif sort_by == SortOrder.DATE:
                # Sort by metadata date if available, otherwise by score
                unique_results.sort(
                    key=lambda x: x.metadata.get("created_at", ""), 
                    reverse=True
                )
            
            # Limit final results
            final_results = unique_results[:limit]
            
            # Generate suggestions
            suggestions = await self.get_suggestions(query, 3)
            
            result_data = {
                "results": final_results,
                "suggestions": [s.suggestion for s in suggestions]
            }
            
            if include_analytics:
                analytics_data.update({
                    "total_unique_results": len(unique_results),
                    "final_results": len(final_results),
                    "search_modes_used": search_modes,
                    "processing_timestamp": datetime.now().isoformat()
                })
                result_data["analytics"] = analytics_data
            
            logger.info(f"Comprehensive search completed: {len(final_results)} results")
            return result_data
            
        except Exception as e:
            logger.error(f"Comprehensive search failed: {e}")
            raise Exception(f"Comprehensive search failed: {e}")
    
    async def batch_search(
        self,
        queries: List[Union[VectorSearchQuery, GraphSearchQuery, HybridSearchQuery]],
        parallel: bool = True
    ) -> List[SearchResponse]:
        """Perform batch search operations"""
        
        logger.info(f"Batch search: {len(queries)} queries")
        
        try:
            if parallel:
                # Execute searches in parallel
                tasks = []
                for query in queries:
                    if isinstance(query, VectorSearchQuery):
                        task = self._execute_vector_search_query(query)
                    else:
                        task = self._create_error_response(query, "Only vector search queries are supported")
                    
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Convert exceptions to error responses
                final_results = []
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        error_response = self._create_error_response(
                            queries[i], str(result)
                        )
                        final_results.append(error_response)
                    else:
                        final_results.append(result)
                
                return final_results
            
            else:
                # Execute searches sequentially
                results = []
                for query in queries:
                    try:
                        if isinstance(query, VectorSearchQuery):
                            result = await self._execute_vector_search_query(query)
                        else:
                            result = self._create_error_response(query, "Only vector search queries are supported")
                        
                        results.append(result)
                        
                    except Exception as e:
                        error_response = self._create_error_response(query, str(e))
                        results.append(error_response)
                
                return results
                
        except Exception as e:
            logger.error(f"Batch search failed: {e}")
            raise Exception(f"Batch search failed: {e}")
    
    async def get_analytics(self) -> SearchAnalytics:
        """Get search usage analytics"""
        
        avg_time = sum(self.search_times) / len(self.search_times) if self.search_times else 0
        
        return SearchAnalytics(
            total_searches=self.search_count,
            avg_response_time_ms=avg_time,
            popular_queries=self.popular_queries[-10:],  # Last 10 queries
            search_type_distribution={
                SearchType.VECTOR: self.search_count // 2,  # Mock data
                SearchType.GRAPH: self.search_count // 4,
                SearchType.HYBRID: self.search_count // 4
            },
            success_rate=0.95,  # Mock success rate
            timestamp=datetime.now()
        )
    
    async def get_suggestions(self, query: str, limit: int = 5) -> List[SearchSuggestion]:
        """Get search query suggestions"""
        
        # Simple mock suggestions - in production, use NLP or ML models
        suggestions = []
        
        if "error" in query.lower():
            suggestions.extend([
                SearchSuggestion(suggestion="error handling", confidence=0.9, category="technical"),
                SearchSuggestion(suggestion="error logs", confidence=0.8, category="debugging"),
                SearchSuggestion(suggestion="error recovery", confidence=0.7, category="technical")
            ])
        
        if "server" in query.lower():
            suggestions.extend([
                SearchSuggestion(suggestion="server configuration", confidence=0.9, category="infrastructure"),
                SearchSuggestion(suggestion="server monitoring", confidence=0.8, category="ops"),
                SearchSuggestion(suggestion="server deployment", confidence=0.7, category="deployment")
            ])
        
        # Add generic suggestions
        suggestions.extend([
            SearchSuggestion(suggestion=f"{query} documentation", confidence=0.6, category="docs"),
            SearchSuggestion(suggestion=f"{query} examples", confidence=0.5, category="examples")
        ])
        
        return suggestions[:limit]
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        
        try:
            qdrant_stats = await self.qdrant_service.get_collection_stats()
            
            return {
                "qdrant": qdrant_stats,
                "search_service": {
                    "total_searches": self.search_count,
                    "avg_response_time_ms": sum(self.search_times) / len(self.search_times) if self.search_times else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            raise Exception(f"Failed to get database statistics: {e}")
    
    def _track_search_metrics(self, query: str):
        """Track search metrics"""
        self.search_count += 1
        self.popular_queries.append(query)
        
        # Keep only last 100 queries
        if len(self.popular_queries) > 100:
            self.popular_queries = self.popular_queries[-100:]
    
    async def _execute_vector_search_query(self, query: VectorSearchQuery) -> SearchResponse:
        """Execute a vector search query and return SearchResponse"""
        start_time = datetime.now()
        
        results = await self.vector_search(
            query=query.query,
            collection=query.collection,
            limit=query.limit,
            threshold=query.threshold,
            include_metadata=query.include_metadata,
            include_content=query.include_content,
            filters=query.filters
        )
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return SearchResponse(
            query=query.query,
            search_type=query.search_type,
            results=results,
            total_results=len(results),
            processing_time_ms=processing_time,
            threshold_used=query.threshold
        )
    
    
    def _create_error_response(self, query, error_message: str) -> SearchResponse:
        """Create an error SearchResponse"""
        return SearchResponse(
            query=query.query if hasattr(query, 'query') else "unknown",
            search_type=query.search_type if hasattr(query, 'search_type') else SearchType.VECTOR,
            results=[],
            total_results=-1,  # Indicate error
            processing_time_ms=0,
            threshold_used=0.0
        )
    
    async def search_and_generate_response(
        self,
        query: str,
        collection: str,
        limit: int = 10,
        threshold: float = 0.7,
        include_metadata: bool = True,
        include_content: bool = True,
        filters: Optional[Dict[str, Any]] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> tuple[List[Union[SearchResult, GraphResult]], str, float, float]:
        """Perform search and generate LLM response in one call"""
        
        logger.info(f"Search and response generation: {query} in collection: {collection}")
        
        search_start_time = time.time()
        
        try:
            # First, perform the vector search
            search_results = await self.vector_search(
                query=query,
                collection=collection,
                limit=limit,
                threshold=threshold,
                include_metadata=include_metadata,
                include_content=include_content,
                filters=filters
            )
            
            search_processing_time = (time.time() - search_start_time) * 1000
            logger.info(f"Search completed: {len(search_results)} results in {search_processing_time:.2f}ms")
            
            # Generate response from search results
            response_start_time = time.time()
            response = await self.generate_response_from_search_results(
                query=query,
                search_results=search_results,
                max_tokens=max_tokens,
                temperature=temperature
            )
            response_processing_time = (time.time() - response_start_time) * 1000
            
            total_processing_time = search_processing_time + response_processing_time
            
            logger.info(f"Response generated: {len(response)} chars in {response_processing_time:.2f}ms")
            logger.info(f"Total processing time: {total_processing_time:.2f}ms")
            
            return search_results, response, search_processing_time, response_processing_time
            
        except Exception as e:
            logger.error(f"Search and response generation failed: {e}")
            raise Exception(f"Search and response generation failed: {e}")
    
    async def generate_response_from_search_results(
        self,
        query: str,
        search_results: List[Union[SearchResult, GraphResult]],
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """Generate LLM response from search results"""
        
        logger.info(f"Generating response for query: {query} with {len(search_results)} results")
        
        try:
            # Convert search results to the format expected by LLM service
            llm_results = []
            for result in search_results:
                if isinstance(result, SearchResult):
                    llm_results.append({
                        "content": result.content,
                        "source_file": result.source_file,
                        "score": result.score,
                        "metadata": result.metadata
                    })
                elif isinstance(result, GraphResult):
                    llm_results.append({
                        "content": result.content,
                        "source_file": result.metadata.get("source_file", "unknown"),
                        "score": result.score,
                        "metadata": result.metadata
                    })
            
            # Generate response using LLM service
            response = await self.llm_service.generate_response(
                query=query,
                search_results=llm_results,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            logger.info(f"Generated response successfully - Length: {len(response)}")
            return response
            
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            raise Exception(f"Failed to generate response: {e}")