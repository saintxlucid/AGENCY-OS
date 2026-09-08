# Authority Model v1 — Design Spec (FROZEN)

Status: FROZEN design spec. Implementation record: `authority-v1.md`.
Read both: design above, code here. Neither drifts without the other.

## Thesis

Access in AGENCY OS is **not one giant role enum**. It is a multi-surface,
multi-dimensional fabric where role, operational tier, department, data scope,
and approval authority are separate dimensions:

```text
IDENTITY → ACCESS PROFILE → AUTHORITY LEVEL → DEPARTMENT SCOPE
→ RESOURCE SCOPE → ACTION PERMISSION → APPROVAL REQUIREMENT → DATA CLASSIFICATION
```

Chain: **RBAC (who you are) → ABAC (what you may access now) →
Capability (what an agent may do) → Approval (human authority) →
Sovereign (final) → Audit (proof).**

## Surfaces

```text
SOVEREIGN (global policy + enforcement)
└── AURORA (control plane / command UI)
    ├── MAINTAINER / DEVELOPER — Tier 0, system access (code, config, schemas,
    │   agents, tools, MCP, deploys, diagnostics). Developer authority ≠ business
    │   authority: no campaign approval, no publish.
    ├── MANAGEMENT / ADMIN — Tier 2 business view (employees, clients, projects,
    │   budgets, approvals, revenue). Still constrained by Sovereign (e.g. publish
    │   needs Creative Director approval → DENY / APPROVAL REQUIRED).
    └── OPERATIONS — Tier 1 (assigned work, submit, collaborate; cannot self-approve,
        publish, govern, or see other departments) → Tier 2 (supervise T1, review,
        assign, department approve, trigger workflows; still ≠ administrator).
```

Cross-cutting surfaces:

- **Cross-Department Viewer** — READ across departments, never WRITE/EXECUTE/APPROVE/ADMIN.
- **HR** — own boundary (HR Viewer / Operator / Manager / Administrator);
  field-level: name → authorized users, performance → manager/HR,
  salary/bank/disciplinary → restricted tiers.
- **Data / Universal Analyst** — organization-wide query via a **semantic/policy
  query engine** (row policy → column policy → redaction → audit), never raw
  SQL/root. Powerful query, flamethrower denied.
- **Client** — external principal: `CLIENT → CLIENT ORG → USERS → PORTAL →
  SCOPED RESOURCES`. Sees own campaigns/briefs/assets/approvals/reports/invoices
  only. Approval-aware: agency submits version → client Approve/Reject/Request
  Changes → Approval object → Sovereign → Operator → next state.

## Fabric dimensions (v2 overlays)

1. **Separate identity/role/scope/authority** — "manager" never implies "sees everything."
2. **Security Administrator** split from Maintainer (identities/roles/policies/audit
   vs infra/deploys; neither gets business data writes for free).
3. **Temporary/delegated access** — grantor/grantee/capabilities/resources/reason/
   window/approval; auto-expires; no base-permission mutation.
4. **Break-glass** — reason → Sovereign → temporary elevation → full audit →
   auto-expire → post-review. Never silent admin.
5. **Data classification** — PUBLIC / INTERNAL / CLIENT-CONFIDENTIAL / SENSITIVE /
   RESTRICTED / HIGHLY-RESTRICTED on every datum; access = user + role + resource
   + classification + purpose.
6. **Purpose-based access** — capacity analysis justifies workload, not salaries.
7. **Row + field security** — analyst sees name/department/utilization, never
   salary/bank/ID/address/medical.
8. **Agent identity** — `human → Aurora → Operator → Pantheon agent → tool`
   carried on every action; agents never ride the spawner's identity.
9. **Capability tokens** — subject/action/version/expiry/purpose/issuer; least
   privilege per task, fits ALPHA delegation.
10. **Verbs** — DISCOVER/READ/ANALYZE/PROPOSE/CREATE/EDIT/SUBMIT/REVIEW/APPROVE/
    REJECT/EXECUTE/PUBLISH/EXPORT/ADMINISTER (+COMMENT/QUERY/AGGREGATE).
11. **Access zones** — Z0 public → Z6 system; multi-zone without global privilege.
12. **Real-time access monitoring** — users/agents/elevations/break-glass/failures/
    sensitive queries/approvals/expiries/violations + WHO/WHAT/WHEN/WHERE/WHY/RESULT.
13. **Continuous evaluation** — login ≠ access; re-evaluate on role/dept/assignment/
    expiry/risk/device/anomaly/policy change.
14. **Client permission builder** — per-client portal profiles (e.g. White Point v3).
15. **Access simulation** — dry-run with reason + redacted alternative.
16. **Access graph** — authorization as Agency Graph relationships; Sovereign
    evaluates graph context.
17. **Unified identity** — HUMAN / AGENT / CLIENT principals → profiles/cards →
    fabric → resource/action/data scopes → Sovereign → ALLOW/DENY/APPROVAL → audit.

## Role counts as profiles, not ranks

9 profiles (security_admin deliberately split from maintainer):
maintainer, security_admin, administrator, manager, operator_t1, operator_t2,
viewer, hr, analyst, client — overlaid with Department × Resource × Action ×
Classification × Purpose × Approval × Time × Risk.

## Non-goals (v1)

No bulk destructives, no permanent elevation without review, no direct DB for
analysts, no agent ambient autonomy, no cross-client visibility, no silent grants.
