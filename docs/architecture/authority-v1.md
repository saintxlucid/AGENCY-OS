# Authority Model v1 — Access Fabric (FROZEN)

Status: FROZEN. RBAC is one input, not the architecture. Sovereign adjudicates final.

## Chain

```text
RBAC (identity + baseline) → ABAC (context) → Capability (scoped grants)
→ Approval (human authority) → Sovereign (final) → Audit (accountability)
```

RBAC tells who you generally are. ABAC tells what you may access right now.
Capabilities tell agents exactly what they may do. Approvals establish human
authority. Sovereign allows/denies/requires-approval. Audit proves what happened.

## Code

- `aurora/access/model.py` — PrincipalType/Profile/Verb/Classification/Zone,
  AccessProfile, AgentIdentityChain, CapabilityToken, Delegation,
  BreakGlassGrant, ClientPortalProfile. Separation laws enforced in
  `AccessProfile.validate()` (maintainer ∌ business APPROVE, security_admin ∌
  PUBLISH/APPROVE, analyst ∌ database_direct_access).
- `aurora/access/policy.py` — ROLE_TO_PROFILE bridge, PURPOSE_MAX_CLASSIFICATION,
  row_allowed(), FIELD_CLASSIFICATION + redact_row(), filter_query_result().
- `aurora/access/decide.py` — pre_check() (fail-closed, steps 2–6),
  evaluate() (fabric → scope → Sovereign), simulate(), rbac_baseline_allowed(),
  on_access_event() audit hook.
- `aurora/agency/sovereign.py:check()` — fabric pre-check first (profile object
  or dict; zone/capability/delegation/break-glass/agent-chain supported),
  then destructive/human-only/spend/expiry policy. Legacy purpose_mismatch flag kept.
- `aurora/agency/api_guard.py` — route→action map + fabric headers
  (X-Profile/X-Principal/X-Department/X-Zone/X-Purpose/X-Classification/
  X-Resource-Scope/X-Actions/X-Org/X-Agent-Actor). Absent → legacy RBAC path.
- `aurora/api/server.py` — sovereign_gate middleware (deny → 403 JSON),
  access audit hook in lifespan, POST /api/v1/access/simulate,
  GET /api/v1/access/monitor.
- `aurora/agency/access.py` — backwards-compat re-export of the stub surface.

## Profiles (9, not rigid roles)

maintainer / security_admin / administrator / manager / operator_t1 /
operator_t2 / viewer / hr / analyst / client — overlaid with
Department × Resource × Action × Classification × Purpose × Approval × Time × Risk.

Developer authority ≠ business authority. Tier 2 ≠ administrator.
Analyst queries through the policy engine (row filter → purpose → redact),
never direct DB. Clients are external principals: scoped portal + approval gates.

## Zones / classifications / verbs

Zones Z0 public → Z6 system; PROFILE_ZONES + PROFILE_MAX_CLASSIFICATION bind
each profile. Classifications PUBLIC → HIGHLY-RESTRICTED; purpose caps
(CAPACITY_ANALYSIS ≤ INTERNAL, etc.). Verbs: DISCOVER/READ/ANALYZE/PROPOSE/
CREATE/EDIT/SUBMIT/REVIEW/APPROVE/REJECT/EXECUTE/PUBLISH/EXPORT/ADMINISTER/
COMMENT/QUERY/AGGREGATE.

## Invariants

- Agents never inherit human identity (AgentIdentityChain required).
- Capabilities are least-privilege, version-pinned, short-lived (30m default).
- Delegations auto-expire (48h default); break-glass needs reason, auto-expires
  (30m), full audit, post-review flag.
- Expired base never allows without a live grant. Unknown mapping denies.
- Every sensitive decision emits WHO/WHAT/WHEN/WHERE/WHY/RESULT/POLICY/APPROVAL.
