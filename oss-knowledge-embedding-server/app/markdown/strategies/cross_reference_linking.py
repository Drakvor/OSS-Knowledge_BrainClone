"""
Cross-Reference Link Chunking Strategy
======================================

Uses internal links, references, and citations to create relationship-aware chunks.
Detects markdown links, footnotes, and cross-references, then creates chunks that 
include both source and target content while building citation graphs.
"""

import uuid
import logging
import re
from typing import List, Dict, Any, Set, Tuple
from datetime import datetime

from app.markdown.base import (
    MarkdownElement, MarkdownElementType, MarkdownChunk, 
    MarkdownRelationship, MarkdownChunkingStrategy
)

logger = logging.getLogger(__name__)


class CrossReferenceLinkingChunker:
    """Creates chunks based on cross-references and link structures."""
    
    def __init__(self, min_chunk_size: int = 200, max_chunk_size: int = 1500):
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.strategy = MarkdownChunkingStrategy.CROSS_REFERENCE_LINKING
        
        # Patterns for different types of references
        self.footnote_pattern = re.compile(r'\[\^([^\]]+)\]')
        self.reference_pattern = re.compile(r'\[([^\]]+)\]\s*:\s*(.+)')
        self.internal_link_pattern = re.compile(r'\[([^\]]+)\]\(#([^)]+)\)')
        self.wiki_link_pattern = re.compile(r'\[\[([^\]]+)\]\]')
    
    def chunk(self, elements: List[MarkdownElement]) -> tuple[List[MarkdownChunk], List[MarkdownRelationship]]:
        """Create chunks based on cross-reference patterns."""
        chunks = []
        relationships = []
        
        if not elements:
            return chunks, relationships
        
        # Build reference maps
        reference_map = self._build_reference_map(elements)
        link_graph = self._build_link_graph(elements, reference_map)
        
        # Create reference-aware chunks
        reference_clusters = self._create_reference_clusters(elements, link_graph)
        
        # Convert clusters to chunks
        for cluster_idx, cluster in enumerate(reference_clusters):
            chunk = self._create_reference_chunk(cluster, cluster_idx, reference_map)
            if chunk:
                chunks.append(chunk)
        
        # Create citation relationships
        relationships = self._create_citation_relationships(chunks, link_graph, reference_map)
        
        logger.info(f"Created {len(chunks)} reference-aware chunks with {len(relationships)} relationships")
        return chunks, relationships
    
    def _build_reference_map(self, elements: List[MarkdownElement]) -> Dict[str, Any]:
        """Build a map of all references, footnotes, and links."""
        reference_map = {
            'footnotes': {},
            'references': {},
            'internal_links': {},
            'wiki_links': {}
        }
        
        for element in elements:
            content = element.content
            
            # Extract footnotes
            footnotes = self.footnote_pattern.findall(content)
            for footnote in footnotes:
                if footnote not in reference_map['footnotes']:
                    reference_map['footnotes'][footnote] = []
                reference_map['footnotes'][footnote].append(element)
            
            # Extract reference definitions
            references = self.reference_pattern.findall(content)
            for ref_key, ref_url in references:
                reference_map['references'][ref_key] = {
                    'url': ref_url,
                    'element': element
                }
            
            # Extract internal links
            internal_links = self.internal_link_pattern.findall(content)
            for link_text, anchor in internal_links:
                if anchor not in reference_map['internal_links']:
                    reference_map['internal_links'][anchor] = []
                reference_map['internal_links'][anchor].append({
                    'text': link_text,
                    'element': element
                })
            
            # Extract wiki-style links
            wiki_links = self.wiki_link_pattern.findall(content)
            for wiki_link in wiki_links:
                if wiki_link not in reference_map['wiki_links']:
                    reference_map['wiki_links'][wiki_link] = []
                reference_map['wiki_links'][wiki_link].append(element)
        
        return reference_map
    
    def _build_link_graph(self, elements: List[MarkdownElement], reference_map: Dict[str, Any]) -> Dict[str, Set[str]]:
        """Build a graph of links between elements."""
        link_graph = {}
        
        # Create element ID mapping
        element_ids = {id(elem): f"elem_{i}" for i, elem in enumerate(elements)}
        
        for element in elements:
            elem_id = element_ids[id(element)]
            link_graph[elem_id] = set()
            
            # Find all references in this element
            content = element.content
            
            # Process footnote references
            footnotes = self.footnote_pattern.findall(content)
            for footnote in footnotes:
                if footnote in reference_map['footnotes']:
                    for target_elem in reference_map['footnotes'][footnote]:
                        if id(target_elem) != id(element):
                            target_id = element_ids[id(target_elem)]
                            link_graph[elem_id].add(target_id)
            
            # Process internal links
            internal_links = self.internal_link_pattern.findall(content)
            for _, anchor in internal_links:
                # Find elements with headers matching this anchor
                anchor_pattern = anchor.replace('-', '[-\\s_]?')
                for target_elem in elements:
                    if (target_elem.element_type == MarkdownElementType.HEADER and
                        re.search(anchor_pattern, target_elem.content.lower())):
                        target_id = element_ids[id(target_elem)]
                        if target_id != elem_id:
                            link_graph[elem_id].add(target_id)
            
            # Process wiki links
            wiki_links = self.wiki_link_pattern.findall(content)
            for wiki_link in wiki_links:
                if wiki_link in reference_map['wiki_links']:
                    for target_elem in reference_map['wiki_links'][wiki_link]:
                        if id(target_elem) != id(element):
                            target_id = element_ids[id(target_elem)]
                            link_graph[elem_id].add(target_id)
        
        return link_graph
    
    def _create_reference_clusters(self, elements: List[MarkdownElement], link_graph: Dict[str, Set[str]]) -> List[List[MarkdownElement]]:
        """Create clusters of elements based on reference relationships."""
        if not elements:
            return []
        
        element_ids = {id(elem): f"elem_{i}" for i, elem in enumerate(elements)}
        id_to_element = {f"elem_{i}": elem for i, elem in enumerate(elements)}
        
        clusters = []
        visited = set()
        
        for element in elements:
            elem_id = element_ids[id(element)]
            
            if elem_id in visited:
                continue
            
            # Build cluster around this element
            cluster = self._build_reference_cluster(elem_id, link_graph, id_to_element, visited)
            
            if cluster:
                # Sort cluster by position
                cluster.sort(key=lambda x: x.position)
                clusters.append(cluster)
        
        # Merge small clusters that are adjacent
        merged_clusters = self._merge_adjacent_clusters(clusters)
        
        return merged_clusters
    
    def _build_reference_cluster(self, start_elem_id: str, link_graph: Dict[str, Set[str]], 
                                id_to_element: Dict[str, MarkdownElement], visited: Set[str]) -> List[MarkdownElement]:
        """Build a cluster starting from an element."""
        cluster = []
        to_visit = [start_elem_id]
        local_visited = set()
        
        while to_visit and len(cluster) < 10:  # Limit cluster size
            current_id = to_visit.pop(0)
            
            if current_id in local_visited or current_id in visited:
                continue
            
            local_visited.add(current_id)
            visited.add(current_id)
            
            element = id_to_element[current_id]
            cluster.append(element)
            
            # Add linked elements
            if current_id in link_graph:
                for linked_id in link_graph[current_id]:
                    if linked_id not in local_visited:
                        to_visit.append(linked_id)
            
            # Add elements that link to this one
            for elem_id, links in link_graph.items():
                if current_id in links and elem_id not in local_visited:
                    to_visit.append(elem_id)
        
        return cluster
    
    def _merge_adjacent_clusters(self, clusters: List[List[MarkdownElement]]) -> List[List[MarkdownElement]]:
        """Merge small adjacent clusters."""
        if len(clusters) <= 1:
            return clusters
        
        merged = []
        current_cluster = clusters[0]
        
        for next_cluster in clusters[1:]:
            current_size = sum(len(elem.content) for elem in current_cluster)
            next_size = sum(len(elem.content) for elem in next_cluster)
            
            # Check if clusters are adjacent and small
            current_end = max(elem.position for elem in current_cluster)
            next_start = min(elem.position for elem in next_cluster)
            
            should_merge = (
                current_size < self.min_chunk_size * 1.5 or
                next_size < self.min_chunk_size * 1.5
            ) and current_size + next_size <= self.max_chunk_size
            
            if should_merge:
                current_cluster.extend(next_cluster)
                current_cluster.sort(key=lambda x: x.position)
            else:
                merged.append(current_cluster)
                current_cluster = next_cluster
        
        merged.append(current_cluster)
        return merged
    
    def _create_reference_chunk(self, cluster: List[MarkdownElement], cluster_idx: int, 
                               reference_map: Dict[str, Any]) -> MarkdownChunk:
        """Create a chunk from a reference cluster."""
        if not cluster:
            return None
        
        # Build content
        content_parts = []
        element_types = set()
        references = []
        
        for element in cluster:
            content_parts.append(element.content)
            element_types.add(element.element_type.value)
            
            # Extract references from this element
            refs = self._extract_element_references(element, reference_map)
            references.extend(refs)
        
        content = '\n\n'.join(content_parts)
        
        # Skip if too small
        if len(content) < self.min_chunk_size:
            return None
        
        # Truncate if too large
        if len(content) > self.max_chunk_size:
            content = content[:self.max_chunk_size] + "..."
        
        chunk_id = f"md_crossref_{uuid.uuid4().hex[:8]}"
        
        return MarkdownChunk(
            chunk_id=chunk_id,
            content=content,
            elements=cluster,
            chunk_type="cross_referenced",
            structural_metadata={
                "cluster_index": cluster_idx,
                "element_count": len(cluster),
                "element_types": list(element_types),
                "reference_count": len(references),
                "has_footnotes": any('footnote' in ref['type'] for ref in references),
                "has_internal_links": any('internal_link' in ref['type'] for ref in references)
            },
            semantic_metadata={
                "references": references,
                "reference_types": list(set(ref['type'] for ref in references)),
                "cross_reference_density": len(references) / len(content.split()) if content else 0,
                "connectivity_score": self._calculate_connectivity_score(cluster, reference_map)
            },
            position_start=cluster[0].position,
            position_end=cluster[-1].position,
            word_count=len(content.split())
        )
    
    def _extract_element_references(self, element: MarkdownElement, reference_map: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract all references from an element."""
        references = []
        content = element.content
        
        # Extract footnotes
        footnotes = self.footnote_pattern.findall(content)
        for footnote in footnotes:
            references.append({
                'type': 'footnote',
                'key': footnote,
                'text': footnote
            })
        
        # Extract internal links
        internal_links = self.internal_link_pattern.findall(content)
        for link_text, anchor in internal_links:
            references.append({
                'type': 'internal_link',
                'key': anchor,
                'text': link_text
            })
        
        # Extract wiki links
        wiki_links = self.wiki_link_pattern.findall(content)
        for wiki_link in wiki_links:
            references.append({
                'type': 'wiki_link',
                'key': wiki_link,
                'text': wiki_link
            })
        
        return references
    
    def _calculate_connectivity_score(self, cluster: List[MarkdownElement], reference_map: Dict[str, Any]) -> float:
        """Calculate how well-connected the cluster is."""
        total_refs = 0
        total_elements = len(cluster)
        
        for element in cluster:
            refs = self._extract_element_references(element, reference_map)
            total_refs += len(refs)
        
        if total_elements == 0:
            return 0.0
        
        return total_refs / total_elements
    
    def _create_citation_relationships(self, chunks: List[MarkdownChunk], link_graph: Dict[str, Set[str]], 
                                     reference_map: Dict[str, Any]) -> List[MarkdownRelationship]:
        """Create relationships based on citations and cross-references."""
        relationships = []
        
        # Create citation relationships
        for i, chunk in enumerate(chunks):
            references = chunk.semantic_metadata.get('references', [])
            
            for ref in references:
                # Find chunks that contain the target of this reference
                for j, target_chunk in enumerate(chunks):
                    if i == j:  # Skip self-references
                        continue
                    
                    if self._chunk_contains_reference_target(target_chunk, ref, reference_map):
                        relationships.append(MarkdownRelationship(
                            source_chunk_id=chunk.chunk_id,
                            target_chunk_id=target_chunk.chunk_id,
                            relationship_type="citation",
                            relationship_metadata={
                                "reference_type": ref['type'],
                                "reference_key": ref['key'],
                                "reference_text": ref['text']
                            },
                            confidence=0.9
                        ))
        
        # Create bidirectional reference relationships
        for i, chunk1 in enumerate(chunks):
            for j, chunk2 in enumerate(chunks[i + 1:], i + 1):
                mutual_refs = self._find_mutual_references(chunk1, chunk2)
                
                if mutual_refs:
                    relationships.append(MarkdownRelationship(
                        source_chunk_id=chunk1.chunk_id,
                        target_chunk_id=chunk2.chunk_id,
                        relationship_type="mutual_reference",
                        relationship_metadata={
                            "mutual_references": mutual_refs,
                            "reference_strength": len(mutual_refs)
                        },
                        confidence=min(1.0, len(mutual_refs) / 3.0)
                    ))
        
        return relationships
    
    def _chunk_contains_reference_target(self, chunk: MarkdownChunk, reference: Dict[str, Any], 
                                       reference_map: Dict[str, Any]) -> bool:
        """Check if chunk contains the target of a reference."""
        ref_type = reference['type']
        ref_key = reference['key']
        
        if ref_type == 'footnote':
            # Check if chunk contains footnote definition
            return any('[^' + ref_key + ']:' in elem.content for elem in chunk.elements)
        
        elif ref_type == 'internal_link':
            # Check if chunk contains header matching the anchor
            anchor_pattern = ref_key.replace('-', '[-\\s_]?')
            return any(
                elem.element_type == MarkdownElementType.HEADER and
                re.search(anchor_pattern, elem.content.lower())
                for elem in chunk.elements
            )
        
        elif ref_type == 'wiki_link':
            # Check if chunk contains content related to wiki link
            return any(ref_key.lower() in elem.content.lower() for elem in chunk.elements)
        
        return False
    
    def _find_mutual_references(self, chunk1: MarkdownChunk, chunk2: MarkdownChunk) -> List[str]:
        """Find mutual references between two chunks."""
        refs1 = set(ref['key'] for ref in chunk1.semantic_metadata.get('references', []))
        refs2 = set(ref['key'] for ref in chunk2.semantic_metadata.get('references', []))
        
        # Find references that appear in both chunks
        mutual = list(refs1 & refs2)
        
        return mutual