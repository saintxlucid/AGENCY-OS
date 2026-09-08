"""Access Fabric — decision engine. Fail-closed. Sovereign adjudicates final.

Order (each step can only narrow):
  1. RBAC baseline (role permissions) — unknown mapping → deny
  2. Profile validity + action membership + expiry
  3. Zone membership
  4. Classification ceiling (profile max + declared data_classification)
  5. Purpose cap
  6. Delegation / break-glass / capability (temporary grants widen ONLY
     within steps 2–5 ceilings, never above them)
  7. Sovereign.check() — final adjudication (approval/spend/human-only/expiry)
  8. Audit event (via hook; never silent on sensitive paths)

RBAC never grants alone: evaluate() returns allow ONLY if fabric pre-check
passes AND Sovereign allows. simulate() runs 1–7 without side effects.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from .model import (
    PROFILE_MAX_CLASSIFICATION,
    AccessProfile,
    AgentIdentityChain,
    BreakGlassGrant,
    CapabilityToken,
    Delegation,
    classification_rank,
)
from .policy import baseline_profile_for_role, purpose_allows

AuditHook = Callable[[Dict[str, Any]], None]
_audit_hooks: List[AuditHook] = []


def on_access_event(hook: AuditHook) -> Callable[[], None]:
    _audit_hooks.append(hook)

    def _off():
        try:
            _audit_hooks.remove(hook)
        except ValueError:
            pass

    return _off


def _emit(event: Dict[str, Any]) -> None:
    for hook in list(_audit_hooks):
        try:
            hook(event)
        except Exception:
            pass


def _profile_from_dict(d: Dict[str, Any]) -> AccessProfile:
    return AccessProfile(
        principal=d.get("principal", "human"),
        profile=d.get("profile", "viewer"),
        department=d.get("department", ""),
        resource_scope=list(d.get("resource_scope", [])),
        actions=list(d.get("actions", [])),
        approval_authority=list(d.get("approval_authority", [])),
        data_classification=list(d.get("data_classification", [])),
        organization=d.get("organization", ""),
        zones=list(d.get("zones", [])),
        expires_at=d.get("expires_at", ""),
        database_direct_access=bool(d.get("database_direct_access", False)),
    )


def pre_check(profile_d: Dict[str, Any], action: str, classification: str = "INTERNAL",
              purpose: str = "", zone: str = "",
              capability: Optional[CapabilityToken] = None,
              delegation: Optional[Delegation] = None,
              break_glass: Optional[BreakGlassGrant] = None,
              agent_chain: Optional[AgentIdentityChain] = None) -> Dict[str, Any]:
    """Fabric pre-check (steps 2–6). Returns dict, never raises on policy."""
    prof = _profile_from_dict(profile_d)
    errs = prof.validate()
    if errs:
        return {"allowed": False, "code": "invalid_profile", "detail": ";".join(errs)}

    # Agent identity: agents must present a chain, never ride human identity
    if prof.principal == "agent":
        chain = agent_chain or AgentIdentityChain(agent_actor=profile_d.get("agent_actor", ""))
        chain_errs = chain.validate()
        if chain_errs:
            return {"allowed": False, "code": "deny_agent_identity", "detail": ";".join(chain_errs)}

    # Expiry (delegation / temporary). Expired base never allows on its own;
    # only a live widening grant below can rescue the decision.
    from datetime import datetime as _dt

    base_expired = False
    if prof.expires_at:
        try:
            base_expired = _dt.now() > _dt.fromisoformat(prof.expires_at)
        except Exception:
            return {"allowed": False, "code": "expired", "detail": "bad expiry"}

    action_ok = action.upper() in [a.upper() for a in prof.actions]
    widened_by: Optional[str] = None

    # Temporary grants can supply a missing action ONLY within ceilings
    if not action_ok:
        if delegation is not None and delegation.active() and action in delegation.capabilities:
            action_ok = True
            widened_by = f"delegation:{delegation.delegation_id or 'unnamed'}"
        elif break_glass is not None and break_glass.active() and (
            not break_glass.scopes or action in break_glass.scopes or "*" in break_glass.scopes
        ):
            action_ok = True
            widened_by = f"break_glass:{break_glass.grant_id or 'unnamed'}"
        elif capability is not None and not capability.expired() and capability.action.upper() == action.upper():
            action_ok = True
            widened_by = f"capability:{capability.capability_id or capability.subject}"
    if not action_ok:
        # Expired profile with no live grant → expired, else plain deny
        if base_expired:
            return {"allowed": False, "code": "expired", "detail": "delegation expired"}
        return {"allowed": False, "code": "deny_action", "detail": f"{action} not in profile actions"}
    if base_expired and not widened_by:
        return {"allowed": False, "code": "expired", "detail": "delegation expired"}

    # Zone
    if zone and zone not in prof.effective_zones():
        return {"allowed": False, "code": "deny_zone", "detail": f"{zone} outside {prof.effective_zones()}"}

    # Classification ceiling: profile max AND declared list both bind
    ceiling = PROFILE_MAX_CLASSIFICATION.get(prof.profile, "INTERNAL")
    if classification_rank(classification) > classification_rank(ceiling):
        return {"allowed": False, "code": "deny_classification",
                "detail": f"{classification} above {prof.profile} ceiling {ceiling}"}
    if prof.data_classification and classification not in prof.data_classification:
        return {"allowed": False, "code": "deny_classification",
                "detail": f"{classification} outside {prof.data_classification}"}

    # Purpose cap
    if purpose and not purpose_allows(purpose, classification):
        return {"allowed": False, "code": "deny_purpose",
                "detail": f"purpose '{purpose}' does not justify {classification}"}

    needs_approval = action.upper() in ("APPROVE", "PUBLISH", "EXECUTE", "EXPORT", "ADMINISTER")
    out: Dict[str, Any] = {"allowed": True,
                           "code": "allow_check" if not needs_approval else "need_approval_check",
                           "detail": "pre-check pass; Sovereign adjudicates final"}
    if widened_by:
        out["widened_by"] = widened_by
    return out


def evaluate(profile_d: Dict[str, Any], action: str, classification: str = "INTERNAL",
             purpose: str = "", zone: str = "", resource_scope_ok: bool = True,
             approval: Optional[Dict] = None, is_human: bool = False,
             amount_usd: float = 0.0, actor_role: str = "",
             capability: Optional[CapabilityToken] = None,
             delegation: Optional[Delegation] = None,
             break_glass: Optional[BreakGlassGrant] = None,
             agent_chain: Optional[AgentIdentityChain] = None,
             audit_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Full decision: fabric pre-check → resource scope → Sovereign. Fail-closed."""
    pre = pre_check(profile_d, action, classification, purpose, zone,
                    capability, delegation, break_glass, agent_chain)
    if not pre["allowed"]:
        _emit({"result": "deny", "stage": "fabric", **{k: v for k, v in pre.items()},
               "action": action, "ctx": audit_context or {}})
        return pre
    if not resource_scope_ok:
        res = {"allowed": False, "code": "deny_scope", "detail": "resource outside scope"}
        _emit({"result": "deny", "stage": "scope", **res, "action": action, "ctx": audit_context or {}})
        return res

    # Sovereign final (import here: agency layer owns Sovereign; access must not cycle at import)
    try:
        from aurora.agency.sovereign import Sovereign

        r = Sovereign().check(action, is_human=is_human, approval=approval,
                              amount_usd=amount_usd, actor_role=actor_role)
        if not r.allowed:
            res = {"allowed": False, "code": r.code, "detail": r.detail,
                   "approval_required_by": r.approval_required_by}
            _emit({"result": "deny", "stage": "sovereign", **res, "action": action,
                   "ctx": audit_context or {}})
            return res
    except Exception as e:
        res = {"allowed": False, "code": "deny_sovereign_unavailable", "detail": f"sovereign error: {e}"}
        _emit({"result": "deny", "stage": "sovereign", **res, "action": action,
               "ctx": audit_context or {}})
        return res

    res = {"allowed": True, "code": "allow", "detail": pre["detail"],
           "approval": approval or None}
    if pre.get("widened_by"):
        res["widened_by"] = pre["widened_by"]
    _emit({"result": "allow", "stage": "sovereign", **res, "action": action,
           "ctx": audit_context or {}})
    return res


def simulate(profile_d: Dict[str, Any], action: str, **kw) -> Dict[str, Any]:
    """Access simulation for admins: same path as evaluate, no side effects."""
    res = evaluate(profile_d, action, **kw)
    if not res["allowed"] and res["code"] in ("deny_classification", "deny_purpose", "deny_action"):
        res["alternative"] = "request redacted scope or narrower purpose"
    return {"simulation": True, **res}


def rbac_baseline_allowed(role: str, permission: str, org_id: str,
                          user_roles: Dict[str, str]) -> bool:
    """Evaluate the RBAC baseline input (EnterpriseCore semantics, dependency-free).

    user_roles: org_id → role value. Returns False for unknown role/permission.
    Mirrors User.has_permission without importing enterprise (avoids cycles in tests).
    """
    try:
        from aurora.enterprise.core import Permission, Role

        r = user_roles.get(org_id)
        if not r:
            return False
        role_e = Role(r)
        perm = Permission(permission)
        return perm in Role.permissions(role_e)
    except Exception:
        return False
