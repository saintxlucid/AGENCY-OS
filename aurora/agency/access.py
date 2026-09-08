"""Authority fabric (v1). Canonical home is aurora.access; this module re-exports it.

Kept for backwards compatibility (existing imports).
New code should use: `from aurora.access import ...`.
Sovereign remains final adjudicator; fabric shapes the request it judges.
"""
from __future__ import annotations

from typing import Any, Dict

from aurora.access import (
    CLASSIFICATIONS,
    PROFILES,
    VERBS,
    ZONES,
    AccessProfile,
    CapabilityToken,
    pre_check,
)


def _profile_to_dict(profile: Any) -> Dict[str, Any]:
    if isinstance(profile, dict):
        return profile
    get = lambda k, d="": getattr(profile, k, d)  # noqa
    return {
        "principal": get("principal", "human"),
        "profile": get("profile", "viewer"),
        "department": get("department", ""),
        "resource_scope": list(get("resource_scope", []) or []),
        "actions": list(get("actions", []) or []),
        "approval_authority": list(get("approval_authority", []) or []),
        "data_classification": list(get("data_classification", []) or []),
        "organization": get("organization", ""),
        "zones": list(get("zones", []) or []),
        "expires_at": get("expires_at", ""),
        "database_direct_access": bool(get("database_direct_access", False)),
    }


def decide(profile: Any, action: str, classification: str = "INTERNAL",
           purpose: str = "", zone: str = "",
           is_sensitive_purpose_mismatch: bool = False,
           **kw: Any) -> Dict[str, Any]:
    """Backward-compatible wrapper over canonical pre_check.

    Legacy callers pass AccessProfile objects + mismatch bool; new callers pass
    dicts + zone/capability/delegation. Mismatch True forces deny_purpose
    (preserves pre-canonical test contract); otherwise delegates to pre_check.
    """
    if is_sensitive_purpose_mismatch:
        return {"allowed": False, "code": "deny_purpose",
                "detail": f"purpose '{purpose}' does not justify {classification}"}
    return pre_check(_profile_to_dict(profile), action, classification,
                     purpose=purpose, zone=zone, **kw)


__all__ = ["AccessProfile", "CapabilityToken", "decide", "pre_check",
           "VERBS", "CLASSIFICATIONS", "ZONES", "PROFILES"]
