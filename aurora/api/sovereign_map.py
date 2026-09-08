"""
ASTRA OS — API Sovereign route map (PHASE 1 seam: external surface).

Mutating routes require Sovereign check. Reads stay open per RBAC.
Map derived from aurora/api/server.py @app.* decorators (evidence in reconciliation.md).
"""
from __future__ import annotations

from typing import Dict, Tuple

from aurora.agency.sovereign import Sovereign

# (method, prefix) → {action, human_only, destructive}
MUTATING_ROUTES: Dict[Tuple[str, str], Dict[str, object]] = {
    ("POST", "/api/v1/interpret"): {"action": "intel.interpret", "human_only": False, "destructive": False},
    ("POST", "/api/v1/query"): {"action": "intel.query", "human_only": False, "destructive": False},
    ("POST", "/api/v1/projects"): {"action": "project.create", "human_only": False, "destructive": False},
    ("POST", "/api/v1/observe"): {"action": "observe.start", "human_only": False, "destructive": False},
    ("DELETE", "/api/v1/observe"): {"action": "observe.stop", "human_only": False, "destructive": False},
    ("POST", "/api/v1/erp/invoices"): {"action": "finance.invoice_create", "human_only": False, "destructive": False},
    ("POST", "/api/v1/erp/tasks"): {"action": "project.task_create", "human_only": False, "destructive": False},
    ("POST", "/api/v1/ai/query"): {"action": "intel.query", "human_only": False, "destructive": False},
    ("POST", "/api/v1/batch"): {"action": "batch.execute", "human_only": False, "destructive": False},
    ("POST", "/api/v1/webhooks"): {"action": "external.ingest", "human_only": False, "destructive": False},
    ("POST", "/api/v1/mcp"): {"action": "tool.exec", "human_only": False, "destructive": False},
}

READ_PREFIXES = ("/api/v1/health", "/api/v1/status", "/api/v1/projects",
                 "/api/v1/observe", "/api/v1/erp/", "/api/v1/ai/",
                 "/api/v1/mcp/", "/api/v1/enterprise/")


def check_mutating_route(method: str, path: str, is_human: bool = False,
                         approval: dict | None = None,
                         sovereign: Sovereign | None = None,
                         access_profile: object | None = None,
                         classification: str = "",
                         purpose: str = "",
                         purpose_mismatch: bool = False,
                         rbac_allowed: object | None = None) -> dict:
    """Gate helper for FastAPI dependencies. Returns {gated, allowed, code}.

    ABAC pre-check runs inside Sovereign.check when access_profile is given;
    RBAC False denies immediately. Reads stay open per RBAC (ungated here)."""
    sov = sovereign or Sovereign()
    for (m, prefix), rule in MUTATING_ROUTES.items():
        if method == m and path.startswith(prefix):
            action = str(rule["action"])
            if rule.get("human_only") and not is_human and not (approval or {}).get("decision"):
                return {"gated": True, "allowed": False, "code": "need_approval",
                        "action": action}
            r = sov.check(action, is_human=is_human, approval=approval,
                          access_profile=access_profile, classification=classification,
                          purpose=purpose, purpose_mismatch=purpose_mismatch,
                          rbac_allowed=rbac_allowed)
            return {"gated": True, "allowed": r.allowed, "code": r.code, "action": action}
    return {"gated": False, "allowed": True, "code": "read", "action": "read"}
