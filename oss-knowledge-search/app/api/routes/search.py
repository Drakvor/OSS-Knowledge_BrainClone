"""
Search API routes
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from typing import List, Union, Set
import time
import json
import structlog
import re
import asyncio

from app.models.search import (
    VectorSearchQuery, GraphSearchQuery, HybridSearchQuery, ComprehensiveSearchQuery,
    BatchSearchQuery, SearchResponse, BatchSearchResponse, SearchResult, GraphResult,
    SearchAnalytics, SearchSuggestionsResponse, SearchResponseQuery, SearchResponseResponse,
    SearchType
)
from app.services.search_service import SearchService
from app.services.container_validation_service import container_validator

logger = structlog.get_logger(__name__)

router = APIRouter()


def extract_mention_collections(query_text: str, default_collection: str = None) -> List[str]:
    """
    Extract @mentioned department names from query text and map them to collection names.
    Returns list of collection names, or single-item list with default if no mentions found.
    """
    # Extract @mentions using regex: @ followed by non-whitespace, non-@ characters
    mentions = re.findall(r'@([^\s@]+)', query_text)
    
    if not mentions:
        # No mentions found, use default collection if provided
        if default_collection:
            return [default_collection]
        return []
    
    # Map mentions to collection names using container validator
    collections = []
    for mention in mentions:
        try:
            # Try to get collection name from container validator
            collection_name = container_validator.get_container_collection_name(mention)
            if collection_name and collection_name not in collections:
                collections.append(collection_name)
        except Exception as e:
            # If validation fails, try using mention directly as collection name
            logger.warning(f"Failed to validate mention '{mention}', using as-is: {e}")
            if mention not in collections:
                collections.append(mention)
    
    # If no valid collections found but we have default, use it
    if not collections and default_collection:
        collections = [default_collection]
    
    return collections


async def search_multiple_collections(
    search_service: SearchService,
    query_text: str,
    collections: List[str],
    limit: int,
    threshold: float,
    include_metadata: bool,
    include_content: bool,
    filters: dict = None
) -> List[SearchResult]:
    """
    Search multiple collections in parallel and merge results by score.
    Each result is annotated with its source collection.
    """
    if not collections:
        return []
    
    if len(collections) == 1:
        # Single collection - use existing path
        return await search_service.vector_search(
            query=query_text,
            collection=collections[0],
            limit=limit,
            threshold=threshold,
            include_metadata=include_metadata,
            include_content=include_content,
            filters=filters
        )
    
    # Multiple collections - search in parallel
    logger.info(f"Searching {len(collections)} collections in parallel: {collections}")
    
    async def search_one(collection: str) -> List[SearchResult]:
        try:
            results = await search_service.vector_search(
                query=query_text,
                collection=collection,
                limit=limit,  # Get limit results from each collection
                threshold=threshold,
                include_metadata=include_metadata,
                include_content=include_content,
                filters=filters
            )
            # Annotate each result with source collection
            for result in results:
                if hasattr(result, 'metadata') and isinstance(result.metadata, dict):
                    # Update existing metadata dict
                    result.metadata['source_collection'] = collection
                elif isinstance(result, dict):
                    # Handle dict results
                    if 'metadata' not in result:
                        result['metadata'] = {}
                    result['metadata']['source_collection'] = collection
            return results
        except Exception as e:
            logger.warning(f"Search failed for collection '{collection}': {e}")
            return []
    
    # Run all searches in parallel
    all_results = await asyncio.gather(*[search_one(coll) for coll in collections])
    
    # Flatten and merge results
    merged_results = []
    for results in all_results:
        merged_results.extend(results)
    
    # Sort by score (descending) and limit
    def get_score(result):
        if hasattr(result, 'score'):
            return result.score
        elif isinstance(result, dict):
            return result.get('score', 0.0)
        return 0.0
    
    merged_results.sort(key=get_score, reverse=True)
    merged_results = merged_results[:limit]
    
    logger.info(f"Merged {len(merged_results)} results from {len(collections)} collections")
    return merged_results


@router.get("/search/test")
async def test_search_endpoint():
    """Test endpoint to verify routing works"""
    return {"message": "Search endpoint is working"}

@router.post("/search/simple")
async def simple_search_endpoint():
    """Simple POST endpoint to test routing"""
    return {"message": "Simple POST endpoint is working"}


def get_search_service(request: Request) -> SearchService:
    """Dependency to get search service from app state"""
    logger.info("=== SEARCH SERVICE DEPENDENCY INJECTION ===")
    logger.info(f"Qdrant service available: {request.app.state.qdrant_service is not None}")
    logger.info(f"Embedding service available: {request.app.state.embedding_service is not None}")
    logger.info(f"LLM service available: {request.app.state.llm_service is not None}")
    
    if request.app.state.qdrant_service is None:
        logger.warning("Qdrant service is None!")
    if request.app.state.embedding_service is None:
        logger.warning("Embedding service is None!")
    if request.app.state.llm_service is None:
        logger.warning("LLM service is None!")
    
    logger.info("Creating SearchService instance...")
    return SearchService(
        qdrant_service=request.app.state.qdrant_service,
        embedding_service=request.app.state.embedding_service,
        llm_service=request.app.state.llm_service
    )


@router.post("/search/similarity", response_model=SearchResponse)
async def vector_similarity_search(
    query: VectorSearchQuery,
    search_service: SearchService = Depends(get_search_service)
) -> SearchResponse:
    """Perform vector similarity search using Qdrant"""
    
    start_time = time.time()
    logger.info("=== VECTOR SEARCH REQUEST START ===")
    logger.info(f"Query: '{query.query}'")
    logger.info(f"Collection: '{query.collection}'")
    logger.info(f"Limit: {query.limit}")
    logger.info(f"Threshold: {query.threshold}")
    logger.info(f"Include metadata: {query.include_metadata}")
    logger.info(f"Include content: {query.include_content}")
    logger.info(f"Filters: {query.filters}")
    
    try:
        logger.info("Calling search_service.vector_search...")
        results = await search_service.vector_search(
            query=query.query,
            collection=query.collection,
            limit=query.limit,
            threshold=query.threshold,
            include_metadata=query.include_metadata,
            include_content=query.include_content,
            filters=query.filters
        )
        logger.info(f"Search service returned {len(results) if results else 0} results")
        
        processing_time = (time.time() - start_time) * 1000
        logger.info(f"Processing time: {processing_time:.2f}ms")
        
        logger.info("Creating SearchResponse object...")
        response = SearchResponse(
            query=query.query,
            search_type=query.search_type,
            results=results,
            total_results=len(results),
            processing_time_ms=processing_time,
            threshold_used=query.threshold
        )
        
        logger.info("Vector search completed successfully", 
                   results_count=len(results), 
                   processing_time_ms=processing_time)
        logger.info("=== VECTOR SEARCH REQUEST END ===")
        
        return response
        
    except ValueError as e:
        error_msg = str(e)
        logger.error("=== VECTOR SEARCH ERROR (ValueError) ===")
        logger.error(f"Error message: {error_msg}")
        logger.error(f"Error type: {type(e).__name__}")
        
        if "Embedding service is not available" in error_msg or "Qdrant service is not available" in error_msg:
            logger.error("Service unavailable error detected")
            logger.error("=== VECTOR SEARCH REQUEST END (503) ===")
            raise HTTPException(status_code=503, detail=f"Service unavailable: {error_msg}")
        else:
            logger.warning("Vector search validation failed")
            logger.error("=== VECTOR SEARCH REQUEST END (400) ===")
            raise HTTPException(status_code=400, detail=f"Invalid request: {error_msg}")
    except Exception as e:
        logger.error("=== VECTOR SEARCH ERROR (Exception) ===")
        logger.error(f"Error message: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error details: {repr(e)}")
        logger.error("=== VECTOR SEARCH REQUEST END (500) ===")
        raise HTTPException(status_code=500, detail=f"Vector search failed: {str(e)}")




@router.post("/search/comprehensive", response_model=SearchResponse)
async def comprehensive_search(
    query: ComprehensiveSearchQuery,
    search_service: SearchService = Depends(get_search_service)
) -> SearchResponse:
    """Perform comprehensive search (vector only)"""
    
    start_time = time.time()
    logger.info("Comprehensive search request", 
               query=query.query,
               search_modes=query.search_modes,
               include_analytics=query.include_analytics)
    
    try:
        # Only support vector search mode now
        if SearchType.VECTOR not in query.search_modes:
            raise HTTPException(status_code=400, detail="Only vector search is supported. Please include VECTOR in search_modes.")
        
        results = await search_service.comprehensive_search(
            query=query.query,
            collection=query.collection,
            search_modes=[SearchType.VECTOR],  # Force vector only
            limit=query.limit,
            threshold=query.threshold,
            vector_weight=query.vector_weight,
            graph_weight=0.0,  # No graph weight
            max_depth=0,  # No graph depth
            sort_by=query.sort_by,
            include_analytics=query.include_analytics,
            filters=query.filters
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        # Extract results and analytics
        search_results = results.get("results", [])
        analytics = results.get("analytics") if query.include_analytics else None
        suggestions = results.get("suggestions")
        
        response = SearchResponse(
            query=query.query,
            search_type=query.search_type,
            results=search_results,
            total_results=len(search_results),
            processing_time_ms=processing_time,
            threshold_used=query.threshold,
            analytics=analytics,
            suggestions=suggestions
        )
        
        logger.info("Comprehensive search completed", 
                   results_count=len(search_results), 
                   processing_time_ms=processing_time)
        
        return response
        
    except Exception as e:
        logger.error("Comprehensive search failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Comprehensive search failed: {str(e)}")


@router.post("/search/batch", response_model=BatchSearchResponse)
async def batch_search(
    batch_query: BatchSearchQuery,
    search_service: SearchService = Depends(get_search_service)
) -> BatchSearchResponse:
    """Perform batch search operations"""
    
    start_time = time.time()
    logger.info("Batch search request", 
               queries_count=len(batch_query.queries),
               parallel=batch_query.parallel)
    
    try:
        results = await search_service.batch_search(
            queries=batch_query.queries,
            parallel=batch_query.parallel
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        # Count successful and failed queries
        successful_queries = len([r for r in results if r.total_results >= 0])
        failed_queries = len(results) - successful_queries
        
        response = BatchSearchResponse(
            results=results,
            total_processing_time_ms=processing_time,
            successful_queries=successful_queries,
            failed_queries=failed_queries
        )
        
        logger.info("Batch search completed", 
                   total_queries=len(batch_query.queries),
                   successful=successful_queries,
                   failed=failed_queries,
                   processing_time_ms=processing_time)
        
        return response
        
    except Exception as e:
        logger.error("Batch search failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Batch search failed: {str(e)}")


@router.get("/search/analytics", response_model=SearchAnalytics)
async def get_search_analytics(
    search_service: SearchService = Depends(get_search_service)
) -> SearchAnalytics:
    """Get search usage analytics"""
    
    logger.info("Search analytics request")
    
    try:
        analytics = await search_service.get_analytics()
        
        logger.info("Search analytics completed", 
                   total_searches=analytics.total_searches)
        
        return analytics
        
    except Exception as e:
        logger.error("Search analytics failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Search analytics failed: {str(e)}")


@router.get("/search/suggestions", response_model=SearchSuggestionsResponse)
async def get_search_suggestions(
    query: str,
    limit: int = 5,
    search_service: SearchService = Depends(get_search_service)
) -> SearchSuggestionsResponse:
    """Get search query suggestions"""
    
    start_time = time.time()
    logger.info("Search suggestions request", query=query, limit=limit)
    
    try:
        suggestions = await search_service.get_suggestions(query, limit)
        
        processing_time = (time.time() - start_time) * 1000
        
        response = SearchSuggestionsResponse(
            query=query,
            suggestions=suggestions,
            processing_time_ms=processing_time
        )
        
        logger.info("Search suggestions completed", 
                   suggestions_count=len(suggestions),
                   processing_time_ms=processing_time)
        
        return response
        
    except Exception as e:
        logger.error("Search suggestions failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Search suggestions failed: {str(e)}")


@router.get("/search/stats")
async def get_search_stats(
    search_service: SearchService = Depends(get_search_service)
):
    """Get database statistics"""

    logger.info("Search stats request")

    try:
        stats = await search_service.get_database_stats()

        logger.info("Search stats completed")
        return stats

    except Exception as e:
        logger.error("Search stats failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Search stats failed: {str(e)}")


@router.get("/search/collections")
async def get_available_collections():
    """Get list of available collections/containers"""

    logger.info("Available collections request")

    try:
        containers = container_validator.get_available_containers()

        logger.info("Available collections completed", count=len(containers))
        return {
            "collections": containers,
            "total": len(containers)
        }

    except Exception as e:
        logger.error("Get available collections failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get available collections: {str(e)}")


@router.get("/search/collections/validate/{collection_name}")
async def validate_collection(collection_name: str):
    """Validate a specific collection name"""

    logger.info("Collection validation request", collection=collection_name)

    try:
        validation_result = container_validator.validate_container_with_suggestions(collection_name)

        logger.info("Collection validation completed",
                   collection=collection_name,
                   valid=validation_result['valid'])
        return validation_result

    except Exception as e:
        logger.error("Collection validation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Collection validation failed: {str(e)}")


@router.post("/search/response")
async def search_and_generate_response(
    query: SearchResponseQuery,
    stream: bool = False,
    search_service: SearchService = Depends(get_search_service),
    request: Request = None
):
    """Perform search and generate LLM response in one call with optional streaming"""
    
    start_time = time.time()
    logger.info("Search and response generation request", 
               query=query.query, 
               collection=query.collection,
               limit=query.limit,
               threshold=query.threshold,
               max_tokens=query.max_tokens,
               session_id=query.session_id,
               stream=stream)
    
    chat_context = query.chat_context
    print(f"\n{'='*80}")
    print(f"SEARCH_ROUTE: Received request with chat_context")
    print(f"{'='*80}")
    if chat_context:
        history = chat_context.get("chat_history") or []
        history_count = len(history) if isinstance(history, list) else 0
        print(f"SEARCH_ROUTE: session_id={chat_context.get('session_id')}")
        print(f"SEARCH_ROUTE: chat_history_count={history_count}")
        logger.info(
            "SEARCH_ROUTE_CHAT_CONTEXT: Received chat_context",
            session_id=chat_context.get("session_id"),
            has_summary=bool(chat_context.get("context_summary")),
            chat_history_count=history_count
        )
        # Log each message in chat_history with role and content preview
        if isinstance(history, list):
            for i, msg in enumerate(history):
                if isinstance(msg, dict):
                    content = msg.get("content", "")
                    content_preview = content[:200] + ("..." if len(content) > 200 else "")
                    print(f"SEARCH_ROUTE: chat_history[{i}] role={msg.get('role')}, content_length={len(content)}")
                    print(f"SEARCH_ROUTE: chat_history[{i}] content_preview={content_preview}")
                    logger.info(
                        f"SEARCH_ROUTE_CHAT_HISTORY[{i}]",
                        role=msg.get("role"),
                        content_length=len(content),
                        content_preview=content_preview
                    )
        else:
            print(f"SEARCH_ROUTE: chat_history is not a list: {type(history)}")
    else:
        print(f"SEARCH_ROUTE: No chat_context provided in request")
        logger.info("SEARCH_ROUTE_CHAT_CONTEXT: No chat context provided in request")
    print(f"{'='*80}\n")
    
    try:
        if stream:
            # Streaming response
            async def generate_stream():
                try:
                    # Send initial metadata
                    yield f"data: {json.dumps({'type': 'metadata', 'data': {'timestamp': time.time()}})}\n\n"
                    
                    # Extract collections from @mentions or use default collection
                    collections = extract_mention_collections(query.query, query.collection if query.collection else None)
                    
                    # Skip search entirely if no collections found (direct conversational chat)
                    if not collections:
                        logger.info("No collections specified - skipping search for direct conversational streaming chat")
                        search_results = []
                        searched_collections = []
                    else:
                        # Perform multi-collection search
                        logger.info(f"Performing multi-collection search for streaming response: {collections}")
                        search_results = await search_multiple_collections(
                            search_service=search_service,
                            query_text=query.query,
                            collections=collections,
                            limit=query.limit,
                            threshold=query.threshold,
                            include_metadata=query.include_metadata,
                            include_content=query.include_content,
                            filters=query.filters
                        )
                        searched_collections = collections
                    
                    # 유사도 측정 주석
                    # Log similarity scores for search results
                    # if search_results:
                    #     scores = [result.score for result in search_results]
                    #     print(f"[STREAM] Search similarity scores - min={min(scores):.4f}, max={max(scores):.4f}, avg={sum(scores)/len(scores):.4f}")
                    #     for i, result in enumerate(search_results[:3], 1):
                    #         print(f"[STREAM]   Top {i}: score={result.score:.4f}, source={result.source_file[:50]}...")
                    
                    # Send search results
                    search_data = {
                        'type': 'search_results',
                        'data': {
                            'search_results': [result.dict() for result in search_results],
                            'search_results_count': len(search_results),
                            'search_processing_time_ms': (time.time() - start_time) * 1000
                        }
                    }
                    yield f"data: {json.dumps(search_data)}\n\n"
                    
                    # Generate streaming response with context
                    logger.info(f"[ROUTE_STREAMING] Generating streaming response with context...")
                    logger.info(f"[ROUTE_STREAMING] Calling generate_streaming_response_with_context with user_id={query.user_id}, session_id={query.session_id}")
                    logger.debug(f"[ROUTE_STREAMING] query.user_id type: {type(query.user_id)}, value: {query.user_id}")
                    logger.debug(f"[ROUTE_STREAMING] query.session_id type: {type(query.session_id)}, value: {query.session_id}")
                    response_generator = await search_service.llm_service.generate_streaming_response_with_context(
                        query=query.query,
                        context_results=search_results,
                        chat_context=chat_context,  # Can be None - method handles this
                        max_tokens=query.max_tokens,
                        temperature=query.temperature,
                        searched_collections=searched_collections if len(searched_collections) > 1 else None,
                        user_id=query.user_id,
                        session_id=query.session_id
                    )
                    
                    # Stream the response content
                    full_response = ""
                    async for chunk in response_generator:
                        if chunk:
                            full_response += chunk
                            content_data = {
                                'type': 'content',
                                'data': {'content': chunk, 'full_content': full_response}
                            }
                            yield f"data: {json.dumps(content_data)}\n\n"
                    
                    # Extract unique source files and generate download links
                    from app.models.search import SourceInfo
                    from app.core.azure_file_service import azure_file_service
                    
                    unique_sources = {}
                    for result in search_results:
                        source_file = getattr(result, 'source_file', None) or (result.get('source_file') if isinstance(result, dict) else None)
                        # Skip "unknown" sources - they're not valid file sources
                        if source_file and source_file != "unknown" and source_file not in unique_sources:
                            # Try to get azure_file_path from metadata
                            # Note: In Qdrant, chunk.metadata is nested under "metadata" key in payload
                            metadata = getattr(result, 'metadata', {}) if hasattr(result, 'metadata') else (result.get('metadata', {}) if isinstance(result, dict) else {})
                            
                            # Try nested metadata first (chunk.metadata stored in payload["metadata"])
                            chunk_metadata = metadata.get('metadata', {}) if isinstance(metadata, dict) else {}
                            
                            # Read download_url directly from metadata (preferred)
                            download_url = chunk_metadata.get('download_url') if chunk_metadata else None
                            upload_status = chunk_metadata.get('upload_status', 'unknown') if chunk_metadata else 'unknown'
                            
                            # If download_url not found, fallback to generating from azure_file_path
                            if not download_url:
                                azure_file_path = chunk_metadata.get('azure_file_path') if chunk_metadata else None
                                
                                # If not found in nested metadata, try top-level payload (for backwards compatibility)
                                if not azure_file_path and isinstance(metadata, dict):
                                    azure_file_path = metadata.get('azure_file_path')
                                    if not upload_status or upload_status == 'unknown':
                                        upload_status = metadata.get('upload_status', 'unknown')
                                
                                # If not in metadata, try to construct path from container and filename
                                if not azure_file_path:
                                    container = query.collection if query.collection else "general"
                                    azure_file_path = f"{container}/{source_file}"
                                
                                # Generate download URL if upload succeeded
                                if upload_status == 'completed' and azure_file_path and azure_file_service.initialized:
                                    try:
                                        download_url = azure_file_service.generate_download_url(azure_file_path)
                                    except Exception as e:
                                        logger.warning(f"Failed to generate download URL for {azure_file_path}: {e}")
                            
                            unique_sources[source_file] = {
                                'filename': source_file,
                                'download_url': download_url,
                                'upload_status': upload_status
                            }
                    
                    sources_list = list(unique_sources.values())
                    
                    # Send completion signal
                    completion_data = {
                        'type': 'done',
                        'data': {
                            'total_processing_time_ms': (time.time() - start_time) * 1000,
                            'model_info': search_service.llm_service.get_model_info(),
                            'final_response': full_response,
                            'sources': sources_list
                        }
                    }
                    yield f"data: {json.dumps(completion_data)}\n\n"
                    
                    logger.info("Streaming response completed", 
                               response_length=len(full_response),
                               search_results_count=len(search_results),
                               processing_time_ms=(time.time() - start_time) * 1000)
                    
                    # Save conversation to memory after streaming completes
                    if query.user_id and query.session_id and full_response:
                        try:
                            mem0_service = search_service.llm_service.mem0_service
                            
                            if mem0_service:
                                from app.config import settings
                                
                                response_len_check = len(full_response) > 200
                                keyword_check = any(keyword in query.query.lower() for keyword in ['좋아', '싫어', '선호', '취향', '습관'])
                                auto_save_check = settings.MEM0_AUTO_SAVE_IMPORTANT
                                
                                is_important = (
                                    response_len_check or
                                    keyword_check or
                                    auto_save_check
                                )
                                
                                save_result = await mem0_service.add_conversation_memory(
                                    query=query.query,
                                    response=full_response,
                                    user_id=query.user_id,
                                    session_id=query.session_id,
                                    is_important=is_important
                                )
                                
                                logger.info(f"Saved streaming conversation to memory - user: {query.user_id}, session: {query.session_id}, important: {is_important}")
                        except Exception as e:
                            logger.warning(f"Failed to save streaming conversation to memory: {type(e).__name__}: {e}")
                    
                except Exception as e:
                    logger.error("Streaming response failed", error=str(e))
                    error_data = {
                        'type': 'error',
                        'data': {'error': str(e), 'timestamp': time.time()}
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
            
            return StreamingResponse(
                generate_stream(),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Content-Type": "text/plain; charset=utf-8"
                }
            )
        
        else:
            # Non-streaming response with chat context
            logger.info("Performing search for non-streaming response...")
            
            # Extract collections from @mentions or use default collection
            collections = extract_mention_collections(query.query, query.collection if query.collection else None)
            
            # Skip search entirely if no collections found (direct conversational chat)
            if not collections:
                logger.info("No collections specified - skipping search for direct conversational chat")
                search_results = []
                search_processing_time = 0  # No search time
                searched_collections = []
            else:
                try:
                    logger.info(f"Performing multi-collection search: {collections}")
                    search_results = await search_multiple_collections(
                        search_service=search_service,
                        query_text=query.query,
                        collections=collections,
                        limit=query.limit,
                        threshold=query.threshold,
                        include_metadata=query.include_metadata,
                        include_content=query.include_content,
                        filters=query.filters
                    )
                    searched_collections = collections
                except Exception as search_error:
                    logger.error(f"Multi-collection search failed: {search_error}")
                    # 임시로 빈 검색 결과 반환
                    search_results = []
                    searched_collections = []
                
                search_processing_time = (time.time() - start_time) * 1000
            
            # 유사도 측정 주석
            # Log similarity scores for search results
            # if search_results:
            #     scores = [result.score for result in search_results]
            #     print(f"[API] Search similarity scores - min={min(scores):.4f}, max={max(scores):.4f}, avg={sum(scores)/len(scores):.4f}")
            #     for i, result in enumerate(search_results[:3], 1):  # Log top 3
            #         print(f"[API]   Top {i}: score={result.score:.4f}, source={result.source_file[:50]}...")
            
            # Generate response with chat context (always use context-aware method)
            logger.info("Generating response with chat context...")
            
            # Convert search results to dict format for LLM service
            search_results_dict = []
            for result in search_results:
                if hasattr(result, 'dict'):
                    search_results_dict.append(result.dict())
                else:
                    search_results_dict.append(result)
            
            # Always use generate_response_with_context (it handles both cases: with and without chat_context)
            response = await search_service.llm_service.generate_response_with_context(
                query=query.query,
                search_results=search_results_dict,
                chat_context=chat_context,  # Can be None - method handles this
                max_tokens=query.max_tokens,
                temperature=query.temperature,
                searched_collections=searched_collections if len(searched_collections) > 1 else None,
                user_id=query.user_id,
                session_id=query.session_id,
                active_collection=query.collection
            )
            
            response_processing_time = (time.time() - start_time) * 1000 - search_processing_time
            total_processing_time = (time.time() - start_time) * 1000
            
            # Get model info and augment with search stats
            model_info = search_service.llm_service.get_model_info()
            try:
                scores = [r.score for r in search_results if hasattr(r, 'score')]
            except Exception:
                scores = []
            hits = len(search_results)
            top_score = max(scores) if scores else 0.0
            avg_score = (sum(scores) / len(scores)) if scores else 0.0
            model_info.update({
                "hits": hits,
                "top_score": round(top_score, 4),
                "avg_score": round(avg_score, 4),
                "collection": query.collection,
                "collections_searched": searched_collections if searched_collections else [query.collection] if query.collection else [],
            })
            logger.info("RAG stats", collections=searched_collections if searched_collections else [query.collection], hits=hits, top_score=top_score)
            
            # Extract unique source files and generate download links
            from app.models.search import SourceInfo
            from app.core.azure_file_service import azure_file_service
            
            unique_sources = {}
            for result in search_results:
                source_file = getattr(result, 'source_file', None) or (result.get('source_file') if isinstance(result, dict) else None)
                # Skip "unknown" sources - they're not valid file sources
                if source_file and source_file != "unknown" and source_file not in unique_sources:
                    # Try to get azure_file_path from metadata
                    # Note: In Qdrant, chunk.metadata is nested under "metadata" key in payload
                    metadata = getattr(result, 'metadata', {}) if hasattr(result, 'metadata') else (result.get('metadata', {}) if isinstance(result, dict) else {})
                    
                    # Try nested metadata first (chunk.metadata stored in payload["metadata"])
                    chunk_metadata = metadata.get('metadata', {}) if isinstance(metadata, dict) else {}
                    
                    # Read download_url directly from metadata (preferred)
                    download_url = chunk_metadata.get('download_url') if chunk_metadata else None
                    upload_status = chunk_metadata.get('upload_status', 'unknown') if chunk_metadata else 'unknown'
                    
                    # If download_url not found, fallback to generating from azure_file_path
                    if not download_url:
                        azure_file_path = chunk_metadata.get('azure_file_path') if chunk_metadata else None
                        
                        # If not found in nested metadata, try top-level payload (for backwards compatibility)
                        if not azure_file_path and isinstance(metadata, dict):
                            azure_file_path = metadata.get('azure_file_path')
                            if not upload_status or upload_status == 'unknown':
                                upload_status = metadata.get('upload_status', 'unknown')
                        
                        # If not in metadata, try to construct path from container and filename
                        if not azure_file_path:
                            container = query.collection if query.collection else "general"
                            azure_file_path = f"{container}/{source_file}"
                        
                        # Generate download URL if upload succeeded
                        if upload_status == 'completed' and azure_file_path and azure_file_service.initialized:
                            try:
                                download_url = azure_file_service.generate_download_url(azure_file_path)
                            except Exception as e:
                                logger.warning(f"Failed to generate download URL for {azure_file_path}: {e}")
                    
                    unique_sources[source_file] = SourceInfo(
                        filename=source_file,
                        download_url=download_url,
                        upload_status=upload_status
                    )
            
            sources_list = list(unique_sources.values())
            
            response_data = SearchResponseResponse(
                query=query.query,
                response=response,
                search_results=search_results,
                search_results_count=len(search_results),
                search_processing_time_ms=search_processing_time,
                response_processing_time_ms=response_processing_time,
                total_processing_time_ms=total_processing_time,
                threshold_used=query.threshold,
                model_info=model_info,
                sources=sources_list
            )
            
            logger.info("Search and response generation completed", 
                       response_length=len(response),
                       search_results_count=len(search_results),
                       total_processing_time_ms=total_processing_time,
                       has_chat_context=bool(chat_context))
            
            return response_data
        
    except Exception as e:
        logger.error("Search and response generation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Search and response generation failed: {str(e)}")