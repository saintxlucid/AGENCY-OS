"""
ALPHA 03 — OPERATOR. The Hands.
Plans, routes, executes approved work with pre-flight + receipts. Fail-closed.
Caps: max 8 workers, 3 retries, 30min plan without checkpoint (v1 constants).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

MAX_WORKERS = 8
MAX_RETRIES = 3

from aurora.agency.sovereign import Sovereign


@dataclass
class PlanStep:
    step_id: str
    op: str
    owner: str
    verifies: str = ""
    needs_approval: str = ""


@dataclass
class ExecutionReceipt:
    receipt_id: str
    action_id: str
    result_ref: str
    status: str  # ok | failed | blocked
    detail: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Blocker:
    blocker_id: str
    subject_id: str
    reason: str
    code: str
    age_hours: float = 0.0


class Operator:
    def __init__(self, sovereign: Sovereign | None = None):
        self.sovereign = sovereign or Sovereign()
        self.receipts: List[ExecutionReceipt] = []
        self.blockers: List[Blocker] = []
        self._n = 0

    def build_plan(self, goal: str, steps: List[PlanStep]) -> Dict[str, Any]:
        if len(steps) > 16:
            raise ValueError("plan too large for v1 (max 16 steps)")
        return {"plan_id": f"ag_plan_{len(steps)}s", "goal": goal,
                "steps": steps, "max_workers": MAX_WORKERS}

    def execute_step(
        self,
        action_id: str,
        action: str,
        subject_version_approved: int | None,
        subject_version_executing: int,
        approval: Dict[str, Any] | None,
        evidence_ids: List[str],
        executor: Callable[[], str] | None = None,
        is_human: bool = False,
        amount_usd: float = 0.0,
    ) -> ExecutionReceipt:
        # Pre-flight 1: evidence for proposals that mutate on basis of intel
        if action.startswith("intel.") and not evidence_ids:
            return self._blocked(action_id, "proposal", "missing_evidence",
                                 "intel action needs evidence")
        # Pre-flight 2: version pin for publish
        if action == "asset.publish":
            if subject_version_approved is None:
                return self._blocked(action_id, "publish", "need_approval",
                                     "publish needs approved version")
            r = self.sovereign.preflight_publish(
                subject_version_approved, subject_version_executing, approval,
                is_human=is_human)
            if not r.allowed:
                return self._blocked(action_id, "publish", r.code, r.detail)
        else:
            r = self.sovereign.check(action, is_human=is_human,
                                     approval=approval, amount_usd=amount_usd)
            if not r.allowed:
                return self._blocked(action_id, action, r.code, r.detail)
        # Execute (injected or no-op receipt for harness)
        try:
            result = executor() if executor else f"ref:{action_id}"
            self._n += 1
            rc = ExecutionReceipt(receipt_id=f"ag_rcpt_{self._n:04d}",
                                  action_id=action_id, result_ref=result, status="ok")
            self.receipts.append(rc)
            return rc
        except Exception as e:  # noqa - harness records failure, no silent retry loop here
            return self._blocked(action_id, action, "failed", str(e))

    def _blocked(self, action_id: str, subject: str, code: str, reason: str) -> ExecutionReceipt:
        self._n += 1
        rc = ExecutionReceipt(receipt_id=f"ag_rcpt_{self._n:04d}",
                              action_id=action_id, result_ref="",
                              status="blocked",
                              detail={"code": code, "reason": reason})
        self.receipts.append(rc)
        self.blockers.append(Blocker(blocker_id=f"ag_blk_{self._n:04d}",
                                     subject_id=subject, reason=reason, code=code))
        return rc
