"""
Processing Service
Main orchestration service for file processing jobs
"""

import asyncio
import logging
import os
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.config import settings
from app.processors.excel.excel_processor import ExcelProcessor
from app.processors.excel.excel_models import ExcelProcessingOptions
from app.processors.markdown.markdown_models import MarkdownProcessingOptions, UserEditedChunk
from app.services.markdown_processor import MarkdownProcessorService
from app.processors.base.base_models import (
    ProcessingStatus, ProcessingStatusEnum, FileRecord, StorageType
)
from app.services.storage_service import StorageService
from app.services.metadata_sync_service import metadata_sync_service
from app.core.exceptions import ProcessingException

logger = logging.getLogger(__name__)


class ProcessingService:
    """Main processing service for orchestrating file processing jobs with container isolation"""
    
    def __init__(self):
        self.storage_services: Dict[str, StorageService] = {}  # Container-specific storage services
        self.excel_processor = ExcelProcessor()
        self.markdown_processor = MarkdownProcessorService()
        self.active_jobs: Dict[str, ProcessingStatus] = {}
        self.job_semaphore = None  # Initialize in async method
    
    async def get_storage_service(self, container: str) -> StorageService:
        """Get or create storage service for specific container"""
        if container not in self.storage_services:
            storage_service = StorageService(container=container)
            await storage_service.initialize()
            self.storage_services[container] = storage_service
            logger.info(f"Created storage service for container: {container}")
        
        return self.storage_services[container]
    
    async def initialize(self):
        """Initialize processing service"""
        # Initialize semaphore here where we have an event loop
        if self.job_semaphore is None:
            self.job_semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_JOBS)
        
        # Initialize default storage service
        await self.get_storage_service("general")
        logger.info("Processing service initialized")
    
    def process_excel_file_sync(
        self,
        job_id: str,
        file_path: str,
        filename: str,
        options: ExcelProcessingOptions
    ) -> None:
        """Process Excel file in background task (sync wrapper)"""
        import asyncio
        try:
            # Get or create event loop for background task
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run the async processing
        loop.run_until_complete(
            self.process_excel_file_async(job_id, file_path, filename, options)
        )

    async def process_excel_file_async(
        self,
        job_id: str,
        file_path: str,
        filename: str,
        options: ExcelProcessingOptions
    ) -> None:
        """Process Excel file in background task (async implementation)"""
        
        # Create initial job status
        job_status = ProcessingStatus(
            job_id=job_id,
            status=ProcessingStatusEnum.PROCESSING,
            progress=0,
            current_step="Starting Excel processing",
            message=f"Processing {filename}",
            started_at=datetime.now()
        )
        
        self.active_jobs[job_id] = job_status
        
        # Get container-specific storage service
        storage_service = await self.get_storage_service(options.container)
        await storage_service.update_job_status(job_id, job_status.dict())
        
        # Ensure semaphore is initialized
        if self.job_semaphore is None:
            self.job_semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_JOBS)
            
        async with self.job_semaphore:
            try:
                await self._process_excel_with_status_updates(
                    job_id, file_path, filename, options
                )
                
            except Exception as e:
                logger.error(f"Processing failed for job {job_id}: {str(e)}")
                # Get storage service for error reporting
                storage_service = await self.get_storage_service(options.container)
                await self._update_job_status(
                    job_id,
                    ProcessingStatusEnum.FAILED,
                    100,
                    "Processing failed",
                    f"Error: {str(e)}",
                    storage_service=storage_service,
                    error=str(e)
                )
            finally:
                # Cleanup temp file
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.info(f"Cleaned up temp file: {file_path}")
                except Exception as e:
                    logger.warning(f"Could not clean up temp file {file_path}: {e}")
    
    async def _process_excel_with_status_updates(
        self,
        job_id: str,
        file_path: str,
        filename: str,
        options: ExcelProcessingOptions
    ):
        """Process Excel file with progress updates"""
        
        # Get container-specific storage service
        storage_service = await self.get_storage_service(options.container)
        
        # Step 1: Validate file
        await self._update_job_status(
            job_id, ProcessingStatusEnum.PROCESSING, 10,
            "Validating file", f"Validating {filename}",
            storage_service=storage_service
        )
        
        if not os.path.exists(file_path):
            raise ProcessingException(f"File not found: {file_path}")
        
        # Step 2: Process file
        await self._update_job_status(
            job_id, ProcessingStatusEnum.PROCESSING, 20,
            "Processing Excel file", "Analyzing sheets and extracting data",
            storage_service=storage_service
        )
        
        processing_result = await self.excel_processor.process_file(
            file_path, options, job_id
        )
        
        chunks = processing_result.get("chunks", [])
        # Normalize source_file to original filename (not temp path or sheet name)
        if chunks:
            for ch in chunks:
                try:
                    ch.source_file = filename
                except Exception:
                    pass
        embeddings = processing_result.get("embeddings", [])
        relationships = processing_result.get("relationships", [])
        file_analysis = processing_result.get("file_analysis")
        
        # Step 3: Generate embeddings (if not done)
        if options.generate_embeddings and not embeddings:
            await self._update_job_status(
                job_id, ProcessingStatusEnum.PROCESSING, 60,
                "Generating embeddings", f"Creating embeddings for {len(chunks)} chunks",
                storage_service=storage_service
            )
            
            from app.core.azure_embedding import AzureEmbeddingService
            embedding_service = AzureEmbeddingService()
            await embedding_service.initialize()
            embeddings = await embedding_service.embed_chunks(chunks)
        
        # Step 4: Create file record
        await self._update_job_status(
            job_id, ProcessingStatusEnum.PROCESSING, 80,
            "Preparing storage", "Creating file record and metadata",
            storage_service=storage_service
        )
        
        file_record = FileRecord(
            file_id=job_id,
            original_filename=filename,
            file_type="excel",
            file_size=os.path.getsize(file_path),
            processed_at=datetime.now(),
            processing_options=options.dict(),
            total_chunks=len(chunks),
            total_embeddings=len(embeddings),
            total_relationships=len(relationships),
            domains_detected=self._extract_domains_from_analysis(file_analysis),
            stored_in=[StorageType.VECTOR_DB, StorageType.GRAPH_DB, StorageType.DOCUMENT_STORE]
        )
        
        # Step 5: Store results
        await self._update_job_status(
            job_id, ProcessingStatusEnum.PROCESSING, 90,
            "Storing results", "Saving to external databases",
            storage_service=storage_service
        )
        
        storage_service = await self.get_storage_service(options.container)
        storage_result = await storage_service.store_processing_results(
            job_id, chunks, embeddings, relationships, file_record,
            create_graph=options.create_graph
        )
        
        # Step 6: Complete
        await self._update_job_status(
            job_id, ProcessingStatusEnum.PROCESSING, 95,
            "Syncing metadata", "Synchronizing with Java backend",
            storage_service=storage_service,
            chunks_created=len(chunks),
            embeddings_generated=len(embeddings),
            relationships_detected=len(relationships),
            storage_operations={"success": storage_result.total_success, "failed": storage_result.total_failed}
        )
        
        # Step 7: Sync metadata with Java backend
        try:
            sync_result = await metadata_sync_service.sync_document_metadata(
                document_name=filename,
                document_path=f"embedded/{filename}",
                file_type="excel",
                file_size=file_record.file_size,
                container=options.container,
                embedding_status="embedded"
            )
            
            if sync_result.get("success"):
                logger.info(f"Successfully synced metadata for {filename} with Java backend")
            else:
                logger.warning(f"Failed to sync metadata for {filename}: {sync_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error syncing metadata for {filename}: {str(e)}")
        
        # Step 8: Final completion
        await self._update_job_status(
            job_id, ProcessingStatusEnum.COMPLETED, 100,
            "Processing complete", f"Successfully processed {filename}",
            storage_service=storage_service,
            chunks_created=len(chunks),
            embeddings_generated=len(embeddings),
            relationships_detected=len(relationships),
            storage_operations={"success": storage_result.total_success, "failed": storage_result.total_failed}
        )
        
        logger.info(f"Excel processing completed for job {job_id}: {len(chunks)} chunks, {len(embeddings)} embeddings")
    
    async def process_markdown_content_async(
        self,
        job_id: str,
        content: str,
        filename: str,
        container: str,
        chunking_strategy: str,
        create_graph: bool,
        detect_relationships: bool,
        detect_domains: bool,
        generate_embeddings: bool,
        embedding_model: Optional[str] = None
    ) -> None:
        """Process Markdown content with container isolation"""
        
        # Create processing options
        options = MarkdownProcessingOptions(
            container=container,
            chunking_strategy=chunking_strategy,
            create_graph=create_graph,
            detect_relationships=detect_relationships,
            detect_domains=detect_domains,
            generate_embeddings=generate_embeddings,
            embedding_model=embedding_model or settings.EMBEDDING_MODEL
        )
        
        # Create initial job status
        job_status = ProcessingStatus(
            job_id=job_id,
            status=ProcessingStatusEnum.PROCESSING,
            progress=0,
            current_step="Starting Markdown processing",
            message=f"Processing {filename}",
            started_at=datetime.now()
        )
        
        self.active_jobs[job_id] = job_status
        
        # Get container-specific storage service
        storage_service = await self.get_storage_service(container)
        await storage_service.update_job_status(job_id, job_status.dict())
        
        # Ensure semaphore is initialized
        if self.job_semaphore is None:
            self.job_semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_JOBS)
            
        async with self.job_semaphore:
            try:
                await self._process_markdown_with_status_updates(
                    job_id, content, filename, options
                )
                
            except Exception as e:
                logger.error(f"Markdown processing failed for job {job_id}: {str(e)}")
                # Get storage service for error reporting
                storage_service = await self.get_storage_service(container)
                await self._update_job_status(
                    job_id,
                    ProcessingStatusEnum.FAILED,
                    100,
                    "Processing failed",
                    f"Error: {str(e)}",
                    storage_service=storage_service,
                    error=str(e)
                )
    
    async def _process_markdown_with_status_updates(
        self,
        job_id: str,
        content: str,
        filename: str,
        options: MarkdownProcessingOptions
    ):
        """Process Markdown content with progress updates"""
        
        # Get container-specific storage service
        storage_service = await self.get_storage_service(options.container)
        
        # Step 0: Upload file to Azure File Share FIRST (before chunking)
        azure_file_path = None
        upload_status = 'unknown'
        download_url = None
        try:
            from app.core.azure_file_service import azure_file_service
            file_content_bytes = content.encode('utf-8')
            upload_result = await azure_file_service.upload_file(
                file_content=file_content_bytes,
                filename=filename,
                container=options.container
            )
            
            azure_file_path = upload_result.get('azure_file_path')
            upload_status = upload_result.get('upload_status', 'unknown')
            
            # Generate download URL immediately after successful upload
            if upload_status == 'completed' and azure_file_path:
                download_url = azure_file_service.generate_download_url(azure_file_path)
                if download_url:
                    logger.info(f"Generated download URL for {azure_file_path}: {download_url}")
                else:
                    logger.warning(f"Failed to generate download URL for {azure_file_path}")
            
            if upload_status == 'completed':
                logger.info(f"Successfully uploaded {filename} to Azure File Share")
            else:
                logger.warning(f"Failed to upload {filename} to Azure File Share: {upload_result.get('error_message')}")
        except Exception as e:
            logger.error(f"Error uploading file to Azure File Share: {str(e)}", exc_info=True)
            upload_status = 'failed'
        
        # Step 1: Initialize markdown processor
        await self._update_job_status(
            job_id, ProcessingStatusEnum.PROCESSING, 10,
            "Initializing processor", f"Setting up markdown processing for {filename}",
            storage_service=storage_service
        )
        
        if not self.markdown_processor.initialized:
            await self.markdown_processor.initialize()
        
        # Step 2: Process markdown content
        await self._update_job_status(
            job_id, ProcessingStatusEnum.PROCESSING, 30,
            "Processing markdown", "Parsing structure and creating chunks",
            storage_service=storage_service
        )
        
        from app.services.markdown_processor import MarkdownProcessingRequest
        processing_request = MarkdownProcessingRequest(
            content=content,
            source_id=job_id,
            metadata={"filename": filename, "container": options.container}
        )
        
        # Process the markdown content
        markdown_result = await self.markdown_processor.process_markdown(processing_request, options.embedding_model)
        
        # Step 3: Convert to storage format
        await self._update_job_status(
            job_id, ProcessingStatusEnum.PROCESSING, 60,
            "Converting results", "Preparing chunks and relationships for storage",
            storage_service=storage_service
        )
        
        # Convert markdown chunks to base chunk format
        chunks = []
        relationships = []
        
        for md_chunk in markdown_result.chunks:
            # Convert to ProcessedChunk format
            from app.processors.base.base_models import ProcessedChunk
            # Extract metadata safely from MarkdownChunk
            structural_metadata = md_chunk.structural_metadata if hasattr(md_chunk, 'structural_metadata') else {}
            semantic_metadata = md_chunk.semantic_metadata if hasattr(md_chunk, 'semantic_metadata') else {}

            chunk = ProcessedChunk(
                chunk_id=md_chunk.chunk_id,
                content=md_chunk.content,
                chunk_type=md_chunk.chunk_type,
                source_file=filename,
                source_section=structural_metadata.get("section", ""),
                start_position=getattr(md_chunk, 'position_start', 0),
                end_position=getattr(md_chunk, 'position_end', 0),
                semantic_type=semantic_metadata.get("type", "text"),
                domain=options.container,
                confidence=semantic_metadata.get("confidence", 1.0),
                metadata={
                    "structural": structural_metadata,
                    "semantic": semantic_metadata,
                    "azure_file_path": azure_file_path,
                    "upload_status": upload_status,
                    "download_url": download_url
                }
            )
            chunks.append(chunk)
        
        # Convert relationships
        for md_rel in markdown_result.relationships:
            from app.processors.base.base_models import ChunkRelationship
            relationship = ChunkRelationship(
                relationship_id=f"rel_{md_rel.source_chunk_id}_{md_rel.target_chunk_id}",
                from_chunk_id=md_rel.source_chunk_id,
                to_chunk_id=md_rel.target_chunk_id,
                relationship_type=md_rel.relationship_type,
                confidence=md_rel.confidence,
                metadata=md_rel.metadata
            )
            relationships.append(relationship)
        
        # Step 3.5: Generate embeddings using Azure OpenAI (if requested)
        embeddings = []
        if options.generate_embeddings:
            await self._update_job_status(
                job_id, ProcessingStatusEnum.PROCESSING, 70,
                "Generating embeddings", f"Creating Azure OpenAI embeddings for {len(chunks)} chunks",
                storage_service=storage_service
            )
            
            from app.core.azure_embedding import AzureEmbeddingService
            embedding_service = AzureEmbeddingService()
            await embedding_service.initialize()
            embeddings = await embedding_service.embed_chunks(chunks)
        
        # Step 4: Create file record
        await self._update_job_status(
            job_id, ProcessingStatusEnum.PROCESSING, 80,
            "Preparing storage", "Creating file record and metadata",
            storage_service=storage_service
        )
        
        file_record = FileRecord(
            file_id=job_id,
            original_filename=filename,
            file_type="markdown",
            file_size=len(content.encode('utf-8')),
            processed_at=datetime.now(),
            processing_options=options.dict(),
            total_chunks=len(chunks),
            total_embeddings=len(embeddings),
            total_relationships=len(relationships),
            domains_detected=[options.container],
            stored_in=[StorageType.VECTOR_DB, StorageType.GRAPH_DB, StorageType.DOCUMENT_STORE]
        )
        
        # Store upload status in file_record metadata
        if 'storage_metadata' not in file_record.storage_metadata:
            file_record.storage_metadata = {}
        file_record.storage_metadata['azure_file_path'] = azure_file_path
        file_record.storage_metadata['upload_status'] = upload_status
        if download_url:
            file_record.storage_metadata['download_url'] = download_url
        
        # Step 5: Store results
        await self._update_job_status(
            job_id, ProcessingStatusEnum.PROCESSING, 90,
            "Storing results", "Saving to external databases",
            storage_service=storage_service
        )
        
        storage_result = await storage_service.store_processing_results(
            job_id, chunks, embeddings, relationships, file_record,
            create_graph=options.create_graph
        )
        
        # Step 6: Complete
        await self._update_job_status(
            job_id, ProcessingStatusEnum.PROCESSING, 95,
            "Syncing metadata", "Synchronizing with Java backend",
            storage_service=storage_service,
            chunks_created=len(chunks),
            embeddings_generated=len(embeddings),
            relationships_detected=len(relationships),
            storage_operations={"success": storage_result.total_success, "failed": storage_result.total_failed}
        )
        
        # Step 7: Sync metadata with Java backend
        try:
            sync_result = await metadata_sync_service.sync_document_metadata(
                document_name=filename,
                document_path=f"embedded/{filename}",
                file_type="markdown",
                file_size=file_record.file_size,
                container=options.container,
                embedding_status="embedded"
            )
            
            if sync_result.get("success"):
                logger.info(f"Successfully synced metadata for {filename} with Java backend")
            else:
                logger.warning(f"Failed to sync metadata for {filename}: {sync_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error syncing metadata for {filename}: {str(e)}")
        
        # Step 8: Final completion
        await self._update_job_status(
            job_id, ProcessingStatusEnum.COMPLETED, 100,
            "Processing complete", f"Successfully processed {filename}",
            storage_service=storage_service,
            chunks_created=len(chunks),
            embeddings_generated=len(embeddings),
            relationships_detected=len(relationships),
            storage_operations={"success": storage_result.total_success, "failed": storage_result.total_failed}
        )
        
        logger.info(f"Markdown processing completed for job {job_id}: {len(chunks)} chunks, {len(embeddings)} embeddings")
    
    async def _update_job_status(
        self,
        job_id: str,
        status: ProcessingStatusEnum,
        progress: int,
        current_step: str,
        message: str,
        error: Optional[str] = None,
        storage_service: Optional[StorageService] = None,
        **kwargs
    ):
        """Update job processing status"""
        
        if job_id in self.active_jobs:
            job_status = self.active_jobs[job_id]
            job_status.status = status
            job_status.progress = progress
            job_status.current_step = current_step
            job_status.message = message
            job_status.error = error
            
            if status == ProcessingStatusEnum.COMPLETED:
                job_status.completed_at = datetime.now()
            
            # Update additional fields
            for key, value in kwargs.items():
                if hasattr(job_status, key):
                    setattr(job_status, key, value)
            
            # Store in external storage
            if storage_service:
                await storage_service.update_job_status(job_id, job_status.dict())
            else:
                # Fallback to general storage for backward compatibility
                general_storage = await self.get_storage_service("general")
                await general_storage.update_job_status(job_id, job_status.dict())
    
    async def get_job_status(self, job_id: str) -> Optional[ProcessingStatus]:
        """Get job processing status"""
        
        # First check active jobs
        if job_id in self.active_jobs:
            return self.active_jobs[job_id]
        
        # Then check storage across all containers
        for container, storage_service in self.storage_services.items():
            status_data = await storage_service.get_job_status(job_id)
            if status_data:
                return ProcessingStatus(**status_data)
        
        return None
    
    async def delete_job(self, job_id: str) -> bool:
        """Delete job and cleanup resources"""
        
        try:
            # Remove from active jobs
            if job_id in self.active_jobs:
                del self.active_jobs[job_id]
            
            # Note: In a full implementation, this would also:
            # - Delete from external storage systems
            # - Cancel running job if still processing
            # - Clean up any remaining temp files
            
            logger.info(f"Job {job_id} deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting job {job_id}: {str(e)}")
            return False
    
    async def list_jobs(
        self, 
        status_filter: Optional[str] = None, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List processing jobs with optional filtering"""
        
        jobs = []
        
        # Get jobs from active jobs (in-memory)
        for job_id, job_status in list(self.active_jobs.items())[:limit]:
            if not status_filter or job_status.status == status_filter:
                jobs.append({
                    "job_id": job_id,
                    "status": job_status.status,
                    "progress": job_status.progress,
                    "started_at": job_status.started_at.isoformat(),
                    "current_step": job_status.current_step,
                    "message": job_status.message
                })
        
        # Note: In a full implementation, this would also query
        # external storage for completed/failed jobs
        
        return jobs[:limit]
    
    def _extract_domains_from_analysis(self, file_analysis) -> List[str]:
        """Extract detected domains from file analysis"""
        
        domains = []

        if file_analysis and hasattr(file_analysis, 'sheets'):
            for sheet in file_analysis.sheets:
                if sheet.detected_domain and sheet.detected_domain != "unknown":
                    domains.append(sheet.detected_domain)

        return list(set(domains))  # Remove duplicates

    # ===== INTERACTIVE MARKDOWN CHUNKING METHODS =====

    async def preview_markdown_chunking(
        self,
        markdown_content: str,
        filename: str,
        chunking_strategy: str = "structure_aware_hierarchical"
    ) -> Dict[str, Any]:
        """
        Generate chunking preview for markdown content without storing data

        Args:
            markdown_content: Raw markdown content
            filename: Original filename
            chunking_strategy: Chunking strategy to use

        Returns:
            Dict with 'strategy' info and 'chunks' list
        """

        try:
            # Process markdown to get chunking preview
            result = await self.markdown_processor.preview_chunking(
                content=markdown_content,
                filename=filename,
                chunking_strategy=chunking_strategy
            )

            logger.info(f"Generated chunking preview for {filename}: {len(result['chunks'])} chunks")
            return result

        except Exception as e:
            logger.error(f"Failed to generate markdown chunking preview: {str(e)}")
            raise ProcessingException(f"Chunking preview failed: {str(e)}")

    async def process_user_edited_chunks_async(
        self,
        job_id: str,
        filename: str,
        container: str,
        user_chunks: List[UserEditedChunk],
        create_graph: bool = False,
        detect_relationships: bool = False,
        detect_domains: bool = False,
        generate_embeddings: bool = True,
        embedding_model: Optional[str] = None,
        file_type: Optional[str] = None
    ) -> None:
        """
        Process user-edited chunks and store them

        Args:
            job_id: Unique job identifier
            filename: Original filename
            container: Target container for storage
            user_chunks: List of user-edited chunks
            create_graph: Whether to create graph relationships
            detect_relationships: Whether to detect relationships
            detect_domains: Whether to detect domains
            generate_embeddings: Whether to generate embeddings
            embedding_model: Embedding model to use
        """

        # Update job status
        storage_service = await self.get_storage_service(container)

        await storage_service.update_job_status(job_id, {
            "status": "processing",
            "progress": 10,
            "current_step": "Processing user-edited chunks",
            "started_at": datetime.now()
        })

        try:
            # Step 0: Upload file to Azure File Share FIRST (before processing chunks)
            # Reconstruct file content from chunks
            file_content = "\n\n".join([chunk.content for chunk in user_chunks])
            azure_file_path = None
            upload_status = 'unknown'
            download_url = None
            try:
                from app.core.azure_file_service import azure_file_service
                file_content_bytes = file_content.encode('utf-8')
                upload_result = await azure_file_service.upload_file(
                    file_content=file_content_bytes,
                    filename=filename,
                    container=container
                )
                
                azure_file_path = upload_result.get('azure_file_path')
                upload_status = upload_result.get('upload_status', 'unknown')
                
                # Generate download URL immediately after successful upload
                if upload_status == 'completed' and azure_file_path:
                    download_url = azure_file_service.generate_download_url(azure_file_path)
                    if download_url:
                        logger.info(f"Generated download URL for {azure_file_path}: {download_url}")
                    else:
                        logger.warning(f"Failed to generate download URL for {azure_file_path}")
                
                if upload_status == 'completed':
                    logger.info(f"Successfully uploaded {filename} to Azure File Share")
                else:
                    logger.warning(f"Failed to upload {filename} to Azure File Share: {upload_result.get('error_message')}")
            except Exception as e:
                logger.error(f"Error uploading file to Azure File Share: {str(e)}", exc_info=True)
                upload_status = 'failed'
            
            # Process user-edited chunks directly
            # Determine file type from filename if not provided
            if file_type is None:
                if filename.lower().endswith(('.xlsx', '.xls')):
                    file_type = "excel"
                elif filename.lower().endswith(('.md', '.markdown')):
                    file_type = "markdown"
                else:
                    file_type = "text"
            
            # Pass Azure metadata to markdown processor so it can include in chunk metadata
            result = await self.markdown_processor.process_user_edited_chunks(
                job_id=job_id,
                filename=filename,
                container=container,
                user_chunks=user_chunks,
                create_graph=create_graph,
                detect_relationships=detect_relationships,
                detect_domains=detect_domains,
                generate_embeddings=generate_embeddings,
                embedding_model=embedding_model,
                file_type=file_type,
                azure_file_path=azure_file_path,
                upload_status=upload_status,
                download_url=download_url
            )

            # Update job status to syncing
            await storage_service.update_job_status(job_id, {
                "status": "processing",
                "progress": 95,
                "current_step": "Syncing metadata",
                "chunks_created": len(user_chunks),
                "embeddings_generated": result.get('embeddings_generated', 0)
            })

            # Sync metadata with Java backend
            try:
                # Determine file type for metadata sync
                sync_file_type = file_type if file_type else "text"
                if not sync_file_type or sync_file_type == "text":
                    if filename.lower().endswith(('.xlsx', '.xls')):
                        sync_file_type = "excel"
                    elif filename.lower().endswith(('.md', '.markdown')):
                        sync_file_type = "markdown"
                
                sync_result = await metadata_sync_service.sync_document_metadata(
                    document_name=filename,
                    document_path=f"embedded/{filename}",
                    file_type=sync_file_type,
                    file_size=len(str(user_chunks).encode('utf-8')),  # Approximate size
                    container=container,
                    embedding_status="embedded"
                )
                
                if sync_result.get("success"):
                    logger.info(f"Successfully synced metadata for {filename} with Java backend")
                else:
                    logger.warning(f"Failed to sync metadata for {filename}: {sync_result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                logger.error(f"Error syncing metadata for {filename}: {str(e)}")

            # Update job status to completed
            await storage_service.update_job_status(job_id, {
                "status": "completed",
                "progress": 100,
                "current_step": "Completed",
                "chunks_created": len(user_chunks),
                "embeddings_generated": result.get('embeddings_generated', 0),
                "completed_at": datetime.now()
            })

            logger.info(f"Completed processing user-edited chunks for job {job_id}: {len(user_chunks)} chunks")

        except Exception as e:
            # Update job status to failed
            await storage_service.update_job_status(job_id, {
                "status": "failed",
                "progress": 0,
                "current_step": "Failed",
                "error": str(e),
                "completed_at": datetime.now()
            })

            logger.error(f"Failed to process user-edited chunks for job {job_id}: {str(e)}")
            raise ProcessingException(f"User chunk processing failed: {str(e)}")