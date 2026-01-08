"""
Collection Management API Routes
================================

API endpoints for managing Qdrant collections for RAG departments.
"""

from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import logging
from urllib.parse import unquote, quote

from qdrant_client.http import models
from app.core.qdrant_storage import QdrantVectorStorage
from app.config.settings import settings
from app.core.azure_file_service import azure_file_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/collections", tags=["collections"])


class CollectionCreateRequest(BaseModel):
    """Request model for creating a collection"""
    collection_name: str
    vector_size: Optional[int] = None
    similarity_function: Optional[str] = "cosine"


class CollectionResponse(BaseModel):
    """Response model for collection operations"""
    collection_name: str
    status: str
    message: str
    vector_count: Optional[int] = None


class CollectionListResponse(BaseModel):
    """Response model for listing collections"""
    collections: List[dict]
    total_count: int


def get_qdrant_storage() -> QdrantVectorStorage:
    """Dependency to get Qdrant storage instance"""
    return QdrantVectorStorage()


@router.post("/create", response_model=CollectionResponse)
async def create_collection(
    request: CollectionCreateRequest,
    storage: QdrantVectorStorage = Depends(get_qdrant_storage)
):
    """
    Create a new Qdrant collection for a RAG department.
    
    Args:
        request: Collection creation request
        storage: Qdrant storage instance
        
    Returns:
        Collection creation response
    """
    try:
        logger.info(f"Creating collection: {request.collection_name}")
        
        # Ensure client is initialized
        if not storage.client:
            logger.error("Qdrant client is not initialized")
            raise HTTPException(
                status_code=500,
                detail="Qdrant client is not initialized"
            )
        
        # Set vector size from request or use default (OpenAI text-embedding-3-large = 3072)
        vector_size = request.vector_size or 3072
        
        # Create collection
        success = await storage.create_collection(
            collection_name=request.collection_name,
            dimension=vector_size,
            metadata_schema=None
        )
        
        if success:
            logger.info(f"Successfully created collection: {request.collection_name}")
            return CollectionResponse(
                collection_name=request.collection_name,
                status="created",
                message=f"Collection '{request.collection_name}' created successfully",
                vector_count=0
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create collection '{request.collection_name}'"
            )
            
    except Exception as e:
        logger.error(f"Error creating collection {request.collection_name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create collection: {str(e)}"
        )


@router.delete("/{collection_name}", response_model=CollectionResponse)
async def delete_collection(
    collection_name: str,
    storage: QdrantVectorStorage = Depends(get_qdrant_storage)
):
    """
    Delete a Qdrant collection.
    
    Args:
        collection_name: Name of the collection to delete
        storage: Qdrant storage instance
        
    Returns:
        Collection deletion response
    """
    try:
        logger.info(f"Deleting collection: {collection_name}")
        
        # Ensure client is initialized
        if not storage.client:
            logger.error("Qdrant client is not initialized")
            raise HTTPException(
                status_code=500,
                detail="Qdrant client is not initialized"
            )
        
        # Check if collection exists
        collections = storage.client.get_collections()
        collection_names = [col.name for col in collections.collections]
        
        if collection_name not in collection_names:
            raise HTTPException(
                status_code=404,
                detail=f"Collection '{collection_name}' not found"
            )
        
        # Get vector count before deletion
        collection_info = storage.client.get_collection(collection_name)
        vector_count = collection_info.vectors_count
        
        # Delete collection
        storage.client.delete_collection(collection_name)
        
        logger.info(f"Successfully deleted collection: {collection_name}")
        return CollectionResponse(
            collection_name=collection_name,
            status="deleted",
            message=f"Collection '{collection_name}' deleted successfully",
            vector_count=vector_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting collection {collection_name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete collection: {str(e)}"
        )


@router.get("/list", response_model=CollectionListResponse)
async def list_collections(
    storage: QdrantVectorStorage = Depends(get_qdrant_storage)
):
    """
    List all Qdrant collections.
    
    Args:
        storage: Qdrant storage instance
        
    Returns:
        List of collections with metadata
    """
    try:
        logger.info("Listing all collections")
        
        collections = storage.client.get_collections()
        collection_list = []
        
        for collection in collections.collections:
            try:
                # Get detailed info for each collection
                info = storage.client.get_collection(collection.name)
                collection_list.append({
                    "name": collection.name,
                    "vectors_count": info.vectors_count,
                    "status": info.status,
                    "config": {
                        "vector_size": info.config.params.vectors.size,
                        "distance": info.config.params.vectors.distance
                    }
                })
            except Exception as e:
                logger.warning(f"Could not get info for collection {collection.name}: {e}")
                collection_list.append({
                    "name": collection.name,
                    "vectors_count": 0,
                    "status": "unknown",
                    "config": {}
                })
        
        logger.info(f"Found {len(collection_list)} collections")
        return CollectionListResponse(
            collections=collection_list,
            total_count=len(collection_list)
        )
        
    except Exception as e:
        logger.error(f"Error listing collections: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list collections: {str(e)}"
        )


@router.get("/{collection_name}/info", response_model=dict)
async def get_collection_info(
    collection_name: str,
    storage: QdrantVectorStorage = Depends(get_qdrant_storage)
):
    """
    Get detailed information about a specific collection.
    
    Args:
        collection_name: Name of the collection
        storage: Qdrant storage instance
        
    Returns:
        Collection information
    """
    try:
        logger.info(f"Getting info for collection: {collection_name}")
        
        # Check if collection exists
        collections = storage.client.get_collections()
        collection_names = [col.name for col in collections.collections]
        
        if collection_name not in collection_names:
            raise HTTPException(
                status_code=404,
                detail=f"Collection '{collection_name}' not found"
            )
        
        # Get collection info
        info = storage.client.get_collection(collection_name)
        
        # vectors_count가 None인 경우 다른 방법으로 벡터 수 계산
        vectors_count = info.vectors_count
        if vectors_count is None:
            # scroll을 사용해서 실제 벡터 수 계산
            try:
                scroll_result = storage.client.scroll(
                    collection_name=collection_name,
                    limit=1,
                    with_payload=False,
                    with_vectors=False
                )
                vectors_count = len(scroll_result[0]) if scroll_result[0] else 0
                logger.info(f"Calculated vectors count for {collection_name}: {vectors_count}")
            except Exception as e:
                logger.error(f"Failed to calculate vectors count for {collection_name}: {e}")
                vectors_count = 0
        
        # 안전하게 속성에 접근
        result = {
            "name": collection_name,
            "vectors_count": vectors_count,
            "status": info.status,
            "config": {
                "vector_size": info.config.params.vectors.size,
                "distance": info.config.params.vectors.distance
            }
        }
        
        # 선택적 config 속성들을 안전하게 추가
        if hasattr(info.config.params, 'shard_number'):
            result["config"]["shard_number"] = info.config.params.shard_number
        if hasattr(info.config.params, 'replication_factor'):
            result["config"]["replication_factor"] = info.config.params.replication_factor
        if hasattr(info.config.params, 'write_consistency_factor'):
            result["config"]["write_consistency_factor"] = info.config.params.write_consistency_factor
        if hasattr(info.config.params, 'on_disk_payload'):
            result["config"]["on_disk_payload"] = info.config.params.on_disk_payload
            
        # HNSW config 안전하게 추가
        if hasattr(info.config, 'hnsw_config'):
            result["hnsw_config"] = {}
            if hasattr(info.config.hnsw_config, 'm'):
                result["hnsw_config"]["m"] = info.config.hnsw_config.m
            if hasattr(info.config.hnsw_config, 'ef_construct'):
                result["hnsw_config"]["ef_construct"] = info.config.hnsw_config.ef_construct
            if hasattr(info.config.hnsw_config, 'full_scan_threshold'):
                result["hnsw_config"]["full_scan_threshold"] = info.config.hnsw_config.full_scan_threshold
            if hasattr(info.config.hnsw_config, 'max_indexing_threads'):
                result["hnsw_config"]["max_indexing_threads"] = info.config.hnsw_config.max_indexing_threads
            if hasattr(info.config.hnsw_config, 'on_disk'):
                result["hnsw_config"]["on_disk"] = info.config.hnsw_config.on_disk
                
        # Optimizer config 안전하게 추가
        if hasattr(info.config, 'optimizer_config'):
            result["optimizer_config"] = {}
            if hasattr(info.config.optimizer_config, 'deleted_threshold'):
                result["optimizer_config"]["deleted_threshold"] = info.config.optimizer_config.deleted_threshold
            if hasattr(info.config.optimizer_config, 'vacuum_min_vector_number'):
                result["optimizer_config"]["vacuum_min_vector_number"] = info.config.optimizer_config.vacuum_min_vector_number
            if hasattr(info.config.optimizer_config, 'default_segment_number'):
                result["optimizer_config"]["default_segment_number"] = info.config.optimizer_config.default_segment_number
            if hasattr(info.config.optimizer_config, 'max_segment_size'):
                result["optimizer_config"]["max_segment_size"] = info.config.optimizer_config.max_segment_size
            if hasattr(info.config.optimizer_config, 'memmap_threshold'):
                result["optimizer_config"]["memmap_threshold"] = info.config.optimizer_config.memmap_threshold
            if hasattr(info.config.optimizer_config, 'indexing_threshold'):
                result["optimizer_config"]["indexing_threshold"] = info.config.optimizer_config.indexing_threshold
            if hasattr(info.config.optimizer_config, 'flush_interval_sec'):
                result["optimizer_config"]["flush_interval_sec"] = info.config.optimizer_config.flush_interval_sec
            if hasattr(info.config.optimizer_config, 'max_optimization_threads'):
                result["optimizer_config"]["max_optimization_threads"] = info.config.optimizer_config.max_optimization_threads
                
        # WAL config 안전하게 추가
        if hasattr(info.config, 'wal_config'):
            result["wal_config"] = {}
            if hasattr(info.config.wal_config, 'wal_capacity_mb'):
                result["wal_config"]["wal_capacity_mb"] = info.config.wal_config.wal_capacity_mb
            if hasattr(info.config.wal_config, 'wal_segments_ahead'):
                result["wal_config"]["wal_segments_ahead"] = info.config.wal_config.wal_segments_ahead
            if hasattr(info.config.wal_config, 'wal_retain_closed'):
                result["wal_config"]["wal_retain_closed"] = info.config.wal_config.wal_retain_closed
        
        # 선택적 속성들을 안전하게 추가
        if hasattr(info, 'disk_data_size'):
            result["disk_data_size"] = info.disk_data_size
        else:
            result["disk_data_size"] = 0
            
        if hasattr(info, 'ram_data_size'):
            result["ram_data_size"] = info.ram_data_size
        else:
            result["ram_data_size"] = 0
            
        if hasattr(info, 'points_count'):
            result["points_count"] = info.points_count
        else:
            result["points_count"] = 0
            
        if hasattr(info, 'segments_count'):
            result["segments_count"] = info.segments_count
        else:
            result["segments_count"] = 0
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting collection info for {collection_name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get collection info: {str(e)}"
        )


@router.post("/{collection_name}/health", response_model=dict)
async def check_collection_health(
    collection_name: str,
    storage: QdrantVectorStorage = Depends(get_qdrant_storage)
):
    """
    Check the health status of a specific collection.
    
    Args:
        collection_name: Name of the collection
        storage: Qdrant storage instance
        
    Returns:
        Collection health status
    """
    try:
        logger.info(f"Checking health for collection: {collection_name}")
        
        # Check if collection exists
        collections = storage.client.get_collections()
        collection_names = [col.name for col in collections.collections]
        
        if collection_name not in collection_names:
            return {
                "collection_name": collection_name,
                "status": "not_found",
                "healthy": False,
                "message": f"Collection '{collection_name}' does not exist"
            }
        
        # Get collection info
        info = storage.client.get_collection(collection_name)
        
        return {
            "collection_name": collection_name,
            "status": info.status,
            "healthy": info.status == "green",
            "vectors_count": info.vectors_count,
            "message": f"Collection '{collection_name}' is {info.status}"
        }
        
    except Exception as e:
        logger.error(f"Error checking collection health for {collection_name}: {str(e)}")
        return {
            "collection_name": collection_name,
            "status": "error",
            "healthy": False,
            "message": f"Error checking collection health: {str(e)}"
        }


class ChunkRetrievalRequest(BaseModel):
    """Request model for retrieving document chunks"""
    document_name: str
    limit: Optional[int] = 100


@router.post("/{collection_name}/chunks", response_model=dict)
async def get_document_chunks(
    collection_name: str,
    request: ChunkRetrievalRequest,
    storage: QdrantVectorStorage = Depends(get_qdrant_storage)
):
    """
    Retrieve chunks for a specific document from a collection.
    
    Args:
        collection_name: Name of the collection
        request: Chunk retrieval request
        storage: Qdrant storage instance
        
    Returns:
        Document chunks with metadata
    """
    try:
        logger.info(f"Retrieving chunks for document '{request.document_name}' from collection '{collection_name}'")
        
        # Check if collection exists
        collections = storage.client.get_collections()
        collection_names = [col.name for col in collections.collections]
        
        if collection_name not in collection_names:
            raise HTTPException(
                status_code=404,
                detail=f"Collection '{collection_name}' not found"
            )
        
        # Search for chunks belonging to the specific document
        search_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="source_file",
                    match=models.MatchValue(value=request.document_name)
                )
            ]
        )
        
        # Use scroll to get all chunks for the document
        scroll_result = storage.client.scroll(
            collection_name=collection_name,
            scroll_filter=search_filter,
            limit=request.limit,
            with_payload=True,
            with_vectors=False
        )
        
        # Format results
        chunks = []
        for point in scroll_result[0]:  # scroll_result is a tuple (points, next_page_offset)
            # 실제 메타데이터에서 점수 계산
            payload = point.payload
            
            # 품질 점수 계산 (coherence_score 기반)
            quality_score = payload.get("coherence_score", 0.0)
            if quality_score > 0:
                quality_score = min(10, max(0, quality_score * 10))  # 0-1을 0-10으로 변환
            else:
                quality_score = payload.get("quality_score", 0)  # fallback
            
            # 의미 점수 계산 (connectivity_score 기반)
            semantic_score = payload.get("connectivity_score", 0.0)
            if semantic_score > 0:
                semantic_score = min(10, max(0, semantic_score * 10))  # 0-1을 0-10으로 변환
            else:
                semantic_score = payload.get("semantic_score", 0)  # fallback
            
            # 중복 점수 계산 (기본적으로 낮게 설정)
            duplicate_score = payload.get("duplicate_score", 0)
            
            chunk_data = {
                "chunk_id": payload.get("chunk_id", str(point.id)),
                "content": payload.get("content", ""),
                "document_name": payload.get("source_file", request.document_name),
                "chunk_type": payload.get("chunk_type", "text"),
                "start_position": payload.get("start_position", 0),
                "end_position": payload.get("end_position", 0),
                "metadata": payload,
                "score": 1.0,  # Default score for direct retrieval
                "quality_score": quality_score,
                "semantic_score": semantic_score,
                "duplicate_score": duplicate_score
            }
            chunks.append(chunk_data)
        
        logger.info(f"Found {len(chunks)} chunks for document '{request.document_name}'")
        
        return {
            "document_name": request.document_name,
            "collection_name": collection_name,
            "chunks": chunks,
            "total_chunks": len(chunks)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving chunks for document '{request.document_name}': {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve document chunks: {str(e)}"
        )


@router.delete("/{collection_name}/documents/{document_name}", response_model=dict)
async def delete_document(
    collection_name: str,
    document_name: str,
    storage: QdrantVectorStorage = Depends(get_qdrant_storage)
):
    """
    Delete a specific document and all its chunks from a collection.
    
    Args:
        collection_name: Name of the collection
        document_name: Name of the document to delete
        storage: Qdrant storage instance
        
    Returns:
        Deletion result with count of deleted chunks
    """
    try:
        logger.info(f"Deleting document '{document_name}' from collection '{collection_name}'")
        
        # Check if collection exists
        collections = storage.client.get_collections()
        collection_names = [col.name for col in collections.collections]
        
        if collection_name not in collection_names:
            raise HTTPException(
                status_code=404,
                detail=f"Collection '{collection_name}' not found"
            )
        
        # Search for chunks belonging to the specific document
        search_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="source_file",
                    match=models.MatchValue(value=document_name)
                )
            ]
        )
        
        # Get all chunks for the document to count them
        scroll_result = storage.client.scroll(
            collection_name=collection_name,
            scroll_filter=search_filter,
            limit=10000,  # Large limit to get all chunks
            with_payload=False,
            with_vectors=False
        )
        
        chunk_count = len(scroll_result[0])
        
        if chunk_count == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Document '{document_name}' not found in collection '{collection_name}'"
            )
        
        # Delete all chunks for the document
        storage.client.delete(
            collection_name=collection_name,
            points_selector=models.FilterSelector(
                filter=search_filter
            )
        )
        
        logger.info(f"Successfully deleted {chunk_count} chunks for document '{document_name}'")
        
        return {
            "document_name": document_name,
            "collection_name": collection_name,
            "deleted_chunks": chunk_count,
            "status": "deleted",
            "message": f"Document '{document_name}' and {chunk_count} chunks deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document '{document_name}': {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.get("/{collection_name}/documents", response_model=dict)
async def get_collection_documents(
    collection_name: str,
    storage: QdrantVectorStorage = Depends(get_qdrant_storage)
):
    """
    Get all unique documents in a collection.
    
    Args:
        collection_name: Name of the collection
        storage: Qdrant storage instance
        
    Returns:
        List of unique documents with metadata
    """
    try:
        logger.info(f"Getting all documents from collection: {collection_name}")
        
        # Check if collection exists
        collections = storage.client.get_collections()
        collection_names = [col.name for col in collections.collections]
        
        if collection_name not in collection_names:
            raise HTTPException(
                status_code=404,
                detail=f"Collection '{collection_name}' not found"
            )
        
        # Get all points from the collection
        scroll_result = storage.client.scroll(
            collection_name=collection_name,
            limit=10000,  # Large limit to get all documents
            with_payload=True,
            with_vectors=False
        )
        
        # Group by source_file to get unique documents
        documents = {}
        for point in scroll_result[0]:  # scroll_result is a tuple (points, next_page_offset)
            doc_name = point.payload.get("source_file") or point.payload.get("document_name")
            if doc_name:
                if doc_name not in documents:
                    # 첫 번째 청크의 created_at을 문서 생성 날짜로 사용
                    created_at = point.payload.get("created_at", "")
                    
                    # Extract Azure metadata from chunk metadata (nested under "metadata" key)
                    chunk_metadata = point.payload.get("metadata", {})
                    if isinstance(chunk_metadata, dict):
                        azure_file_path = chunk_metadata.get("azure_file_path")
                        upload_status = chunk_metadata.get("upload_status", "unknown")
                        download_url = chunk_metadata.get("download_url")
                    else:
                        azure_file_path = None
                        upload_status = "unknown"
                        download_url = None
                    
                    documents[doc_name] = {
                        "document_name": doc_name,
                        "chunk_count": 0,
                        "file_type": point.payload.get("file_type", "unknown"),
                        "file_size": point.payload.get("file_size", 0),
                        "upload_date": created_at,  # created_at을 upload_date로 사용
                        "container": point.payload.get("container", collection_name),
                        "status": point.payload.get("status", "processed"),
                        "metadata": {
                            "first_chunk_id": str(point.id),
                            "chunk_type": point.payload.get("chunk_type", "text"),
                            "quality_score": point.payload.get("quality_score", 0),
                            "semantic_score": point.payload.get("semantic_score", 0),
                            "azure_file_path": azure_file_path,
                            "upload_status": upload_status,
                            "download_url": download_url
                        }
                    }
                documents[doc_name]["chunk_count"] += 1
        
        # Convert to list and sort by document name
        document_list = list(documents.values())
        document_list.sort(key=lambda x: x["document_name"])
        
        logger.info(f"Found {len(document_list)} unique documents in collection '{collection_name}'")
        
        return {
            "collection_name": collection_name,
            "documents": document_list,
            "total_documents": len(document_list),
            "total_chunks": sum(doc["chunk_count"] for doc in document_list)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting documents from collection '{collection_name}': {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get collection documents: {str(e)}"
        )


def _encode_filename_for_header(filename: str) -> str:
    """
    Encode filename for Content-Disposition header using RFC 5987.
    Supports non-ASCII characters by providing both ASCII fallback and UTF-8 encoded version.
    
    Args:
        filename: Original filename (may contain non-ASCII characters)
    
    Returns:
        Properly encoded Content-Disposition filename value
    """
    try:
        # Check if filename contains only ASCII characters
        filename.encode('ascii')
        # If it's ASCII, use simple format
        return f'attachment; filename="{filename}"'
    except UnicodeEncodeError:
        # Filename contains non-ASCII characters, use RFC 5987 encoding
        # Create ASCII fallback by replacing non-ASCII characters
        ascii_fallback = filename.encode('ascii', 'replace').decode('ascii').replace('?', '_')
        # If fallback is empty or just underscores, use a generic name
        if not ascii_fallback or ascii_fallback.replace('_', '').replace('.', '') == '':
            # Extract extension if possible
            ext = ''
            if '.' in filename:
                ext = '.' + filename.split('.')[-1]
            ascii_fallback = f"file{ext}"
        
        # Encode the original filename using UTF-8 and percent-encoding
        utf8_encoded = quote(filename.encode('utf-8'), safe='')
        
        # RFC 5987 format: filename="fallback"; filename*=UTF-8''encoded-filename
        return f'attachment; filename="{ascii_fallback}"; filename*=UTF-8\'\'{utf8_encoded}'


@router.get("/files/download")
async def download_file_proxy(
    path: str,
    response: Response
):
    """
    Proxy endpoint to download files from Azure File Share without SAS tokens.
    Uses account key server-side for secure access.
    
    Args:
        path: URL-encoded file path in Azure File Share (e.g., "PCP/oss_voc_architecture.md")
    
    Returns:
        File content as streaming response
    """
    try:
        # Decode the file path
        file_path = unquote(path)
        
        if not file_path:
            raise HTTPException(status_code=400, detail="File path is required")
        
        # Download file from Azure using account key (server-side, no SAS tokens)
        file_content = azure_file_service.download_file(file_path)
        
        if file_content is None:
            raise HTTPException(
                status_code=404,
                detail=f"File not found or could not be downloaded: {file_path}"
            )
        
        # Extract filename for Content-Disposition header
        filename = file_path.split('/')[-1] if '/' in file_path else file_path
        
        # Set appropriate headers with proper encoding for non-ASCII filenames
        headers = {
            "Content-Disposition": _encode_filename_for_header(filename),
            "Content-Type": "application/octet-stream"
        }
        
        # Return file content with headers
        return Response(content=file_content, media_type="application/octet-stream", headers=headers)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download file {path}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download file: {str(e)}"
        )
