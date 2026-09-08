"""
AGENCY OS — Creative Object Model (CRP Layer 1)

Traditional ERP stores rows. This stores a graph.

A CreativeObject is any node in the creative economy: an idea, a brief,
a moodboard, a design file, a cut, a track, a review, a result. Objects
are connected by typed, directed edges carrying provenance. The graph —
not the module list — is the defensible asset.

Deliberately dependency-free (stdlib only) so it can be embedded, tested,
and serialized without ChromaDB / NetworkX. The semantic layer in
aurora/memory/graph.py projects onto this model, it does not replace it.
"""
from __future__ import annotations

import json
import uuid
from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple


def _id(prefix: str = "co_") -> str:
    return f"{prefix}{uuid.uuid4().hex[:12]}"


def _now() -> str:
    return datetime.now().isoformat()


# ═══════════════════════════════════════════════════════════════
# Object taxonomy
# ═══════════════════════════════════════════════════════════════

class ObjectKind(Enum):
    """What a creative object *is*. Kinds are stable; stages move."""
    IDEA = "idea"
    RESEARCH = "research"
    STRATEGY = "strategy"
    BRIEF = "brief"
    PERSONA = "persona"
    COMPETITOR = "competitor"
    MOODBOARD = "moodboard"
    CONCEPT = "concept"
    SCRIPT = "script"
    STORYBOARD = "storyboard"
    DESIGN = "design"
    ARTWORK = "artwork"
    VIDEO = "video"
    AUDIO = "audio"
    MUSIC = "music"
    VOICEOVER = "voiceover"
    THREE_D = "3d"
    COPY = "copy"
    DELIVERABLE = "deliverable"
    REVIEW = "review"
    RESULT = "result"
    LEARNING = "learning"
    BRAND_DNA = "brand_dna"
    DESIGN_SYSTEM = "design_system"
    CAMPAIGN = "campaign"


class EdgeType(Enum):
    """Typed relationships. Direction matters: source -> target."""
    PART_OF = "part_of"              # asset -> campaign
    DERIVED_FROM = "derived_from"    # v2 -> v1
    VERSION_OF = "version_of"        # variant -> canonical
    REFERENCES = "references"        # design -> moodboard
    INSPIRED_BY = "inspired_by"      # concept -> prior campaign
    RESPONDS_TO = "responds_to"      # revision -> review
    FULFILLS = "fulfills"            # deliverable -> brief
    MEASURES = "measures"            # result -> deliverable
    PRODUCED_BY = "produced_by"      # object -> actor (human or agent)
    APPROVED_BY = "approved_by"      # object -> actor
    GOVERNED_BY = "governed_by"      # object -> policy / brand DNA
    SIMILAR_TO = "similar_to"        # semantic, usually machine-inferred
    TEACHES = "teaches"              # learning -> future objects


class ActorType(Enum):
    HUMAN = "human"
    AGENT = "agent"
    SYSTEM = "system"
    CLIENT = "client"
    VENDOR = "vendor"


# ═══════════════════════════════════════════════════════════════
# Lifecycle state machine
# ═══════════════════════════════════════════════════════════════

class Stage(Enum):
    """The creative supply chain. Every object walks this path."""
    IDEA = "idea"
    RESEARCH = "research"
    STRATEGY = "strategy"
    BRIEF = "brief"
    MOODBOARD = "moodboard"
    CONCEPT = "concept"
    DESIGN = "design"
    REVIEW = "review"
    REVISION = "revision"
    APPROVAL = "approval"
    PRODUCTION = "production"
    DELIVERY = "delivery"
    ANALYTICS = "analytics"
    LEARNING = "learning"
    ARCHIVED = "archived"
    KILLED = "killed"


# Allowed transitions. Anything not listed is rejected — this is what makes
# the pipeline observable instead of a free-text `status` column.
TRANSITIONS: Dict[Stage, Set[Stage]] = {
    Stage.IDEA:       {Stage.RESEARCH, Stage.STRATEGY, Stage.BRIEF, Stage.KILLED},
    Stage.RESEARCH:   {Stage.STRATEGY, Stage.BRIEF, Stage.KILLED},
    Stage.STRATEGY:   {Stage.BRIEF, Stage.RESEARCH, Stage.KILLED},
    Stage.BRIEF:      {Stage.MOODBOARD, Stage.CONCEPT, Stage.STRATEGY, Stage.KILLED},
    Stage.MOODBOARD:  {Stage.CONCEPT, Stage.BRIEF, Stage.KILLED},
    Stage.CONCEPT:    {Stage.DESIGN, Stage.MOODBOARD, Stage.REVIEW, Stage.KILLED},
    Stage.DESIGN:     {Stage.REVIEW, Stage.CONCEPT, Stage.KILLED},
    Stage.REVIEW:     {Stage.REVISION, Stage.APPROVAL, Stage.KILLED},
    Stage.REVISION:   {Stage.REVIEW, Stage.DESIGN, Stage.KILLED},
    Stage.APPROVAL:   {Stage.PRODUCTION, Stage.REVISION, Stage.KILLED},
    Stage.PRODUCTION: {Stage.DELIVERY, Stage.REVIEW, Stage.KILLED},
    Stage.DELIVERY:   {Stage.ANALYTICS, Stage.ARCHIVED},
    Stage.ANALYTICS:  {Stage.LEARNING, Stage.ARCHIVED},
    Stage.LEARNING:   {Stage.ARCHIVED},
    Stage.ARCHIVED:   set(),
    Stage.KILLED:     set(),
}

# Stages that must not be entered without an explicit human decision.
GATED_STAGES: Set[Stage] = {Stage.APPROVAL, Stage.PRODUCTION, Stage.DELIVERY}


class TransitionError(Exception):
    """Raised when a stage move violates the lifecycle."""


@dataclass
class StageEvent:
    """One hop in the supply chain. The unit of process observability."""
    event_id: str
    object_id: str
    from_stage: Optional[str]
    to_stage: str
    actor_id: Optional[str] = None
    actor_type: str = ActorType.HUMAN.value
    reason: Optional[str] = None
    at: str = field(default_factory=_now)

    # Set when the transition closes out a previous stage.
    duration_seconds: Optional[float] = None


# ═══════════════════════════════════════════════════════════════
# Core node + edge
# ═══════════════════════════════════════════════════════════════

@dataclass
class CreativeObject:
    """
    A first-class creative entity.

    Note what is NOT here: no `quality_score` float pretending to be truth.
    Quality is expressed as `signals` — named, sourced, and dated — so the
    provenance of every judgement survives.
    """
    object_id: str
    org_id: str
    kind: ObjectKind
    title: str

    stage: Stage = Stage.IDEA
    summary: Optional[str] = None

    # Business anchors — the join keys back into the classic ERP tables.
    client_id: Optional[str] = None
    project_id: Optional[str] = None
    campaign_id: Optional[str] = None
    brief_id: Optional[str] = None

    # Where the bytes live, if this object has any.
    uri: Optional[str] = None
    mime_type: Optional[str] = None
    checksum: Optional[str] = None
    bytes_size: int = 0

    # Versioning
    version: int = 1
    parent_id: Optional[str] = None
    is_canonical: bool = True

    # Judgements: {"brand_fit": {"value": 0.82, "source": "agent:qa", "at": ...}}
    signals: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Free-form creative metadata (palette, tempo, aspect ratio, etc.)
    attributes: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    # Provenance
    created_by: Optional[str] = None
    created_by_type: str = ActorType.HUMAN.value
    ai_generated: bool = False
    ai_assisted: bool = False

    history: List[StageEvent] = field(default_factory=list)
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)

    # ─── Signals ───

    def set_signal(self, name: str, value: Any, source: str, confidence: float = 1.0) -> None:
        """Record a judgement with its provenance. Never overwrite silently."""
        prior = self.signals.get(name)
        self.signals[name] = {
            "value": value,
            "source": source,
            "confidence": confidence,
            "at": _now(),
            "previous": prior.get("value") if prior else None,
        }
        self.updated_at = _now()

    def signal(self, name: str, default: Any = None) -> Any:
        entry = self.signals.get(name)
        return entry["value"] if entry else default

    # ─── Lifecycle ───

    def can_advance_to(self, target: Stage) -> bool:
        return target in TRANSITIONS.get(self.stage, set())

    def advance(
        self,
        target: Stage,
        actor_id: Optional[str] = None,
        actor_type: ActorType = ActorType.HUMAN,
        reason: Optional[str] = None,
        allow_gated: bool = False,
    ) -> StageEvent:
        """
        Move the object along the supply chain.

        Gated stages refuse automatic entry unless `allow_gated` is passed by a
        caller that has already cleared a human approval. The governance layer
        is the intended caller.
        """
        if not self.can_advance_to(target):
            raise TransitionError(
                f"{self.object_id}: {self.stage.value} -> {target.value} is not a legal transition"
            )
        if target in GATED_STAGES and actor_type is ActorType.AGENT and not allow_gated:
            raise TransitionError(
                f"{self.object_id}: stage '{target.value}' requires human approval; "
                f"agent '{actor_id}' cannot self-advance"
            )

        previous = self.history[-1] if self.history else None
        duration = None
        if previous:
            try:
                duration = (
                    datetime.fromisoformat(_now()) - datetime.fromisoformat(previous.at)
                ).total_seconds()
            except ValueError:
                duration = None

        event = StageEvent(
            event_id=_id("ev_"),
            object_id=self.object_id,
            from_stage=self.stage.value,
            to_stage=target.value,
            actor_id=actor_id,
            actor_type=actor_type.value,
            reason=reason,
            duration_seconds=duration,
        )
        self.stage = target
        self.history.append(event)
        self.updated_at = _now()
        return event

    # ─── Metrics ───

    def time_in_stage(self, stage: Stage) -> float:
        """Total seconds this object has spent in a given stage historically."""
        total = 0.0
        for i, ev in enumerate(self.history):
            if ev.from_stage == stage.value and ev.duration_seconds:
                total += ev.duration_seconds
        return total

    def revision_count(self) -> int:
        return sum(1 for ev in self.history if ev.to_stage == Stage.REVISION.value)

    def touched_by(self) -> Set[str]:
        return {ev.actor_id for ev in self.history if ev.actor_id}

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["kind"] = self.kind.value
        d["stage"] = self.stage.value
        return d


@dataclass
class CreativeEdge:
    """A typed, weighted, provenance-carrying relationship."""
    edge_id: str
    source_id: str
    target_id: str
    edge_type: EdgeType
    weight: float = 1.0
    inferred: bool = False          # True if machine-derived, not asserted
    confidence: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)
    created_by: Optional[str] = None
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["edge_type"] = self.edge_type.value
        return d


@dataclass
class Actor:
    """A human, agent, client, or system that can act on creative objects."""
    actor_id: str
    org_id: str
    name: str
    actor_type: ActorType = ActorType.HUMAN
    employee_id: Optional[str] = None   # join to erp.Employee
    model: Optional[str] = None         # for agents
    capabilities: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now)


# ═══════════════════════════════════════════════════════════════
# The graph
# ═══════════════════════════════════════════════════════════════

class CreativeGraph:
    """
    In-memory creative object graph with adjacency indexes.

    Scope note: this is the reference implementation and the schema of record.
    A production deployment backs it with Postgres + pgvector or Neo4j; the
    public method surface is designed to survive that swap unchanged.
    """

    def __init__(self, persist_dir: str = "./agency_os_data"):
        self.persist_dir = Path(persist_dir)
        self.objects: Dict[str, CreativeObject] = {}
        self.edges: Dict[str, CreativeEdge] = {}
        self.actors: Dict[str, Actor] = {}

        self._out: Dict[str, Set[str]] = {}   # object_id -> edge_ids
        self._in: Dict[str, Set[str]] = {}    # object_id -> edge_ids

    # ─── Mutation ───

    def add_object(self, obj: CreativeObject) -> CreativeObject:
        self.objects[obj.object_id] = obj
        self._out.setdefault(obj.object_id, set())
        self._in.setdefault(obj.object_id, set())
        return obj

    def create_object(self, org_id: str, kind: ObjectKind, title: str, **kwargs) -> CreativeObject:
        obj = CreativeObject(object_id=_id(), org_id=org_id, kind=kind, title=title, **kwargs)
        return self.add_object(obj)

    def link(
        self,
        source_id: str,
        target_id: str,
        edge_type: EdgeType,
        weight: float = 1.0,
        inferred: bool = False,
        confidence: float = 1.0,
        created_by: Optional[str] = None,
        **properties,
    ) -> CreativeEdge:
        if source_id not in self.objects and source_id not in self.actors:
            raise KeyError(f"unknown source node: {source_id}")
        if target_id not in self.objects and target_id not in self.actors:
            raise KeyError(f"unknown target node: {target_id}")

        edge = CreativeEdge(
            edge_id=_id("e_"),
            source_id=source_id,
            target_id=target_id,
            edge_type=edge_type,
            weight=weight,
            inferred=inferred,
            confidence=confidence,
            created_by=created_by,
            properties=properties,
        )
        self.edges[edge.edge_id] = edge
        self._out.setdefault(source_id, set()).add(edge.edge_id)
        self._in.setdefault(target_id, set()).add(edge.edge_id)
        return edge

    def add_actor(self, actor: Actor) -> Actor:
        self.actors[actor.actor_id] = actor
        self._out.setdefault(actor.actor_id, set())
        self._in.setdefault(actor.actor_id, set())
        return actor

    def new_version(
        self,
        object_id: str,
        actor_id: Optional[str] = None,
        **overrides,
    ) -> CreativeObject:
        """Fork a new canonical version, wiring DERIVED_FROM provenance."""
        parent = self.objects[object_id]
        child = CreativeObject(
            object_id=_id(),
            org_id=parent.org_id,
            kind=parent.kind,
            title=overrides.pop("title", parent.title),
            stage=parent.stage,
            client_id=parent.client_id,
            project_id=parent.project_id,
            campaign_id=parent.campaign_id,
            brief_id=parent.brief_id,
            version=parent.version + 1,
            parent_id=parent.object_id,
            attributes=dict(parent.attributes),
            tags=list(parent.tags),
            created_by=actor_id,
            # AI involvement is inherited: a human edit on top of generated
            # work is still AI-assisted output for disclosure purposes.
            ai_generated=overrides.pop("ai_generated", parent.ai_generated),
            ai_assisted=overrides.pop("ai_assisted", parent.ai_assisted or parent.ai_generated),
            **overrides,
        )
        parent.is_canonical = False
        self.add_object(child)
        self.link(child.object_id, parent.object_id, EdgeType.DERIVED_FROM, created_by=actor_id)
        return child

    # ─── Traversal ───

    def neighbors(
        self,
        object_id: str,
        edge_type: Optional[EdgeType] = None,
        direction: str = "out",
    ) -> List[Tuple[CreativeEdge, str]]:
        """Return (edge, other_node_id) pairs. direction: out | in | both."""
        pairs: List[Tuple[CreativeEdge, str]] = []
        if direction in ("out", "both"):
            for eid in self._out.get(object_id, set()):
                e = self.edges[eid]
                if edge_type is None or e.edge_type is edge_type:
                    pairs.append((e, e.target_id))
        if direction in ("in", "both"):
            for eid in self._in.get(object_id, set()):
                e = self.edges[eid]
                if edge_type is None or e.edge_type is edge_type:
                    pairs.append((e, e.source_id))
        return pairs

    def traverse(
        self,
        start_id: str,
        max_depth: int = 3,
        edge_types: Optional[Iterable[EdgeType]] = None,
        direction: str = "both",
    ) -> List[Tuple[str, int]]:
        """Breadth-first walk. Returns (node_id, depth), excluding the start."""
        allowed = set(edge_types) if edge_types else None
        seen: Set[str] = {start_id}
        out: List[Tuple[str, int]] = []
        q: deque = deque([(start_id, 0)])

        while q:
            node, depth = q.popleft()
            if depth >= max_depth:
                continue
            for edge, other in self.neighbors(node, direction=direction):
                if allowed and edge.edge_type not in allowed:
                    continue
                if other in seen:
                    continue
                seen.add(other)
                out.append((other, depth + 1))
                q.append((other, depth + 1))
        return out

    def lineage(self, object_id: str) -> List[CreativeObject]:
        """Full ancestry chain via DERIVED_FROM, oldest first."""
        chain: List[CreativeObject] = []
        cursor = self.objects.get(object_id)
        guard = 0
        while cursor and guard < 1000:
            chain.append(cursor)
            cursor = self.objects.get(cursor.parent_id) if cursor.parent_id else None
            guard += 1
        return list(reversed(chain))

    def provenance(self, object_id: str) -> Dict[str, Any]:
        """
        Answer 'where did this come from and who touched it'.
        This is the query an enterprise legal team actually asks.
        """
        obj = self.objects[object_id]
        chain = self.lineage(object_id)
        refs = [t for _, t in self.neighbors(object_id, EdgeType.REFERENCES)]
        inspiration = [t for _, t in self.neighbors(object_id, EdgeType.INSPIRED_BY)]

        # Provenance must span the whole ancestry: a v3 approved by one person
        # still inherits everyone who shaped v1 and v2. Asking "who touched
        # this" and getting only the last fork's actors is a liability.
        actors: Set[str] = set()
        for ancestor in chain:
            actors.update(ancestor.touched_by())
            if ancestor.created_by:
                actors.add(ancestor.created_by)
            for _, t in self.neighbors(ancestor.object_id, EdgeType.PRODUCED_BY):
                actors.add(t)
            for _, t in self.neighbors(ancestor.object_id, EdgeType.APPROVED_BY):
                actors.add(t)

        return {
            "object_id": object_id,
            "title": obj.title,
            "version": obj.version,
            "ai_generated": obj.ai_generated,
            "ai_assisted": obj.ai_assisted,
            "lineage": [{"id": o.object_id, "version": o.version, "title": o.title} for o in chain],
            "references": refs,
            "inspired_by": inspiration,
            "actors": sorted(actors),
            "stage_events": len(obj.history),
            "revisions": obj.revision_count(),
        }

    # ─── Queries ───

    def by_kind(self, org_id: str, kind: ObjectKind) -> List[CreativeObject]:
        return [o for o in self.objects.values() if o.org_id == org_id and o.kind is kind]

    def by_stage(self, org_id: str, stage: Stage) -> List[CreativeObject]:
        return [o for o in self.objects.values() if o.org_id == org_id and o.stage is stage]

    def campaign_tree(self, campaign_id: str) -> List[CreativeObject]:
        return [o for o in self.objects.values() if o.campaign_id == campaign_id]

    def stalled(self, org_id: str, threshold_seconds: float = 172800) -> List[CreativeObject]:
        """Objects sitting in one stage past threshold (default 48h)."""
        now = datetime.now()
        out = []
        for o in self.objects.values():
            if o.org_id != org_id or o.stage in (Stage.ARCHIVED, Stage.KILLED):
                continue
            marker = o.history[-1].at if o.history else o.created_at
            try:
                age = (now - datetime.fromisoformat(marker)).total_seconds()
            except ValueError:
                continue
            if age > threshold_seconds:
                out.append(o)
        return out

    def bottlenecks(self, org_id: str) -> Dict[str, Dict[str, float]]:
        """
        Mean dwell time per stage. This is the number that makes the
        'observable, measurable, improvable' claim actually true.
        """
        buckets: Dict[str, List[float]] = {}
        for o in self.objects.values():
            if o.org_id != org_id:
                continue
            for ev in o.history:
                if ev.from_stage and ev.duration_seconds is not None:
                    buckets.setdefault(ev.from_stage, []).append(ev.duration_seconds)
        return {
            stage: {
                "mean_seconds": sum(v) / len(v),
                "max_seconds": max(v),
                "samples": len(v),
            }
            for stage, v in buckets.items() if v
        }

    def funnel(self, org_id: str) -> Dict[str, int]:
        counts = {s.value: 0 for s in Stage}
        for o in self.objects.values():
            if o.org_id == org_id:
                counts[o.stage.value] += 1
        return counts

    def ai_attribution(self, org_id: str) -> Dict[str, Any]:
        """
        What share of shipped creative was machine-made.
        Needed for client disclosure, insurance, and pricing conversations.
        """
        scoped = [o for o in self.objects.values() if o.org_id == org_id]
        shipped = [o for o in scoped if o.stage in (Stage.DELIVERY, Stage.ANALYTICS,
                                                    Stage.LEARNING, Stage.ARCHIVED)]
        total = len(shipped) or 1
        return {
            "total_objects": len(scoped),
            "shipped": len(shipped),
            "ai_generated": sum(1 for o in shipped if o.ai_generated),
            "ai_assisted": sum(1 for o in shipped if o.ai_assisted),
            "human_only": sum(1 for o in shipped if not o.ai_generated and not o.ai_assisted),
            "ai_generated_share": sum(1 for o in shipped if o.ai_generated) / total,
        }

    # ─── Persistence ───

    def save(self, filename: str = "creative_graph.json") -> Path:
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        path = self.persist_dir / filename
        payload = {
            "objects": {k: v.to_dict() for k, v in self.objects.items()},
            "edges": {k: v.to_dict() for k, v in self.edges.items()},
            "actors": {
                k: {**asdict(v), "actor_type": v.actor_type.value}
                for k, v in self.actors.items()
            },
            "saved_at": _now(),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)
        return path

    def load(self, filename: str = "creative_graph.json") -> None:
        path = self.persist_dir / filename
        if not path.exists():
            return
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        for k, v in data.get("actors", {}).items():
            v["actor_type"] = ActorType(v["actor_type"])
            self.add_actor(Actor(**v))

        for k, v in data.get("objects", {}).items():
            v["kind"] = ObjectKind(v["kind"])
            v["stage"] = Stage(v["stage"])
            v["history"] = [StageEvent(**h) for h in v.get("history", [])]
            self.add_object(CreativeObject(**v))

        for k, v in data.get("edges", {}).items():
            v["edge_type"] = EdgeType(v["edge_type"])
            edge = CreativeEdge(**v)
            self.edges[edge.edge_id] = edge
            self._out.setdefault(edge.source_id, set()).add(edge.edge_id)
            self._in.setdefault(edge.target_id, set()).add(edge.edge_id)

    def stats(self) -> Dict[str, Any]:
        kinds: Dict[str, int] = {}
        for o in self.objects.values():
            kinds[o.kind.value] = kinds.get(o.kind.value, 0) + 1
        edge_kinds: Dict[str, int] = {}
        for e in self.edges.values():
            edge_kinds[e.edge_type.value] = edge_kinds.get(e.edge_type.value, 0) + 1
        return {
            "objects": len(self.objects),
            "edges": len(self.edges),
            "actors": len(self.actors),
            "inferred_edges": sum(1 for e in self.edges.values() if e.inferred),
            "by_kind": kinds,
            "by_edge_type": edge_kinds,
        }
