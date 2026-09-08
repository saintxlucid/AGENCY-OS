"""
Creative Memory Graph — Persistent knowledge storage with vector search.
Uses ChromaDB for embeddings + NetworkX for relationship graph.
"""
from __future__ import annotations

import os
import json
import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

import chromadb
from chromadb.config import Settings
import networkx as nx

# NOTE: sentence-transformers (torch/CUDA) is HEAVY and optional.
# Import lazily inside _get_embedder() so `import aurora.memory.graph`
# and unit tests work on CPU-only / minimal installs.
# Install with:  pip install -e .[local]


class RelationType(Enum):
    """Types of relationships in the creative graph."""
    SIMILAR_TO = "similar_to"
    INSPIRED_BY = "inspired_by"
    PART_OF = "part_of"
    CONTAINS = "contains"
    REFERENCES = "references"
    EVOLVED_FROM = "evolved_from"
    SHARES_STYLE = "shares_style"
    SHARES_COLORS = "shares_colors"
    SHARES_AUDIENCE = "shares_audience"
    SEQUENCE = "sequence"  # Version history


@dataclass
class GraphNode:
    """Node in the creative knowledge graph."""
    node_id: str
    node_type: str  # media, project, concept, brand, style
    label: str
    properties: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class GraphEdge:
    """Edge in the creative knowledge graph."""
    source: str
    target: str
    relation: RelationType
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class CreativeMemoryGraph:
    """
    Hybrid memory system:
    - ChromaDB for vector similarity search
    - NetworkX for explicit relationship graph
    - SQLite for structured metadata queries
    """
    
    def __init__(self, persist_dir: str = "./aurora_memory"):
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        # ChromaDB for embeddings
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.persist_dir / "chroma"),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Collections
        self.media_collection = self.chroma_client.get_or_create_collection(
            "media_interpretations",
            metadata={"hnsw:space": "cosine"}
        )
        self.project_collection = self.chroma_client.get_or_create_collection(
            "projects",
            metadata={"hnsw:space": "cosine"}
        )
        self.insight_collection = self.chroma_client.get_or_create_collection(
            "insights",
            metadata={"hnsw:space": "cosine"}
        )
        
        # NetworkX graph for relationships
        self.graph = nx.MultiDiGraph()

        # Embedding model — lazy (heavy torch/CUDA). See _get_embedder().
        self._embedder = None
        self._embedder_failed = False
        
        # Project index
        self.projects: Dict[str, Dict] = {}
        
        print(f"📚 Memory initialized at: {self.persist_dir}")

    def _get_embedder(self):
        """Lazy loader with hash fallback (no torch required)."""
        if self._embedder is not None:
            return self._embedder
        if self._embedder_failed:
            return None
        try:
            from sentence_transformers import SentenceTransformer

            self._embedder = SentenceTransformer("all-MiniLM-L6-v2")
            return self._embedder
        except Exception as e:  # torch/CUDA missing, offline, etc.
            print(f"  ⚠️  Embedder unavailable, using hash fallback: {e}")
            self._embedder_failed = True
            return None

    def _embed_text(self, text: str):
        """Encode text or deterministic hash fallback (384-dim)."""
        embedder = self._get_embedder()
        if embedder is not None:
            return embedder.encode(text).tolist()
        import hashlib

        h = hashlib.sha256(text.encode("utf-8")).digest()
        # Expand to 384 floats in [0,1)
        vals = [(h[i % len(h)] + (i * 7) % 256) / 512.0 for i in range(384)]
        return vals
    
    async def initialize(self):
        """Load existing graph from disk."""
        graph_path = self.persist_dir / "graph.gpickle"
        if graph_path.exists():
            import pickle
            with open(graph_path, 'rb') as f:
                self.graph = pickle.load(f)
            print(f"  📖 Loaded graph: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")
        
        # Load project index
        index_path = self.persist_dir / "projects.json"
        if index_path.exists():
            with open(index_path) as f:
                self.projects = json.load(f)
    
    # ─── Media Storage ───
    
    async def store(self, interpretation) -> str:
        """Store a media interpretation in memory."""
        from aurora.core import MediaInterpretation
        
        media_id = interpretation.media_id
        
        # Prepare document for ChromaDB
        doc_text = self._interpretation_to_text(interpretation)
        embedding = self._embed_text(doc_text)
        
        # Store in ChromaDB
        self.media_collection.upsert(
            ids=[media_id],
            documents=[doc_text],
            embeddings=[embedding],
            metadatas=[{
                "media_type": interpretation.media_type.value if hasattr(interpretation.media_type, 'value') else str(interpretation.media_type),
                "quality_score": interpretation.quality_score,
                "timestamp": interpretation.timestamp,
                "tags": ",".join(interpretation.tags),
                "summary": interpretation.summary[:500],
            }]
        )
        
        # Add to graph
        self._add_media_node(interpretation)
        
        # Auto-link to similar media
        await self._auto_link_similar(media_id, embedding)
        
        # Persist graph
        self._persist_graph()
        
        return media_id
    
    def _interpretation_to_text(self, interpretation) -> str:
        """Convert interpretation to searchable text."""
        parts = [
            f"Summary: {interpretation.summary}",
            f"Media type: {interpretation.media_type.value if hasattr(interpretation.media_type, 'value') else interpretation.media_type}",
            f"Tags: {', '.join(interpretation.tags)}",
        ]
        
        for insight in interpretation.insights:
            parts.append(f"[{insight.domain.value}] {insight.category}: {insight.finding}")
            if insight.suggestions:
                parts.append(f"  Suggestions: {'; '.join(insight.suggestions)}")
        
        return "\n".join(parts)
    
    def _add_media_node(self, interpretation):
        """Add media node to graph."""
        media_id = interpretation.media_id
        
        self.graph.add_node(
            media_id,
            node_type="media",
            label=interpretation.summary[:100],
            media_type=interpretation.media_type.value if hasattr(interpretation.media_type, 'value') else str(interpretation.media_type),
            quality_score=interpretation.quality_score,
            tags=interpretation.tags,
            timestamp=interpretation.timestamp,
            properties=interpretation.metadata_graph
        )
        
        # Add insight nodes
        for insight in interpretation.insights:
            insight_id = f"{media_id}_insight_{uuid.uuid4().hex[:8]}"
            self.graph.add_node(
                insight_id,
                node_type="insight",
                label=insight.finding[:100],
                domain=insight.domain.value if hasattr(insight.domain, 'value') else str(insight.domain),
                category=insight.category,
                confidence=insight.confidence
            )
            self.graph.add_edge(
                media_id, insight_id,
                relation=RelationType.CONTAINS,
                weight=insight.confidence
            )
    
    async def _auto_link_similar(self, media_id: str, embedding: List[float], threshold: float = 0.75, limit: int = 5):
        """Automatically link to similar media in memory."""
        results = self.media_collection.query(
            query_embeddings=[embedding],
            n_results=limit + 1,  # +1 because it includes self
            include=["metadatas", "distances"]
        )
        
        if results['ids'] and results['ids'][0]:
            for i, (other_id, distance) in enumerate(zip(results['ids'][0], results['distances'][0])):
                if other_id == media_id:
                    continue
                
                similarity = 1 - distance
                if similarity >= threshold:
                    self.graph.add_edge(
                        media_id, other_id,
                        relation=RelationType.SIMILAR_TO,
                        weight=similarity,
                        properties={"auto_linked": True}
                    )
    
    # ─── Project Management ───
    
    async def create_project(self, project) -> str:
        """Create a new project."""
        project_id = project.project_id
        
        doc_text = f"Project: {project.name}\nDescription: {project.description}\nBrief: {project.brief or ''}\nGoals: {', '.join(project.goals)}"
        embedding = self._embed_text(doc_text)
        
        self.project_collection.upsert(
            ids=[project_id],
            documents=[doc_text],
            embeddings=[embedding],
            metadatas=[{
                "name": project.name,
                "created_at": project.created_at,
                "target_audience": project.target_audience or "",
            }]
        )
        
        # Add to graph
        self.graph.add_node(
            project_id,
            node_type="project",
            label=project.name,
            properties=asdict(project)
        )
        
        self.projects[project_id] = {
            "name": project.name,
            "description": project.description,
            "brief": project.brief,
            "brand_guidelines": project.brand_guidelines,
            "target_audience": project.target_audience,
            "goals": project.goals,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
        }
        
        self._persist_projects()
        return project_id
    
    async def link_to_project(self, media_id: str, project_id: str):
        """Link media to a project."""
        if self.graph.has_node(media_id) and self.graph.has_node(project_id):
            self.graph.add_edge(
                project_id, media_id,
                relation=RelationType.CONTAINS,
                weight=1.0
            )
            self._persist_graph()
    
    # ─── Query & Retrieval ───
    
    async def query(self, question: str, domain: Optional[str] = None) -> str:
        """Natural language query over memory."""
        # Embed question
        query_embedding = self._embed_text(question)
        
        # Search media
        results = self.media_collection.query(
            query_embeddings=[query_embedding],
            n_results=10,
            include=["documents", "metadatas", "distances"]
        )
        
        if not results['ids'] or not results['ids'][0]:
            return "No relevant memories found."
        
        # Build context
        context_parts = []
        for i, (doc, meta, dist) in enumerate(zip(
            results['documents'][0], results['metadatas'][0], results['distances'][0]
        )):
            similarity = 1 - dist
            context_parts.append(f"[Match {i+1}, {similarity:.0%}] {doc[:500]}")
        
        # Use LLM to synthesize answer (placeholder - would use actual LLM)
        context = "\n\n".join(context_parts)
        return f"Based on creative memory:\n\n{context}\n\n[Synthesized answer would be generated by LLM here]"
    
    async def find_similar(self, media_id: str, limit: int = 10) -> List[Dict]:
        """Find similar media by graph relationships."""
        if not self.graph.has_node(media_id):
            return []
        
        similar = []
        for neighbor in self.graph.neighbors(media_id):
            edge_data = self.graph.get_edge_data(media_id, neighbor)
            for edge_key, edge_attrs in edge_data.items():
                if edge_attrs.get('relation') == RelationType.SIMILAR_TO.value:
                    weight = edge_attrs.get('weight', 0)
                    if self.graph.has_node(neighbor):
                        node_data = self.graph.nodes[neighbor]
                        similar.append({
                            "media_id": neighbor,
                            "label": node_data.get('label', ''),
                            "similarity": weight,
                            "media_type": node_data.get('media_type', ''),
                            "quality_score": node_data.get('quality_score', 0),
                        })
        
        similar.sort(key=lambda x: x['similarity'], reverse=True)
        return similar[:limit]
    
    async def get_project_timeline(self, project_id: str) -> List[Dict]:
        """Get chronological timeline of project assets."""
        if not self.graph.has_node(project_id):
            return []
        
        timeline = []
        for neighbor in self.graph.successors(project_id):
            edge_data = self.graph.get_edge_data(project_id, neighbor)
            for edge_key, edge_attrs in edge_data.items():
                if edge_attrs.get('relation') == RelationType.CONTAINS.value:
                    if self.graph.has_node(neighbor):
                        node_data = self.graph.nodes[neighbor]
                        timeline.append({
                            "media_id": neighbor,
                            "label": node_data.get('label', ''),
                            "media_type": node_data.get('media_type', ''),
                            "quality_score": node_data.get('quality_score', 0),
                            "timestamp": node_data.get('timestamp', ''),
                            "tags": node_data.get('tags', []),
                        })
        
        timeline.sort(key=lambda x: x['timestamp'])
        return timeline
    
    async def get_media(self, media_id: str) -> Optional[Dict]:
        """Retrieve full media interpretation by ID."""
        results = self.media_collection.get(ids=[media_id], include=["documents", "metadatas", "embeddings"])
        if results['ids']:
            return {
                "media_id": media_id,
                "document": results['documents'][0],
                "metadata": results['metadatas'][0],
                "embedding": results['embeddings'][0] if results['embeddings'] else None,
            }
        return None
    
    # ─── Graph Operations ───
    
    def get_related_concepts(self, media_id: str, depth: int = 2) -> List[Dict]:
        """Get related concepts via graph traversal."""
        if not self.graph.has_node(media_id):
            return []
        
        concepts = []
        visited = set()
        queue = [(media_id, 0)]
        
        while queue:
            node, d = queue.pop(0)
            if node in visited or d > depth:
                continue
            visited.add(node)
            
            if d > 0 and self.graph.nodes[node].get('node_type') in ('insight', 'concept', 'style', 'brand'):
                concepts.append({
                    "node_id": node,
                    "label": self.graph.nodes[node].get('label', ''),
                    "type": self.graph.nodes[node].get('node_type', ''),
                    "depth": d,
                })
            
            for neighbor in self.graph.neighbors(node):
                if neighbor not in visited:
                    queue.append((neighbor, d + 1))
        
        return concepts
    
    def stats(self) -> Dict:
        """Get memory statistics."""
        return {
            "total_media": self.media_collection.count(),
            "total_projects": self.project_collection.count(),
            "total_insights": self.insight_collection.count(),
            "graph_nodes": self.graph.number_of_nodes(),
            "graph_edges": self.graph.number_of_edges(),
            "memory_path": str(self.persist_dir),
        }
    
    def _persist_graph(self):
        """Save graph to disk."""
        import pickle
        with open(self.persist_dir / "graph.gpickle", 'wb') as f:
            pickle.dump(self.graph, f)
    
    def _persist_projects(self):
        """Save project index."""
        with open(self.persist_dir / "projects.json", 'w') as f:
            json.dump(self.projects, f, indent=2, default=str)
    
    async def close(self):
        """Close connections."""
        self._persist_graph()
        self._persist_projects()
        print("💾 Memory persisted")


# ─── Singleton Access ───

_memory_instance: Optional[CreativeMemoryGraph] = None


def get_memory(persist_dir: str = "./aurora_memory") -> CreativeMemoryGraph:
    """Get or create memory singleton."""
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = CreativeMemoryGraph(persist_dir)
    return _memory_instance