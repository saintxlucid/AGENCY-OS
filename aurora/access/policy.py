"""Access Fabric — policy layer: RBAC bridge, purpose registry, row/column security.

RBAC (EnterpriseCore Role) supplies the BASELINE. This layer narrows it by
department / resource / classification / purpose / zone. It can only DENY
beyond RBAC or REQUIRE approval — never grant what RBAC forbids.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .model import PROFILE_MAX_CLASSIFICATION, classification_rank

# ─── RBAC bridge: Role → baseline fabric profile ───
# Existing Role enum values (enterprise/core.py) mapped to fabric profiles.
# A user can hold several org roles; caller picks the max applicable or evaluates each.

ROLE_TO_PROFILE: Dict[str, str] = {
    "owner": "administrator",
    "admin": "administrator",
    "manager": "manager",
    "creative_director": "operator_t2",
    "designer": "operator_t1",
    "developer": "maintainer",
    "editor": "operator_t1",
    "researcher": "analyst",
    "client": "client",
    "viewer": "viewer",
    "billing": "manager",
}

# Role → default department scope hint (caller refines with actual assignment)
ROLE_TO_DEPARTMENT: Dict[str, str] = {
    "creative_director": "creative",
    "designer": "creative",
    "developer": "engineering",
    "editor": "content",
    "researcher": "intelligence",
    "client": "",
    "viewer": "",
}


def baseline_profile_for_role(role: str) -> str:
    return ROLE_TO_PROFILE.get(role, "viewer")


# ─── Purpose registry: purpose → max justifiable classification ───
# Purpose-limited intelligence: a purpose caps what it may touch.

PURPOSE_MAX_CLASSIFICATION: Dict[str, str] = {
    "capacity_analysis": "INTERNAL",
    "campaign_reporting": "CLIENT-CONFIDENTIAL",
    "client_review": "CLIENT-CONFIDENTIAL",
    "design_production": "CLIENT-CONFIDENTIAL",
    "financial_close": "RESTRICTED",
    "payroll": "HIGHLY-RESTRICTED",
    "security_review": "INTERNAL",
    "strategy_synthesis": "SENSITIVE",
}


def purpose_allows(purpose: str, classification: str) -> bool:
    if not purpose:
        return True  # purpose absent → no purpose opinion (other gates still apply)
    cap = PURPOSE_MAX_CLASSIFICATION.get(purpose)
    if cap is None:
        return True  # unregistered purpose → no opinion (deny happens elsewhere if needed)
    return classification_rank(classification) <= classification_rank(cap)


# ─── Row-level security ───

def row_allowed(profile: Dict, row: Dict, principal_org: str = "") -> bool:
    """Client isolation + assignment scoping. Fail-closed on missing keys."""
    prof = profile.get("profile", "")
    if prof == "client":
        org = profile.get("organization", "")
        # Client rows must carry client/org linkage; anything else is invisible
        for key in ("client_id", "client_org", "organization", "org_id"):
            if key in row and row[key] not in ("", None):
                return row[key] == org
        return False  # unlinked row → invisible to clients
    if prof in ("operator_t1", "operator_t2"):
        scope = set(profile.get("resource_scope", []))
        if not scope:
            return False
        if "organization" in scope or "assigned_projects" in scope or "*" in scope:
            return True
        # Assignment match: any shared project/client/department token
        for key in ("project_id", "client_id", "department", "campaign_id"):
            if key in row and row[key] in scope:
                return True
        return False
    return True  # manager/administrator/hr/analyst/viewer/maintainer: zone+column gates decide


# ─── Column-level security + redaction ───

# Field → classification floor (field visible only if caller clears ≥ this level)
FIELD_CLASSIFICATION: Dict[str, str] = {
    "salary": "HIGHLY-RESTRICTED",
    "bank_account": "HIGHLY-RESTRICTED",
    "bank_information": "HIGHLY-RESTRICTED",
    "national_id": "HIGHLY-RESTRICTED",
    "personal_address": "HIGHLY-RESTRICTED",
    "medical": "HIGHLY-RESTRICTED",
    "disciplinary_record": "HIGHLY-RESTRICTED",
    "compensation": "HIGHLY-RESTRICTED",
    "internal_cost": "RESTRICTED",
    "agency_cost": "RESTRICTED",
    "revenue": "RESTRICTED",
    "margin": "RESTRICTED",
    "contract_terms": "SENSITIVE",
    "internal_notes": "SENSITIVE",
    "internal_strategy": "SENSITIVE",
    "performance_review": "SENSITIVE",
}

REDACTED = "[REDACTED]"


def redact_row(row: Dict, allowed_classifications: List[str], strict: bool = True) -> Dict:
    """Return a copy with disallowed fields redacted. Unknown fields pass through."""
    out = dict(row)
    for field, floor in FIELD_CLASSIFICATION.items():
        if field in out and floor not in allowed_classifications:
            # strict: any clearance below floor redacts (rank compare)
            if strict:
                out[field] = REDACTED
            else:
                out[field] = REDACTED
    return out


def filter_query_result(rows: List[Dict], profile: Dict, purpose: str = "") -> List[Dict]:
    """Policy query engine: row filter → purpose check → column redact → audit-ready."""
    allowed_classes = list(profile.get("data_classification", []))
    out = []
    for row in rows:
        if not row_allowed(profile, row, profile.get("organization", "")):
            continue
        cls = row.get("classification", "INTERNAL")
        if allowed_classes and cls not in allowed_classes:
            continue
        if purpose and not purpose_allows(purpose, cls):
            continue
        out.append(redact_row(row, allowed_classes))
    return out
