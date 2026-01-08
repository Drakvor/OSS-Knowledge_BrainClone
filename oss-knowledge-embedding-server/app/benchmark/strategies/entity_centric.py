"""
Entity-Centric Excel Chunking Strategy
======================================

Strategy 5: Entity-focused chunking that identifies and groups by key entities.
Creates chunks centered around specific entities (tickets, users, assets).
"""

import pandas as pd
from typing import List, Tuple, Dict, Any, Set
import logging
import re
from collections import defaultdict, Counter

from app.benchmark.base import BenchmarkStrategy, BenchmarkConfig, StrategyType
from app.processors.base.base_models import ProcessedChunk, ChunkRelationship

logger = logging.getLogger(__name__)


class EntityCentricStrategy(BenchmarkStrategy):
    """Entity-centric chunking strategy implementation"""
    
    def __init__(self, config: BenchmarkConfig):
        super().__init__(config)
        self.entity_patterns = {
            "ticket_id": [r'ITSM-\d+', r'TKT-\d+', r'INC-\d+', r'REQ-\d+', r'티켓-\d+'],
            "user_id": [r'USER-\d+', r'USR\d+', r'사용자\d+', r'[가-힣]{2,3}[님]?$'],
            "asset_id": [r'SERVER-\d+', r'PC-\d+', r'ASSET-\d+', r'자산-\d+'],
            "system_id": [r'SYS-\d+', r'시스템\d+', r'APP-\d+']
        }
        self.max_chunk_size = 10
        self.min_entities_per_chunk = 1
    
    async def process_excel_data(self, excel_data: pd.DataFrame) -> Tuple[List[ProcessedChunk], List[ChunkRelationship]]:
        """Process Excel data using entity-centric chunking"""
        
        chunks = []
        relationships = []
        
        headers = list(excel_data.columns)
        total_rows = len(excel_data)
        
        logger.info(f"Processing {total_rows} rows with entity-centric analysis")
        
        # Step 1: Extract entities from all rows
        entity_data = self._extract_entities_from_data(excel_data, headers)
        
        # Step 2: Group rows by primary entities
        entity_groups = self._group_rows_by_entities(excel_data, entity_data)
        
        # Step 3: Create entity-centric chunks
        chunk_id_counter = 0
        
        for entity_type, entity_groups_dict in entity_groups.items():
            for entity_value, row_indices in entity_groups_dict.items():
                if not row_indices:
                    continue
                
                # Create chunks for this entity (split if too large)
                entity_chunks = self._create_entity_chunks(
                    excel_data, headers, entity_type, entity_value, row_indices, chunk_id_counter
                )
                
                chunks.extend(entity_chunks)
                chunk_id_counter += len(entity_chunks)
                
                # Create relationships within entity chunks
                for i in range(len(entity_chunks) - 1):
                    relationship = ChunkRelationship(
                        relationship_id=f"entity_seq_{entity_chunks[i].chunk_id}_{entity_chunks[i + 1].chunk_id}",
                        from_chunk_id=entity_chunks[i].chunk_id,
                        to_chunk_id=entity_chunks[i + 1].chunk_id,
                        relationship_type="same_entity_sequence",
                        confidence=0.8,
                        description="Same entity sequence",
                        metadata={
                            "entity_type": entity_type,
                            "entity_value": entity_value,
                            "sequence_order": i + 1
                        }
                    )
                    relationships.append(relationship)
        
        # Step 4: Create cross-entity relationships
        cross_relationships = self._create_cross_entity_relationships(chunks, entity_data)
        relationships.extend(cross_relationships)
        
        # Step 5: Handle orphaned rows (no clear entities)
        orphaned_chunks = self._handle_orphaned_rows(excel_data, headers, entity_data, chunk_id_counter)
        chunks.extend(orphaned_chunks)
        
        logger.info(f"Created {len(chunks)} entity-centric chunks with {len(relationships)} relationships")
        logger.info(f"Entity types found: {list(entity_groups.keys())}")
        
        return chunks, relationships
    
    def _extract_entities_from_data(self, data: pd.DataFrame, headers: List[str]) -> Dict[int, Dict[str, List[str]]]:
        """Extract entities from each row of data"""
        
        entity_data = {}
        
        for idx, row in data.iterrows():
            row_entities = defaultdict(list)
            
            for col in headers:
                if pd.isna(row[col]):
                    continue
                    
                cell_value = str(row[col])
                
                # Check each entity pattern
                for entity_type, patterns in self.entity_patterns.items():
                    for pattern in patterns:
                        matches = re.findall(pattern, cell_value, re.IGNORECASE)
                        for match in matches:
                            if match not in row_entities[entity_type]:
                                row_entities[entity_type].append(match)
            
            entity_data[idx] = dict(row_entities)
        
        return entity_data
    
    def _group_rows_by_entities(self, data: pd.DataFrame, entity_data: Dict[int, Dict[str, List[str]]]) -> Dict[str, Dict[str, List[int]]]:
        """Group rows by their primary entities"""
        
        entity_groups = defaultdict(lambda: defaultdict(list))
        
        for row_idx, entities in entity_data.items():
            if not entities:
                continue
            
            # Determine primary entity for this row
            primary_entity_type, primary_entity_value = self._determine_primary_entity(entities)
            
            if primary_entity_type and primary_entity_value:
                entity_groups[primary_entity_type][primary_entity_value].append(row_idx)
        
        return dict(entity_groups)
    
    def _determine_primary_entity(self, entities: Dict[str, List[str]]) -> Tuple[str, str]:
        """Determine the primary entity for a row"""
        
        # Priority order for entity types
        priority_order = ["ticket_id", "user_id", "asset_id", "system_id"]
        
        for entity_type in priority_order:
            if entity_type in entities and entities[entity_type]:
                return entity_type, entities[entity_type][0]  # Take first entity of this type
        
        # If no priority entities, take any available
        for entity_type, entity_list in entities.items():
            if entity_list:
                return entity_type, entity_list[0]
        
        return None, None
    
    def _create_entity_chunks(self, data: pd.DataFrame, headers: List[str], entity_type: str, 
                            entity_value: str, row_indices: List[int], base_chunk_id: int) -> List[ProcessedChunk]:
        """Create chunks for a specific entity"""
        
        chunks = []
        
        # Sort row indices
        row_indices = sorted(row_indices)
        
        # Split into manageable chunks if too many rows
        for chunk_start in range(0, len(row_indices), self.max_chunk_size):
            chunk_end = min(chunk_start + self.max_chunk_size, len(row_indices))
            chunk_row_indices = row_indices[chunk_start:chunk_end]
            
            # Get chunk data
            chunk_data = data.iloc[chunk_row_indices]
            
            # Create chunk content
            chunk_content = self._create_entity_chunk_content(
                chunk_data, headers, entity_type, entity_value, chunk_row_indices
            )
            
            chunk_id = self.create_chunk_id(f"entity_{entity_type}_{entity_value}", len(chunks))
            
            # Extract related entities from this chunk
            related_entities = self._extract_related_entities(chunk_data, headers, entity_type, entity_value)
            
            metadata = {
                "strategy": self.strategy_type.value,
                "chunk_type": "entity_centric",
                "primary_entity_type": entity_type,
                "primary_entity_value": entity_value,
                "related_entities": related_entities,
                "row_indices": chunk_row_indices,
                "row_count": len(chunk_data),
                "columns": headers,
                "entity_frequency": len(chunk_row_indices)
            }
            
            processed_chunk = ProcessedChunk(
                chunk_id=chunk_id,
                content=chunk_content,
                chunk_type="entity_centric",
                metadata=metadata,
                source_file=self.config.test_data_path,
                processing_metadata={"strategy": "entity_centric"}
            )
            
            chunks.append(processed_chunk)
        
        return chunks
    
    def _extract_related_entities(self, chunk_data: pd.DataFrame, headers: List[str], 
                                primary_entity_type: str, primary_entity_value: str) -> Dict[str, List[str]]:
        """Extract related entities from chunk data"""
        
        related_entities = defaultdict(set)
        
        for _, row in chunk_data.iterrows():
            for col in headers:
                if pd.isna(row[col]):
                    continue
                    
                cell_value = str(row[col])
                
                for entity_type, patterns in self.entity_patterns.items():
                    # Skip the primary entity type
                    if entity_type == primary_entity_type:
                        continue
                        
                    for pattern in patterns:
                        matches = re.findall(pattern, cell_value, re.IGNORECASE)
                        for match in matches:
                            related_entities[entity_type].add(match)
        
        # Convert sets to lists
        return {entity_type: list(entities) for entity_type, entities in related_entities.items()}
    
    def _create_entity_chunk_content(self, chunk_data: pd.DataFrame, headers: List[str], 
                                   entity_type: str, entity_value: str, row_indices: List[int]) -> str:
        """Create content for entity-centric chunk"""
        
        content_lines = [
            f"엔티티 중심 청크",
            f"주요 엔티티: {entity_type} = {entity_value}",
            f"관련 행: {len(chunk_data)}개 ({min(row_indices)+1}-{max(row_indices)+1})",
            "=" * 50
        ]
        
        # Add entity analysis
        content_lines.append("\\n엔티티 분석:")
        content_lines.append(f"- 엔티티 유형: {entity_type}")
        content_lines.append(f"- 엔티티 값: {entity_value}")
        content_lines.append(f"- 출현 빈도: {len(chunk_data)}회")
        
        # Add related entities summary
        related_entities = self._extract_related_entities(chunk_data, headers, entity_type, entity_value)
        if related_entities:
            content_lines.append("- 관련 엔티티:")
            for rel_type, rel_values in related_entities.items():
                if rel_values:
                    content_lines.append(f"  * {rel_type}: {', '.join(rel_values[:3])}{'...' if len(rel_values) > 3 else ''}")
        
        content_lines.append("\\n데이터:")
        
        # Add chunk data with entity highlighting
        for i, (original_idx, row) in enumerate(chunk_data.iterrows()):
            row_values = []
            for header in headers:
                value = str(row[header]) if pd.notna(row[header]) else "[비어있음]"
                
                # Highlight primary entity
                if entity_value in value:
                    value = f"**{value}**"
                
                row_values.append(f"{header}: {value}")
            
            content_lines.append(f"행 {original_idx + 1}: " + " | ".join(row_values))
        
        return "\\n".join(content_lines)
    
    def _create_cross_entity_relationships(self, chunks: List[ProcessedChunk], 
                                         entity_data: Dict[int, Dict[str, List[str]]]) -> List[ChunkRelationship]:
        """Create relationships between chunks with related entities"""
        
        relationships = []
        
        # Build entity-to-chunks mapping
        entity_chunks = defaultdict(list)
        for chunk in chunks:
            primary_entity = chunk.metadata.get("primary_entity_value")
            primary_type = chunk.metadata.get("primary_entity_type")
            if primary_entity and primary_type:
                entity_chunks[f"{primary_type}:{primary_entity}"].append(chunk)
            
            # Also map related entities
            related_entities = chunk.metadata.get("related_entities", {})
            for rel_type, rel_values in related_entities.items():
                for rel_value in rel_values:
                    entity_chunks[f"{rel_type}:{rel_value}"].append(chunk)
        
        # Create relationships between chunks sharing entities
        processed_pairs = set()
        
        for entity_key, related_chunks in entity_chunks.items():
            if len(related_chunks) < 2:
                continue
            
            for i, chunk1 in enumerate(related_chunks):
                for chunk2 in related_chunks[i + 1:]:
                    # Avoid duplicate relationships
                    pair_key = tuple(sorted([chunk1.chunk_id, chunk2.chunk_id]))
                    if pair_key in processed_pairs:
                        continue
                    
                    processed_pairs.add(pair_key)
                    
                    # Determine relationship strength
                    strength = self._calculate_entity_relationship_strength(chunk1, chunk2, entity_key)
                    
                    relationship_type = "entity_related"
                    if entity_key.startswith("ticket_id"):
                        relationship_type = "same_ticket"
                    elif entity_key.startswith("user_id"):
                        relationship_type = "same_user"
                    elif entity_key.startswith("asset_id"):
                        relationship_type = "same_asset"
                    
                    relationship = ChunkRelationship(
                        relationship_id=f"cross_entity_{chunk1.chunk_id}_{chunk2.chunk_id}",
                        from_chunk_id=chunk1.chunk_id,
                        to_chunk_id=chunk2.chunk_id,
                        relationship_type=relationship_type,
                        confidence=strength,
                        description="Cross-entity shared relationship",
                        metadata={
                            "shared_entity": entity_key,
                            "relationship_strength": strength,
                            "connection_type": "shared_entity"
                        }
                    )
                    relationships.append(relationship)
        
        return relationships
    
    def _calculate_entity_relationship_strength(self, chunk1: ProcessedChunk, chunk2: ProcessedChunk, shared_entity: str) -> float:
        """Calculate relationship strength between entity chunks"""
        
        strength = 0.5  # Base strength
        
        # Check if it's the primary entity for both chunks
        if (chunk1.metadata.get("primary_entity_value") in shared_entity and 
            chunk2.metadata.get("primary_entity_value") in shared_entity):
            strength += 0.3
        
        # Check number of shared related entities
        related1 = chunk1.metadata.get("related_entities", {})
        related2 = chunk2.metadata.get("related_entities", {})
        
        shared_related = 0
        for entity_type in related1:
            if entity_type in related2:
                shared_values = set(related1[entity_type]) & set(related2[entity_type])
                shared_related += len(shared_values)
        
        strength += min(shared_related * 0.1, 0.2)
        
        return min(strength, 1.0)
    
    def _handle_orphaned_rows(self, data: pd.DataFrame, headers: List[str], 
                            entity_data: Dict[int, Dict[str, List[str]]], base_chunk_id: int) -> List[ProcessedChunk]:
        """Handle rows without clear entities"""
        
        orphaned_indices = []
        
        for idx in range(len(data)):
            if idx not in entity_data or not entity_data[idx]:
                orphaned_indices.append(idx)
        
        if not orphaned_indices:
            return []
        
        chunks = []
        
        # Group orphaned rows into chunks
        for chunk_start in range(0, len(orphaned_indices), self.max_chunk_size):
            chunk_end = min(chunk_start + self.max_chunk_size, len(orphaned_indices))
            chunk_indices = orphaned_indices[chunk_start:chunk_end]
            
            chunk_data = data.iloc[chunk_indices]
            
            content_lines = [
                "고아 데이터 청크 (엔티티 없음)",
                f"행 수: {len(chunk_data)}",
                f"행 번호: {', '.join(str(i+1) for i in chunk_indices)}",
                "=" * 40,
                "\\n데이터:"
            ]
            
            for i, (original_idx, row) in enumerate(chunk_data.iterrows()):
                row_values = []
                for header in headers:
                    value = str(row[header]) if pd.notna(row[header]) else "[비어있음]"
                    row_values.append(f"{header}: {value}")
                
                content_lines.append(f"행 {original_idx + 1}: " + " | ".join(row_values))
            
            chunk_id = self.create_chunk_id("orphaned", base_chunk_id + len(chunks))
            
            metadata = {
                "strategy": self.strategy_type.value,
                "chunk_type": "orphaned_data",
                "primary_entity_type": None,
                "primary_entity_value": None,
                "related_entities": {},
                "row_indices": chunk_indices,
                "row_count": len(chunk_data),
                "columns": headers,
                "entity_frequency": 0
            }
            
            processed_chunk = ProcessedChunk(
                chunk_id=chunk_id,
                content="\\n".join(content_lines),
                chunk_type="entity_centric_orphaned",
                metadata=metadata,
                source_file=self.config.test_data_path,
                processing_metadata={"strategy": "entity_centric"}
            )
            
            chunks.append(processed_chunk)
        
        return chunks
    
    def get_search_config(self) -> Dict[str, Any]:
        """Get entity-centric search configuration"""
        return {
            "strategy_name": "entity_centric",
            "search_type": "entity_aware_semantic",
            "embedding_fields": ["content"],
            "boost_fields": {
                "entity_analysis": 1.5,
                "primary_entity": 1.8,
                "related_entities": 1.2,
                "data_content": 1.0
            },
            "filter_metadata": {
                "strategy": self.strategy_type.value,
                "chunk_type": "entity_centric"
            },
            "entity_type_weights": {
                "ticket_id": 1.5,
                "user_id": 1.2,
                "asset_id": 1.3,
                "system_id": 1.1
            },
            "relationship_traversal": {
                "enabled": True,
                "max_depth": 2,
                "relationship_types": ["same_ticket", "same_user", "same_asset", "entity_related"],
                "entity_boost": True,
                "traverse_related_entities": True
            }
        }
    
    def get_strategy_description(self) -> str:
        """Get strategy description"""
        return (
            f"Entity-Centric Chunking: Groups data by key entities (tickets, users, assets). "
            f"Uses regex patterns to identify Korean ITSM entities. "
            f"Max {self.max_chunk_size} rows per entity chunk. Creates cross-entity relationships."
        )