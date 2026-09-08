"""ASTRA OS — Sovereign API guard (PHASE 1 seam + Access Fabric v1).

Explicit route → action map. Reads stay open per RBAC; mutating routes
fail closed via Sovereign.check() with optional fabric pre-check.
Header contract (v1, no auth rewrite):
  X-Human: "true"              → is_human=True
  X-Approval-Decision: approved → approval={"decision":"approved",...}
  X-Approval-Expires: ISO      → approval expiry
  X-Amount-USD: float          → spend preflight
  Fabric (all optional; absent → legacy RBAC-only path, tests unaffected):
  X-Profile / X-Principal / X-Department / X-Zone / X-Purpose /
  X-Classification / X-Resource-Scope (csv) / X-Actions (csv) /
  X-Org (client org) / X-Agent-Actor
Deny → HTTP 403 with Sovereign/fabric code; expiry → 403 expired.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from fastapi import Header, HTTPException, Request

from aurora.agency.sovereign import Sovereign

_shared = Sovereign()

# (METHOD, path-prefix) → canonical action. Longest prefix wins.
SOVEREIGN_ROUTE_MAP: Dict[Tuple[str, str], str] = {
    ("POST", "/api/v1/interpret"): "intel.analyze",
    ("POST", "/api/v1/projects"): "project.create",
    ("POST", "/api/v1/observe"): "watch.subscribe",
    ("DELETE", "/api/v1/observe"): "watch.unsubscribe",
    ("POST", "/api/v1/erp/invoices"): "invoice.create",
    ("PATCH", "/api/v1/erp/invoices"): "invoice.transition",
    ("POST", "/api/v1/erp/tasks"): "task.create",
    ("PATCH", "/api/v1/erp/tasks"): "task.transition",
    ("POST", "/api/v1/batch"): "batch.execute",
    ("POST", "/api/v1/webhooks"): "webhook.ingest",
    ("POST", "/api/v1/ai/query"): "ai.query",
    ("POST", "/api/v1/access/simulate"): "access.simulate",
}

MUTATING_PREFIXES = tuple(sorted({p for _, p in SOVEREIGN_ROUTE_MAP}, key=len, reverse=True))


def action_for(method: str, path: str) -> Optional[str]:
    for (m, prefix), action in SOVEREIGN_ROUTE_MAP.items():
        if method == m and path.startswith(prefix):
            return action
    return None


def _approval_from_headers(decision: Optional[str], expires: Optional[str]) -> Optional[Dict]:
    if not decision:
        return None
    return {"decision": decision, "expires_at": expires or ""}


def _csv(v: Optional[str]) -> List[str]:
    return [p.strip() for p in (v or "").split(",") if p.strip()]


def fabric_profile_from_headers(
    profile: Optional[str] = None,
    principal: Optional[str] = None,
    department: Optional[str] = None,
    resource_scope: Optional[str] = None,
    actions: Optional[str] = None,
    organization: Optional[str] = None,
    agent_actor: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Build a fabric profile dict from headers. None → fabric skipped (legacy path)."""
    if not profile:
        return None
    d: Dict[str, Any] = {
        "principal": principal or "human",
        "profile": profile,
        "department": department or "",
        "resource_scope": _csv(resource_scope),
        "actions": _csv(actions),
        "organization": organization or "",
    }
    if agent_actor:
        d["agent_actor"] = agent_actor
    return d


def guard_or_403(action: str, is_human: bool = False,
                 approval: Optional[Dict] = None, amount_usd: float = 0.0,
                 actor_role: str = "",
                 access_profile: Optional[Dict[str, Any]] = None,
                 classification: str = "", purpose: str = "",
                 purpose_mismatch: bool = False, rbac_allowed: Any = None,
                 zone: str = "", capability: Any = None,
                 delegation: Any = None, break_glass: Any = None,
                 agent_chain: Any = None) -> None:
    r = _shared.check(action, is_human=is_human, approval=approval,
                      amount_usd=amount_usd, actor_role=actor_role,
                      access_profile=access_profile, classification=classification,
                      purpose=purpose, purpose_mismatch=purpose_mismatch,
                      rbac_allowed=rbac_allowed, zone=zone, capability=capability,
                      delegation=delegation, break_glass=break_glass,
                      agent_chain=agent_chain)
    if not r.allowed:
        raise HTTPException(status_code=403, detail={"sovereign": r.code, "reason": r.detail})


async def sovereign_guard(
    request: Request,
    x_human: Optional[str] = Header(default=None, alias="X-Human"),
    x_approval: Optional[str] = Header(default=None, alias="X-Approval-Decision"),
    x_expires: Optional[str] = Header(default=None, alias="X-Approval-Expires"),
    x_amount: Optional[str] = Header(default=None, alias="X-Amount-USD"),
    x_profile: Optional[str] = Header(default=None, alias="X-Profile"),
    x_principal: Optional[str] = Header(default=None, alias="X-Principal"),
    x_department: Optional[str] = Header(default=None, alias="X-Department"),
    x_zone: Optional[str] = Header(default=None, alias="X-Zone"),
    x_purpose: Optional[str] = Header(default=None, alias="X-Purpose"),
    x_classification: Optional[str] = Header(default=None, alias="X-Classification"),
    x_scope: Optional[str] = Header(default=None, alias="X-Resource-Scope"),
    x_actions: Optional[str] = Header(default=None, alias="X-Actions"),
    x_org: Optional[str] = Header(default=None, alias="X-Org"),
    x_agent: Optional[str] = Header(default=None, alias="X-Agent-Actor"),
) -> None:
    action = action_for(request.method, request.url.path)
    if action is None:
        return  # reads / unmapped: RBAC layer owns them
    try:
        amount = float(x_amount) if x_amount else 0.0
    except ValueError:
        amount = 0.0
    access_profile = fabric_profile_from_headers(
        x_profile, x_principal, x_department, x_scope, x_actions, x_org, x_agent)
    agent_chain = None
    if access_profile is not None and access_profile.get("principal") == "agent":
        from aurora.access import AgentIdentityChain

        agent_chain = AgentIdentityChain(agent_actor=x_agent or "", human_actor="")
    guard_or_403(action, is_human=(x_human == "true"),
                 approval=_approval_from_headers(x_approval, x_expires),
                 amount_usd=amount, access_profile=access_profile,
                 classification=x_classification or "", purpose=x_purpose or "",
                 zone=x_zone or "", agent_chain=agent_chain)
