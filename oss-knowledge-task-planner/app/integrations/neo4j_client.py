"""
Neo4j client for topic hierarchy and graph queries in Task Planner
"""

import logging
import os
from typing import List, Dict, Any, Optional
from neo4j import AsyncGraphDatabase
from neo4j.exceptions import Neo4jError

logger = logging.getLogger(__name__)

class Neo4jClientService:
    """Neo4j client for topic hierarchy and graph relationships"""
    
    def __init__(self):
        self.driver = None
        self.uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
        self.username = os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password")
        self.database = os.getenv("NEO4J_DATABASE", "neo4j")
        self.timeout = int(os.getenv("NEO4J_TIMEOUT", "30"))
        self.initialized = False
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Neo4jClientService initialized - URI: {self.uri}, Database: {self.database}")
    
    async def initialize(self) -> bool:
        """Initialize Neo4j driver"""
        if self.initialized and self.driver:
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
                    self.logger.info(f"Neo4j connected successfully - Database: {info.get('name', 'unknown')}")
                
                # Check node count
                result = await session.run("MATCH (n) RETURN count(n) as node_count")
                count_record = await result.single()
                node_count = count_record["node_count"] if count_record else 0
                
                self.logger.info(f"Neo4j database contains {node_count} nodes")
            
            self.initialized = True
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Neo4j client: {e}")
            return False
    
    async def get_topic_hierarchy(
        self,
        topic: Optional[str] = None,
        max_depth: int = 3,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get topic hierarchy from Neo4j
        
        Args:
            topic: Starting topic name (if None, returns general hierarchy)
            max_depth: Maximum depth to traverse
            limit: Maximum number of results
            
        Returns:
            List of topic relationships
        """
        if not self.initialized:
            await self.initialize()
        
        if not self.driver:
            raise Exception("Neo4j driver not initialized")
        
        try:
            async with self.driver.session() as session:
                if topic:
                    # Query for specific topic hierarchy
                    query = """
                    MATCH path = (start:Topic {name: $topic})-[*1..%d]-(related:Topic)
                    RETURN DISTINCT start, related, relationships(path) as rels
                    LIMIT $limit
                    """ % max_depth
                    result = await session.run(query, topic=topic, limit=limit)
                else:
                    # Query for general topic hierarchy
                    query = """
                    MATCH (t:Topic)-[r]->(related:Topic)
                    RETURN t, r, related
                    LIMIT $limit
                    """
                    result = await session.run(query, limit=limit)
                
                topics = []
                async for record in result:
                    if topic:
                        topics.append({
                            "start": dict(record["start"]),
                            "related": dict(record["related"]),
                            "relationships": [dict(rel) for rel in record["rels"]]
                        })
                    else:
                        topics.append({
                            "topic": dict(record["t"]),
                            "relationship": dict(record["r"]),
                            "related": dict(record["related"])
                        })
                
                return topics
                
        except Exception as e:
            self.logger.error(f"Neo4j topic hierarchy query failed: {e}")
            raise
    
    async def find_related_documents(
        self,
        topic: str,
        relationship_type: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Find documents related to a topic
        
        Args:
            topic: Topic name
            relationship_type: Type of relationship to follow (optional)
            limit: Maximum number of results
            
        Returns:
            List of related documents
        """
        if not self.initialized:
            await self.initialize()
        
        if not self.driver:
            raise Exception("Neo4j driver not initialized")
        
        try:
            async with self.driver.session() as session:
                if relationship_type:
                    query = """
                    MATCH (t:Topic {name: $topic})-[r:%s]-(d:Document)
                    RETURN d, r, t
                    LIMIT $limit
                    """ % relationship_type
                else:
                    query = """
                    MATCH (t:Topic {name: $topic})-[r]-(d:Document)
                    RETURN d, r, t
                    LIMIT $limit
                    """
                
                result = await session.run(query, topic=topic, limit=limit)
                
                documents = []
                async for record in result:
                    documents.append({
                        "document": dict(record["d"]),
                        "relationship": dict(record["r"]),
                        "topic": dict(record["t"])
                    })
                
                return documents
                
        except Exception as e:
            self.logger.error(f"Neo4j document query failed: {e}")
            raise
    
    async def graph_search(
        self,
        start_node_id: Optional[str] = None,
        start_node_type: Optional[str] = None,
        max_depth: int = 3,
        relationship_types: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Perform graph traversal search
        
        Args:
            start_node_id: ID of starting node
            start_node_type: Type of starting node (Topic, Document, etc.)
            max_depth: Maximum traversal depth
            relationship_types: Types of relationships to follow
            limit: Maximum number of results
            
        Returns:
            List of graph paths
        """
        if not self.initialized:
            await self.initialize()
        
        if not self.driver:
            raise Exception("Neo4j driver not initialized")
        
        try:
            async with self.driver.session() as session:
                # Build query
                if start_node_id and start_node_type:
                    if relationship_types:
                        rel_filter = ":" + "|".join(relationship_types)
                    else:
                        rel_filter = ""
                    
                    query = f"""
                    MATCH path = (start:{start_node_type} {{id: $start_id}})-[*1..{max_depth}{rel_filter}]-(related)
                    RETURN path, start, related
                    LIMIT $limit
                    """
                    result = await session.run(query, start_id=start_node_id, limit=limit)
                else:
                    # General graph search
                    query = """
                    MATCH (n)-[r]->(m)
                    RETURN n, r, m
                    LIMIT $limit
                    """
                    result = await session.run(query, limit=limit)
                
                paths = []
                async for record in result:
                    if start_node_id:
                        paths.append({
                            "start": dict(record["start"]),
                            "related": dict(record["related"]),
                            "path": record["path"]
                        })
                    else:
                        paths.append({
                            "from": dict(record["n"]),
                            "relationship": dict(record["r"]),
                            "to": dict(record["m"])
                        })
                
                return paths
                
        except Exception as e:
            self.logger.error(f"Neo4j graph search failed: {e}")
            raise

