"""
ASTRA OS — Agency Graph Schema v1 (frozen architecture → buildable types).

Single graph. Typed nodes + edges. Explicit states. No new deps (dataclasses + enums).
ULIDs: ag_<type>_<26-char>. History append-only. Provenance required on Reality writes.
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


def _now() -> str:
    return datetime.now().isoformat()


def new_id(kind: str, org_slug: str = "x") -> str:
    # ULID-ish: timestamp + random, readable in logs. Not strict ULID spec, stable + sortable enough for v1.
    return f"ag_{kind}_{uuid.uuid4().hex[:12]}"


# ─── Node kinds + states (closed enums) ───

class NodeKind(str, Enum):
    CLIENT = "client"
    BRAND = "brand"
    CAMPAIGN = "campaign"
    BRIEF = "brief"
    STRATEGY = "strategy"
    CONCEPT = "concept"
    ASSET = "asset"
    APPROVAL = "approval"
    PUBLICATION = "publication"
    PERFORMANCE = "performance"
    LEARNING = "learning"
    PERSON = "person"
    PROPOSAL = "proposal"
    SCOPE = "scope"
    INVOICE = "invoice"
    TASK = "task"
    MILESTONE = "milestone"
    BLOCKER = "blocker"
    REQUEST = "request"
    MEETING = "meeting"


STATES: Dict[str, List[str]] = {
    "client": ["prospect", "active", "paused", "churned"],
    "brand": ["draft", "active", "archived"],
    "campaign": ["pitched", "scoped", "active", "in_review", "completed", "killed"],
    "brief": ["draft", "submitted", "clarified", "approved", "superseded"],
    "strategy": ["draft", "proposed", "selected", "rejected"],
    "concept": ["draft", "in_critique", "revised", "approved_for_production", "killed"],
    "asset": ["wip", "in_qc", "qc_passed", "approved", "qc_failed"],
    "approval": ["requested", "pending", "decided"],
    "publication": ["scheduled", "published", "taken_down"],
    "performance": ["collecting", "reported", "learned_from"],
    "learning": ["draft", "validated", "embedded"],
    "task": ["todo", "doing", "blocked", "done"],
}

# Legal transitions (from → to). Anything else = rejected with code.
TRANSITIONS: Dict[str, List[tuple]] = {
    "client": [("prospect", "active"), ("active", "paused"), ("paused", "active"),
               ("active", "churned"), ("paused", "churned")],
    "brief": [("draft", "submitted"), ("submitted", "clarified"), ("clarified", "submitted"),
              ("clarified", "approved"), ("submitted", "approved"), ("approved", "superseded")],
    "strategy": [("draft", "proposed"), ("proposed", "selected"), ("proposed", "rejected")],
    "concept": [("draft", "in_critique"), ("in_critique", "revised"), ("revised", "in_critique"),
                ("revised", "approved_for_production"), ("in_critique", "approved_for_production"),
                ("draft", "killed"), ("in_critique", "killed"), ("revised", "killed")],
    "asset": [("wip", "in_qc"), ("in_qc", "qc_passed"), ("in_qc", "qc_failed"),
              ("qc_failed", "wip"), ("qc_passed", "approved")],
    "approval": [("requested", "pending"), ("pending", "decided")],
    "publication": [("scheduled", "published"), ("published", "taken_down")],
    "performance": [("collecting", "reported"), ("reported", "learned_from")],
    "learning": [("draft", "validated"), ("validated", "embedded")],
    "task": [("todo", "doing"), ("doing", "blocked"), ("blocked", "doing"),
             ("doing", "done"), ("todo", "done")],
}


def can_transition(kind: str, frm: str, to: str) -> bool:
    return (frm, to) in TRANSITIONS.get(kind, [])


class EdgeKind(str, Enum):
    OWNS = "owns"
    HAS = "has"
    ISSUES = "issues"
    GROUNDS = "grounds"
    SELECTS = "selects"
    YIELDS = "yields"
    REALIZES = "realizes"
    REQUIRES = "requires"
    AUTHORIZES = "authorizes"
    MEASURES = "measures"
    DISTILLS = "distills"
    EMBEDS_IN = "embeds_in"
    INFORMS = "informs"
    SUPERSEDES = "supersedes"
    SUPERSEDED_BY = "superseded_by"
    REJECTS = "rejects"
    GOVERNED_BY = "governed_by"
    BLOCKED_BY = "blocked_by"
    DELIVERS = "delivers"
    TRIGGERS = "triggers"
    CONTAINS = "contains"
    REFERENCES = "references"


@dataclass
class AgencyNode:
    id: str
    kind: str  # NodeKind value
    org_id: str
    state: str
    owner_role: str = ""
    owner_user_id: str = ""
    version: int = 1
    parent_id: str = ""
    evidence_ids: List[str] = field(default_factory=list)
    created_by: str = ""
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    properties: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        errs = []
        if not self.id or not self.id.startswith("ag_"):
            errs.append("id must be ag_<kind>_<id>")
        if self.kind not in [k.value for k in NodeKind]:
            errs.append(f"unknown kind {self.kind}")
        allowed = STATES.get(self.kind, [])
        if allowed and self.state not in allowed:
            errs.append(f"state {self.state} not in {allowed}")
        if not self.org_id:
            errs.append("org_id required")
        if self.kind in ("brief", "strategy", "concept", "asset", "campaign") and not (
            self.owner_role or self.owner_user_id
        ):
            errs.append("owner required")
        return errs


@dataclass
class AgencyEdge:
    source_id: str
    target_id: str
    kind: str  # EdgeKind value
    actor: str = ""
    rationale: str = ""
    timestamp: str = field(default_factory=_now)
    properties: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        errs = []
        if not self.source_id or not self.target_id:
            errs.append("source/target required")
        if self.kind not in [k.value for k in EdgeKind]:
            errs.append(f"unknown edge {self.kind}")
        return errs


@dataclass
class HistoryEvent:
    event_id: str
    subject_id: str
    actor: str
    action: str
    before: Dict[str, Any] = field(default_factory=dict)
    after: Dict[str, Any] = field(default_factory=dict)
    rationale: str = ""
    timestamp: str = field(default_factory=_now)


# ─── Invariants (v1, enforce at write path + pre-flight) ───
# - Campaign needs active Client (checked by caller with client_state).
# - Strategy needs approved Brief (brief_state == approved).
# - Publication needs exact-version approved Approval (approval_decision == approved, versions match, not expired).
# - Performance needs publication_id. Learning needs performance + approval evidence.
