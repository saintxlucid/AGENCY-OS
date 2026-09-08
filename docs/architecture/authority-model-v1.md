# Authority Model v1 — Access Fabric (FROZEN amendment)

Status: FROZEN. Amends reconciliation.md. RBAC is one input, not the architecture.

## Hierarchy (locked)
SOVEREIGN (global policy + enforcement)
→ AURORA (control plane / command UI) + IDENTITY (access engine)
→ ACCESS DECISION → RESOURCE/ACTION/DATA scopes → APPROVAL GATE → EXECUTION GATE → OPERATOR → CRP Runtime.
RBAC → baseline identity/permissions. ABAC → context/resource/department/data/purpose.
Capability security → scoped agent + temporary permissions. Approvals → human authority.
Sovereign → final adjudication. Audit → immutable accountability.

Rule: RBAC tells who you generally are. ABAC what you can access now. Capabilities what agents may do.
Approvals establish human authority. Sovereign adjudicates. Audit proves.

## Separation law (locked)
Developer authority ≠ Business authority. Tier 2 ≠ Administrator.
Maintainer ≠ Analyst ≠ Manager ≠ Operator ≠ Client. None inherit the others.
Security Administrator ≠ System Maintainer (privilege separation: identities/policies/audit vs runtime/deploy).

## Principal profiles (9 access profiles, not rigid roles)
Maintainer/Developer (Tier 0 system: code, config, schemas, agents, tools, MCP, logs, deploy, diagnostics — no business approval).
Security Administrator (identities, roles, policies, audit, auth, incidents, reviews — no business data mutation).
Administrator/Manager (org as business: projects, people, budgets, approvals, capacity — constrained by Sovereign).
Operator T1 (assigned work: view/create/update tasks, upload, submit, comment — no self-approve/publish/governance).
Operator T2 (T1 + supervise T1, review, assign, department approve, trigger workflows — no Finance/HR/DB admin).
Cross-Department Viewer (READ across departments, no WRITE/EXECUTE/APPROVE/ADMIN).
HR (own boundary: Viewer/Operator/Manager/Administrator; field-level: name→authorized, salary/bank/disciplinary→restricted).
Data/Universal Analyst (query/aggregate/export via Semantic Policy Query Engine + row/column security + redaction — never direct SQL/root).
Client (external principal: scoped portal per client org — campaigns/briefs/assets/approvals/reports/invoices; approval-aware; never internal).

## Dimensions (every decision)
IDENTITY → ACCESS PROFILE → AUTHORITY LEVEL → DEPARTMENT SCOPE → RESOURCE SCOPE → ACTION PERMISSION → APPROVAL REQUIREMENT → DATA CLASSIFICATION.
Plus: purpose, time (delegation/expiry), risk (continuous evaluation).

Verbs (canonical, not READ/WRITE): DISCOVER, READ, ANALYZE, PROPOSE, CREATE, EDIT, SUBMIT, REVIEW, APPROVE, REJECT, EXECUTE, PUBLISH, EXPORT, ADMINISTER.
Client subset: READ, COMMENT, APPROVE, REQUEST_CHANGES.

## Data classification (locked)
PUBLIC, INTERNAL, CLIENT-CONFIDENTIAL, SENSITIVE, RESTRICTED, HIGHLY-RESTRICTED.
Access = user + role + resource + classification + purpose. Purpose-limited: capacity analysis allows workload/utilization, denies salaries.

## Zones
Z0 PUBLIC, Z1 CLIENT PORTAL, Z2 OPERATIONAL, Z3 MANAGEMENT, Z4 SENSITIVE, Z5 SECURITY/GOVERNANCE, Z6 SYSTEM/MAINTAINER.
Multi-zone access without global privilege.

## Delegation / break-glass (locked)
Delegation {granted_by/to, capabilities, resources, reason, starts/expires, approval_id} auto-expires, no permanent change.
Break-glass: reason → Sovereign evaluation → temporary elevation → full audit → auto-expire → post-review. Never silent.

## Agent identity (locked)
Chain: human_actor → delegating (Aurora) → agent_actor (ALPHA/Pantheon) → tool_actor. Every action carries all four.
Agents never operate under human identity. Capabilities scoped: {subject, action, version, expires 30m, purpose, issued_by Operator}.

## Query path (analyst safety)
Query → Sovereign → RBAC → row-level → column-level → classification → execution → audit. No database flamethrower.

## Monitoring + continuous evaluation
Access Command Center: active users/agents, elevated/break-glass sessions, failed auth, sensitive queries, pending approvals, expiring delegations, violations — with WHO/WHAT/WHEN/WHERE/WHY/RESULT/POLICY/APPROVAL.
Re-evaluate on: role/dept/assignment change, project close, approval expiry, risk/device/anomaly, sensitive request, policy change. LOGIN ≠ ACCESS.

## Product surfaces (v1 deferred, designed)
Client Permission Builder (per-client portal profiles), Access Simulation (dry-run with reason + redacted alternative), Access Graph (User→Role→Dept→Client→Project→Asset→Action as graph context for Sovereign).

## Amendment to reconciliation
RBAC (`enterprise/core.py`) promoted to identity/baseline layer. Sovereign above it. ABAC + capabilities + approvals added as dimensions. No replacement of existing RBAC tables.
