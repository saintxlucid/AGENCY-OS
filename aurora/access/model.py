"""ASTRA OS — Access Fabric v1: canonical authority model.

RBAC (EnterpriseCore) = identity + baseline permissions (ONE input).
ABAC (this package)   = context: department / resource / data / purpose / time / risk.
Capabilities          = scoped agent + temporary permissions.
Approvals             = human authority.
Sovereign             = final adjudication (unbypassable).
Audit                 = immutable accountability.

No stores. No business mutation. Pure decision helpers + in-memory
registries for delegations/grants/tokens (expiry-enforced).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional


# ─── Dimensions ───

class PrincipalType(str, Enum):
    HUMAN = "human"
    AGENT = "agent"
    CLIENT = "client"
    SYSTEM = "system"


class Profile(str, Enum):
    MAINTAINER = "maintainer"           # system/infra, no business authority
    SECURITY_ADMIN = "security_admin"   # identities/policies/audit, no business data writes
    ADMINISTRATOR = "administrator"
    MANAGER = "manager"
    OPERATOR_T1 = "operator_t1"         # normal employee tier
    OPERATOR_T2 = "operator_t2"         # elevated ops, ≠ administrator
    VIEWER = "viewer"                   # cross-department read
    HR = "hr"
    ANALYST = "analyst"                 # universal query via policy engine, never direct DB
    CLIENT = "client"                   # external principal, scoped portal


class Verb(str, Enum):
    DISCOVER = "DISCOVER"; READ = "READ"; ANALYZE = "ANALYZE"; PROPOSE = "PROPOSE"
    CREATE = "CREATE"; EDIT = "EDIT"; SUBMIT = "SUBMIT"; REVIEW = "REVIEW"
    APPROVE = "APPROVE"; REJECT = "REJECT"; EXECUTE = "EXECUTE"; PUBLISH = "PUBLISH"
    EXPORT = "EXPORT"; ADMINISTER = "ADMINISTER"; COMMENT = "COMMENT"
    QUERY = "QUERY"; AGGREGATE = "AGGREGATE"


class Classification(str, Enum):
    PUBLIC = "PUBLIC"; INTERNAL = "INTERNAL"; CLIENT_CONFIDENTIAL = "CLIENT-CONFIDENTIAL"
    SENSITIVE = "SENSITIVE"; RESTRICTED = "RESTRICTED"; HIGHLY_RESTRICTED = "HIGHLY-RESTRICTED"


class Zone(str, Enum):
    Z0_PUBLIC = "Z0"; Z1_CLIENT_PORTAL = "Z1"; Z2_OPERATIONAL = "Z2"
    Z3_MANAGEMENT = "Z3"; Z4_SENSITIVE = "Z4"; Z5_SECURITY = "Z5"; Z6_SYSTEM = "Z6"


# Backwards-compatible string lists (agency/access.py stub shape)
VERBS = [v.value for v in Verb]
CLASSIFICATIONS = [c.value for c in Classification]
ZONES = [z.value for z in Zone]
PROFILES = [p.value for p in Profile]

# Profile → default zones (deny outside without explicit grant)
PROFILE_ZONES: Dict[str, List[str]] = {
    "maintainer": ["Z6", "Z2"],
    "security_admin": ["Z5", "Z2"],
    "administrator": ["Z3", "Z2", "Z1"],
    "manager": ["Z3", "Z2", "Z1"],
    "operator_t1": ["Z2"],
    "operator_t2": ["Z2", "Z1"],
    "viewer": ["Z2", "Z1", "Z0"],
    "hr": ["Z4", "Z2"],
    "analyst": ["Z2", "Z3", "Z1", "Z0"],
    "client": ["Z1", "Z0"],
}

# Profile → max classification (anything above = deny even with action present)
PROFILE_MAX_CLASSIFICATION: Dict[str, str] = {
    "maintainer": "INTERNAL",
    "security_admin": "INTERNAL",
    "administrator": "RESTRICTED",
    "manager": "RESTRICTED",
    "operator_t1": "CLIENT-CONFIDENTIAL",
    "operator_t2": "SENSITIVE",
    "viewer": "INTERNAL",
    "hr": "HIGHLY-RESTRICTED",
    "analyst": "RESTRICTED",
    "client": "CLIENT-CONFIDENTIAL",
}

_CLASS_RANK = {c: i for i, c in enumerate(
    ["PUBLIC", "INTERNAL", "CLIENT-CONFIDENTIAL", "SENSITIVE", "RESTRICTED", "HIGHLY-RESTRICTED"])}


def classification_rank(c: str) -> int:
    return _CLASS_RANK.get(c, 99)


# ─── Identity ───

@dataclass
class AccessProfile:
    principal: str  # human | agent | client | system
    profile: str
    department: str = ""
    resource_scope: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    approval_authority: List[str] = field(default_factory=list)
    data_classification: List[str] = field(default_factory=list)
    organization: str = ""   # client org for client principals
    zones: List[str] = field(default_factory=list)
    expires_at: str = ""
    database_direct_access: bool = False  # always False for analyst; enforced

    def validate(self) -> List[str]:
        errs = []
        if self.principal not in ("human", "agent", "client", "system"):
            errs.append("bad principal")
        if self.profile not in PROFILES:
            errs.append(f"unknown profile {self.profile}")
        known_actions = [v.lower() for v in VERBS] + ["read", "comment", "query", "aggregate", "export", "create", "update", "submit"]
        for a in self.actions:
            if a.lower() not in known_actions:
                errs.append(f"unknown action {a}")
        for c in self.data_classification:
            if c not in CLASSIFICATIONS and c not in ("internal", "client_scoped"):
                errs.append(f"unknown classification {c}")
        if self.profile == "client" and not self.organization:
            errs.append("client profile needs organization")
        if self.profile == "maintainer" and "APPROVE" in [a.upper() for a in self.actions]:
            errs.append("maintainer must not carry business APPROVE")
        if self.profile == "security_admin" and any(
            a.upper() in ("PUBLISH", "APPROVE") for a in self.actions
        ):
            errs.append("security_admin must not carry business PUBLISH/APPROVE")
        if self.profile == "analyst" and self.database_direct_access:
            errs.append("analyst must never have database_direct_access")
        return errs

    def effective_zones(self) -> List[str]:
        return self.zones or PROFILE_ZONES.get(self.profile, [])


@dataclass
class AgentIdentityChain:
    """Agents never act as the human. Full delegation chain, every hop named."""
    human_actor: str = ""
    delegating_actor: str = "Aurora"   # Aurora → Operator → Pantheon → Tool
    agent_actor: str = ""
    tool_actor: str = ""
    capability_id: str = ""

    def validate(self) -> List[str]:
        errs = []
        if not self.agent_actor:
            errs.append("agent_actor required (agents never inherit human identity)")
        return errs

    def describe(self) -> str:
        return f"{self.human_actor or '?'}→{self.delegating_actor}→{self.agent_actor}→{self.tool_actor or '∅'}"


@dataclass
class CapabilityToken:
    """Scoped least-privilege grant for one agent task. Short-lived by construction."""
    subject: str
    action: str
    version: int = 1
    purpose: str = ""
    issued_by: str = "Operator"
    issued_to: str = ""          # agent_actor
    capability_id: str = ""
    expires_at: str = field(default_factory=lambda: (datetime.now() + timedelta(minutes=30)).isoformat())

    def expired(self) -> bool:
        if not self.expires_at:
            return False
        try:
            return datetime.now() > datetime.fromisoformat(self.expires_at)
        except Exception:
            return True

    def covers(self, subject: str, action: str, version: Optional[int] = None) -> bool:
        if self.expired():
            return False
        if self.subject != subject or self.action.upper() != action.upper():
            return False
        if version is not None and self.version != version:
            return False
        return True


@dataclass
class Delegation:
    """Temporary human→human grant. Auto-expires; never mutates base permissions."""
    granted_by: str
    granted_to: str
    capabilities: List[str] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)
    reason: str = ""
    approval_id: str = ""
    starts_at: str = field(default_factory=lambda: datetime.now().isoformat())
    expires_at: str = field(default_factory=lambda: (datetime.now() + timedelta(hours=48)).isoformat())
    delegation_id: str = ""

    def active(self) -> bool:
        try:
            now = datetime.now()
            if self.starts_at and now < datetime.fromisoformat(self.starts_at):
                return False
            if self.expires_at and now > datetime.fromisoformat(self.expires_at):
                return False
            return True
        except Exception:
            return False


@dataclass
class BreakGlassGrant:
    """Emergency elevation. Reason + audit + auto-expire + post-review flag."""
    granted_to: str
    reason: str
    scopes: List[str] = field(default_factory=list)
    minutes: int = 30
    granted_at: str = field(default_factory=lambda: datetime.now().isoformat())
    expires_at: str = ""
    reviewed: bool = False
    grant_id: str = ""

    def __post_init__(self):
        if not self.expires_at:
            try:
                base = datetime.fromisoformat(self.granted_at)
            except Exception:
                base = datetime.now()
            self.expires_at = (base + timedelta(minutes=self.minutes)).isoformat()

    def active(self) -> bool:
        try:
            return datetime.now() <= datetime.fromisoformat(self.expires_at)
        except Exception:
            return False


@dataclass
class ClientPortalProfile:
    """Per-client portal builder output. Versioned; least-privilege by default."""
    organization: str
    version: str = "v1"
    campaigns: bool = True; assets: bool = True; reports: bool = True
    approvals: bool = True; invoices: bool = True
    allow_comment: bool = True; allow_approve: bool = True
    allow_internal_strategy: bool = False; allow_costs: bool = False
    allow_employees: bool = False; allow_internal_notes: bool = False

    def to_scope(self) -> Dict[str, Any]:
        return {
            "organization": self.organization,
            "resource_scope": [self.organization],
            "zones": ["Z1", "Z0"],
            "actions": ["READ"]
            + (["COMMENT"] if self.allow_comment else [])
            + (["APPROVE", "REJECT"] if self.allow_approve else []),
            "denied": [
                k for k, v in {
                    "internal_strategy": self.allow_internal_strategy,
                    "costs": self.allow_costs,
                    "employees": self.allow_employees,
                    "internal_notes": self.allow_internal_notes,
                }.items() if not v
            ],
        }
