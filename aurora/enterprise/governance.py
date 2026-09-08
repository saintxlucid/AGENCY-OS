"""
AGENCY OS — Governance Layer (CRP Layer 3)

Governance is the enterprise sale. Intelligence gets the demo; governance
gets the signature. Built as a subsystem every action routes through, not
a reporting view bolted on after the fact.

Three primitives:
  1. PolicyEngine   — deterministic rules evaluated before an action runs.
  2. ApprovalGate   — durable human decisions with expiry and delegation.
  3. AuditChain     — hash-chained, tamper-evident event log.

Deliberately deterministic. An LLM does not decide whether an action is
permitted; it may only propose actions that the engine then adjudicates.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set


def _id(prefix: str = "gv_") -> str:
    return f"{prefix}{uuid.uuid4().hex[:12]}"


def _now() -> str:
    return datetime.now().isoformat()


# ═══════════════════════════════════════════════════════════════
# Policy
# ═══════════════════════════════════════════════════════════════

class Effect(Enum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"
    ALLOW_WITH_CONDITIONS = "allow_with_conditions"


class Severity(Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PolicyContext:
    """Everything the engine is allowed to reason about. No hidden globals."""
    org_id: str
    action: str                              # "asset.publish", "agent.execute", ...
    actor_id: Optional[str] = None
    actor_type: str = "human"                # human | agent | system | client
    actor_role: Optional[str] = None

    object_id: Optional[str] = None
    object_kind: Optional[str] = None
    target_stage: Optional[str] = None

    client_id: Optional[str] = None
    project_id: Optional[str] = None

    # Signals the rules may test against
    ai_generated: bool = False
    external_facing: bool = False
    contains_pii: bool = False
    contains_client_ip: bool = False
    estimated_cost_usd: float = 0.0
    brand_fit: Optional[float] = None
    accessibility_score: Optional[float] = None
    jurisdiction: Optional[str] = None

    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Policy:
    """
    A named rule. `condition` is a pure predicate over PolicyContext.

    Rules are ordered by `priority` descending; the first DENY wins outright,
    otherwise the strictest effect encountered applies. Explicit precedence
    beats implicit ordering.
    """
    policy_id: str
    org_id: str
    name: str
    action_pattern: str                      # "asset.*", "*", "agent.execute"
    effect: Effect
    condition: Optional[Callable[[PolicyContext], bool]] = None
    severity: Severity = Severity.MEDIUM
    priority: int = 100
    rationale: str = ""
    conditions_text: List[str] = field(default_factory=list)
    approver_roles: List[str] = field(default_factory=list)
    enabled: bool = True
    created_at: str = field(default_factory=_now)

    def matches(self, action: str) -> bool:
        """
        Supports '*', prefix globs ('asset.*'), suffix globs ('*.delete'),
        and exact matches. Suffix matching exists because verb-scoped rules
        ('nothing may be deleted by an agent') are the most valuable class
        of policy and must not be written once per resource type.
        """
        p = self.action_pattern
        if p == "*":
            return True
        if p.startswith("*.") and p.endswith(".*") and len(p) > 4:
            return f".{p[2:-2]}." in f".{action}."
        if p.endswith(".*"):
            return action.startswith(p[:-1])
        if p.startswith("*."):
            return action.endswith(p[1:])
        return p == action

    def applies(self, ctx: PolicyContext) -> bool:
        if not self.enabled or not self.matches(ctx.action):
            return False
        if self.condition is None:
            return True
        try:
            return bool(self.condition(ctx))
        except Exception:
            # A broken rule must never silently permit an action.
            return True


@dataclass
class Decision:
    """The adjudicated result. Always explainable — that is the requirement."""
    decision_id: str
    effect: Effect
    action: str
    allowed: bool
    matched_policies: List[Dict[str, Any]] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)
    approval_id: Optional[str] = None
    risk_score: float = 0.0
    explanation: str = ""
    at: str = field(default_factory=_now)


# ─── Built-in baseline policies ───

def default_policies(org_id: str) -> List[Policy]:
    """
    Sane defaults an agency can ship with. Opinionated on purpose:
    every one of these reflects a real way agencies get burned.
    """
    return [
        Policy(
            policy_id=_id("pol_"), org_id=org_id,
            name="Client-facing AI output requires human sign-off",
            action_pattern="asset.publish", effect=Effect.REQUIRE_APPROVAL,
            condition=lambda c: c.ai_generated and c.external_facing,
            severity=Severity.HIGH, priority=900,
            rationale="Unreviewed generative output reaching a client is the "
                      "single most common source of brand and legal incidents.",
            approver_roles=["creative_director", "manager", "admin", "owner"],
        ),
        Policy(
            policy_id=_id("pol_"), org_id=org_id,
            name="Agents may not delete",
            action_pattern="*.delete", effect=Effect.DENY,
            condition=lambda c: c.actor_type == "agent",
            severity=Severity.CRITICAL, priority=1000,
            rationale="Autonomous destruction has no acceptable failure mode.",
        ),
        Policy(
            policy_id=_id("pol_"), org_id=org_id,
            name="PII must not leave the tenant",
            action_pattern="asset.export", effect=Effect.DENY,
            condition=lambda c: c.contains_pii and c.external_facing,
            severity=Severity.CRITICAL, priority=1000,
            rationale="GDPR Art. 5 / 32 — export of personal data outside "
                      "the controlled boundary.",
        ),
        Policy(
            policy_id=_id("pol_"), org_id=org_id,
            name="Client IP may not train models",
            action_pattern="model.finetune", effect=Effect.REQUIRE_APPROVAL,
            condition=lambda c: c.contains_client_ip,
            severity=Severity.CRITICAL, priority=980,
            rationale="Most MSAs prohibit derivative use of client materials; "
                      "requires explicit contractual review.",
            approver_roles=["owner", "admin"],
        ),
        Policy(
            policy_id=_id("pol_"), org_id=org_id,
            name="Expensive runs need approval",
            action_pattern="agent.execute", effect=Effect.REQUIRE_APPROVAL,
            condition=lambda c: c.estimated_cost_usd > 50.0,
            severity=Severity.MEDIUM, priority=500,
            rationale="Runaway agent loops are a cost incident, not a bug.",
            approver_roles=["manager", "admin", "owner"],
        ),
        Policy(
            policy_id=_id("pol_"), org_id=org_id,
            name="Off-brand work cannot ship",
            action_pattern="asset.publish", effect=Effect.REQUIRE_APPROVAL,
            condition=lambda c: c.brand_fit is not None and c.brand_fit < 0.6,
            severity=Severity.MEDIUM, priority=600,
            rationale="Brand drift compounds silently; force a human call.",
            approver_roles=["creative_director", "owner"],
        ),
        Policy(
            policy_id=_id("pol_"), org_id=org_id,
            name="Accessibility floor on public deliverables",
            action_pattern="asset.publish", effect=Effect.ALLOW_WITH_CONDITIONS,
            condition=lambda c: c.external_facing
            and c.accessibility_score is not None and c.accessibility_score < 0.9,
            severity=Severity.MEDIUM, priority=400,
            rationale="WCAG 2.1 AA is contractual for public-sector and most "
                      "enterprise clients.",
            conditions_text=[
                "Attach an accessibility remediation note",
                "Flag for WCAG re-audit within 5 business days",
            ],
        ),
        Policy(
            policy_id=_id("pol_"), org_id=org_id,
            name="AI disclosure on delivered creative",
            action_pattern="asset.deliver", effect=Effect.ALLOW_WITH_CONDITIONS,
            condition=lambda c: c.ai_generated,
            severity=Severity.LOW, priority=300,
            rationale="Disclosure obligations are tightening (EU AI Act "
                      "transparency duties); cheaper to log from day one.",
            conditions_text=["Record AI provenance on the delivery manifest"],
        ),
    ]


# ═══════════════════════════════════════════════════════════════
# Approvals
# ═══════════════════════════════════════════════════════════════

class ApprovalState(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    WITHDRAWN = "withdrawn"


@dataclass
class Approval:
    """A durable human decision. Expiry is mandatory — stale approvals rot."""
    approval_id: str
    org_id: str
    action: str
    requested_by: Optional[str]
    object_id: Optional[str] = None
    reason: str = ""
    policy_ids: List[str] = field(default_factory=list)
    approver_roles: List[str] = field(default_factory=list)
    state: ApprovalState = ApprovalState.PENDING
    decided_by: Optional[str] = None
    decided_at: Optional[str] = None
    decision_note: str = ""
    expires_at: str = field(default_factory=lambda: (datetime.now() + timedelta(days=3)).isoformat())
    created_at: str = field(default_factory=_now)

    @property
    def is_expired(self) -> bool:
        if self.state is not ApprovalState.PENDING:
            return False
        try:
            return datetime.now() > datetime.fromisoformat(self.expires_at)
        except ValueError:
            return False


# ═══════════════════════════════════════════════════════════════
# Audit chain
# ═══════════════════════════════════════════════════════════════

@dataclass
class AuditEvent:
    """One tamper-evident link. `prev_hash` chains to the record before it."""
    event_id: str
    org_id: str
    action: str
    actor_id: Optional[str]
    actor_type: str
    outcome: str
    details: Dict[str, Any] = field(default_factory=dict)
    prev_hash: str = ""
    hash: str = ""
    at: str = field(default_factory=_now)

    def compute_hash(self) -> str:
        payload = json.dumps({
            "event_id": self.event_id, "org_id": self.org_id, "action": self.action,
            "actor_id": self.actor_id, "actor_type": self.actor_type,
            "outcome": self.outcome, "details": self.details,
            "prev_hash": self.prev_hash, "at": self.at,
        }, sort_keys=True, default=str)
        return hashlib.sha256(payload.encode()).hexdigest()


class AuditChain:
    """
    Append-only, hash-chained log.

    Honest scope: this is tamper-*evident*, not tamper-*proof*. Anyone with
    write access to the file can recompute the whole chain. Real immutability
    requires an external anchor (WORM storage, or periodic digest to a
    third-party notary). `head()` exists to be published for that purpose.
    """

    GENESIS = "0" * 64

    def __init__(self):
        self.events: List[AuditEvent] = []

    def append(
        self,
        org_id: str,
        action: str,
        outcome: str,
        actor_id: Optional[str] = None,
        actor_type: str = "human",
        **details,
    ) -> AuditEvent:
        prev = self.events[-1].hash if self.events else self.GENESIS
        ev = AuditEvent(
            event_id=_id("au_"), org_id=org_id, action=action,
            actor_id=actor_id, actor_type=actor_type,
            outcome=outcome, details=details, prev_hash=prev,
        )
        ev.hash = ev.compute_hash()
        self.events.append(ev)
        return ev

    def verify(self) -> Dict[str, Any]:
        """Walk the chain and report the first break, if any."""
        prev = self.GENESIS
        for i, ev in enumerate(self.events):
            if ev.prev_hash != prev:
                return {"valid": False, "broken_at": i, "event_id": ev.event_id,
                        "reason": "prev_hash mismatch"}
            if ev.compute_hash() != ev.hash:
                return {"valid": False, "broken_at": i, "event_id": ev.event_id,
                        "reason": "content hash mismatch"}
            prev = ev.hash
        return {"valid": True, "length": len(self.events), "head": prev}

    def head(self) -> str:
        return self.events[-1].hash if self.events else self.GENESIS

    def for_object(self, object_id: str) -> List[AuditEvent]:
        return [e for e in self.events if e.details.get("object_id") == object_id]


# ═══════════════════════════════════════════════════════════════
# Engine
# ═══════════════════════════════════════════════════════════════

# Effects ranked by strictness. DENY always wins.
_STRICTNESS = {
    Effect.ALLOW: 0,
    Effect.ALLOW_WITH_CONDITIONS: 1,
    Effect.REQUIRE_APPROVAL: 2,
    Effect.DENY: 3,
}

_RISK_WEIGHT = {
    Severity.INFO: 0.0, Severity.LOW: 0.15, Severity.MEDIUM: 0.4,
    Severity.HIGH: 0.7, Severity.CRITICAL: 1.0,
}


class GovernanceEngine:
    """
    Single chokepoint for every consequential action.

    Usage contract: callers ask `evaluate()` *before* acting and honour the
    returned Decision. Nothing here can enforce that on its own — wire it
    into the agent executor and the API layer, or it is theatre.
    """

    def __init__(self, persist_dir: str = "./agency_os_data"):
        self.persist_dir = Path(persist_dir)
        self.policies: Dict[str, Policy] = {}
        self.approvals: Dict[str, Approval] = {}
        self.audit = AuditChain()

    def install_defaults(self, org_id: str) -> int:
        for p in default_policies(org_id):
            self.policies[p.policy_id] = p
        return len(self.policies)

    def add_policy(self, policy: Policy) -> Policy:
        self.policies[policy.policy_id] = policy
        self.audit.append(policy.org_id, "policy.created", "success",
                          actor_type="system", policy_id=policy.policy_id,
                          name=policy.name)
        return policy

    # ─── Evaluation ───

    def evaluate(self, ctx: PolicyContext, auto_request_approval: bool = True) -> Decision:
        candidates = sorted(
            [p for p in self.policies.values()
             if p.org_id == ctx.org_id and p.applies(ctx)],
            key=lambda p: -p.priority,
        )

        effect = Effect.ALLOW
        conditions: List[str] = []
        matched: List[Dict[str, Any]] = []
        risk = 0.0

        for p in candidates:
            matched.append({
                "policy_id": p.policy_id, "name": p.name,
                "effect": p.effect.value, "severity": p.severity.value,
                "rationale": p.rationale,
            })
            risk = max(risk, _RISK_WEIGHT[p.severity])
            if _STRICTNESS[p.effect] > _STRICTNESS[effect]:
                effect = p.effect
            if p.effect is Effect.ALLOW_WITH_CONDITIONS:
                conditions.extend(p.conditions_text)
            if p.effect is Effect.DENY:
                effect = Effect.DENY
                break

        decision = Decision(
            decision_id=_id("dec_"),
            effect=effect,
            action=ctx.action,
            allowed=effect in (Effect.ALLOW, Effect.ALLOW_WITH_CONDITIONS),
            matched_policies=matched,
            conditions=conditions,
            risk_score=round(risk, 2),
            explanation=self._explain(effect, matched, conditions),
        )

        if effect is Effect.REQUIRE_APPROVAL and auto_request_approval:
            approver_roles: Set[str] = set()
            for p in candidates:
                if p.effect is Effect.REQUIRE_APPROVAL:
                    approver_roles.update(p.approver_roles)
            approval = self.request_approval(
                ctx,
                policy_ids=[m["policy_id"] for m in matched
                            if m["effect"] == Effect.REQUIRE_APPROVAL.value],
                approver_roles=sorted(approver_roles),
            )
            decision.approval_id = approval.approval_id

        self.audit.append(
            ctx.org_id, ctx.action, effect.value,
            actor_id=ctx.actor_id, actor_type=ctx.actor_type,
            object_id=ctx.object_id, decision_id=decision.decision_id,
            risk_score=decision.risk_score,
            policies=[m["policy_id"] for m in matched],
        )
        return decision

    def _explain(self, effect: Effect, matched: List[Dict], conditions: List[str]) -> str:
        if not matched:
            return "No policy matched; default allow."
        if effect is Effect.DENY:
            blocker = next(m for m in matched if m["effect"] == "deny")
            return f"Denied by '{blocker['name']}' ({blocker['severity']}). {blocker['rationale']}"
        if effect is Effect.REQUIRE_APPROVAL:
            names = [m["name"] for m in matched if m["effect"] == "require_approval"]
            return f"Human approval required by: {'; '.join(names)}."
        if effect is Effect.ALLOW_WITH_CONDITIONS:
            return f"Allowed with {len(conditions)} condition(s): {'; '.join(conditions)}"
        return f"Allowed. {len(matched)} policy check(s) passed."

    # ─── Approvals ───

    def request_approval(
        self,
        ctx: PolicyContext,
        policy_ids: Optional[List[str]] = None,
        approver_roles: Optional[List[str]] = None,
        ttl_hours: int = 72,
    ) -> Approval:
        a = Approval(
            approval_id=_id("ap_"), org_id=ctx.org_id, action=ctx.action,
            requested_by=ctx.actor_id, object_id=ctx.object_id,
            reason=f"{ctx.action} on {ctx.object_kind or 'object'}",
            policy_ids=policy_ids or [],
            approver_roles=approver_roles or [],
            expires_at=(datetime.now() + timedelta(hours=ttl_hours)).isoformat(),
        )
        self.approvals[a.approval_id] = a
        self.audit.append(ctx.org_id, "approval.requested", "pending",
                          actor_id=ctx.actor_id, actor_type=ctx.actor_type,
                          approval_id=a.approval_id, object_id=ctx.object_id)
        return a

    def decide(
        self,
        approval_id: str,
        approver_id: str,
        approve: bool,
        note: str = "",
        approver_role: Optional[str] = None,
    ) -> Approval:
        a = self.approvals[approval_id]

        if a.is_expired:
            a.state = ApprovalState.EXPIRED
            self.audit.append(a.org_id, "approval.expired", "expired",
                              actor_id=approver_id, approval_id=approval_id)
            raise PermissionError(f"approval {approval_id} expired at {a.expires_at}")

        if a.state is not ApprovalState.PENDING:
            raise PermissionError(f"approval {approval_id} already {a.state.value}")

        if a.approver_roles and approver_role and approver_role not in a.approver_roles:
            self.audit.append(a.org_id, "approval.denied_role", "rejected",
                              actor_id=approver_id, approval_id=approval_id,
                              role=approver_role, required=a.approver_roles)
            raise PermissionError(
                f"role '{approver_role}' cannot approve; requires one of {a.approver_roles}"
            )

        if approver_id == a.requested_by:
            self.audit.append(a.org_id, "approval.self_approval_blocked", "rejected",
                              actor_id=approver_id, approval_id=approval_id)
            raise PermissionError("self-approval is not permitted")

        a.state = ApprovalState.APPROVED if approve else ApprovalState.REJECTED
        a.decided_by = approver_id
        a.decided_at = _now()
        a.decision_note = note
        self.audit.append(a.org_id, "approval.decided", a.state.value,
                          actor_id=approver_id, approval_id=approval_id,
                          object_id=a.object_id, note=note)
        return a

    def is_cleared(self, approval_id: Optional[str]) -> bool:
        """Has a gate actually been opened by a human."""
        if not approval_id:
            return False
        a = self.approvals.get(approval_id)
        return bool(a and a.state is ApprovalState.APPROVED and not a.is_expired)

    def pending(self, org_id: str, role: Optional[str] = None) -> List[Approval]:
        out = []
        for a in self.approvals.values():
            if a.org_id != org_id:
                continue
            if a.is_expired:
                a.state = ApprovalState.EXPIRED
                continue
            if a.state is not ApprovalState.PENDING:
                continue
            if role and a.approver_roles and role not in a.approver_roles:
                continue
            out.append(a)
        return sorted(out, key=lambda x: x.created_at)

    # ─── Reporting ───

    def risk_report(self, org_id: str) -> Dict[str, Any]:
        events = [e for e in self.audit.events if e.org_id == org_id]
        denied = [e for e in events if e.outcome == Effect.DENY.value]
        gated = [e for e in events if e.outcome == Effect.REQUIRE_APPROVAL.value]
        approvals = [a for a in self.approvals.values() if a.org_id == org_id]
        decided = [a for a in approvals if a.state in
                   (ApprovalState.APPROVED, ApprovalState.REJECTED)]

        return {
            "audited_events": len(events),
            "denied": len(denied),
            "approval_gated": len(gated),
            "pending_approvals": len(self.pending(org_id)),
            "expired_approvals": sum(1 for a in approvals if a.state is ApprovalState.EXPIRED),
            "approval_rate": round(
                sum(1 for a in decided if a.state is ApprovalState.APPROVED) / len(decided), 4
            ) if decided else None,
            "avg_risk_score": round(
                sum(e.details.get("risk_score", 0.0) for e in events) / len(events), 3
            ) if events else 0.0,
            "chain": self.audit.verify(),
            "active_policies": sum(1 for p in self.policies.values()
                                   if p.org_id == org_id and p.enabled),
        }

    # ─── Persistence ───

    def save(self, filename: str = "governance.json") -> Path:
        """
        Policies with callable conditions are not serialized — code-defined
        rules live in code. Only their metadata is exported, for audit.
        """
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        path = self.persist_dir / filename
        payload = {
            "policies": [
                {k: v for k, v in asdict(p).items() if k != "condition"}
                | {"effect": p.effect.value, "severity": p.severity.value,
                   "code_defined": p.condition is not None}
                for p in self.policies.values()
            ],
            "approvals": [
                {**asdict(a), "state": a.state.value} for a in self.approvals.values()
            ],
            "audit": [asdict(e) for e in self.audit.events],
            "chain_head": self.audit.head(),
            "saved_at": _now(),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)
        return path
