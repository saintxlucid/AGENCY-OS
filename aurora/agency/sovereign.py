"""
ASTRA OS — Sovereign policy pack (frozen v1 over governance.py).

Wraps GovernanceEngine (deterministic, no LLM adjudication).
L0-L4 + thresholds + destructive taxonomy + pre-flight fail-closed checks.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple


def _now() -> str:
    return datetime.now().isoformat()


# ─── Authority + thresholds (locked defaults) ───

HUMAN_ONLY_ACTIONS = {
    "brief.approve",
    "concept.approve_production",
    "asset.publish",
    "message.send_external",
    "performance.report",
    "knowledge.embed",
    "brand.guideline_change",
}

DESTRUCTIVE_ACTIONS = {
    "archive",
    "takedown",
    "budget_change",
    "scope_change",
    "guideline_change",
    "client_stage_change",
    "retainer_change",
    "delete_request",
    "permission_grant",
    "external_send",
}

SPEND_L2_MAX = 500.0
SPEND_L3_MAX = 5000.0
APPROVAL_TTL_HOURS = 72


@dataclass
class PreflightResult:
    allowed: bool
    code: str  # ok | deny_permission | need_approval | version_mismatch | budget_exceeded | missing_evidence | expired
    detail: str = ""
    approval_required_by: str = ""


class Sovereign:
    """Deterministic gate. Wraps GovernanceEngine when available, else standalone rules."""

    def __init__(self, org_id: str = "org_saintlucid"):
        self.org_id = org_id
        self._engine = None
        try:
            from aurora.enterprise.governance import GovernanceEngine, default_policies

            eng = GovernanceEngine(org_id=org_id)
            for p in default_policies(org_id):
                try:
                    eng.add_policy(p)
                except Exception:
                    pass
            self._engine = eng
        except Exception:
            self._engine = None

    def check(
        self,
        action: str,
        actor_type: str = "agent",
        actor_role: str = "",
        actor_id: str = "",
        is_human: bool = False,
        approval: Optional[Dict[str, Any]] = None,
        amount_usd: float = 0.0,
        access_profile: Any = None,
        classification: str = "",
        purpose: str = "",
        purpose_mismatch: bool = False,
        rbac_allowed: Any = None,
    ) -> PreflightResult:
        # ABAC pre-check (access fabric) before policy evaluation. Sovereign adjudicates final.
        # RBAC is one input: explicit False denies immediately; True/None continues.
        if rbac_allowed is False:
            return PreflightResult(False, "deny_permission",
                                   "RBAC denies baseline permission", "")
        if access_profile is not None:
            try:
                from aurora.agency.access import decide as _abac
            except Exception as e:
                return PreflightResult(False, "deny_permission",
                                       f"access fabric unavailable: {e}", "")
            verb = action.split(".")[-1] if "." in action else action
            d = _abac(access_profile, verb, classification or "INTERNAL",
                      purpose=purpose,
                      is_sensitive_purpose_mismatch=purpose_mismatch)
            if not d.get("allowed"):
                return PreflightResult(False, str(d.get("code", "deny_permission")),
                                       str(d.get("detail", "")), "")
        base = action.split(".")[0] if "." in action else action
        # Destructive always needs approval record
        if base in DESTRUCTIVE_ACTIONS or action in DESTRUCTIVE_ACTIONS:
            if not approval or approval.get("decision") != "approved":
                return PreflightResult(False, "need_approval",
                                       f"destructive {action} requires approved Approval",
                                       "human L4")
        # Human-only in v1
        if action in HUMAN_ONLY_ACTIONS and not is_human:
            if not approval or approval.get("decision") != "approved":
                return PreflightResult(False, "need_approval",
                                       f"{action} is human-only in v1",
                                       "human L3")
        # Spend thresholds
        if amount_usd > SPEND_L3_MAX:
            if not approval or approval.get("decision") != "approved":
                return PreflightResult(False, "need_approval",
                                       f"spend ${amount_usd} > ${SPEND_L3_MAX} needs L4 dual",
                                       "human L4")
        elif amount_usd > SPEND_L2_MAX:
            if not approval or approval.get("decision") != "approved":
                if not is_human and actor_role not in ("Account Director", "Producer"):
                    return PreflightResult(False, "need_approval",
                                           f"spend ${amount_usd} needs L3",
                                           "human L3")
        # Approval expiry
        if approval:
            exp = approval.get("expires_at", "")
            if exp:
                try:
                    if datetime.now() > datetime.fromisoformat(exp):
                        return PreflightResult(False, "expired", "approval expired", "human")
                except Exception:
                    pass
            if approval.get("decision") != "approved":
                return PreflightResult(False, "need_approval", "approval not approved", "human")
        return PreflightResult(True, "ok", "allowed")

    def preflight_publish(
        self,
        approved_version: int,
        executing_version: int,
        approval: Optional[Dict[str, Any]],
        is_human: bool = False,
    ) -> PreflightResult:
        if approved_version != executing_version:
            return PreflightResult(False, "version_mismatch",
                                   f"approved v{approved_version} != executing v{executing_version}")
        return self.check("asset.publish", is_human=is_human, approval=approval)

    def preflight_proposal(self, evidence_ids: List[str]) -> PreflightResult:
        if not evidence_ids:
            return PreflightResult(False, "missing_evidence",
                                   "proposal requires ≥1 evidence_id")
        return PreflightResult(True, "ok", "evidence present")
