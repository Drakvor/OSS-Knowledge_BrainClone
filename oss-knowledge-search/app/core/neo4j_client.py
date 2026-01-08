"""
Neo4j Graph Database Client for Search Operations
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from neo4j import GraphDatabase, AsyncGraphDatabase
from neo4j.exceptions import Neo4jError

from app.config import settings

logger = logging.getLogger(__name__)


class Neo4jService:
    """Neo4j graph database service for relationship-based search"""
    
    def __init__(self):
        self.driver = None
        self.uri = settings.NEO4J_URI
        self.username = settings.NEO4J_USERNAME
        self.password = settings.NEO4J_PASSWORD
        self.database = settings.NEO4J_DATABASE
        self.timeout = settings.NEO4J_TIMEOUT
        self.initialized = False
        
        logger.info(f"Neo4j Service initialized - URI: {self.uri}, Database: {self.database}")
    
    async def initialize(self) -> bool:
        """Initialize Neo4j driver and verify connection"""
        
        if self.initialized:
            return True
        
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
                database=self.database
            )
            
            # Test connection
            await self.driver.verify_connectivity()
            
            # Get database info
            async with self.driver.session() as session:
                result = await session.run("CALL db.info()")
                info = await result.single()
                
                if info:
                    logger.info(f"Neo4j connected successfully - Database: {info.get('name', 'unknown')}")
                
                # Check if we have any nodes
                result = await session.run("MATCH (n) RETURN count(n) as node_count")
                count_record = await result.single()
                node_count = count_record["node_count"] if count_record else 0
                
                logger.info(f"Neo4j database contains {node_count} nodes")
            
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j service: {e}")
            return False
    
    async def graph_search(
        self,
        start_node_id: str,
        max_depth: int = 3,
        relationship_types: Optional[List[str]] = None,
        node_types: Optional[List[str]] = None,
        limit: int = 50,
        collection: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Perform graph traversal search from a starting node"""
        
        if not self.initialized:
            await self.initialize()
        
        if not self.driver:
            raise Exception("Neo4j driver not initialized")
        
        try:
            async with self.driver.session() as session:
                # Build the Cypher query
                cypher_parts = []
                
                # Start with the initial node
                cypher_parts.append(f"MATCH (start) WHERE start.chunk_id = $start_node_id")
                
                # Build relationship pattern
                rel_pattern = ""
                if relationship_types:
                    rel_types = "|".join(relationship_types)
                    rel_pattern = f"[r:{rel_types}*1..{max_depth}]"
                else:
                    rel_pattern = f"[r*1..{max_depth}]"
                
                # Add traversal pattern
                cypher_parts.append(f"MATCH (start)-{rel_pattern}-(connected)")
                
                # Add filters
                where_conditions = []

                # Add node type filter if specified
                if node_types:
                    node_filter = " OR ".join([f"connected:{node_type}" for node_type in node_types])
                    where_conditions.append(f"({node_filter})")

                # Add collection filter if specified
                if collection:
                    where_conditions.append(f"connected.collection = '{collection}'")

                if where_conditions:
                    cypher_parts.append(f"WHERE {' AND '.join(where_conditions)}")
                
                # Return clause
                cypher_parts.append("RETURN DISTINCT connected, r, length(r) as depth")
                cypher_parts.append(f"ORDER BY depth ASC LIMIT {limit}")
                
                cypher_query = " ".join(cypher_parts)
                
                logger.info(f"Executing graph search: {cypher_query}")
                
                result = await session.run(cypher_query, start_node_id=start_node_id)
                records = await result.data()
                
                # Format results
                formatted_results = []
                for record in records:
                    node = record["connected"]
                    relationships = record["r"]
                    depth = record["depth"]
                    
                    # Extract node properties
                    node_data = dict(node)
                    
                    # Process relationships
                    rel_data = []
                    if isinstance(relationships, list):
                        for rel in relationships:
                            rel_info = {
                                "type": rel.type,
                                "properties": dict(rel)
                            }
                            rel_data.append(rel_info)
                    else:
                        rel_info = {
                            "type": relationships.type,
                            "properties": dict(relationships)
                        }
                        rel_data.append(rel_info)
                    
                    formatted_result = {
                        "id": node_data.get("chunk_id", str(node.id)),
                        "content": node_data.get("content", ""),
                        "node_type": list(node.labels)[0] if node.labels else "unknown",
                        "depth": depth,
                        "relationships": rel_data,
                        "metadata": {k: v for k, v in node_data.items() if k not in ["chunk_id", "content"]}
                    }
                    formatted_results.append(formatted_result)
                
                logger.info(f"Graph search completed - Starting node: {start_node_id}, Results: {len(formatted_results)}")
                return formatted_results
                
        except Exception as e:
            logger.error(f"Graph search failed: {e}")
            raise Exception(f"Failed to perform graph search: {e}")
    
    async def find_related_nodes(
        self,
        node_ids: List[str],
        relationship_types: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Find nodes directly related to the given node IDs"""
        
        if not self.initialized:
            await self.initialize()
        
        if not self.driver:
            raise Exception("Neo4j driver not initialized")
        
        try:
            async with self.driver.session() as session:
                # Build relationship pattern
                rel_pattern = "-[r]-"
                if relationship_types:
                    rel_types = "|".join(relationship_types)
                    rel_pattern = f"-[r:{rel_types}]-"
                
                cypher_query = f"""
                MATCH (start) WHERE start.chunk_id IN $node_ids
                MATCH (start){rel_pattern}(connected)
                WHERE NOT connected.chunk_id IN $node_ids
                RETURN DISTINCT connected, r, start.chunk_id as source_id
                LIMIT {limit}
                """
                
                result = await session.run(cypher_query, node_ids=node_ids)
                records = await result.data()
                
                # Format results
                formatted_results = []
                for record in records:
                    node = record["connected"]
                    relationship = record["r"]
                    source_id = record["source_id"]
                    
                    node_data = dict(node)
                    
                    formatted_result = {
                        "id": node_data.get("chunk_id", str(node.id)),
                        "content": node_data.get("content", ""),
                        "node_type": list(node.labels)[0] if node.labels else "unknown",
                        "source_id": source_id,
                        "relationship": {
                            "type": relationship.type,
                            "properties": dict(relationship)
                        },
                        "metadata": {k: v for k, v in node_data.items() if k not in ["chunk_id", "content"]}
                    }
                    formatted_results.append(formatted_result)
                
                logger.info(f"Related nodes search completed - Input nodes: {len(node_ids)}, Results: {len(formatted_results)}")
                return formatted_results
                
        except Exception as e:
            logger.error(f"Related nodes search failed: {e}")
            raise Exception(f"Failed to find related nodes: {e}")
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        
        if not self.initialized:
            await self.initialize()
        
        if not self.driver:
            raise Exception("Neo4j driver not initialized")
        
        try:
            async with self.driver.session() as session:
                # Get node count
                result = await session.run("MATCH (n) RETURN count(n) as node_count")
                node_count_record = await result.single()
                node_count = node_count_record["node_count"] if node_count_record else 0
                
                # Get relationship count
                result = await session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
                rel_count_record = await result.single()
                rel_count = rel_count_record["rel_count"] if rel_count_record else 0
                
                # Get node labels
                result = await session.run("CALL db.labels()")
                labels = [record["label"] for record in await result.data()]
                
                # Get relationship types
                result = await session.run("CALL db.relationshipTypes()")
                rel_types = [record["relationshipType"] for record in await result.data()]
                
                return {
                    "database": self.database,
                    "node_count": node_count,
                    "relationship_count": rel_count,
                    "node_labels": labels,
                    "relationship_types": rel_types
                }
                
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            raise Exception(f"Failed to get database statistics: {e}")
    
    async def close(self):
        """Close Neo4j driver"""
        if self.driver:
            try:
                await self.driver.close()
                logger.info("Neo4j driver closed")
            except Exception as e:
                logger.error(f"Error closing Neo4j driver: {e}")
            finally:
                self.driver = None
                self.initialized = False