"""
Neo4j Graph Storage Implementation
Production-ready graph storage for relationship management
"""

import logging
import uuid
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from neo4j import GraphDatabase, Transaction
from neo4j.exceptions import ServiceUnavailable, AuthError, ConfigurationError

from app.config import settings
from app.processors.base.interfaces import GraphStorageInterface
from app.processors.base.base_models import (
    ProcessedChunk, ChunkRelationship, FileRecord, StorageOperation, StorageType
)
from app.core.exceptions import StorageError

logger = logging.getLogger(__name__)


class Neo4jGraphStorage(GraphStorageInterface):
    """Production Neo4j graph storage with rich relationship modeling and container isolation"""
    
    def __init__(self, container: str = "general"):
        self.driver = None
        self.uri = settings.NEO4J_URI
        self.user = settings.NEO4J_USER
        self.password = settings.NEO4J_PASSWORD
        self.container = container
        self.database = f"{settings.NEO4J_DATABASE}_{container}"
        self.connected = False
        
        logger.info(f"Neo4j storage initialized - Container: {container}, URI: {self.uri}, Database: {self.database}")
    
    async def initialize(self) -> bool:
        """Initialize Neo4j driver and create constraints"""
        
        if self.connected:
            return True
        
        try:
            # Initialize Neo4j driver - first connect to default database to create container database
            default_driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                database=settings.NEO4J_DATABASE  # Use default database for admin operations
            )
            
            # Create container-specific database if it doesn't exist
            await self._ensure_database_exists(default_driver)
            default_driver.close()
            
            # Now connect to the container-specific database
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                database=self.database
            )
            
            # Test connection
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                test_value = result.single()["test"]
                if test_value != 1:
                    raise StorageError("Neo4j connection test failed", "neo4j")
            
            logger.info("Connected to Neo4j successfully")
            
            # Create constraints and indexes
            await self._create_constraints_and_indexes()
            
            self.connected = True
            return True
            
        except (ServiceUnavailable, AuthError, ConfigurationError) as e:
            logger.error(f"Failed to initialize Neo4j storage: {str(e)}")
            raise StorageError(f"Neo4j initialization failed: {str(e)}", "neo4j")
    
    async def _ensure_database_exists(self, admin_driver):
        """Ensure container-specific database exists"""
        try:
            with admin_driver.session() as session:
                # Check if database exists
                result = session.run("SHOW DATABASES")
                existing_databases = [record["name"] for record in result]
                
                if self.database not in existing_databases:
                    logger.info(f"Creating Neo4j database: {self.database}")
                    session.run(f"CREATE DATABASE `{self.database}`")
                    logger.info(f"Created Neo4j database: {self.database}")
                else:
                    logger.info(f"Neo4j database already exists: {self.database}")
        except Exception as e:
            # Database creation might fail if not Neo4j Enterprise or insufficient permissions
            # In community edition, we'll use the default database with container-specific node labels
            logger.warning(f"Could not create database {self.database}: {e}. Using default database with container labels.")
            self.database = settings.NEO4J_DATABASE  # Fall back to default database
    
    async def _create_constraints_and_indexes(self):
        """Create necessary constraints and indexes for optimal performance"""
        
        try:
            with self.driver.session() as session:
                # Create constraints for uniqueness
                constraints = [
                    "CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS FOR (c:Chunk) REQUIRE c.chunk_id IS UNIQUE",
                    "CREATE CONSTRAINT job_id_unique IF NOT EXISTS FOR (j:Job) REQUIRE j.job_id IS UNIQUE",
                    "CREATE CONSTRAINT file_unique IF NOT EXISTS FOR (f:File) REQUIRE f.file_path IS UNIQUE"
                ]
                
                # Create indexes for performance
                indexes = [
                    "CREATE INDEX chunk_job_idx IF NOT EXISTS FOR (c:Chunk) ON (c.job_id)",
                    "CREATE INDEX chunk_type_idx IF NOT EXISTS FOR (c:Chunk) ON (c.chunk_type)",
                    "CREATE INDEX chunk_semantic_idx IF NOT EXISTS FOR (c:Chunk) ON (c.semantic_type)",
                    "CREATE INDEX chunk_domain_idx IF NOT EXISTS FOR (c:Chunk) ON (c.domain)",
                    "CREATE INDEX chunk_created_idx IF NOT EXISTS FOR (c:Chunk) ON (c.created_at)",
                    "CREATE INDEX relationship_type_idx IF NOT EXISTS FOR ()-[r]-() ON (r.relationship_type)"
                ]
                
                # Execute constraints
                for constraint in constraints:
                    try:
                        session.run(constraint)
                        logger.debug(f"Created constraint: {constraint}")
                    except Exception as e:
                        logger.warning(f"Constraint creation failed (may already exist): {e}")
                
                # Execute indexes
                for index in indexes:
                    try:
                        session.run(index)
                        logger.debug(f"Created index: {index}")
                    except Exception as e:
                        logger.warning(f"Index creation failed (may already exist): {e}")
                
                logger.info("Neo4j constraints and indexes created successfully")
                
        except Exception as e:
            logger.error(f"Failed to create Neo4j constraints/indexes: {str(e)}")
            raise StorageError(f"Neo4j schema setup failed: {str(e)}", "neo4j")
    
    async def health_check(self) -> bool:
        """Check Neo4j health"""
        
        try:
            if not self.driver:
                return False
            
            with self.driver.session() as session:
                result = session.run("RETURN 1")
                return result.single() is not None
                
        except Exception:
            return False
    
    async def close(self) -> None:
        """Close Neo4j connection"""
        
        if self.driver:
            try:
                self.driver.close()
            except Exception as e:
                logger.warning(f"Error closing Neo4j driver: {e}")
        
        self.connected = False
        logger.info("Neo4j storage connection closed")
    
    async def store_relationships(
        self,
        job_id: str,
        relationships: List[ChunkRelationship]
    ) -> StorageOperation:
        """Store relationships in Neo4j graph"""
        
        if not self.connected:
            await self.initialize()
        
        try:
            logger.info(f"Storing {len(relationships)} relationships in Neo4j for job {job_id}")
            
            with self.driver.session() as session:
                # Store relationships in batches
                batch_size = settings.BATCH_SIZE
                total_stored = 0
                
                for i in range(0, len(relationships), batch_size):
                    batch_relationships = relationships[i:i + batch_size]
                    
                    # Create relationship batch query
                    # NOTE: This uses APOC plugin - ensure Neo4j has APOC installed
                    # Alternative query without APOC is provided below
                    def create_relationships_batch(tx: Transaction, batch_rels: List[ChunkRelationship]):
                        # Using standard Cypher without APOC for broader compatibility
                        query = """
                        UNWIND $relationships AS rel
                        MATCH (source:Chunk {chunk_id: rel.from_chunk_id})
                        MATCH (target:Chunk {chunk_id: rel.to_chunk_id})
                        WITH source, target, rel
                        CALL {
                            WITH source, target, rel
                            WITH source, target, rel,
                                 CASE rel.relationship_type
                                   WHEN 'RELATED_TO' THEN 'RELATED_TO'
                                   WHEN 'CONTAINS' THEN 'CONTAINS'
                                   WHEN 'REFERENCES' THEN 'REFERENCES'
                                   WHEN 'FOLLOWS' THEN 'FOLLOWS'
                                   ELSE 'RELATED_TO'
                                 END AS safe_rel_type
                            CREATE (source)-[r:RELATED_TO]->(target)
                            SET r.relationship_id = rel.relationship_id,
                                r.job_id = rel.job_id,
                                r.confidence = rel.confidence,
                                r.context = rel.context,
                                r.created_at = rel.created_at,
                                r.metadata_json = rel.metadata_json,
                                r.original_type = rel.relationship_type
                            RETURN r
                        }
                        RETURN count(r) as relationships_created
                        """
                        
                        # Convert relationships to dict format
                        rel_data = []
                        for rel in batch_rels:
                            # Convert metadata to string for Neo4j storage
                            metadata_str = ""
                            if rel.metadata:
                                try:
                                    import json
                                    metadata_str = json.dumps(rel.metadata)
                                except:
                                    metadata_str = str(rel.metadata)
                            
                            rel_data.append({
                                "relationship_id": rel.relationship_id,
                                "job_id": job_id,
                                "from_chunk_id": rel.from_chunk_id,
                                "to_chunk_id": rel.to_chunk_id,
                                "relationship_type": rel.relationship_type,
                                "confidence": rel.confidence,
                                "context": rel.description or "",
                                "created_at": datetime.now().isoformat(),
                                "metadata_json": metadata_str
                            })
                        
                        result = tx.run(query, relationships=rel_data)
                        return result.single()["relationships_created"]
                    
                    # Execute batch
                    created_count = session.execute_write(create_relationships_batch, batch_relationships)
                    total_stored += created_count
                    
                    logger.debug(f"Stored batch {i//batch_size + 1}: {created_count} relationships")
            
            logger.info(f"Successfully stored {total_stored} relationships in Neo4j")
            
            return StorageOperation(
                storage_type=StorageType.GRAPH_DB,
                operation="store_relationships",
                success=True,
                records_processed=total_stored,
                storage_id=f"neo4j_{job_id}_relationships"
            )
            
        except Exception as e:
            logger.error(f"Failed to store relationships in Neo4j: {str(e)}")
            return StorageOperation(
                storage_type=StorageType.GRAPH_DB,
                operation="store_relationships",
                success=False,
                records_processed=0,
                error_message=str(e)
            )
    
    async def store_chunks_as_nodes(
        self,
        job_id: str,
        chunks: List[ProcessedChunk]
    ) -> StorageOperation:
        """Store chunks as nodes in Neo4j graph"""
        
        if not self.connected:
            await self.initialize()
        
        try:
            logger.info(f"Storing {len(chunks)} chunks as nodes in Neo4j for job {job_id}")
            
            with self.driver.session() as session:
                # Create or update job node first
                def create_job_node(tx: Transaction):
                    query = """
                    MERGE (j:Job {job_id: $job_id})
                    ON CREATE SET 
                        j.created_at = $created_at,
                        j.status = 'processing',
                        j.chunk_count = $chunk_count
                    ON MATCH SET 
                        j.updated_at = $created_at,
                        j.chunk_count = $chunk_count
                    RETURN j
                    """
                    
                    tx.run(query, 
                          job_id=job_id, 
                          created_at=datetime.now().isoformat(),
                          chunk_count=len(chunks))
                
                session.execute_write(create_job_node)
                
                # Store chunks in batches
                batch_size = settings.BATCH_SIZE
                total_stored = 0
                
                for i in range(0, len(chunks), batch_size):
                    batch_chunks = chunks[i:i + batch_size]
                    
                    def create_chunks_batch(tx: Transaction, batch_chunks: List[ProcessedChunk]):
                        query = """
                        UNWIND $chunks AS chunk
                        MERGE (c:Chunk {chunk_id: chunk.chunk_id})
                        SET 
                            c.job_id = chunk.job_id,
                            c.content = chunk.content,
                            c.chunk_type = chunk.chunk_type,
                            c.source_file = chunk.source_file,
                            c.source_section = chunk.source_section,
                            c.start_position = chunk.start_position,
                            c.end_position = chunk.end_position,
                            c.semantic_type = chunk.semantic_type,
                            c.domain = chunk.domain,
                            c.confidence = chunk.confidence,
                            c.created_at = chunk.created_at,
                            c.metadata_json = chunk.metadata_json
                        
                        WITH c, chunk
                        MATCH (j:Job {job_id: chunk.job_id})
                        MERGE (c)-[:BELONGS_TO]->(j)
                        
                        RETURN count(c) as chunks_created
                        """
                        
                        # Convert chunks to dict format
                        chunk_data = []
                        for chunk in batch_chunks:
                            # Convert metadata to string for Neo4j storage
                            metadata_str = ""
                            if chunk.metadata:
                                try:
                                    import json
                                    metadata_str = json.dumps(chunk.metadata)
                                except:
                                    metadata_str = str(chunk.metadata)
                            
                            chunk_data.append({
                                "chunk_id": chunk.chunk_id,
                                "job_id": job_id,
                                "content": chunk.content,
                                "chunk_type": chunk.chunk_type,
                                "source_file": chunk.source_file,
                                "source_section": chunk.source_section or "",
                                "start_position": chunk.start_position,
                                "end_position": chunk.end_position,
                                "semantic_type": chunk.semantic_type or "",
                                "domain": chunk.domain or "",
                                "confidence": chunk.confidence,
                                "created_at": datetime.now().isoformat(),
                                "metadata_json": metadata_str
                            })
                        
                        result = tx.run(query, chunks=chunk_data)
                        return result.single()["chunks_created"]
                    
                    # Execute batch
                    created_count = session.execute_write(create_chunks_batch, batch_chunks)
                    total_stored += created_count
                    
                    logger.debug(f"Stored batch {i//batch_size + 1}: {created_count} chunk nodes")
            
            logger.info(f"Successfully stored {total_stored} chunk nodes in Neo4j")
            
            return StorageOperation(
                storage_type=StorageType.GRAPH_DB,
                operation="store_chunks_as_nodes",
                success=True,
                records_processed=total_stored,
                storage_id=f"neo4j_{job_id}_nodes"
            )
            
        except Exception as e:
            logger.error(f"Failed to store chunk nodes in Neo4j: {str(e)}")
            return StorageOperation(
                storage_type=StorageType.GRAPH_DB,
                operation="store_chunks_as_nodes",
                success=False,
                records_processed=0,
                error_message=str(e)
            )
    
    async def create_relationship_graph(
        self,
        job_id: str,
        chunks: List[ProcessedChunk],
        relationships: List[ChunkRelationship]
    ) -> StorageOperation:
        """Create complete relationship graph combining nodes and relationships"""
        
        if not self.connected:
            await self.initialize()
        
        try:
            logger.info(f"Creating complete relationship graph for job {job_id}")
            
            # Store chunks as nodes first
            nodes_result = await self.store_chunks_as_nodes(job_id, chunks)
            if not nodes_result.success:
                return nodes_result
            
            # Store relationships
            rels_result = await self.store_relationships(job_id, relationships)
            if not rels_result.success:
                return rels_result
            
            # Create additional derived relationships based on content similarity
            with self.driver.session() as session:
                def create_derived_relationships(tx: Transaction):
                    # Create proximity relationships for chunks that are adjacent in source
                    proximity_query = """
                    MATCH (c1:Chunk {job_id: $job_id}), (c2:Chunk {job_id: $job_id})
                    WHERE c1.source_file = c2.source_file 
                      AND c1.chunk_id <> c2.chunk_id
                      AND abs(c1.start_position - c2.end_position) <= 100
                    MERGE (c1)-[r:ADJACENT_TO]->(c2)
                    ON CREATE SET 
                        r.relationship_type = 'ADJACENT_TO',
                        r.created_at = $created_at,
                        r.derived = true
                    RETURN count(r) as proximity_relationships
                    """
                    
                    # Create semantic grouping relationships for same semantic types
                    semantic_query = """
                    MATCH (c1:Chunk {job_id: $job_id}), (c2:Chunk {job_id: $job_id})
                    WHERE c1.semantic_type = c2.semantic_type 
                      AND c1.chunk_id <> c2.chunk_id
                      AND c1.semantic_type IS NOT NULL
                      AND c1.semantic_type <> ''
                    MERGE (c1)-[r:SAME_SEMANTIC_TYPE]->(c2)
                    ON CREATE SET 
                        r.relationship_type = 'SAME_SEMANTIC_TYPE',
                        r.created_at = $created_at,
                        r.derived = true
                    RETURN count(r) as semantic_relationships
                    """
                    
                    created_at = datetime.now().isoformat()
                    
                    prox_result = tx.run(proximity_query, job_id=job_id, created_at=created_at)
                    prox_count = prox_result.single()["proximity_relationships"]
                    
                    sem_result = tx.run(semantic_query, job_id=job_id, created_at=created_at)
                    sem_count = sem_result.single()["semantic_relationships"]
                    
                    return prox_count + sem_count
                
                derived_count = session.execute_write(create_derived_relationships)
                logger.info(f"Created {derived_count} derived relationships")
            
            total_processed = nodes_result.records_processed + rels_result.records_processed + derived_count
            
            logger.info(f"Successfully created complete relationship graph for job {job_id}")
            
            return StorageOperation(
                storage_type=StorageType.GRAPH_DB,
                operation="create_relationship_graph",
                success=True,
                records_processed=total_processed,
                storage_id=f"neo4j_{job_id}_complete_graph"
            )
            
        except Exception as e:
            logger.error(f"Failed to create relationship graph in Neo4j: {str(e)}")
            return StorageOperation(
                storage_type=StorageType.GRAPH_DB,
                operation="create_relationship_graph",
                success=False,
                records_processed=0,
                error_message=str(e)
            )
    
    async def query_related_chunks(
        self,
        chunk_id: str,
        relationship_types: Optional[List[str]] = None,
        max_depth: int = 2,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Query related chunks using graph traversal"""
        
        if not self.connected:
            await self.initialize()
        
        try:
            with self.driver.session() as session:
                # Build relationship type filter
                rel_filter = ""
                if relationship_types:
                    rel_types = "|".join(relationship_types)
                    rel_filter = f"[r:{rel_types}*1..{max_depth}]"
                else:
                    rel_filter = f"[r*1..{max_depth}]"
                
                query = f"""
                MATCH (start:Chunk {{chunk_id: $chunk_id}})
                MATCH path = (start)-{rel_filter}-(related:Chunk)
                WHERE start.chunk_id <> related.chunk_id
                WITH related, relationships(path) as rels, length(path) as depth
                RETURN DISTINCT
                    related.chunk_id as chunk_id,
                    related.content as content,
                    related.semantic_type as semantic_type,
                    related.domain as domain,
                    related.confidence as confidence,
                    depth,
                    [rel in rels | type(rel)] as relationship_path
                ORDER BY depth ASC, related.confidence DESC
                LIMIT $limit
                """
                
                result = session.run(query, chunk_id=chunk_id, limit=limit)
                
                related_chunks = []
                for record in result:
                    related_chunks.append({
                        "chunk_id": record["chunk_id"],
                        "content": record["content"],
                        "semantic_type": record["semantic_type"],
                        "domain": record["domain"],
                        "confidence": record["confidence"],
                        "depth": record["depth"],
                        "relationship_path": record["relationship_path"]
                    })
                
                logger.info(f"Found {len(related_chunks)} related chunks for {chunk_id}")
                return related_chunks
                
        except Exception as e:
            logger.error(f"Graph query failed: {str(e)}")
            return []
    
    async def get_graph_statistics(self, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Get graph statistics for monitoring"""
        
        if not self.connected:
            await self.initialize()
        
        try:
            with self.driver.session() as session:
                # Build job filter
                job_filter = "WHERE c.job_id = $job_id" if job_id else ""
                job_params = {"job_id": job_id} if job_id else {}
                
                stats_query = f"""
                MATCH (c:Chunk) {job_filter}
                WITH count(c) as chunk_count
                MATCH (c1:Chunk)-[r]->(c2:Chunk) {job_filter.replace('c.', 'c1.')}
                RETURN 
                    chunk_count,
                    count(r) as relationship_count,
                    count(DISTINCT type(r)) as relationship_types,
                    collect(DISTINCT type(r)) as relationship_type_list
                """
                
                result = session.run(stats_query, **job_params)
                record = result.single()
                
                if record:
                    return {
                        "job_id": job_id,
                        "chunk_count": record["chunk_count"],
                        "relationship_count": record["relationship_count"],
                        "relationship_types_count": record["relationship_types"],
                        "relationship_types": record["relationship_type_list"],
                        "generated_at": datetime.now().isoformat()
                    }
                else:
                    return {"error": "No data found"}
                
        except Exception as e:
            logger.error(f"Failed to get graph statistics: {str(e)}")
            return {"error": str(e)}

    async def create_simple_document_graph(
        self,
        job_id: str,
        file_record: FileRecord,
        container: str
    ) -> StorageOperation:
        """Create simple document node connected to department/container"""

        if not self.connected:
            await self.initialize()

        try:
            logger.info(f"Creating simple document graph for {file_record.original_filename} in container {container}")

            with self.driver.session() as session:
                def create_document_department_graph(tx: Transaction):
                    # Create or merge department node
                    department_query = """
                    MERGE (dept:Department {name: $container})
                    ON CREATE SET
                        dept.created_at = $created_at,
                        dept.type = 'container'
                    RETURN dept
                    """

                    # Create document node and connect to department
                    document_query = """
                    MERGE (doc:Document {job_id: $job_id, file_id: $file_id})
                    SET
                        doc.filename = $filename,
                        doc.file_type = $file_type,
                        doc.file_size = $file_size,
                        doc.processed_at = $processed_at,
                        doc.container = $container,
                        doc.total_chunks = $total_chunks,
                        doc.created_at = $created_at
                    WITH doc
                    MATCH (dept:Department {name: $container})
                    MERGE (doc)-[:BELONGS_TO]->(dept)
                    RETURN doc, dept
                    """

                    created_at = datetime.now().isoformat()

                    # Create department
                    tx.run(department_query, container=container, created_at=created_at)

                    # Create document and relationship
                    result = tx.run(document_query,
                        job_id=job_id,
                        file_id=file_record.file_id,
                        filename=file_record.original_filename,
                        file_type=file_record.file_type,
                        file_size=file_record.file_size,
                        processed_at=file_record.processed_at.isoformat(),
                        container=container,
                        total_chunks=file_record.total_chunks,
                        created_at=created_at
                    )

                    return result.consume().counters.nodes_created + result.consume().counters.relationships_created

                records_processed = session.execute_write(create_document_department_graph)

            logger.info(f"Successfully created simple document graph: document '{file_record.original_filename}' -> department '{container}'")

            return StorageOperation(
                storage_type=StorageType.GRAPH_DB,
                operation="create_simple_document_graph",
                success=True,
                records_processed=records_processed,
                storage_id=f"neo4j_{job_id}_simple_doc_graph"
            )

        except Exception as e:
            logger.error(f"Failed to create simple document graph: {str(e)}")
            return StorageOperation(
                storage_type=StorageType.GRAPH_DB,
                operation="create_simple_document_graph",
                success=False,
                records_processed=0,
                error_message=str(e)
            )

    async def health_check(self) -> bool:
        """Check Neo4j connection health"""

        try:
            if not self.driver:
                return False

            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                return result.single()["test"] == 1

        except Exception as e:
            logger.error(f"Neo4j health check failed: {str(e)}")
            return False

    async def close(self) -> None:
        """Close Neo4j connection"""

        if self.driver:
            try:
                self.driver.close()
                self.connected = False
                logger.info("Neo4j storage connection closed")
            except Exception as e:
                logger.error(f"Error closing Neo4j connection: {str(e)}")
        else:
            logger.info("Neo4j storage connection already closed")