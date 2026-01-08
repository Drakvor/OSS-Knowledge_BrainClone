"""
Neo4j Graph Schema Setup for Strategy Benchmarking
=================================================

Creates strategy-specific graph schemas and constraints.
"""

from neo4j import GraphDatabase
from typing import List, Dict, Any
import logging

from app.benchmark.base import StrategyType

logger = logging.getLogger(__name__)


class StrategyGraphManager:
    """Manages strategy-specific Neo4j schemas"""
    
    def __init__(self, uri: str = "neo4j://localhost:7687", user: str = "neo4j", password: str = "!alsrksdlswp5"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self._test_connection()
    
    def _test_connection(self):
        """Test Neo4j connection"""
        try:
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info("✅ Neo4j connection established")
        except Exception as e:
            logger.error(f"❌ Neo4j connection failed: {e}")
            raise
    
    def create_strategy_schemas(self, strategies: List[StrategyType]) -> Dict[str, Dict[str, Any]]:
        """Create graph schemas for each strategy"""
        
        schema_definitions = {
            StrategyType.ROW_BASED: {
                "nodes": ["ExcelRow", "DataField", "Sheet"],
                "relationships": ["HAS_FIELD", "NEXT_ROW", "BELONGS_TO_SHEET"],
                "constraints": [
                    "CREATE CONSTRAINT row_id_unique IF NOT EXISTS FOR (r:ExcelRow) REQUIRE r.row_id IS UNIQUE",
                    "CREATE CONSTRAINT field_id_unique IF NOT EXISTS FOR (f:DataField) REQUIRE f.field_id IS UNIQUE"
                ],
                "indexes": [
                    "CREATE INDEX row_content_index IF NOT EXISTS FOR (r:ExcelRow) ON (r.content)",
                    "CREATE INDEX field_value_index IF NOT EXISTS FOR (f:DataField) ON (f.value)"
                ]
            },
            
            StrategyType.HIERARCHICAL: {
                "nodes": ["ChunkGroup", "ChunkLevel", "ParentChunk", "ChildChunk"],
                "relationships": ["PARENT_OF", "BELONGS_TO_GROUP", "SAME_LEVEL", "HIERARCHICAL_LINK"],
                "constraints": [
                    "CREATE CONSTRAINT group_id_unique IF NOT EXISTS FOR (g:ChunkGroup) REQUIRE g.group_id IS UNIQUE",
                    "CREATE CONSTRAINT level_id_unique IF NOT EXISTS FOR (l:ChunkLevel) REQUIRE l.level_id IS UNIQUE"
                ],
                "indexes": [
                    "CREATE INDEX hierarchy_depth_index IF NOT EXISTS FOR (c:ParentChunk) ON (c.depth)",
                    "CREATE INDEX group_type_index IF NOT EXISTS FOR (g:ChunkGroup) ON (g.group_type)"
                ]
            },
            
            StrategyType.COLUMN_SEMANTIC: {
                "nodes": ["Column", "SemanticField", "FieldCluster", "DataType"],
                "relationships": ["SEMANTIC_SIMILAR", "FIELD_TYPE", "IN_CLUSTER", "COLUMN_RELATION"],
                "constraints": [
                    "CREATE CONSTRAINT column_name_unique IF NOT EXISTS FOR (c:Column) REQUIRE c.name IS UNIQUE",
                    "CREATE CONSTRAINT cluster_id_unique IF NOT EXISTS FOR (fc:FieldCluster) REQUIRE fc.cluster_id IS UNIQUE"
                ],
                "indexes": [
                    "CREATE INDEX semantic_score_index IF NOT EXISTS FOR ()-[r:SEMANTIC_SIMILAR]-() ON (r.similarity_score)",
                    "CREATE INDEX column_type_index IF NOT EXISTS FOR (c:Column) ON (c.data_type)"
                ]
            },
            
            StrategyType.ADAPTIVE_SMART: {
                "nodes": ["SmartChunk", "AdaptiveRule", "ContextWindow", "DecisionPoint"],
                "relationships": ["ADAPTS_TO", "CONTEXT_AWARE", "RULE_APPLIED", "SMART_MERGE"],
                "constraints": [
                    "CREATE CONSTRAINT smart_chunk_id_unique IF NOT EXISTS FOR (sc:SmartChunk) REQUIRE sc.chunk_id IS UNIQUE",
                    "CREATE CONSTRAINT rule_id_unique IF NOT EXISTS FOR (ar:AdaptiveRule) REQUIRE ar.rule_id IS UNIQUE"
                ],
                "indexes": [
                    "CREATE INDEX adaptation_score_index IF NOT EXISTS FOR (sc:SmartChunk) ON (sc.adaptation_score)",
                    "CREATE INDEX context_size_index IF NOT EXISTS FOR (cw:ContextWindow) ON (cw.window_size)"
                ]
            },
            
            StrategyType.ENTITY_CENTRIC: {
                "nodes": ["Entity", "EntityType", "EntityChunk", "EntityRelation"],
                "relationships": ["IS_TYPE", "CONTAINS_ENTITY", "ENTITY_LINK", "CO_OCCURS"],
                "constraints": [
                    "CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.entity_id IS UNIQUE",
                    "CREATE CONSTRAINT entity_type_unique IF NOT EXISTS FOR (et:EntityType) REQUIRE et.type_name IS UNIQUE"
                ],
                "indexes": [
                    "CREATE INDEX entity_name_index IF NOT EXISTS FOR (e:Entity) ON (e.entity_name)",
                    "CREATE INDEX co_occurrence_index IF NOT EXISTS FOR ()-[r:CO_OCCURS]-() ON (r.frequency)"
                ]
            },
            
            StrategyType.SLIDING_WINDOW: {
                "nodes": ["WindowChunk", "WindowPosition", "OverlapRegion", "WindowBoundary"],
                "relationships": ["WINDOW_OVERLAP", "NEXT_WINDOW", "BOUNDARY_DEFINED", "POSITION_IN"],
                "constraints": [
                    "CREATE CONSTRAINT window_id_unique IF NOT EXISTS FOR (wc:WindowChunk) REQUIRE wc.window_id IS UNIQUE",
                    "CREATE CONSTRAINT position_id_unique IF NOT EXISTS FOR (wp:WindowPosition) REQUIRE wp.position_id IS UNIQUE"
                ],
                "indexes": [
                    "CREATE INDEX window_start_index IF NOT EXISTS FOR (wc:WindowChunk) ON (wc.start_position)",
                    "CREATE INDEX overlap_size_index IF NOT EXISTS FOR ()-[r:WINDOW_OVERLAP]-() ON (r.overlap_size)"
                ]
            },
            
            StrategyType.TOPIC_CLUSTERING: {
                "nodes": ["Topic", "TopicCluster", "TopicChunk", "ClusterCentroid"],
                "relationships": ["IN_TOPIC", "TOPIC_SIMILAR", "CLUSTER_MEMBER", "CENTROID_OF"],
                "constraints": [
                    "CREATE CONSTRAINT topic_id_unique IF NOT EXISTS FOR (t:Topic) REQUIRE t.topic_id IS UNIQUE",
                    "CREATE CONSTRAINT cluster_id_unique IF NOT EXISTS FOR (tc:TopicCluster) REQUIRE tc.cluster_id IS UNIQUE"
                ],
                "indexes": [
                    "CREATE INDEX topic_score_index IF NOT EXISTS FOR ()-[r:IN_TOPIC]-() ON (r.topic_score)",
                    "CREATE INDEX cluster_coherence_index IF NOT EXISTS FOR (tc:TopicCluster) ON (tc.coherence_score)"
                ]
            }
        }
        
        results = {}
        
        for strategy in strategies:
            if strategy not in schema_definitions:
                logger.warning(f"No schema definition for strategy: {strategy}")
                continue
                
            try:
                schema_info = self._create_strategy_schema(strategy, schema_definitions[strategy])
                results[strategy.value] = schema_info
                logger.info(f"✅ Created schema for {strategy.value}")
            except Exception as e:
                logger.error(f"❌ Failed to create schema for {strategy.value}: {e}")
                results[strategy.value] = {"error": str(e)}
        
        return results
    
    def _create_strategy_schema(self, strategy: StrategyType, schema_def: Dict[str, Any]) -> Dict[str, Any]:
        """Create schema for a specific strategy"""
        
        with self.driver.session() as session:
            # Create constraints
            constraint_results = []
            for constraint in schema_def.get("constraints", []):
                try:
                    session.run(constraint)
                    constraint_results.append({"constraint": constraint, "status": "created"})
                except Exception as e:
                    constraint_results.append({"constraint": constraint, "status": f"failed: {e}"})
            
            # Create indexes
            index_results = []
            for index in schema_def.get("indexes", []):
                try:
                    session.run(index)
                    index_results.append({"index": index, "status": "created"})
                except Exception as e:
                    index_results.append({"index": index, "status": f"failed: {e}"})
        
        return {
            "strategy": strategy.value,
            "nodes": schema_def.get("nodes", []),
            "relationships": schema_def.get("relationships", []),
            "constraints": constraint_results,
            "indexes": index_results
        }
    
    def cleanup_strategy_data(self, strategy: StrategyType) -> Dict[str, Any]:
        """Clean up data for a specific strategy"""
        
        cleanup_queries = {
            StrategyType.ROW_BASED: [
                "MATCH (r:ExcelRow) WHERE r.strategy = $strategy DELETE r",
                "MATCH (f:DataField) WHERE f.strategy = $strategy DELETE f",
                "MATCH (s:Sheet) WHERE s.strategy = $strategy DELETE s"
            ],
            StrategyType.HIERARCHICAL: [
                "MATCH (g:ChunkGroup) WHERE g.strategy = $strategy DELETE g",
                "MATCH (l:ChunkLevel) WHERE l.strategy = $strategy DELETE l",
                "MATCH (p:ParentChunk) WHERE p.strategy = $strategy DELETE p",
                "MATCH (c:ChildChunk) WHERE c.strategy = $strategy DELETE c"
            ],
            # Add more cleanup queries for other strategies as needed
        }
        
        results = {"deleted_nodes": 0, "deleted_relationships": 0}
        
        with self.driver.session() as session:
            queries = cleanup_queries.get(strategy, [
                f"MATCH (n) WHERE n.strategy = $strategy DELETE n"
            ])
            
            for query in queries:
                try:
                    result = session.run(query, strategy=strategy.value)
                    summary = result.consume()
                    results["deleted_nodes"] += summary.counters.nodes_deleted
                    results["deleted_relationships"] += summary.counters.relationships_deleted
                except Exception as e:
                    logger.warning(f"Cleanup query failed: {e}")
        
        return results
    
    def close(self):
        """Close the database connection"""
        self.driver.close()


def setup_benchmark_schemas() -> Dict[str, Dict[str, Any]]:
    """Setup all benchmark graph schemas"""
    strategies = list(StrategyType)
    manager = StrategyGraphManager()
    
    try:
        schema_results = manager.create_strategy_schemas(strategies)
        return schema_results
    finally:
        manager.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Setting up strategy-specific Neo4j schemas...")
    results = setup_benchmark_schemas()
    
    print(f"\nCreated schemas for {len(results)} strategies:")
    for strategy, result in results.items():
        if "error" in result:
            print(f"  ❌ {strategy}: {result['error']}")
        else:
            print(f"  ✅ {strategy}: {len(result['nodes'])} node types, {len(result['relationships'])} relationship types")