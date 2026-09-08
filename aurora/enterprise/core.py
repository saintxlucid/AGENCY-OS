"""
AGENCY OS — Enterprise Multi-Tenant Core
"""
from __future__ import annotations
import os, json, hashlib, secrets, uuid, re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path


class Permission(Enum):
    ORG_READ = "org:read"; ORG_WRITE = "org:write"; ORG_DELETE = "org:delete"
    ORG_BILLING = "org:billing"; ORG_MEMBERS = "org:members"; ORG_SETTINGS = "org:settings"
    PROJECT_CREATE = "project:create"; PROJECT_READ = "project:read"
    PROJECT_WRITE = "project:write"; PROJECT_DELETE = "project:delete"
    ASSET_CREATE = "asset:create"; ASSET_READ = "asset:read"
    ASSET_WRITE = "asset:write"; ASSET_DELETE = "asset:delete"
    ASSET_EXPORT = "asset:export"; ASSET_APPROVE = "asset:approve"
    WORKFLOW_CREATE = "workflow:create"; WORKFLOW_READ = "workflow:read"
    WORKFLOW_WRITE = "workflow:write"; WORKFLOW_DELETE = "workflow:delete"
    WORKFLOW_EXECUTE = "workflow:execute"
    AGENT_CREATE = "agent:create"; AGENT_READ = "agent:read"
    AGENT_WRITE = "agent:write"; AGENT_DELETE = "agent:delete"
    AGENT_EXECUTE = "agent:execute"
    ANALYTICS_READ = "analytics:read"; ANALYTICS_EXPORT = "analytics:export"
    ADMIN_FULL = "admin:full"; BILLING_MANAGE = "billing:manage"
    INTEGRATION_MANAGE = "integration:manage"; SECURITY_AUDIT = "security:audit"


class Role(Enum):
    OWNER = "owner"; ADMIN = "admin"; MANAGER = "manager"
    CREATIVE_DIRECTOR = "creative_director"; DESIGNER = "designer"
    DEVELOPER = "developer"; EDITOR = "editor"; RESEARCHER = "researcher"
    CLIENT = "client"; VIEWER = "viewer"; BILLING = "billing"

    @classmethod
    def permissions(cls, role: 'Role') -> Set[Permission]:
        m = {
            cls.OWNER: {p for p in Permission},
            cls.ADMIN: {Permission.ORG_READ, Permission.ORG_WRITE, Permission.ORG_MEMBERS,
                Permission.ORG_SETTINGS, Permission.PROJECT_CREATE, Permission.PROJECT_READ,
                Permission.PROJECT_WRITE, Permission.PROJECT_DELETE, Permission.ASSET_CREATE,
                Permission.ASSET_READ, Permission.ASSET_WRITE, Permission.ASSET_DELETE,
                Permission.ASSET_EXPORT, Permission.ASSET_APPROVE, Permission.WORKFLOW_CREATE,
                Permission.WORKFLOW_READ, Permission.WORKFLOW_WRITE, Permission.WORKFLOW_DELETE,
                Permission.WORKFLOW_EXECUTE, Permission.AGENT_CREATE, Permission.AGENT_READ,
                Permission.AGENT_WRITE, Permission.AGENT_DELETE, Permission.AGENT_EXECUTE,
                Permission.ANALYTICS_READ, Permission.ANALYTICS_EXPORT,
                Permission.INTEGRATION_MANAGE, Permission.SECURITY_AUDIT},
            cls.MANAGER: {Permission.ORG_READ, Permission.ORG_MEMBERS, Permission.PROJECT_CREATE,
                Permission.PROJECT_READ, Permission.PROJECT_WRITE, Permission.ASSET_CREATE,
                Permission.ASSET_READ, Permission.ASSET_WRITE, Permission.ASSET_EXPORT,
                Permission.ASSET_APPROVE, Permission.WORKFLOW_CREATE, Permission.WORKFLOW_READ,
                Permission.WORKFLOW_WRITE, Permission.WORKFLOW_EXECUTE, Permission.AGENT_CREATE,
                Permission.AGENT_READ, Permission.AGENT_EXECUTE, Permission.ANALYTICS_READ,
                Permission.ANALYTICS_EXPORT},
            cls.DESIGNER: {Permission.ORG_READ, Permission.PROJECT_READ, Permission.ASSET_CREATE,
                Permission.ASSET_READ, Permission.ASSET_WRITE, Permission.ASSET_EXPORT,
                Permission.WORKFLOW_READ, Permission.WORKFLOW_EXECUTE, Permission.AGENT_READ,
                Permission.AGENT_EXECUTE},
            cls.DEVELOPER: {Permission.ORG_READ, Permission.PROJECT_READ, Permission.ASSET_CREATE,
                Permission.ASSET_READ, Permission.ASSET_WRITE, Permission.ASSET_EXPORT,
                Permission.WORKFLOW_CREATE, Permission.WORKFLOW_READ, Permission.WORKFLOW_WRITE,
                Permission.WORKFLOW_EXECUTE, Permission.AGENT_CREATE, Permission.AGENT_READ,
                Permission.AGENT_WRITE, Permission.AGENT_EXECUTE},
            cls.CLIENT: {Permission.ORG_READ, Permission.PROJECT_READ, Permission.ASSET_READ,
                Permission.ASSET_APPROVE},
            cls.VIEWER: {Permission.ORG_READ, Permission.PROJECT_READ, Permission.ASSET_READ},
        }
        return m.get(role, set())


@dataclass
class User:
    user_id: str; email: str; name: str
    avatar_url: Optional[str] = None
    roles: Dict[str, Role] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)
    mfa_enabled: bool = False; email_verified: bool = False
    last_login: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "active"

    def has_permission(self, org_id: str, permission: Permission) -> bool:
        role = self.roles.get(org_id)
        return permission in Role.permissions(role) if role else False

    def add_to_org(self, org_id: str, role: Role):
        self.roles[org_id] = role


@dataclass
class Organization:
    org_id: str; name: str; slug: str
    description: Optional[str] = None; logo_url: Optional[str] = None
    website: Optional[str] = None; industry: Optional[str] = None
    settings: Dict[str, Any] = field(default_factory=dict)
    billing_plan: str = "starter"; billing_status: str = "active"
    max_projects: int = 10; max_storage_gb: int = 50
    max_team_members: int = 10; max_workflows: int = 20; max_agents: int = 10
    enabled_modules: List[str] = field(default_factory=lambda: [
        "core","design","video","research","marketing","business","automation","developer"])
    member_count: int = 0; project_count: int = 0; asset_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def is_enterprise(self) -> bool:
        return self.billing_plan in ("enterprise", "custom")

    def can_create_project(self) -> bool:
        return self.project_count < self.max_projects

    def can_add_member(self) -> bool:
        return self.member_count < self.max_team_members


@dataclass
class Team:
    team_id: str; org_id: str; name: str
    description: Optional[str] = None; color: Optional[str] = None
    leader_id: Optional[str] = None; member_ids: List[str] = field(default_factory=list)
    project_ids: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Workspace:
    workspace_id: str; org_id: str; name: str
    project_id: Optional[str] = None; team_id: Optional[str] = None
    description: Optional[str] = None; type: str = "creative"
    status: str = "active"
    layout: Dict[str, Any] = field(default_factory=dict)
    pinned_assets: List[str] = field(default_factory=list)
    default_model: str = "gpt-4o"
    auto_analyze: bool = True; auto_tag: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Project:
    project_id: str; org_id: str; name: str
    description: Optional[str] = None; client_id: Optional[str] = None
    team_id: Optional[str] = None; workspace_ids: List[str] = field(default_factory=list)
    status: str = "planning"; priority: str = "medium"; progress: float = 0.0
    start_date: Optional[str] = None; due_date: Optional[str] = None
    completed_at: Optional[str] = None; brief: Optional[str] = None
    goals: List[str] = field(default_factory=list)
    deliverables: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    asset_count: int = 0; task_count: int = 0; comment_count: int = 0
    owner_id: Optional[str] = None; member_ids: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Client:
    client_id: str; org_id: str; name: str
    description: Optional[str] = None; industry: Optional[str] = None
    website: Optional[str] = None; logo_url: Optional[str] = None
    contacts: List[Dict[str, str]] = field(default_factory=list)
    primary_contact_id: Optional[str] = None
    brand_guidelines: Optional[str] = None
    brand_colors: List[str] = field(default_factory=list)
    brand_fonts: List[str] = field(default_factory=list)
    brand_voice: Optional[str] = None; target_audience: Optional[str] = None
    project_ids: List[str] = field(default_factory=list)
    total_billed: float = 0.0; total_projects: int = 0; status: str = "active"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class EnterpriseCore:
    def __init__(self, persist_dir: str = "./agency_os_data"):
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.users: Dict[str, User] = {}
        self.organizations: Dict[str, Organization] = {}
        self.teams: Dict[str, Team] = {}
        self.workspaces: Dict[str, Workspace] = {}
        self.projects: Dict[str, Project] = {}
        self.clients: Dict[str, Client] = {}
        self._sessions: Dict[str, Dict] = {}
        self._api_keys: Dict[str, str] = {}
        self._invite_codes: Dict[str, Dict] = {}
        self._audit_log: List[Dict] = []
        print("AGENCY OS Enterprise Core initialized")

    def create_user(self, email: str, name: str, password: str) -> User:
        for u in self.users.values():
            if u.email == email: raise ValueError(f"User {email} exists")
        uid = str(uuid.uuid4())[:12]
        u = User(user_id=uid, email=email, name=name)
        u.preferences["_pw"] = hashlib.sha256(password.encode()).hexdigest()
        self.users[uid] = u
        self._audit("user_created", uid, {"email": email})
        return u

    def authenticate(self, email: str, password: str) -> Optional[str]:
        for u in self.users.values():
            if u.email == email:
                if u.preferences.get("_pw") == hashlib.sha256(password.encode()).hexdigest():
                    tok = secrets.token_urlsafe(32)
                    self._sessions[tok] = {"user_id": u.user_id, "expires": (datetime.now()+timedelta(days=7)).isoformat()}
                    u.last_login = datetime.now().isoformat()
                    return tok
                return None
        return None

    def create_org(self, name: str, owner_id: str, plan: str = "starter", description: Optional[str] = None) -> Organization:
        if owner_id not in self.users: raise ValueError("Owner not found")
        oid = str(uuid.uuid4())[:12]
        slug = re.sub(r'[^a-z0-9]', '-', name.lower()).strip('-')
        limits = {"starter": (10,50,10,20,10), "professional": (50,500,50,100,50), "enterprise": (9999,9999,9999,9999,9999)}
        l = limits.get(plan, limits["starter"])
        org = Organization(org_id=oid, name=name, slug=slug, description=description,
            billing_plan=plan, max_projects=l[0], max_storage_gb=l[1],
            max_team_members=l[2], max_workflows=l[3], max_agents=l[4])
        self.organizations[oid] = org
        self.users[owner_id].add_to_org(oid, Role.OWNER)
        org.member_count = 1
        self._audit("org_created", owner_id, {"org_id": oid, "name": name})
        return org

    def create_team(self, org_id: str, name: str, leader_id: Optional[str] = None) -> Team:
        tid = str(uuid.uuid4())[:12]
        t = Team(team_id=tid, org_id=org_id, name=name, leader_id=leader_id)
        self.teams[tid] = t
        return t

    def create_workspace(self, org_id: str, name: str, ws_type: str = "creative", project_id: Optional[str] = None) -> Workspace:
        wid = str(uuid.uuid4())[:12]
        w = Workspace(workspace_id=wid, org_id=org_id, name=name, type=ws_type, project_id=project_id)
        self.workspaces[wid] = w
        return w

    def create_project(self, org_id: str, name: str, description: Optional[str] = None,
                       client_id: Optional[str] = None, team_id: Optional[str] = None,
                       brief: Optional[str] = None, owner_id: Optional[str] = None, **kwargs) -> Project:
        org = self.organizations.get(org_id)
        if not org: raise ValueError("Org not found")
        if not org.can_create_project(): raise ValueError("Max projects reached")
        pid = str(uuid.uuid4())[:12]
        p = Project(project_id=pid, org_id=org_id, name=name, description=description,
            client_id=client_id, team_id=team_id, brief=brief, owner_id=owner_id,
            member_ids=[owner_id] if owner_id else [], **kwargs)
        self.projects[pid] = p
        org.project_count += 1
        if team_id and team_id in self.teams: self.teams[team_id].project_ids.append(pid)
        if client_id and client_id in self.clients:
            self.clients[client_id].project_ids.append(pid)
            self.clients[client_id].total_projects += 1
        self._audit("project_created", owner_id, {"project_id": pid, "name": name})
        return p

    def create_client(self, org_id: str, name: str, **kwargs) -> Client:
        cid = str(uuid.uuid4())[:12]
        c = Client(client_id=cid, org_id=org_id, name=name, **kwargs)
        self.clients[cid] = c
        return c

    def invite_member(self, org_id: str, email: str, role: Role, invited_by: str):
        """Invite a member to organization. Returns user_id or invite_code."""
        if org_id not in self.organizations:
            raise ValueError(f"Organization {org_id} not found")
        org = self.organizations[org_id]
        if not org.can_add_member():
            raise ValueError(f"Max members reached ({org.max_team_members})")
        # Check if user already exists
        for user in self.users.values():
            if user.email == email:
                user.add_to_org(org_id, role)
                org.member_count += 1
                self._audit("member_added", invited_by, {"org_id": org_id, "user_id": user.user_id, "role": role.value})
                return user.user_id
        # Create invite code
        invite_code = secrets.token_urlsafe(16)
        self._invite_codes[invite_code] = {
            "org_id": org_id, "role": role, "email": email,
            "invited_by": invited_by,
            "expires_at": (datetime.now() + timedelta(days=7)).isoformat()}
        self._audit("invite_sent", invited_by, {"org_id": org_id, "email": email, "role": role.value})
        return invite_code

    def _audit(self, action: str, uid: Optional[str], details: Dict):
        self._audit_log.append({"event_id": str(uuid.uuid4())[:12], "action": action,
            "user_id": uid, "details": details, "timestamp": datetime.now().isoformat()})

    def status(self) -> Dict:
        return {"users": len(self.users), "orgs": len(self.organizations),
            "projects": len(self.projects), "clients": len(self.clients),
            "teams": len(self.teams), "workspaces": len(self.workspaces)}

    def save(self):
        data = {"users": {k: asdict(v) for k,v in self.users.items()},
            "orgs": {k: asdict(v) for k,v in self.organizations.items()},
            "teams": {k: asdict(v) for k,v in self.teams.items()},
            "workspaces": {k: asdict(v) for k,v in self.workspaces.items()},
            "projects": {k: asdict(v) for k,v in self.projects.items()},
            "clients": {k: asdict(v) for k,v in self.clients.items()},
            "audit": self._audit_log}
        with open(self.persist_dir / "core.json", 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def load(self):
        p = self.persist_dir / "core.json"
        if not p.exists(): return
        with open(p) as f: data = json.load(f)
        for k,v in data.get("users",{}).items(): self.users[k] = User(**v)
        for k,v in data.get("orgs",{}).items(): self.organizations[k] = Organization(**v)
        for k,v in data.get("teams",{}).items(): self.teams[k] = Team(**v)
        for k,v in data.get("workspaces",{}).items(): self.workspaces[k] = Workspace(**v)
        for k,v in data.get("projects",{}).items(): self.projects[k] = Project(**v)
        for k,v in data.get("clients",{}).items(): self.clients[k] = Client(**v)
        self._audit_log = data.get("audit", [])


async def create_agency_os(persist_dir: str = "./agency_os_data") -> EnterpriseCore:
    core = EnterpriseCore(persist_dir)
    core.load()
    return core