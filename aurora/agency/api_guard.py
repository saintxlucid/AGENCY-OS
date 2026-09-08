"""ASTRA OS — Sovereign API guard (PHASE 1 seam: API mutating routes).

Explicit route → action map. Reads stay open per RBAC; mutating routes
fail closed via Sovereign.check(). Header contract (v1, no auth rewrite):
  X-Human: "true"              → is_human=True
  X-Approval-Decision: approved → approval={"decision":"approved",...}
  X-Approval-Expires: ISO      → approval expiry
  X-Amount-USD: float          → spend preflight
Deny → HTTP 403 with Sovereign code; expiry → 403 expired.
"""
from __future__ import annotations

from typing import Dict, Optional, Tuple

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


def guard_or_403(action: str, is_human: bool = False,
                 approval: Optional[Dict] = None, amount_usd: float = 0.0,
                 actor_role: str = "") -> None:
    r = _shared.check(action, is_human=is_human, approval=approval,
                      amount_usd=amount_usd, actor_role=actor_role)
    if not r.allowed:
        raise HTTPException(status_code=403, detail={"sovereign": r.code, "reason": r.detail})


async def sovereign_guard(
    request: Request,
    x_human: Optional[str] = Header(default=None, alias="X-Human"),
    x_approval: Optional[str] = Header(default=None, alias="X-Approval-Decision"),
    x_expires: Optional[str] = Header(default=None, alias="X-Approval-Expires"),
    x_amount: Optional[str] = Header(default=None, alias="X-Amount-USD"),
) -> None:
    action = action_for(request.method, request.url.path)
    if action is None:
        return  # reads / unmapped: RBAC layer owns them
    try:
        amount = float(x_amount) if x_amount else 0.0
    except ValueError:
        amount = 0.0
    guard_or_403(action, is_human=(x_human == "true"),
                 approval=_approval_from_headers(x_approval, x_expires),
                 amount_usd=amount)
