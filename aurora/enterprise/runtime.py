"""
AGENCY OS — CRP Runtime (Layer 4: the chokepoint)

CRP = Creative Resource Planning. See docs/architecture/crp.md for why the
category is named this way and for the CARP / ARP aliases.

The previous three layers are libraries. A library that callers may bypass is
not a control. This module is the single execution path through which every
consequential action must pass, and it is designed so that bypassing it is
harder than using it.

    result = await runtime.execute(intent, handler)

One call performs, in order:
    1. Policy evaluation      (governance)
    2. Approval gate check    (governance)
    3. Budget pre-flight      (aiops)
    4. Handler invocation     (the actual work)
    5. Cost + outcome metering (aiops)
    6. Graph mutation + stage advance (creative)
    7. Audit append           (governance)

Steps 1-3 and 5-7 are not optional and cannot be skipped by a caller who has
only the `execute` method. That is the entire design.
"""
from __future__ import annotations

import asyncio
import inspect
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union

from aurora.enterprise.creative import (
    ActorType, CreativeGraph, CreativeObject, EdgeType, ObjectKind, Stage,
    TransitionError,
)
from aurora.enterprise.aiops import (
    AICall, AIOpsLedger, BudgetExceeded, CallKind, Outcome,
)
from aurora.enterprise.governance import (
    Decision, Effect, GovernanceEngine, PolicyContext,
)


def _id(prefix: str = "rt_") -> str:
    return f"{prefix}{uuid.uuid4().hex[:12]}"


def _now() -> str:
    return datetime.now().isoformat()


# ═══════════════════════════════════════════════════════════════
# Intent — the declared request
# ═══════════════════════════════════════════════════════════════

@dataclass
class Intent:
    """
    A declaration of what is about to happen, made *before* it happens.

    The declaration is what governance adjudicates. If a handler does
    something the intent did not declare, that is a bug in the caller —
    and `Result.declared_vs_actual` exists to surface exactly that.
    """
    org_id: str
    action: str                                  # "asset.publish", "agent.execute"

    actor_id: Optional[str] = None
    actor_type: ActorType = ActorType.HUMAN
    actor_role: Optional[str] = None

    # Graph targets
    object_id: Optional[str] = None
    target_stage: Optional[Stage] = None

    # ERP joins
    client_id: Optional[str] = None
    project_id: Optional[str] = None
    campaign_id: Optional[str] = None

    # Declared risk surface — the caller asserts these; policies test them
    ai_generated: bool = False
    external_facing: bool = False
    contains_pii: bool = False
    contains_client_ip: bool = False
    jurisdiction: Optional[str] = None

    # Declared economics
    model: Optional[str] = None
    estimated_cost_usd: float = 0.0
    call_kind: CallKind = CallKind.COMPLETION
    billable: bool = False

    # Approval already obtained out-of-band (e.g. from a prior turn)
    approval_id: Optional[str] = None

    attributes: Dict[str, Any] = field(default_factory=dict)


class RuntimeState(Enum):
    ALLOWED = "allowed"
    DENIED = "denied"
    AWAITING_APPROVAL = "awaiting_approval"
    BUDGET_BLOCKED = "budget_blocked"
    EXECUTED = "executed"
    FAILED = "failed"


@dataclass
class Result:
    """
    Outcome of a governed execution.

    `state` is authoritative. `value` is only meaningful when
    `state is RuntimeState.EXECUTED`.
    """
    run_id: str
    state: RuntimeState
    action: str
    value: Any = None
    error: Optional[str] = None

    decision: Optional[Decision] = None
    approval_id: Optional[str] = None
    conditions: List[str] = field(default_factory=list)

    call: Optional[AICall] = None
    cost_usd: float = 0.0
    latency_ms: float = 0.0

    object_id: Optional[str] = None
    stage_before: Optional[str] = None
    stage_after: Optional[str] = None

    # Populated when the handler reports usage that contradicts the intent.
    declared_vs_actual: Dict[str, Any] = field(default_factory=dict)

    at: str = field(default_factory=_now)

    @property
    def ok(self) -> bool:
        return self.state is RuntimeState.EXECUTED

    def unwrap(self) -> Any:
        """Return the value or raise. For callers who want fail-fast."""
        if not self.ok:
            raise RuntimeBlocked(self)
        return self.value

    def summary(self) -> str:
        bits = [f"[{self.state.value}] {self.action}"]
        if self.decision and self.decision.explanation:
            bits.append(self.decision.explanation)
        if self.cost_usd:
            bits.append(f"${self.cost_usd:.4f}")
        if self.error:
            bits.append(f"error={self.error}")
        return " | ".join(bits)


class RuntimeBlocked(Exception):
    """Raised by Result.unwrap() when execution did not complete."""

    def __init__(self, result: Result):
        self.result = result
        super().__init__(result.summary())


# ═══════════════════════════════════════════════════════════════
# Handler protocol
# ═══════════════════════════════════════════════════════════════

@dataclass
class Usage:
    """
    What a handler reports back about its own consumption.

    Handlers return `(value, Usage)` or just `value`. Reporting usage is how
    a call becomes billable; a handler that reports nothing is metered at
    zero and flagged in `unmetered_actions()`.
    """
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0
    calls: int = 1
    gpu_seconds: float = 0.0
    model: Optional[str] = None
    tools_called: List[str] = field(default_factory=list)
    outcome: Outcome = Outcome.SUCCESS
    # Handler may correct the intent's risk declarations post-hoc.
    actual_ai_generated: Optional[bool] = None
    actual_external_facing: Optional[bool] = None


Handler = Callable[..., Union[Any, Awaitable[Any]]]


# ═══════════════════════════════════════════════════════════════
# The runtime
# ═══════════════════════════════════════════════════════════════

class CRPRuntime:
    """
    Mandatory execution path binding governance, metering, and the graph.

    Construct once per process, share it. Every agent executor, API route,
    and workflow node calls `execute()` — nothing calls the three subsystems
    directly. `strict_mode` makes that contract enforceable.
    """

    def __init__(
        self,
        graph: Optional[CreativeGraph] = None,
        ledger: Optional[AIOpsLedger] = None,
        governance: Optional[GovernanceEngine] = None,
        persist_dir: str = "./agency_os_data",
        strict_mode: bool = True,
    ):
        self.graph = graph or CreativeGraph(persist_dir)
        self.ledger = ledger or AIOpsLedger(persist_dir)
        self.gov = governance or GovernanceEngine(persist_dir)

        # strict_mode: unknown actions are DENIED rather than allowed by
        # default. Off during development, on in production. An allow-by-
        # default authorization system is not an authorization system.
        self.strict_mode = strict_mode
        self.known_actions: set = set()

        self.runs: List[Result] = []
        self._unmetered: List[str] = []

    # ─── Registration ───

    def register_action(self, *actions: str) -> None:
        """Declare actions the runtime should recognise under strict_mode."""
        self.known_actions.update(actions)

    def bootstrap(self, org_id: str) -> Dict[str, Any]:
        """Install default policies and the standard action vocabulary."""
        count = self.gov.install_defaults(org_id)
        self.register_action(
            "asset.create", "asset.read", "asset.update", "asset.delete",
            "asset.publish", "asset.export", "asset.deliver", "asset.approve",
            "agent.execute", "agent.delegate", "model.finetune", "model.invoke",
            "object.advance", "workflow.execute", "knowledge.write",
        )
        return {"policies": count, "actions": len(self.known_actions)}

    # ─── Preflight ───

    def _to_context(self, intent: Intent) -> PolicyContext:
        obj = self.graph.objects.get(intent.object_id) if intent.object_id else None
        return PolicyContext(
            org_id=intent.org_id,
            action=intent.action,
            actor_id=intent.actor_id,
            actor_type=intent.actor_type.value,
            actor_role=intent.actor_role,
            object_id=intent.object_id,
            object_kind=obj.kind.value if obj else None,
            target_stage=intent.target_stage.value if intent.target_stage else None,
            client_id=intent.client_id or (obj.client_id if obj else None),
            project_id=intent.project_id or (obj.project_id if obj else None),
            ai_generated=intent.ai_generated or (obj.ai_generated if obj else False),
            external_facing=intent.external_facing,
            contains_pii=intent.contains_pii,
            contains_client_ip=intent.contains_client_ip,
            estimated_cost_usd=intent.estimated_cost_usd,
            # Signals are read from the graph, not trusted from the caller —
            # a caller that could assert its own brand_fit could bypass the
            # brand policy simply by lying.
            brand_fit=obj.signal("brand_fit") if obj else None,
            accessibility_score=obj.signal("accessibility") if obj else None,
            jurisdiction=intent.jurisdiction,
            attributes=intent.attributes,
        )

    def preflight(self, intent: Intent) -> Result:
        """
        Adjudicate without executing. Useful for UI affordances ("can I
        click this?") and for agents planning multi-step work.
        """
        run_id = _id()

        if self.strict_mode and self.known_actions and intent.action not in self.known_actions:
            self.gov.audit.append(
                intent.org_id, intent.action, "denied_unknown_action",
                actor_id=intent.actor_id, actor_type=intent.actor_type.value,
                run_id=run_id,
            )
            return Result(
                run_id=run_id, state=RuntimeState.DENIED, action=intent.action,
                error=f"unknown action '{intent.action}' denied under strict_mode",
            )

        ctx = self._to_context(intent)

        # A pre-cleared approval satisfies the gate without re-requesting.
        pre_cleared = self.gov.is_cleared(intent.approval_id)
        decision = self.gov.evaluate(ctx, auto_request_approval=not pre_cleared)

        if decision.effect is Effect.DENY:
            return Result(run_id=run_id, state=RuntimeState.DENIED,
                          action=intent.action, decision=decision,
                          error=decision.explanation)

        if decision.effect is Effect.REQUIRE_APPROVAL and not pre_cleared:
            return Result(run_id=run_id, state=RuntimeState.AWAITING_APPROVAL,
                          action=intent.action, decision=decision,
                          approval_id=decision.approval_id,
                          error="human approval required")

        return Result(
            run_id=run_id, state=RuntimeState.ALLOWED, action=intent.action,
            decision=decision, conditions=list(decision.conditions),
            approval_id=intent.approval_id if pre_cleared else decision.approval_id,
        )

    # ─── Execute ───

    async def execute(
        self,
        intent: Intent,
        handler: Optional[Handler] = None,
        *args,
        **kwargs,
    ) -> Result:
        """
        The chokepoint. Governance -> budget -> work -> meter -> graph -> audit.

        `handler` may be sync or async and may return either `value` or
        `(value, Usage)`. A handler is never invoked if governance blocks.
        """
        gate = self.preflight(intent)
        if gate.state is not RuntimeState.ALLOWED:
            self.runs.append(gate)
            return gate

        run_id = gate.run_id
        obj = self.graph.objects.get(intent.object_id) if intent.object_id else None
        stage_before = obj.stage.value if obj else None

        # ─ Budget preflight: refuse before doing work, not after paying ─
        if intent.model and intent.estimated_cost_usd:
            try:
                self.ledger._check_budgets(
                    AICall(call_id="_preflight", org_id=intent.org_id,
                           model=intent.model, cost_usd=intent.estimated_cost_usd,
                           client_id=intent.client_id, project_id=intent.project_id,
                           agent_id=intent.actor_id)
                )
            except BudgetExceeded as e:
                res = Result(run_id=run_id, state=RuntimeState.BUDGET_BLOCKED,
                             action=intent.action, decision=gate.decision,
                             error=str(e))
                self.gov.audit.append(intent.org_id, intent.action, "budget_blocked",
                                      actor_id=intent.actor_id,
                                      actor_type=intent.actor_type.value,
                                      run_id=run_id, reason=str(e))
                self.runs.append(res)
                return res

        # ─ Do the work ─
        started = time.perf_counter()
        value: Any = None
        usage: Optional[Usage] = None
        error: Optional[str] = None
        outcome = Outcome.SUCCESS

        if handler is not None:
            try:
                out = handler(*args, **kwargs)
                if inspect.isawaitable(out):
                    out = await out
                if isinstance(out, tuple) and len(out) == 2 and isinstance(out[1], Usage):
                    value, usage = out
                else:
                    value = out
                if usage:
                    outcome = usage.outcome
            except asyncio.TimeoutError as e:
                error, outcome = str(e) or "timeout", Outcome.TIMEOUT
            except Exception as e:
                error, outcome = f"{type(e).__name__}: {e}", Outcome.ERROR

        latency_ms = (time.perf_counter() - started) * 1000.0

        # ─ Meter ─
        call: Optional[AICall] = None
        model = (usage.model if usage and usage.model else intent.model)
        if model:
            try:
                call = self.ledger.record(
                    intent.org_id, model, intent.call_kind,
                    enforce_budget=False,          # already pre-flighted
                    agent_id=intent.actor_id if intent.actor_type is ActorType.AGENT else None,
                    user_id=intent.actor_id if intent.actor_type is ActorType.HUMAN else None,
                    client_id=intent.client_id or (obj.client_id if obj else None),
                    project_id=intent.project_id or (obj.project_id if obj else None),
                    campaign_id=intent.campaign_id or (obj.campaign_id if obj else None),
                    object_id=intent.object_id,
                    stage=stage_before,
                    input_tokens=usage.input_tokens if usage else 0,
                    output_tokens=usage.output_tokens if usage else 0,
                    cached_tokens=usage.cached_tokens if usage else 0,
                    calls=usage.calls if usage else 1,
                    gpu_seconds=usage.gpu_seconds if usage else 0.0,
                    latency_ms=latency_ms,
                    billable=intent.billable,
                    outcome=outcome,
                    error=error,
                    tools_called=usage.tools_called if usage else [],
                    trace_id=run_id,
                )
            except BudgetExceeded as e:
                # Work already happened; record it and surface the breach.
                error = error or f"budget breached post-execution: {e}"
        elif handler is not None:
            self._unmetered.append(intent.action)

        # ─ Reconcile declaration against reality ─
        drift: Dict[str, Any] = {}
        if usage:
            if usage.actual_ai_generated is not None and \
                    usage.actual_ai_generated != intent.ai_generated:
                drift["ai_generated"] = {"declared": intent.ai_generated,
                                         "actual": usage.actual_ai_generated}
            if usage.actual_external_facing is not None and \
                    usage.actual_external_facing != intent.external_facing:
                drift["external_facing"] = {"declared": intent.external_facing,
                                            "actual": usage.actual_external_facing}
        if drift:
            # Misdeclaration is a governance event, not a warning to /dev/null.
            self.gov.audit.append(
                intent.org_id, "governance.misdeclaration", "flagged",
                actor_id=intent.actor_id, actor_type=intent.actor_type.value,
                run_id=run_id, object_id=intent.object_id, drift=drift,
            )
            if call:
                self.ledger.annotate(call.call_id, flag="intent_misdeclaration")

        if error:
            res = Result(run_id=run_id, state=RuntimeState.FAILED,
                         action=intent.action, error=error, decision=gate.decision,
                         call=call, cost_usd=call.cost_usd if call else 0.0,
                         latency_ms=latency_ms, object_id=intent.object_id,
                         stage_before=stage_before, stage_after=stage_before,
                         declared_vs_actual=drift)
            self.gov.audit.append(intent.org_id, intent.action, "failed",
                                  actor_id=intent.actor_id,
                                  actor_type=intent.actor_type.value,
                                  run_id=run_id, object_id=intent.object_id,
                                  error=error)
            self.runs.append(res)
            return res

        # ─ Advance the graph ─
        stage_after = stage_before
        if obj is not None:
            if usage and usage.actual_ai_generated:
                obj.ai_generated = True
            if intent.actor_type is ActorType.AGENT:
                obj.ai_assisted = True

            if intent.target_stage is not None:
                try:
                    obj.advance(
                        intent.target_stage,
                        actor_id=intent.actor_id,
                        actor_type=intent.actor_type,
                        reason=f"run:{run_id}",
                        # Gated stages open only because governance said so.
                        allow_gated=self.gov.is_cleared(gate.approval_id),
                    )
                    stage_after = obj.stage.value
                    if gate.approval_id and self.gov.is_cleared(gate.approval_id):
                        approver = self.gov.approvals[gate.approval_id].decided_by
                        if approver and approver in self.graph.actors:
                            self.graph.link(obj.object_id, approver,
                                            EdgeType.APPROVED_BY,
                                            created_by=approver)
                except TransitionError as e:
                    res = Result(run_id=run_id, state=RuntimeState.FAILED,
                                 action=intent.action, error=str(e),
                                 decision=gate.decision, call=call,
                                 cost_usd=call.cost_usd if call else 0.0,
                                 latency_ms=latency_ms, object_id=intent.object_id,
                                 stage_before=stage_before, stage_after=stage_before,
                                 declared_vs_actual=drift)
                    self.gov.audit.append(intent.org_id, intent.action,
                                          "transition_rejected",
                                          actor_id=intent.actor_id,
                                          actor_type=intent.actor_type.value,
                                          run_id=run_id, object_id=intent.object_id,
                                          error=str(e))
                    self.runs.append(res)
                    return res

        # ─ Audit success ─
        self.gov.audit.append(
            intent.org_id, intent.action, "executed",
            actor_id=intent.actor_id, actor_type=intent.actor_type.value,
            run_id=run_id, object_id=intent.object_id,
            stage_before=stage_before, stage_after=stage_after,
            cost_usd=call.cost_usd if call else 0.0,
            conditions=gate.conditions,
        )

        res = Result(
            run_id=run_id, state=RuntimeState.EXECUTED, action=intent.action,
            value=value, decision=gate.decision, approval_id=gate.approval_id,
            conditions=gate.conditions, call=call,
            cost_usd=call.cost_usd if call else 0.0, latency_ms=latency_ms,
            object_id=intent.object_id, stage_before=stage_before,
            stage_after=stage_after, declared_vs_actual=drift,
        )
        self.runs.append(res)
        return res

    # ─── Convenience wrappers (still routed through execute) ───

    async def advance(
        self,
        object_id: str,
        target: Stage,
        actor_id: str,
        actor_type: ActorType = ActorType.HUMAN,
        approval_id: Optional[str] = None,
        **flags,
    ) -> Result:
        obj = self.graph.objects[object_id]
        return await self.execute(Intent(
            org_id=obj.org_id, action="object.advance", actor_id=actor_id,
            actor_type=actor_type, object_id=object_id, target_stage=target,
            approval_id=approval_id, **flags,
        ))

    async def publish(
        self,
        object_id: str,
        actor_id: str,
        actor_type: ActorType = ActorType.HUMAN,
        approval_id: Optional[str] = None,
        external_facing: bool = True,
    ) -> Result:
        obj = self.graph.objects[object_id]
        return await self.execute(Intent(
            org_id=obj.org_id, action="asset.publish", actor_id=actor_id,
            actor_type=actor_type, object_id=object_id,
            ai_generated=obj.ai_generated, external_facing=external_facing,
            approval_id=approval_id,
        ))

    # ─── Health / self-audit ───

    def health(self, org_id: str) -> Dict[str, Any]:
        """
        Whether the control plane is actually functioning.

        `unmetered_actions` and `governance_coverage` exist so that a
        half-wired integration is visible instead of silently degrading
        into the theatre this layer was built to prevent.
        """
        runs = [r for r in self.runs if True]
        executed = [r for r in runs if r.state is RuntimeState.EXECUTED]
        blocked = [r for r in runs if r.state in
                   (RuntimeState.DENIED, RuntimeState.BUDGET_BLOCKED)]
        gated = [r for r in runs if r.state is RuntimeState.AWAITING_APPROVAL]

        return {
            "strict_mode": self.strict_mode,
            "runs": len(runs),
            "executed": len(executed),
            "blocked": len(blocked),
            "awaiting_approval": len(gated),
            "failed": sum(1 for r in runs if r.state is RuntimeState.FAILED),
            "total_cost_usd": round(sum(r.cost_usd for r in runs), 4),
            "misdeclarations": sum(1 for r in runs if r.declared_vs_actual),
            "unmetered_actions": sorted(set(self._unmetered)),
            "governance": self.gov.risk_report(org_id),
            "attribution": self.ledger.attribution_gap(org_id),
            "graph": self.graph.stats(),
            "chain_head": self.gov.audit.head(),
        }

    def save_all(self) -> Dict[str, str]:
        return {
            "graph": str(self.graph.save()),
            "ledger": str(self.ledger.save()),
            "governance": str(self.gov.save()),
        }


# ═══════════════════════════════════════════════════════════════
# Category name aliases
# ═══════════════════════════════════════════════════════════════
#
# The canonical name in code is CRP — Creative Resource Planning.
# ERP already carries "Enterprise", so the earlier "ECRP" doubled it.
#
# Two aliases are supported because different audiences reach for
# different words, and an import that fails on a reasonable guess is a
# papercut with no upside:
#
#   CARPRuntime — Creative Agency Resource Planning. Most literal about
#                 who this serves. Note the collisions before using it in
#                 external material: "to carp" means to complain, and CARP
#                 is also the Common Address Redundancy Protocol.
#   ARPRuntime  — Agency Resource Planning. Phonetically closest to ERP,
#                 but engineers will read ARP as Address Resolution Protocol.
#
# These are the *same class*, not subclasses: isinstance() holds across all
# three names, and there is exactly one implementation to maintain.
#
# ECRPRuntime is retained for backward compatibility with code written
# before the rename.

CARPRuntime = CRPRuntime
ARPRuntime = CRPRuntime
ECRPRuntime = CRPRuntime  # deprecated: redundant "Enterprise" + "Creative"

__all__ = [
    "CRPRuntime", "CARPRuntime", "ARPRuntime", "ECRPRuntime",
    "Intent", "Result", "Usage", "RuntimeState", "RuntimeBlocked",
]
