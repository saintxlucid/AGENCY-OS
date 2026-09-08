"""
Authority fabric stub (v1). Pure decision helpers over profiles × scopes × purpose.
No stores. Sovereign remains final adjudicator; this shapes the request it judges.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List


VERBS = ["DISCOVER", "READ", "ANALYZE", "PROPOSE", "CREATE", "EDIT", "SUBMIT",
         "REVIEW", "APPROVE", "REJECT", "EXECUTE", "PUBLISH", "EXPORT", "ADMINISTER"]

CLASSIFICATIONS = ["PUBLIC", "INTERNAL", "CLIENT-CONFIDENTIAL", "SENSITIVE",
                   "RESTRICTED", "HIGHLY-RESTRICTED"]

ZONES = ["Z0", "Z1", "Z2", "Z3", "Z4", "Z5", "Z6"]

PROFILES = ["maintainer", "security_admin", "administrator", "manager",
            "operator_t1", "operator_t2", "viewer", "hr", "analyst", "client"]


@dataclass
class AccessProfile:
    principal: str  # human | agent | client | system
    profile: str
    department: str = ""
    resource_scope: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    approval_authority: List[str] = field(default_factory=list)
    data_classification: List[str] = field(default_factory=list)
    organization: str = ""  # client org for client principals
    expires_at: str = ""  # delegation / temporary

    def validate(self) -> List[str]:
        errs = []
        if self.principal not in ("human", "agent", "client", "system"):
            errs.append("bad principal")
        if self.profile not in PROFILES:
            errs.append(f"unknown profile {self.profile}")
        for a in self.actions:
            if a.lower() not in [v.lower() for v in VERBS] + ["read", "comment", "query", "aggregate", "export", "create", "update", "submit"]:
                errs.append(f"unknown action {a}")
        for c in self.data_classification:
            if c not in CLASSIFICATIONS and c not in ["internal", "client_scoped"]:
                errs.append(f"unknown classification {c}")
        if self.profile == "client" and not self.organization:
            errs.append("client profile needs organization")
        # Separation laws
        if self.profile == "maintainer" and "APPROVE" in [a.upper() for a in self.actions]:
            errs.append("maintainer must not carry business APPROVE")
        return errs


@dataclass
class CapabilityToken:
    subject: str
    action: str
    version: int = 1
    expires_at: str = ""
    purpose: str = ""
    issued_by: str = "Operator"

    def expired(self) -> bool:
        if not self.expires_at:
            return False
        try:
            return datetime.now() > datetime.fromisoformat(self.expires_at)
        except Exception:
            return True


def decide(profile: AccessProfile, action: str, classification: str,
           purpose: str = "", is_sensitive_purpose_mismatch: bool = False) -> Dict[str, Any]:
    """Minimal ABAC pre-check (Sovereign adjudicates final). Fail-closed."""
    if profile.validate():
        return {"allowed": False, "code": "invalid_profile",
                "detail": ";".join(profile.validate())}
    if action.upper() not in [a.upper() for a in profile.actions]:
        return {"allowed": False, "code": "deny_action", "detail": f"{action} not in profile actions"}
    if classification not in profile.data_classification and profile.data_classification:
        # Universal analyst without HIGHLY-RESTRICTED cannot touch salaries
        return {"allowed": False, "code": "deny_classification",
                "detail": f"{classification} outside {profile.data_classification}"}
    if is_sensitive_purpose_mismatch:
        return {"allowed": False, "code": "deny_purpose",
                "detail": f"purpose '{purpose}' does not justify {classification}"}
    if profile.expires_at:
        try:
            if datetime.now() > datetime.fromisoformat(profile.expires_at):
                return {"allowed": False, "code": "expired", "detail": "delegation expired"}
        except Exception:
            return {"allowed": False, "code": "expired", "detail": "bad expiry"}
    # Approvals still required where authority demands (caller checks Sovereign next)
    needs_approval = action.upper() in ("APPROVE", "PUBLISH", "EXECUTE", "EXPORT", "ADMINISTER")
    return {"allowed": True, "code": "allow_check" if not needs_approval else "need_approval_check",
            "detail": "pre-check pass; Sovereign adjudicates final"}
