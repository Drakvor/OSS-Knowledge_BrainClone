"""
Production Markdown Processor
============================

Clean, production-ready markdown processing service using Structure-Aware Hierarchical strategy.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid
import numpy as np

from app.core.azure_embedding import AzureEmbeddingService  # For user chunk processing
from app.markdown.base import MarkdownChunk, MarkdownChunkingStrategy
from app.markdown.parser import AdvancedMarkdownParser
from app.markdown.strategies.factory import MarkdownStrategyFactory
from app.processors.base.base_models import ProcessedChunk, ChunkEmbedding, FileRecord
from app.processors.markdown.markdown_models import UserEditedChunk

logger = logging.getLogger(__name__)


@dataclass
class MarkdownProcessingRequest:
    """Request model for markdown processing."""
    content: str
    source_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None




@dataclass
class ChunkRelationship:
    """Relationship between chunks."""
    source_chunk_id: str
    target_chunk_id: str
    relationship_type: str
    confidence: float
    metadata: Dict[str, Any]


@dataclass
class MarkdownProcessingResult:
    """Complete result of markdown processing."""
    source_id: str
    chunks: List[ProcessedChunk]
    relationships: List[ChunkRelationship]
    processing_stats: Dict[str, Any]
    created_at: str


class MarkdownProcessorService:
    """Production-ready markdown processing service."""
    
    def __init__(self):
        self.parser = AdvancedMarkdownParser()
        self.strategy_factory = MarkdownStrategyFactory()
        self.embedding_service: Optional[AzureEmbeddingService] = None
        self.initialized = False
    
    async def initialize(self):
        """Initialize the markdown processor."""
        if self.initialized:
            return
        
        logger.info("Initializing markdown processor service...")
        
        # Initialize embedding service
        self.embedding_service = AzureEmbeddingService()
        await self.embedding_service.initialize()
        
        self.initialized = True
        logger.info("Markdown processor service initialized")
    
    async def process_markdown(self, request: MarkdownProcessingRequest, embedding_model: str = "text-embedding-3-large") -> MarkdownProcessingResult:
        """Process markdown content using Structure-Aware Hierarchical strategy."""

        if not self.initialized:
            await self.initialize()

        start_time = datetime.now()
        source_id = request.source_id or str(uuid.uuid4())

        try:
            # Parse markdown content
            logger.info(f"Processing markdown content ({len(request.content)} chars)")
            elements = self.parser.parse(request.content)
            logger.info(f"Parsed {len(elements)} markdown elements")

            # Apply Structure-Aware Hierarchical chunking strategy
            strategy = self.strategy_factory.create_strategy(
                MarkdownChunkingStrategy.STRUCTURE_AWARE_HIERARCHICAL
            )

            chunking_result = strategy.chunk(elements)

            # Handle tuple return format
            if isinstance(chunking_result, tuple):
                chunks, relationships = chunking_result
            else:
                chunks = chunking_result.chunks
                relationships = chunking_result.relationships

            if not chunks:
                raise ValueError("No chunks generated from markdown content")

            logger.info(f"Generated {len(chunks)} chunks with {len(relationships)} relationships")

            # Choose embedding service based on model
            if embedding_model == "text-embedding-3-large":
                embedding_service = AzureEmbeddingService()
                await embedding_service.initialize()
                logger.info("Using Azure OpenAI embedding service")
            else:
                embedding_service = self.embedding_service
                logger.info("Using Azure OpenAI embedding service")

            # Generate embeddings for all chunks
            chunk_texts = [chunk.content for chunk in chunks]
            try:
                embeddings = await embedding_service.generate_embeddings(chunk_texts)
                logger.info(f"Successfully generated {len(embeddings)} embeddings")
            except Exception as e:
                logger.error(f"Embedding generation failed: {e}")
                raise RuntimeError(f"Embedding generation failed: {e}")

            # Convert to processed chunks
            processed_chunks = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                # Convert numpy array to list safely
                if isinstance(embedding, np.ndarray):
                    embedding_list = embedding.tolist()
                elif hasattr(embedding, 'tolist'):
                    embedding_list = embedding.tolist()
                else:
                    embedding_list = list(embedding)

                processed_chunk = ProcessedChunk(
                    chunk_id=chunk.chunk_id,
                    content=chunk.content,
                    chunk_type=chunk.chunk_type,
                    source_file="markdown_processing",
                    start_position=chunk.position_start,
                    end_position=chunk.position_end,
                    metadata={
                        "word_count": chunk.word_count,
                        "structural_metadata": chunk.structural_metadata,
                        "semantic_metadata": chunk.semantic_metadata,
                        "created_at": chunk.created_at.isoformat(),
                        "embedding": embedding_list
                    }
                )
                processed_chunks.append(processed_chunk)

            # Convert relationships
            processed_relationships = []
            for rel in relationships:
                chunk_rel = ChunkRelationship(
                    source_chunk_id=rel.source_chunk_id,
                    target_chunk_id=rel.target_chunk_id,
                    relationship_type=rel.relationship_type,
                    confidence=rel.confidence,
                    metadata=rel.relationship_metadata
                )
                processed_relationships.append(chunk_rel)

            # Calculate processing stats
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds() * 1000  # ms

            # Get embedding dimension safely
            embedding_dimension = 0
            if embeddings is not None and len(embeddings) > 0:
                first_embedding = embeddings[0]
                if isinstance(first_embedding, np.ndarray):
                    embedding_dimension = first_embedding.shape[0]
                else:
                    embedding_dimension = len(first_embedding)

            # Calculate average chunk size from original chunks (which have word_count)
            avg_chunk_size = round(sum(chunk.word_count for chunk in chunks) / len(chunks), 1) if chunks else 0

            processing_stats = {
                "processing_time_ms": round(processing_time, 2),
                "total_chunks": len(processed_chunks),
                "total_relationships": len(processed_relationships),
                "average_chunk_size": avg_chunk_size,
                "content_length": len(request.content),
                "strategy_used": "structure_aware_hierarchical",
                "embedding_dimension": embedding_dimension
            }

            result = MarkdownProcessingResult(
                source_id=source_id,
                chunks=processed_chunks,
                relationships=processed_relationships,
                processing_stats=processing_stats,
                created_at=start_time.isoformat()
            )

            logger.info(f"Markdown processing completed in {processing_time:.1f}ms")
            return result

        except Exception as e:
            logger.error(f"Markdown processing failed: {e}")
            raise
    
    async def get_chunk_by_id(self, chunk_id: str, results: MarkdownProcessingResult) -> Optional[ProcessedChunk]:
        """Get a specific chunk by ID."""
        for chunk in results.chunks:
            if chunk.chunk_id == chunk_id:
                return chunk
        return None
    
    async def get_related_chunks(self, chunk_id: str, results: MarkdownProcessingResult, 
                               max_depth: int = 2) -> List[ProcessedChunk]:
        """Get chunks related to a specific chunk."""
        related_ids = set()
        
        # Find direct relationships
        for rel in results.relationships:
            if rel.source_chunk_id == chunk_id:
                related_ids.add(rel.target_chunk_id)
            elif rel.target_chunk_id == chunk_id:
                related_ids.add(rel.source_chunk_id)
        
        # Find chunks by IDs
        related_chunks = []
        for chunk in results.chunks:
            if chunk.chunk_id in related_ids:
                related_chunks.append(chunk)
        
        return related_chunks
    
    async def search_chunks(self, query: str, results: MarkdownProcessingResult,
                          top_k: int = 10) -> List[Tuple[ProcessedChunk, float]]:
        """Search chunks using semantic similarity."""
        
        if not self.embedding_service:
            raise RuntimeError("Embedding service not initialized")
        
        # Generate query embedding
        query_vector = await self.embedding_service.generate_single_embedding(query)
        
        # Calculate similarity scores
        chunk_scores = []
        for chunk in results.chunks:
            chunk_vector = chunk.embedding
            
            # Calculate cosine similarity
            dot_product = sum(a * b for a, b in zip(query_vector, chunk_vector))
            norm_a = sum(a * a for a in query_vector) ** 0.5
            norm_b = sum(b * b for b in chunk_vector) ** 0.5
            
            if norm_a * norm_b > 0:
                similarity = dot_product / (norm_a * norm_b)
            else:
                similarity = 0.0
            
            chunk_scores.append((chunk, similarity))
        
        # Sort by similarity and return top-k
        chunk_scores.sort(key=lambda x: x[1], reverse=True)
        return chunk_scores[:top_k]
    
    def get_processing_info(self) -> Dict[str, Any]:
        """Get information about the processor configuration."""
        return {
            "strategy": "Structure-Aware Hierarchical",
            "description": "Respects natural document hierarchy defined by markdown headers",
            "best_for": ["Educational content", "Technical documentation", "Structured documents"],
            "features": [
                "Preserves document structure",
                "Maintains context hierarchy", 
                "Creates parent-child relationships",
                "Good for hierarchical navigation"
            ],
            "embedding_model": "text-embedding-3-large" if self.embedding_service else None,
            "embedding_dimension": 3072,
            "initialized": self.initialized
        }

    # ===== INTERACTIVE CHUNKING METHODS =====

    async def preview_chunking(
        self,
        content: str,
        filename: str,
        chunking_strategy: str = "structure_aware_hierarchical"
    ) -> Dict[str, Any]:
        """
        Generate chunking preview without storing data

        Returns dict with 'strategy' info and 'chunks' list
        """

        try:
            # Parse the markdown content
            parser = AdvancedMarkdownParser()
            parsed_document = parser.parse(content)

            # Get the chunking strategy
            from app.markdown.base import MarkdownChunkingStrategy

            # Convert string strategy to enum
            strategy_mapping = {
                "structure_aware_hierarchical": MarkdownChunkingStrategy.STRUCTURE_AWARE_HIERARCHICAL,
                "semantic_block_fusion": MarkdownChunkingStrategy.SEMANTIC_BLOCK_FUSION,
                "cross_reference_linking": MarkdownChunkingStrategy.CROSS_REFERENCE_LINKING,
            }

            strategy_enum = strategy_mapping.get(
                chunking_strategy,
                MarkdownChunkingStrategy.STRUCTURE_AWARE_HIERARCHICAL
            )

            # Create strategy instance
            factory = MarkdownStrategyFactory()
            strategy = factory.create_strategy(strategy_enum)

            # Generate chunks preview
            chunks, relationships = strategy.chunk(parsed_document)

            # Convert chunks to preview format
            chunk_previews = []
            for i, chunk in enumerate(chunks):
                chunk_id = f"preview_{i}_{str(uuid.uuid4())[:8]}"
                chunk_previews.append({
                    'chunk_id': chunk_id,
                    'content': chunk.content,
                    'chunk_type': chunk.chunk_type,
                    'start_position': chunk.position_start,
                    'end_position': chunk.position_end,
                    'metadata': {
                        'word_count': chunk.word_count,
                        'structural_metadata': chunk.structural_metadata,
                        'semantic_metadata': chunk.semantic_metadata
                    }
                })

            # Strategy information
            strategy_info = {
                'name': chunking_strategy,
                'reason': f"Selected {chunking_strategy} strategy for markdown content with {len(chunks)} chunks generated",
                'parameters': {
                    'chunk_count': len(chunks),
                    'total_words': sum(c.word_count for c in chunks),
                    'avg_chunk_size': sum(c.word_count for c in chunks) // len(chunks) if chunks else 0
                }
            }

            return {
                'strategy': strategy_info,
                'chunks': chunk_previews
            }

        except Exception as e:
            logger.error(f"Failed to generate chunking preview: {str(e)}")
            raise

    async def process_user_edited_chunks(
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
        file_type: Optional[str] = None,
        azure_file_path: Optional[str] = None,
        upload_status: str = 'unknown',
        download_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process user-edited chunks and store them
        """

        try:
            # Import storage service here to avoid circular imports
            from app.services.storage_service import StorageService

            # Initialize storage service
            storage_service = StorageService(container=container)
            await storage_service.initialize()

            processed_chunks = []
            embeddings = []

            # Convert user chunks to ProcessedChunk format
            for i, user_chunk in enumerate(user_chunks):
                # Merge user chunk metadata with Azure metadata
                chunk_metadata = user_chunk.metadata or {}
                if not isinstance(chunk_metadata, dict):
                    chunk_metadata = {}
                
                # Add Azure metadata to chunk metadata
                chunk_metadata['azure_file_path'] = azure_file_path
                chunk_metadata['upload_status'] = upload_status
                chunk_metadata['download_url'] = download_url
                
                # Create ProcessedChunk with all required parameters
                processed_chunk = ProcessedChunk(
                    chunk_id=user_chunk.chunk_id,
                    content=user_chunk.content,
                    chunk_type=user_chunk.chunk_type,
                    source_file=filename,
                    metadata=chunk_metadata,
                    container=container
                )
                processed_chunks.append(processed_chunk)

            # Generate embeddings if requested
            if generate_embeddings:
                embedding_service = AzureEmbeddingService()
                await embedding_service.initialize()

                # Generate embeddings for all user chunks
                chunk_texts = [chunk.content for chunk in processed_chunks]
                chunk_embeddings_raw = await embedding_service.generate_embeddings(chunk_texts)

                # Create ChunkEmbedding objects
                chunk_embeddings = []
                for i, (chunk, embedding) in enumerate(zip(processed_chunks, chunk_embeddings_raw)):
                    chunk_embedding = ChunkEmbedding(
                        chunk_id=chunk.chunk_id,
                        embedding=embedding,
                        model_used=embedding_model or "text-embedding-3-large",
                        embedding_dimension=len(embedding)
                    )
                    chunk_embeddings.append(chunk_embedding)
                embeddings.extend(chunk_embeddings)

                logger.info(f"Generated {len(embeddings)} embeddings for user-edited chunks")

            # Determine file type if not provided
            if file_type is None:
                if filename.lower().endswith(('.xlsx', '.xls')):
                    file_type = "excel"
                elif filename.lower().endswith(('.md', '.markdown')):
                    file_type = "markdown"
                else:
                    file_type = "text"
            
            # Create file record
            file_record = FileRecord(
                file_id=job_id,
                original_filename=filename,
                file_type=file_type,
                file_size=len(str(user_chunks)),
                processed_at=datetime.now(),
                processing_options={
                    "chunking_strategy": "user_edited",
                    "embedding_model": embedding_model or "text-embedding-3-large",
                    "generate_embeddings": generate_embeddings,
                    "create_graph": create_graph,
                    "detect_relationships": detect_relationships,
                    "detect_domains": detect_domains
                },
                total_chunks=len(processed_chunks),
                total_embeddings=len(embeddings),
                total_relationships=0
            )
            
            # Store Azure upload status in file_record metadata
            if 'storage_metadata' not in file_record.storage_metadata:
                file_record.storage_metadata = {}
            file_record.storage_metadata['azure_file_path'] = azure_file_path
            file_record.storage_metadata['upload_status'] = upload_status
            if download_url:
                file_record.storage_metadata['download_url'] = download_url

            # Store everything
            storage_result = await storage_service.store_processing_results(
                job_id=job_id,
                chunks=processed_chunks,
                embeddings=embeddings,
                relationships=[],  # No relationships for user-edited chunks
                file_record=file_record,
                create_graph=create_graph
            )

            logger.info(f"Stored {len(processed_chunks)} user-edited chunks for job {job_id}")

            return {
                'chunks_processed': len(processed_chunks),
                'embeddings_generated': len(embeddings),
                'storage_result': storage_result
            }

        except Exception as e:
            logger.error(f"Failed to process user-edited chunks: {str(e)}")
            raise

    async def shutdown(self):
        """Clean up resources."""
        if self.embedding_service:
            await self.embedding_service.shutdown()
        
        self.initialized = False
        logger.info("Markdown processor service shutdown complete")


# Singleton instance
_markdown_processor = None

async def get_markdown_processor() -> MarkdownProcessorService:
    """Get the singleton markdown processor instance."""
    global _markdown_processor
    
    if _markdown_processor is None:
        _markdown_processor = MarkdownProcessorService()
        await _markdown_processor.initialize()
    
    return _markdown_processor