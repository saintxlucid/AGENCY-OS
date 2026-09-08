"""
ASTRA OS — Canonical message envelopes (frozen shapes from proving-slice.md).

All envelopes carry traceability. No ambient autonomy: every Action needs
idempotency + actor + preflight. Every Proposal needs evidence.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


def _now() -> str:
    return datetime.now().isoformat()


def _mid(prefix: str) -> str:
    return f"{prefix}{uuid.uuid4().hex[:12]}"


@dataclass
class Envelope:
    msg_id: str
    trace_id: str
    org_id: str
    actor_type: str  # human | agent | tool | system
    actor_id: str
    timestamp: str = field(default_factory=_now)
    idempotency_key: str = ""


@dataclass
class Action(Envelope):
    intent: str = ""  # publish.asset | transition.state | create.task | spend.commit ...
    subject_type: str = ""
    subject_id: str = ""
    subject_version: int = 1
    payload: Dict[str, Any] = field(default_factory=dict)
    approval_ref: str = ""
    evidence_ids: List[str] = field(default_factory=list)


@dataclass
class Proposal(Envelope):
    subject_id: str = ""
    kind: str = ""  # territory_set | concept_eval | learning | plan
    recommendation: str = ""
    rationale: str = ""
    confidence: float = 0.0
    evidence_ids: List[str] = field(default_factory=list)
    alternatives: List[Dict[str, str]] = field(default_factory=list)
    verification_required: str = ""
    owner_role: str = ""
    measurable_outcome: str = ""


@dataclass
class Observation(Envelope):
    subject_id: str = ""
    kind: str = ""  # state_transition | version_created | receipt | gap_detected | divergence
    before: Dict[str, Any] = field(default_factory=dict)
    after: Dict[str, Any] = field(default_factory=dict)
    source: str = ""
    content_hash: str = ""


@dataclass
class ApprovalRequest(Envelope):
    subject_type: str = ""
    subject_id: str = ""
    subject_version: int = 1
    approver_role: str = ""
    proposal_id: str = ""
    evidence_ids: List[str] = field(default_factory=list)
    diff_summary: str = ""
    expires_at: str = ""


@dataclass
class ApprovalDecision(Envelope):
    approval_id: str = ""
    decision: str = ""  # approved | rejected | changes_requested
    approver_user_id: str = ""
    rationale: str = ""
    conditions: List[str] = field(default_factory=list)


@dataclass
class PlanStep:
    step_id: str
    op: str
    owner: str
    verifies: str = ""
    needs_approval: str = ""


@dataclass
class Plan(Envelope):
    plan_id: str = ""
    goal: str = ""
    steps: List[PlanStep] = field(default_factory=list)
    deps: List[List[str]] = field(default_factory=list)
    max_workers: int = 3
    timeout_min: int = 30


@dataclass
class Receipt(Envelope):
    receipt_id: str = ""
    action_id: str = ""
    result_ref: str = ""
    status: str = ""  # ok | failed
    detail: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LearningProposal(Envelope):
    learning_id: str = ""
    campaign_id: str = ""
    finding: str = ""
    evidence_ids: List[str] = field(default_factory=list)
    applicability: Dict[str, List[str]] = field(default_factory=dict)
    confidence: float = 0.0
    validator_required: bool = True
