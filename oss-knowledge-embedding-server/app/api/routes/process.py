"""
File Processing Endpoints
Single file with all processing endpoints for different formats
"""

import logging
import uuid
import os
import re
import base64
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form, Body
from pydantic import BaseModel, Field

from app.config import settings
from app.services.processing_service import ProcessingService
from app.processors.excel.excel_models import ExcelProcessingOptions
from app.processors.base.base_models import ProcessingStatus, ProcessingResult
from app.processors.markdown.markdown_models import (
    MarkdownChunkingPreview, MarkdownInteractiveProcessing,
    ChunkPreview, ChunkingStrategy, UserEditedChunk,
    LLMChunkingResponse, LLMChunkSuggestion
)
from app.dependencies import get_processing_service, validate_file
from app.services.container_validation_service import container_validator, ContainerValidationError
from app.services.llm_chunking_service import LLMChunkingService

logger = logging.getLogger(__name__)
router = APIRouter()


# ===== HELPER FUNCTIONS =====

def _simple_chunk_text(text: str, strategy: str, chunk_size: int, overlap: int) -> List[Dict[str, Any]]:
    """
    Simple text chunking based on boundary strategy with overlap and fallback strategies.

    Args:
        text: Input text to chunk
        strategy: 'paragraph', 'sentence', or 'word'
        chunk_size: Target size in characters
        overlap: Overlap size in characters
    """
    chunks = []

    # Split text based on strategy
    if strategy == 'paragraph':
        boundaries = re.split(r'\n\s*\n', text)
    elif strategy == 'sentence':
        boundaries = re.split(r'(?<=[.!?])\s+', text)
    elif strategy == 'word':
        boundaries = text.split()
    else:
        boundaries = [text]

    # Build chunks respecting boundaries and size with fallback strategies
    current_chunk = ""
    start_pos = 0
    chunk_index = 0

    for boundary in boundaries:
        # Add boundary to current chunk
        if current_chunk:
            # For paragraph strategy, add double newline separator
            if strategy == 'paragraph':
                test_chunk = current_chunk + '\n\n' + boundary
            else:
                test_chunk = current_chunk + (' ' if strategy == 'word' else '') + boundary
        else:
            test_chunk = boundary

        # Check if the test chunk exceeds size limit
        if len(test_chunk) > chunk_size:
            if current_chunk:
                # Save current chunk first
                end_pos = start_pos + len(current_chunk)
                chunks.append({
                    'chunk_id': f'chunk_{chunk_index}',
                    'content': current_chunk,
                    'start_position': start_pos,
                    'end_position': end_pos,
                    'metadata': {
                        'chunk_index': chunk_index,
                        'length': len(current_chunk),
                        'strategy_used': strategy
                    }
                })
                chunk_index += 1

                # Start new chunk with overlap
                if overlap > 0 and len(current_chunk) > overlap:
                    # Get overlap text
                    overlap_text = current_chunk[-overlap:]

                    # Find the first word boundary (space) in overlap text
                    # This ensures we don't cut words in half
                    first_space = overlap_text.find(' ')
                    if first_space != -1:
                        # Start from first complete word in overlap
                        overlap_text = overlap_text[first_space + 1:]
                        actual_overlap = len(overlap_text)
                    else:
                        # If no space found, use the whole overlap
                        actual_overlap = overlap

                    # For paragraph strategy, maintain proper paragraph separation
                    if strategy == 'paragraph':
                        current_chunk = overlap_text + '\n\n' + boundary
                    else:
                        current_chunk = overlap_text + (' ' if overlap_text else '') + boundary
                    start_pos = end_pos - actual_overlap
                else:
                    current_chunk = boundary
                    start_pos = end_pos
                
                # Check if the new chunk (with or without overlap) exceeds size limit
                if len(current_chunk) > chunk_size:
                    # The new chunk is too large, apply fallback
                    fallback_chunks = _apply_fallback_chunking(
                        current_chunk, chunk_size, overlap, start_pos, chunk_index, strategy
                    )
                    chunks.extend(fallback_chunks)
                    chunk_index += len(fallback_chunks)
                    start_pos += len(current_chunk)
                    current_chunk = ""
            else:
                # Single boundary is too large - apply fallback chunking strategies
                fallback_chunks = _apply_fallback_chunking(
                    test_chunk, chunk_size, overlap, start_pos, chunk_index, strategy
                )
                chunks.extend(fallback_chunks)
                chunk_index += len(fallback_chunks)
                start_pos += len(test_chunk)
                current_chunk = ""
        else:
            # FIXED: Always accumulate content when it fits within chunk_size
            current_chunk = test_chunk

    # Add final chunk if any content remains
    if current_chunk:
        end_pos = start_pos + len(current_chunk)
        chunks.append({
            'chunk_id': f'chunk_{chunk_index}',
            'content': current_chunk,
            'start_position': start_pos,
            'end_position': end_pos,
            'metadata': {
                'chunk_index': chunk_index,
                'length': len(current_chunk),
                'strategy_used': strategy
            }
        })

    return chunks


def _apply_fallback_chunking(
    text: str, 
    chunk_size: int, 
    overlap: int, 
    start_pos: int, 
    chunk_index: int,
    original_strategy: str
) -> List[Dict[str, Any]]:
    """
    Apply fallback chunking strategies when a single boundary exceeds chunk_size.
    
    Fallback order: paragraph -> sentence -> word -> character
    """
    chunks = []
    current_pos = start_pos
    current_chunk_index = chunk_index
    
    # Try sentence-level chunking first
    if original_strategy == 'paragraph':
        sentences = re.split(r'(?<=[.!?])\s+', text)
        current_chunk = ""
        chunk_start = current_pos
        
        for sentence in sentences:
            test_chunk = current_chunk + (' ' if current_chunk else '') + sentence
            
            if len(test_chunk) > chunk_size and current_chunk:
                # Save current chunk
                chunks.append({
                    'chunk_id': f'chunk_{current_chunk_index}',
                    'content': current_chunk,
                    'start_position': chunk_start,
                    'end_position': chunk_start + len(current_chunk),
                    'metadata': {
                        'chunk_index': current_chunk_index,
                        'length': len(current_chunk),
                        'strategy_used': 'sentence_fallback'
                    }
                })
                current_chunk_index += 1
                
                # Start new chunk with overlap
                if overlap > 0 and len(current_chunk) > overlap:
                    overlap_text = current_chunk[-overlap:]
                    first_space = overlap_text.find(' ')
                    if first_space != -1:
                        overlap_text = overlap_text[first_space + 1:]
                    current_chunk = overlap_text + ' ' + sentence
                    chunk_start = chunk_start + len(current_chunk) - len(overlap_text) - len(sentence)
                else:
                    current_chunk = sentence
                    chunk_start = chunk_start + len(current_chunk)
            elif len(sentence) > chunk_size:
                # Single sentence is too large, try word-level chunking
                if current_chunk:
                    # Save current chunk first
                    chunks.append({
                        'chunk_id': f'chunk_{current_chunk_index}',
                        'content': current_chunk,
                        'start_position': chunk_start,
                        'end_position': chunk_start + len(current_chunk),
                        'metadata': {
                            'chunk_index': current_chunk_index,
                            'length': len(current_chunk),
                            'strategy_used': 'sentence_fallback'
                        }
                    })
                    current_chunk_index += 1
                
                word_chunks = _apply_fallback_chunking(
                    sentence, chunk_size, overlap, chunk_start, current_chunk_index, 'sentence'
                )
                chunks.extend(word_chunks)
                current_chunk_index += len(word_chunks)
                chunk_start += len(sentence)
                current_chunk = ""
            else:
                current_chunk = test_chunk
        
        # Add final chunk
        if current_chunk:
            chunks.append({
                'chunk_id': f'chunk_{current_chunk_index}',
                'content': current_chunk,
                'start_position': chunk_start,
                'end_position': chunk_start + len(current_chunk),
                'metadata': {
                    'chunk_index': current_chunk_index,
                    'length': len(current_chunk),
                    'strategy_used': 'sentence_fallback'
                }
            })
    
    # Try word-level chunking
    elif original_strategy in ['paragraph', 'sentence']:
        words = text.split()
        current_chunk = ""
        chunk_start = current_pos
        
        for word in words:
            test_chunk = current_chunk + (' ' if current_chunk else '') + word
            
            if len(test_chunk) > chunk_size and current_chunk:
                # Save current chunk
                chunks.append({
                    'chunk_id': f'chunk_{current_chunk_index}',
                    'content': current_chunk,
                    'start_position': chunk_start,
                    'end_position': chunk_start + len(current_chunk),
                    'metadata': {
                        'chunk_index': current_chunk_index,
                        'length': len(current_chunk),
                        'strategy_used': 'word_fallback'
                    }
                })
                current_chunk_index += 1
                
                # Start new chunk with overlap
                if overlap > 0 and len(current_chunk) > overlap:
                    overlap_text = current_chunk[-overlap:]
                    first_space = overlap_text.find(' ')
                    if first_space != -1:
                        overlap_text = overlap_text[first_space + 1:]
                    current_chunk = overlap_text + ' ' + word
                    chunk_start = chunk_start + len(current_chunk) - len(overlap_text) - len(word)
                else:
                    current_chunk = word
                    chunk_start = chunk_start + len(current_chunk)
            else:
                current_chunk = test_chunk
        
        # Add final chunk
        if current_chunk:
            chunks.append({
                'chunk_id': f'chunk_{current_chunk_index}',
                'content': current_chunk,
                'start_position': chunk_start,
                'end_position': chunk_start + len(current_chunk),
                'metadata': {
                    'chunk_index': current_chunk_index,
                    'length': len(current_chunk),
                    'strategy_used': 'word_fallback'
                }
            })
    
    # Last resort: character-level chunking (truncate)
    else:
        remaining_text = text
        while remaining_text:
            chunk_text = remaining_text[:chunk_size]
            chunks.append({
                'chunk_id': f'chunk_{current_chunk_index}',
                'content': chunk_text,
                'start_position': current_pos,
                'end_position': current_pos + len(chunk_text),
                'metadata': {
                    'chunk_index': current_chunk_index,
                    'length': len(chunk_text),
                    'strategy_used': 'character_fallback'
                }
            })
            current_chunk_index += 1
            current_pos += len(chunk_text)
            remaining_text = remaining_text[chunk_size:]
    
    return chunks


# ===== REQUEST/RESPONSE MODELS =====

class ProcessingJobResponse(BaseModel):
    """Processing job creation response"""
    job_id: str
    status: str
    message: str
    estimated_duration_seconds: Optional[int] = None


class ProcessingStatusResponse(BaseModel):
    """Processing status response"""
    job_id: str
    status: str  # "processing", "completed", "failed"
    progress: int  # 0-100
    current_step: str
    message: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    
    # Results (when completed)
    chunks_created: Optional[int] = None
    embeddings_generated: Optional[int] = None
    relationships_detected: Optional[int] = None
    storage_operations: Optional[Dict[str, Any]] = None


# ===== REQUEST MODELS FOR JSON UPLOADS =====

class ExcelFileRequest(BaseModel):
    """Excel file upload request with Base64 content"""
    filename: str
    content_base64: str
    container: str = "general"
    domain: Optional[str] = None
    chunking_strategy: str = "row_based"
    chunk_size: int = 10
    overlap: int = 0
    sheet_filter: Optional[str] = None
    include_formulas: bool = True
    create_graph: bool = False
    detect_relationships: bool = False
    detect_domains: bool = False
    generate_embeddings: bool = True
    embedding_model: Optional[str] = None


class MarkdownFileRequest(BaseModel):
    """Markdown file upload request with text content"""
    filename: str
    content: str
    container: str = "general"
    domain: Optional[str] = None
    chunking_strategy: str = "structure_aware_hierarchical"
    create_graph: bool = False
    detect_relationships: bool = False
    detect_domains: bool = False
    generate_embeddings: bool = True
    embedding_model: Optional[str] = None


class MarkdownPreviewRequest(BaseModel):
    """Markdown preview request with text content"""
    filename: str
    content: str
    container: str = "general"
    chunking_strategy: str = "paragraph"
    chunk_size: int = 500
    overlap: int = 50


class MarkdownLLMRequest(BaseModel):
    """Markdown LLM suggestion request with text content"""
    filename: str
    content: str
    container: str = "general"


class ExcelPreviewRequest(BaseModel):
    """Excel preview request with Base64 content"""
    filename: str
    content_base64: str
    container: str = "general"
    chunking_strategy: str = "row_based"
    chunk_size: int = 10
    overlap: int = 0


class ExcelLLMRequest(BaseModel):
    """Excel LLM suggestion request with Base64 content"""
    filename: str
    content_base64: str
    container: str = "general"


# ===== EXCEL PROCESSING ENDPOINTS =====

@router.post("/process/excel", response_model=ProcessingJobResponse)
async def process_excel_file(
    request: ExcelFileRequest = Body(...),
    # Dependencies
    processing_service: ProcessingService = Depends(get_processing_service)
):
    """
    Process Excel file with comprehensive semantic analysis
    
    **Processing Pipeline:**
    1. Parse Excel sheets and detect structure
    2. Apply intelligent chunking strategy
    3. Generate embeddings (if enabled)
    4. Detect domains and relationships using LangChain
    5. Store to external databases with container/domain specification
    6. Return job status for tracking
    
    **Request Body (JSON):**
    - **filename**: Excel file name
    - **content_base64**: Base64-encoded Excel file content
    - **container**: Container or domain to store the document (default: "general")
    - **domain**: Alias for container parameter (for backward compatibility)
    - All other processing options as in the request model
    
    **Processing Options:**
    - **chunking_strategy**: "sliding_window" (default), "hierarchical", "semantic"
    - **chunk_size**: Size of text chunks in characters
    - **chunk_overlap**: Overlap between chunks
    - **sheet_filter**: JSON string of sheet names to process
    - **include_formulas**: Include Excel formulas in analysis
    - **create_graph**: Create Neo4j document->department relationship (default: False)
    - **detect_relationships**: Enable complex relationship detection (default: False)
    - **detect_domains**: Enable domain classification (default: False)
    - **generate_embeddings**: Generate vector embeddings (default: True)
    - **embedding_model**: Override default embedding model
    """
    
    # Validate filename extension
    filename = request.filename
    if not filename.lower().endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only .xlsx and .xls files are supported."
        )
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    try:
        # Decode Base64 content
        try:
            file_content = base64.b64decode(request.content_base64)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid Base64 content: {str(e)}"
            )
        
        # Check file size (10MB limit)
        if len(file_content) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail="File size exceeds 10MB limit"
            )
        
        # Parse sheet filter if provided
        sheets_to_process = None
        if request.sheet_filter:
            import json
            sheets_to_process = json.loads(request.sheet_filter)
        
        # Handle container/domain specification
        final_container = request.domain if request.domain is not None else request.container
        
        # Validate container exists in database
        try:
            validation_result = container_validator.validate_container_with_suggestions(final_container)
            if not validation_result['valid']:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "Invalid container",
                        "message": validation_result['error'],
                        "available_containers": validation_result['available_containers'],
                        "suggestions": validation_result['suggestions']
                    }
                )
        except ContainerValidationError as e:
            logger.warning(f"Container validation service error: {e}. Using fallback validation.")
            # Use fallback validation when database is unavailable
            try:
                # Try to get collection name using fallback mapping
                collection_name = container_validator.get_container_collection_name(final_container)
                logger.info(f"Fallback validation successful for container '{final_container}' -> collection '{collection_name}'")
            except Exception as fallback_error:
                logger.error(f"Fallback validation also failed: {fallback_error}")
                raise HTTPException(
                    status_code=503,
                    detail=f"Container validation service unavailable: {str(e)}"
                )
        
        # Create processing options
        from app.processors.excel.excel_models import ExcelChunkingStrategy
        # Clamp overlap to max 10 for Excel (rows/columns, not characters)
        excel_overlap = min(request.overlap, 10)
        if request.overlap > 10:
            logger.warning(f"Excel overlap value {request.overlap} exceeds maximum of 10, clamping to 10")
        options = ExcelProcessingOptions(
            container=final_container,
            domain=request.domain,  # Keep for backward compatibility
            chunking_strategy=ExcelChunkingStrategy(request.chunking_strategy),
            chunk_size=request.chunk_size,
            chunk_overlap=excel_overlap,
            sheet_filter=sheets_to_process,
            include_formulas=request.include_formulas,
            create_graph=request.create_graph,
            detect_relationships=request.detect_relationships,
            detect_domains=request.detect_domains,
            generate_embeddings=request.generate_embeddings,
            embedding_model=request.embedding_model or settings.EMBEDDING_MODEL
        )
        
        # Save decoded file content temporarily
        temp_path = os.path.join(settings.TEMP_DIR, f"{job_id}_{filename}")
        with open(temp_path, "wb") as buffer:
            buffer.write(file_content)
        
        # Initialize processing service if needed
        await processing_service.initialize()
        
        # Process synchronously - this avoids the async/sync mixing issues entirely
        await processing_service.process_excel_file_async(
            job_id, temp_path, filename, options
        )
        
        logger.info(f"Completed Excel processing job: {job_id} for file: {filename}")
        
        return ProcessingJobResponse(
            job_id=job_id,
            status="completed",
            message=f"Excel file '{filename}' processed successfully"
        )
        
    except Exception as e:
        import traceback
        logger.error(f"Failed to process Excel file: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")


# ===== PDF PROCESSING ENDPOINTS (Future) =====

@router.post("/process/pdf", response_model=ProcessingJobResponse)
async def process_pdf_file(
    file: UploadFile = File(...),
    # Container/Domain specification
    container: str = Form("general"),
    domain: Optional[str] = Form(None),  # Alias for container
    # PDF-specific options would go here
    processing_service: ProcessingService = Depends(get_processing_service)
):
    """
    Process PDF file (Future implementation)
    
    **Note:** This endpoint is planned for future implementation.
    Currently returns a placeholder response.
    """
    
    # Placeholder for future PDF processing
    raise HTTPException(
        status_code=501, 
        detail="PDF processing not yet implemented. Currently supports Excel files only."
    )


# ===== MARKDOWN PROCESSING ENDPOINTS =====

@router.post("/process/markdown", response_model=ProcessingJobResponse)
async def process_markdown_file(
    request: MarkdownFileRequest = Body(...),
    # Dependencies
    processing_service: ProcessingService = Depends(get_processing_service)
):
    """
    Process Markdown file with Structure-Aware Hierarchical chunking
    
    **Processing Pipeline:**
    1. Parse markdown structure and elements
    2. Apply Structure-Aware Hierarchical chunking strategy
    3. Generate embeddings (if enabled)
    4. Detect domains and relationships using LangChain
    5. Store to external databases with container/domain specification
    6. Return job status for tracking
    
    **Request Body (JSON):**
    - **filename**: Markdown file name
    - **content**: UTF-8 text content of the markdown file
    - **container**: Container or domain to store the document (default: "general")
    - **domain**: Alias for container parameter (for backward compatibility)
    - All other processing options as in the request model
    
    **Processing Options:**
    - **chunking_strategy**: "structure_aware_hierarchical" (optimized for markdown)
    - **create_graph**: Create Neo4j document->department relationship (default: False)
    - **detect_relationships**: Enable complex relationship detection (default: False)
    - **detect_domains**: Enable domain classification (default: False)
    - **generate_embeddings**: Generate vector embeddings (default: True)
    - **embedding_model**: Override default embedding model
    """
    
    # Validate filename extension
    filename = request.filename
    if not filename.lower().endswith(('.md', '.markdown')):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only .md and .markdown files are supported."
        )
    
    # Check content size (10MB limit for text content)
    content_bytes = request.content.encode('utf-8')
    if len(content_bytes) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="Content size exceeds 10MB limit"
        )
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    try:
        # Handle container/domain specification
        final_container = request.domain if request.domain is not None else request.container
        
        # Validate container exists in database
        try:
            validation_result = container_validator.validate_container_with_suggestions(final_container)
            if not validation_result['valid']:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "Invalid container",
                        "message": validation_result['error'],
                        "available_containers": validation_result['available_containers'],
                        "suggestions": validation_result['suggestions']
                    }
                )
        except ContainerValidationError as e:
            logger.warning(f"Container validation service error: {e}. Using fallback validation.")
            # Use fallback validation when database is unavailable
            try:
                # Try to get collection name using fallback mapping
                collection_name = container_validator.get_container_collection_name(final_container)
                logger.info(f"Fallback validation successful for container '{final_container}' -> collection '{collection_name}'")
            except Exception as fallback_error:
                logger.error(f"Fallback validation also failed: {fallback_error}")
                raise HTTPException(
                    status_code=503,
                    detail=f"Container validation service unavailable: {str(e)}"
                )
        
        # Use content from request
        markdown_content = request.content
        
        # Initialize processing service if needed
        await processing_service.initialize()
        
        # Process markdown content directly (no temporary file needed)
        await processing_service.process_markdown_content_async(
            job_id, markdown_content, filename, final_container,
            request.chunking_strategy, request.create_graph, request.detect_relationships, request.detect_domains,
            request.generate_embeddings, request.embedding_model
        )
        
        logger.info(f"Completed Markdown processing job: {job_id} for file: {filename}")
        
        return ProcessingJobResponse(
            job_id=job_id,
            status="completed",
            message=f"Markdown file '{filename}' processed successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to process Markdown file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")


# ===== UNIVERSAL STATUS ENDPOINT =====

@router.get("/process/status/{job_id}", response_model=ProcessingStatusResponse)
async def get_processing_status(
    job_id: str,
    processing_service: ProcessingService = Depends(get_processing_service)
):
    """
    Get processing status for any job type
    
    **Universal endpoint** that works for Excel, PDF, Markdown, or any future format.
    
    **Status Values:**
    - `processing`: Job is currently running
    - `completed`: Job finished successfully
    - `failed`: Job encountered an error
    
    **Progress:** 0-100 percentage complete
    """
    
    try:
        status = await processing_service.get_job_status(job_id)
        
        if not status:
            raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
        
        return ProcessingStatusResponse(
            job_id=job_id,
            status=status.status,
            progress=status.progress,
            current_step=status.current_step,
            message=status.message,
            started_at=status.started_at,
            completed_at=status.completed_at,
            error=status.error,
            chunks_created=status.chunks_created,
            embeddings_generated=status.embeddings_generated,
            relationships_detected=status.relationships_detected,
            storage_operations=status.storage_operations
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== JOB MANAGEMENT ENDPOINTS =====

@router.delete("/process/jobs/{job_id}")
async def delete_processing_job(
    job_id: str,
    processing_service: ProcessingService = Depends(get_processing_service)
):
    """
    Delete a processing job and cleanup resources
    
    **Use cases:**
    - Clean up completed jobs
    - Cancel running jobs
    - Free up storage space
    
    **Warning:** This will permanently delete all job data and results.
    """
    
    try:
        success = await processing_service.delete_job(job_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
        
        return {"message": f"Job {job_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/process/jobs")
async def list_processing_jobs(
    status_filter: Optional[str] = None,
    limit: int = 50,
    processing_service: ProcessingService = Depends(get_processing_service)
):
    """
    List processing jobs with optional filtering
    
    **Query Parameters:**
    - **status_filter**: Filter by status ("processing", "completed", "failed")
    - **limit**: Maximum number of jobs to return (default: 50)
    
    **Use cases:**
    - Monitor active jobs
    - Review completed jobs
    - Debug failed jobs
    """
    
    try:
        jobs = await processing_service.list_jobs(status_filter, limit)
        
        return {
            "jobs": jobs,
            "total": len(jobs),
            "filter": status_filter
        }
        
    except Exception as e:
        logger.error(f"Error listing jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== CONTAINER MANAGEMENT ENDPOINTS =====

@router.get("/process/containers")
async def get_available_containers():
    """
    Get list of available containers from the database
    
    **Returns:**
    - List of available containers with metadata
    - Each container includes name, description, icon, color, keywords
    - Only returns active containers
    """
    try:
        containers = container_validator.get_available_containers()
        return {
            "containers": containers,
            "total": len(containers)
        }
    except ContainerValidationError as e:
        logger.error(f"Failed to get available containers: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Container service unavailable: {str(e)}"
        )


@router.get("/process/containers/validate/{container_name}")
async def validate_container_name(container_name: str):
    """
    Validate a specific container name
    
    **Returns:**
    - Validation result with suggestions if invalid
    - Available containers list
    - Similar container suggestions
    """
    try:
        validation_result = container_validator.validate_container_with_suggestions(container_name)
        return validation_result
    except ContainerValidationError as e:
        logger.error(f"Container validation failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Container validation service unavailable: {str(e)}"
        )


@router.post("/process/containers/refresh")
async def refresh_containers():
    """
    Refresh the container cache from database
    
    **Use cases:**
    - After adding new containers to the database
    - When containers list appears outdated
    - Administrative cache refresh
    """
    try:
        containers = container_validator.get_available_containers(force_refresh=True)
        return {
            "message": "Container cache refreshed successfully",
            "containers": containers,
            "total": len(containers)
        }
    except ContainerValidationError as e:
        logger.error(f"Container cache refresh failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Container service unavailable: {str(e)}"
        )


# ===== PROCESSING CAPABILITIES ENDPOINT =====

@router.get("/process/capabilities")
async def get_processing_capabilities():
    """
    Get information about processing capabilities and supported formats
    
    **Returns:**
    - Supported file formats
    - Available processing options
    - System limits and constraints
    - Storage interface information
    """
    
    return {
        "supported_formats": {
            "excel": {
                "extensions": [".xlsx", ".xls"],
                "status": "available",
                "features": [
                    "Semantic analysis with LangChain",
                    "Domain detection",
                    "Relationship extraction",
                    "Multiple chunking strategies",
                    "Formula analysis"
                ]
            },
            "pdf": {
                "extensions": [".pdf"],
                "status": "planned",
                "features": ["Text extraction", "Structure analysis", "Embedding generation"]
            },
            "markdown": {
                "extensions": [".md", ".markdown"],
                "status": "available", 
                "features": [
                    "Structure-Aware Hierarchical chunking",
                    "Semantic analysis with LangChain",
                    "Domain detection",
                    "Relationship extraction",
                    "Azure OpenAI text-embedding-3-large embeddings"
                ]
            }
        },
        "processing_options": {
            "chunking_strategies": ["sliding_window", "hierarchical", "semantic"],
            "embedding_models": [
                settings.EMBEDDING_MODEL
            ],
            "max_file_size_mb": settings.MAX_FILE_SIZE // (1024 * 1024),
            "max_concurrent_jobs": settings.MAX_CONCURRENT_JOBS,
            "job_timeout_seconds": settings.JOB_TIMEOUT_SECONDS
        },
        "storage_interfaces": {
            "qdrant_vector_db": {
                "configured": settings.ENABLE_QDRANT,
                "host": settings.QDRANT_HOST,
                "port": settings.QDRANT_PORT
            },
            "neo4j_graph_db": {
                "configured": settings.ENABLE_NEO4J,
                "uri": settings.NEO4J_URI,
                "database": settings.NEO4J_DATABASE
            },
            "embedding_service": {
                "model": settings.EMBEDDING_MODEL,
                "device": settings.EMBEDDING_DEVICE,
                "dimension": settings.VECTOR_SIZE
            }
        }
    }


# ===== INTERACTIVE MARKDOWN CHUNKING ENDPOINTS =====

@router.post("/process/markdown/preview", response_model=MarkdownChunkingPreview)
async def preview_markdown_chunking(
    request: MarkdownPreviewRequest = Body(...),
    processing_service: ProcessingService = Depends(get_processing_service)
):
    """
    **Preview markdown chunking** - Get chunk previews based on simple chunking parameters

    **Interactive Workflow Step 1/2**: Upload markdown content to see how it would be chunked.
    This endpoint does NOT store any data - it only shows you the chunking preview.

    **Request Body (JSON):**
    - **filename**: Markdown file name
    - **content**: UTF-8 text content of the markdown file
    - **container**: Target container for eventual storage (default: "general")
    - **chunking_strategy**: 'paragraph', 'sentence', or 'word' (default: "paragraph")
    - **chunk_size**: Number of characters per chunk (default: 500)
    - **overlap**: Number of characters to overlap between chunks (default: 50)

    **Returns:**
    - Preview of all chunks with content and metadata
    - No data is stored in this step
    """

    # Validate filename extension
    filename = request.filename
    if not filename.lower().endswith(('.md', '.markdown')):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only .md and .markdown files are supported."
        )

    try:
        # Validate container exists in database (temporarily disabled for testing)
        try:
            validation_result = container_validator.validate_container_with_suggestions(request.container)
            if not validation_result['valid']:
                logger.warning(f"Container validation failed for '{request.container}', but allowing for testing")
        except ContainerValidationError as e:
            logger.warning(f"Container validation service error: {e}, but allowing for testing")

        # Use content from request
        markdown_content = request.content

        start_time = datetime.now()

        # Generate simple chunks
        chunks = _simple_chunk_text(markdown_content, request.chunking_strategy, request.chunk_size, request.overlap)

        processing_time = (datetime.now() - start_time).total_seconds()

        logger.info(f"Generated markdown chunking preview for file: {filename} ({len(chunks)} chunks)")

        return MarkdownChunkingPreview(
            filename=filename,
            content_length=len(markdown_content),
            recommended_strategy=ChunkingStrategy(
                strategy_name=request.chunking_strategy,
                reason=f"Chunking by {request.chunking_strategy} with {request.chunk_size} characters and {request.overlap} overlap",
                parameters={
                    "chunk_size": request.chunk_size,
                    "overlap": request.overlap,
                    "boundary": request.chunking_strategy
                }
            ),
            chunks=[
                ChunkPreview(
                    chunk_id=chunk['chunk_id'],
                    content=chunk['content'],
                    chunk_type='text',
                    start_position=chunk['start_position'],
                    end_position=chunk['end_position'],
                    metadata=chunk.get('metadata', {})
                )
                for chunk in chunks
            ],
            total_chunks=len(chunks),
            processing_time_seconds=processing_time
        )

    except Exception as e:
        logger.error(f"Failed to preview markdown chunking: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to preview chunking: {str(e)}")


@router.post("/process/excel/preview", response_model=MarkdownChunkingPreview)
async def preview_excel_chunking(
    request: ExcelPreviewRequest = Body(...),
    processing_service: ProcessingService = Depends(get_processing_service)
):
    """
    **Preview Excel chunking** - Get chunk previews based on chunking parameters

    **Interactive Workflow Step 1/2**: Upload Excel content to see how it would be chunked.
    This endpoint does NOT store any data - it only shows you the chunking preview.

    **Request Body (JSON):**
    - **filename**: Excel file name
    - **content_base64**: Base64-encoded Excel file content
    - **container**: Target container for eventual storage (default: "general")
    - **chunking_strategy**: 'row_based' or 'column_based' (default: "row_based")
    - **chunk_size**: Number of rows (row_based) or columns (column_based) per chunk (default: 10)
    - **overlap**: Number of rows/columns to overlap between chunks (default: 0)

    **Returns:**
    - Preview of all chunks with content and metadata
    - No data is stored in this step
    """

    # Validate filename extension
    filename = request.filename
    if not filename.lower().endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only .xlsx and .xls files are supported."
        )

    try:
        # Validate container exists in database (temporarily disabled for testing)
        try:
            validation_result = container_validator.validate_container_with_suggestions(request.container)
            if not validation_result['valid']:
                logger.warning(f"Container validation failed for '{request.container}', but allowing for testing")
        except ContainerValidationError as e:
            logger.warning(f"Container validation service error: {e}, but allowing for testing")

        # Decode Base64 content
        try:
            file_content = base64.b64decode(request.content_base64)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid Base64 content: {str(e)}"
            )

        # Check file size (10MB limit)
        if len(file_content) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail="File size exceeds 10MB limit"
            )

        # Save decoded file content temporarily
        job_id = str(uuid.uuid4())
        temp_path = os.path.join(settings.TEMP_DIR, f"{job_id}_{filename}")
        os.makedirs(settings.TEMP_DIR, exist_ok=True)
        with open(temp_path, "wb") as buffer:
            buffer.write(file_content)

        try:
            start_time = datetime.now()

            # Create processing options (no embeddings for preview)
            from app.processors.excel.excel_models import ExcelProcessingOptions, ExcelChunkingStrategy
            # Clamp overlap to max 10 for Excel (rows/columns, not characters)
            excel_overlap = min(request.overlap, 10)
            if request.overlap > 10:
                logger.warning(f"Excel overlap value {request.overlap} exceeds maximum of 10, clamping to 10")
            options = ExcelProcessingOptions(
                container=request.container,
                chunking_strategy=ExcelChunkingStrategy(request.chunking_strategy),
                chunk_size=request.chunk_size,
                chunk_overlap=excel_overlap,
                generate_embeddings=False  # No embeddings for preview
            )

            # Process Excel file (no storage)
            from app.processors.excel.excel_processor import ExcelProcessor
            excel_processor = ExcelProcessor()
            processing_result = await excel_processor.process_file(temp_path, options, job_id)

            chunks = processing_result.get("chunks", [])
            processing_time = (datetime.now() - start_time).total_seconds()

            logger.info(f"Generated Excel chunking preview for file: {filename} ({len(chunks)} chunks)")

            # Convert ProcessedChunk to ChunkPreview format
            chunk_previews = []
            for i, chunk in enumerate(chunks):
                # Excel chunks may not have start_position/end_position, provide defaults
                start_pos = chunk.start_position if chunk.start_position is not None else i
                end_pos = chunk.end_position if chunk.end_position is not None else (i + 1)
                
                chunk_previews.append(ChunkPreview(
                    chunk_id=chunk.chunk_id,
                    content=chunk.content,
                    chunk_type=chunk.chunk_type,
                    start_position=start_pos,
                    end_position=end_pos,
                    metadata=chunk.metadata or {}
                ))

            return MarkdownChunkingPreview(
                filename=filename,
                content_length=len(file_content),
                recommended_strategy=ChunkingStrategy(
                    strategy_name=request.chunking_strategy,
                    reason=f"Chunking by {request.chunking_strategy}",
                    parameters={
                        "chunk_size": request.chunk_size,
                        "overlap": request.overlap,
                        "strategy": request.chunking_strategy
                    }
                ),
                chunks=chunk_previews,
                total_chunks=len(chunk_previews),
                processing_time_seconds=processing_time
            )

        finally:
            # Clean up temp file
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception as e:
                logger.warning(f"Could not clean up temp file {temp_path}: {e}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to preview Excel chunking: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to preview chunking: {str(e)}")


@router.post("/process/markdown/confirm", response_model=ProcessingJobResponse)
async def confirm_markdown_processing(
    request: MarkdownInteractiveProcessing,
    processing_service: ProcessingService = Depends(get_processing_service)
):
    """
    **Confirm markdown processing** - Process user-edited chunks and store data

    **Interactive Workflow Step 2/2**: Submit user-edited chunks for final processing.
    This endpoint processes the chunks, generates embeddings, and stores everything.

    **Usage:**
    1. Use `/process/markdown/preview` to get initial chunking
    2. Edit chunk content/boundaries as needed
    3. Submit here for final processing and storage

    **Request Body:**
    - **filename**: Original filename
    - **container**: Target container for storage
    - **chunks**: Array of user-edited chunks
    - **create_graph**: Create Neo4j relationships (default: False)
    - **detect_relationships**: Enable relationship detection (default: False)
    - **detect_domains**: Enable domain classification (default: False)
    - **generate_embeddings**: Generate embeddings (default: True)
    - **embedding_model**: Embedding model to use

    **Processing:**
    - Generates embeddings for user chunks
    - Stores in Qdrant vector database
    - Creates Neo4j graph relationships (if enabled)
    - Stores metadata in document store
    """

    # Generate job ID
    job_id = str(uuid.uuid4())

    try:
        # Validate container exists in database
        try:
            validation_result = container_validator.validate_container_with_suggestions(request.container)
            if not validation_result['valid']:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "Invalid container",
                        "message": validation_result['error'],
                        "available_containers": validation_result['available_containers'],
                        "suggestions": validation_result['suggestions']
                    }
                )
        except ContainerValidationError as e:
            logger.error(f"Container validation service error: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Container validation service unavailable: {str(e)}"
            )

        # Initialize processing service if needed
        await processing_service.initialize()

        # Determine file type from filename
        file_type = "markdown" if request.filename.lower().endswith(('.md', '.markdown')) else "text"
        
        # Process user-edited chunks
        await processing_service.process_user_edited_chunks_async(
            job_id=job_id,
            filename=request.filename,
            container=request.container,
            user_chunks=request.chunks,
            create_graph=request.create_graph,
            detect_relationships=request.detect_relationships,
            detect_domains=request.detect_domains,
            generate_embeddings=request.generate_embeddings,
            embedding_model=request.embedding_model,
            file_type=file_type
        )

        logger.info(f"Completed interactive markdown processing job: {job_id} for file: {request.filename} ({len(request.chunks)} chunks)")

        return ProcessingJobResponse(
            job_id=job_id,
            status="completed",
            message=f"Markdown file '{request.filename}' processed successfully with {len(request.chunks)} user-edited chunks"
        )

    except Exception as e:
        logger.error(f"Failed to process user-edited markdown chunks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process chunks: {str(e)}")


@router.post("/process/excel/confirm", response_model=ProcessingJobResponse)
async def confirm_excel_processing(
    request: MarkdownInteractiveProcessing,
    processing_service: ProcessingService = Depends(get_processing_service)
):
    """
    **Confirm Excel processing** - Process user-edited chunks and store data

    **Interactive Workflow Step 2/2**: Submit user-edited chunks for final processing.
    This endpoint processes the chunks, generates embeddings, and stores everything.

    **Usage:**
    1. Use `/process/excel/preview` to get initial chunking
    2. Edit chunk content/boundaries as needed
    3. Submit here for final processing and storage

    **Request Body:**
    - **filename**: Original filename
    - **container**: Target container for storage
    - **chunks**: Array of user-edited chunks
    - **create_graph**: Create Neo4j relationships (default: False)
    - **detect_relationships**: Enable relationship detection (default: False)
    - **detect_domains**: Enable domain classification (default: False)
    - **generate_embeddings**: Generate embeddings (default: True)
    - **embedding_model**: Embedding model to use

    **Processing:**
    - Generates embeddings for user chunks
    - Stores in Qdrant vector database
    - Creates Neo4j graph relationships (if enabled)
    - Stores metadata in document store
    """

    # Generate job ID
    job_id = str(uuid.uuid4())

    try:
        # Validate container exists in database
        try:
            validation_result = container_validator.validate_container_with_suggestions(request.container)
            if not validation_result['valid']:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "Invalid container",
                        "message": validation_result['error'],
                        "available_containers": validation_result['available_containers'],
                        "suggestions": validation_result['suggestions']
                    }
                )
        except ContainerValidationError as e:
            logger.error(f"Container validation service error: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Container validation service unavailable: {str(e)}"
            )

        # Initialize processing service if needed
        await processing_service.initialize()

        # Determine file type from filename
        file_type = "excel" if request.filename.lower().endswith(('.xlsx', '.xls')) else "markdown"
        
        # Process user-edited chunks (reuse existing method)
        await processing_service.process_user_edited_chunks_async(
            job_id=job_id,
            filename=request.filename,
            container=request.container,
            user_chunks=request.chunks,
            create_graph=request.create_graph,
            detect_relationships=request.detect_relationships,
            detect_domains=request.detect_domains,
            generate_embeddings=request.generate_embeddings,
            embedding_model=request.embedding_model,
            file_type=file_type
        )

        logger.info(f"Completed interactive Excel processing job: {job_id} for file: {request.filename} ({len(request.chunks)} chunks)")

        return ProcessingJobResponse(
            job_id=job_id,
            status="completed",
            message=f"Excel file '{request.filename}' processed successfully with {len(request.chunks)} user-edited chunks"
        )

    except Exception as e:
        error_msg = str(e) if str(e) else repr(e)
        logger.error(f"Failed to process user-edited Excel chunks: {error_msg}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process chunks: {error_msg}")


@router.post("/process/markdown/llm-suggest", response_model=LLMChunkingResponse)
async def suggest_llm_chunking(
    request: MarkdownLLMRequest = Body(...)
):
    """
    **LLM 청킹 제안** - Azure OpenAI를 사용하여 마크다운 문서의 최적 청크 경계를 제안
    
    이 엔드포인트는 1MB 이하의 마크다운 파일을 분석하여 의미론적으로 최적화된 청크 분할을 제안합니다.
    기존의 paragraph/sentence/word 전략을 사용하지 않고, 문서의 의미와 구조를 분석하여 커스텀 청크 경계를 제안합니다.
    
    **Request Body (JSON):**
    - **filename**: 마크다운 파일 이름 (.md, .markdown)
    - **content**: UTF-8 텍스트 내용
    - **container**: 대상 컨테이너 (기본값: "general")
    
    **Returns:**
    - LLM이 제안한 청크 목록과 메타데이터
    - 토큰 사용량 정보
    - 처리 시간 통계
    
    **File Size Limit:**
    - 최대 10MB (텍스트 내용 기준)
    """
    
    # Validate filename extension
    filename = request.filename
    if not filename.lower().endswith(('.md', '.markdown')):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only .md and .markdown files are supported."
        )
    
    # Check content size (10MB limit for text content)
    content_bytes = request.content.encode('utf-8')
    file_size = len(content_bytes)
    
    # Check reasonable file size limit (10MB for safety)
    MAX_REASONABLE_SIZE = 10 * 1024 * 1024  # 10MB
    if file_size > MAX_REASONABLE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"파일이 너무 큽니다. 최대 {MAX_REASONABLE_SIZE / 1024 / 1024}MB 파일만 지원합니다."
        )
    
    try:
        # Validate container exists in database
        try:
            validation_result = container_validator.validate_container_with_suggestions(request.container)
            if not validation_result['valid']:
                logger.warning(f"Container validation failed for '{request.container}', but allowing for testing")
        except ContainerValidationError as e:
            logger.warning(f"Container validation service error: {e}, but allowing for testing")
        
        # Use content from request
        markdown_content = request.content
        
        start_time = datetime.now()
        
        # Initialize LLM chunking service
        llm_service = LLMChunkingService()
        
        # Get LLM suggestions
        suggestions = await llm_service.suggest_chunks(markdown_content)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Convert suggestions to response format
        suggested_chunks = []
        for suggestion in suggestions:
            suggested_chunks.append(LLMChunkSuggestion(
                start_position=suggestion.start_position,
                end_position=suggestion.end_position,
                content=suggestion.content,
                reasoning=suggestion.reasoning,
                semantic_score=suggestion.semantic_score
            ))
        
        logger.info(f"Generated LLM chunking suggestions for file: {filename} ({len(suggestions)} chunks)")
        
        return LLMChunkingResponse(
            filename=filename,
            content_length=len(markdown_content),
            file_size_mb=file_size / (1024 * 1024),
            llm_model_used=settings.OPENAI_MODEL,
            suggested_chunks=suggested_chunks,
            total_chunks=len(suggestions),
            processing_time_seconds=processing_time,
            token_usage={
                "prompt_tokens": 0,  # Will be updated if we track this
                "completion_tokens": 0,
                "total_tokens": 0
            }
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (like file size limit)
        raise
    except Exception as e:
        logger.error(f"Failed to generate LLM chunking suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"LLM 청킹 제안 생성 중 오류가 발생했습니다: {str(e)}")


@router.post("/process/excel/llm-suggest", response_model=LLMChunkingResponse)
async def suggest_excel_llm_chunking(
    request: ExcelLLMRequest = Body(...)
):
    """
    **LLM 청킹 제안** - Azure OpenAI를 사용하여 Excel 문서의 최적 청크 경계를 제안
    
    이 엔드포인트는 Excel 파일을 분석하여 의미론적으로 최적화된 청크 분할을 제안합니다.
    Excel을 텍스트 표현으로 변환한 후 LLM으로 분석합니다.
    
    **Request Body (JSON):**
    - **filename**: Excel 파일 이름 (.xlsx, .xls)
    - **content_base64**: Base64-encoded Excel file content
    - **container**: 대상 컨테이너 (기본값: "general")
    
    **Returns:**
    - LLM이 제안한 청크 목록과 메타데이터
    - 토큰 사용량 정보
    - 처리 시간 통계
    
    **File Size Limit:**
    - 최대 10MB
    """
    
    # Validate filename extension
    filename = request.filename
    if not filename.lower().endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only .xlsx and .xls files are supported."
        )
    
    try:
        # Decode Base64 content
        try:
            file_content = base64.b64decode(request.content_base64)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid Base64 content: {str(e)}"
            )
        
        # Check file size (10MB limit)
        file_size = len(file_content)
        MAX_REASONABLE_SIZE = 10 * 1024 * 1024  # 10MB
        if file_size > MAX_REASONABLE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"파일이 너무 큽니다. 최대 {MAX_REASONABLE_SIZE / 1024 / 1024}MB 파일만 지원합니다."
            )
        
        # Validate container exists in database
        try:
            validation_result = container_validator.validate_container_with_suggestions(request.container)
            if not validation_result['valid']:
                logger.warning(f"Container validation failed for '{request.container}', but allowing for testing")
        except ContainerValidationError as e:
            logger.warning(f"Container validation service error: {e}, but allowing for testing")
        
        # Save decoded file content temporarily
        job_id = str(uuid.uuid4())
        temp_path = os.path.join(settings.TEMP_DIR, f"{job_id}_{filename}")
        os.makedirs(settings.TEMP_DIR, exist_ok=True)
        with open(temp_path, "wb") as buffer:
            buffer.write(file_content)
        
        try:
            start_time = datetime.now()
            
            # Process Excel to get text representation
            from app.processors.excel.excel_models import ExcelProcessingOptions, ExcelChunkingStrategy
            from app.processors.excel.excel_processor import ExcelProcessor
            
            options = ExcelProcessingOptions(
                container=request.container,
                chunking_strategy=ExcelChunkingStrategy.ROW_BASED,
                chunk_size=10,
                chunk_overlap=0,
                generate_embeddings=False
            )
            
            excel_processor = ExcelProcessor()
            processing_result = await excel_processor.process_file(temp_path, options, job_id)
            chunks = processing_result.get("chunks", [])
            
            # Combine all chunk content into text for LLM analysis
            excel_text = "\n\n".join([chunk.content for chunk in chunks])
            
            # Initialize LLM chunking service
            llm_service = LLMChunkingService()
            
            # Get LLM suggestions
            suggestions = await llm_service.suggest_chunks(excel_text)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Convert suggestions to response format
            suggested_chunks = []
            for suggestion in suggestions:
                suggested_chunks.append(LLMChunkSuggestion(
                    start_position=suggestion.start_position,
                    end_position=suggestion.end_position,
                    content=suggestion.content,
                    reasoning=suggestion.reasoning,
                    semantic_score=suggestion.semantic_score
                ))
            
            logger.info(f"Generated LLM chunking suggestions for Excel file: {filename} ({len(suggestions)} chunks)")
            
            return LLMChunkingResponse(
                filename=filename,
                content_length=len(excel_text),
                file_size_mb=file_size / (1024 * 1024),
                llm_model_used=settings.OPENAI_MODEL,
                suggested_chunks=suggested_chunks,
                total_chunks=len(suggestions),
                processing_time_seconds=processing_time,
                token_usage={
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            )
        
        finally:
            # Clean up temp file
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception as e:
                logger.warning(f"Could not clean up temp file {temp_path}: {e}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate LLM chunking suggestions for Excel: {str(e)}")
        raise HTTPException(status_code=500, detail=f"LLM 청킹 제안 생성 중 오류가 발생했습니다: {str(e)}")