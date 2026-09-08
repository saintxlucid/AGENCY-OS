# Reconciliation — Substrate → Canonical (PHASE 0)

Date: 2026-09-08. Method: file:line evidence. Rule: wrap > refactor > deprecate. No parallel brains.

## Identity clarification (locked)
- AURORA = control-plane identity (conductor + governor + human command).
- AuroraCore (`aurora/core.py:118`) = implementation substrate → evolves into kernel. No second orchestrator.
- CreativeMemoryGraph (`aurora/memory/graph.py:59`) → Agency Graph substrate (Chroma + NetworkX, lazy embedder).
- CRPRuntime (`aurora/enterprise/runtime.py:207`, preflight `:283`, health `:561`) → Governed Action / Operator substrate.
- GovernanceEngine (`aurora/enterprise/governance.py:382`, evaluate `:411`, default_policies `:154`) → Sovereign enforcement substrate.
- WorkflowEngine (`aurora/workflows/engine.py:147`, handlers, campaign template `:703`) → Delivery pipeline substrate (3 templates max in v1).

## Classification matrix

| Subsystem | Location | Verdict | Canonical role | Seam / action |
|---|---|---|---|---|
| AuroraCore init/memory | `core.py:118,150,165` | EXISTS+NEEDS REFACTOR | Aurora kernel substrate | Keep. Done: memory_dir overridable, status field. Next: conductor methods delegate to ALPHAs, Sovereign gate on create/publish paths. |
| Memory graph | `memory/graph.py:59,72,95` | EXISTS+NEEDS REFACTOR | Agency Graph substrate | Keep Chroma+NetworkX. Bind `aurora/agency/schema.py` validation + History append. Do not replace with parallel store. |
| Observation | `observation/watcher.py:74,93,178,215` FileWatcher + LiveObserver events list `:85` | PARTIAL | Sentinel substrate | Wrap: Sentinel.observe/stage consumes ObservationEvent. Add subscription (not duplicate polling), coverage gaps, provenance hash. |
| Documents/synthesis | `aurora/documents/`, prompts | PARTIAL | Scribe substrate | Insert citation gate (`scribe.propose` requires evidence). Drafts expire/regenerate from graph. |
| CRP Runtime | `enterprise/runtime.py:207,239,243,256,283` Intent/Result/RuntimeBlocked `:62,115,166` | EXISTS+WRONG BOUNDARY | Governed execution substrate | Decide: Operator plans → CRP preflight+execute, single path. Our `alphas/operator.py` must call `CRPRuntime.preflight` not duplicate it. TODO: bind. |
| WorkflowEngine | `workflows/engine.py:147,194,340,703` | EXISTS+CORRECT | Delivery pipelines | Keep. Constrain to 3 campaign templates in v1. Operator manages instances, Engine executes nodes. |
| Governance | `enterprise/governance.py:40,56,85,154,246,310,382,411,486` | EXISTS+CORRECT | Sovereign substrate | Our `agency/sovereign.py` wraps it (policy pack L0-L4). Add thresholds as config. No fork. Single call path with RBAC. |
| RBAC | `enterprise/core.py:13,32,39,76,86,95` User.has_permission, Role.permissions | EXISTS+CORRECT | Authority/identity | Sovereign.check must consult RBAC. No dual enforcement. |
| EnterpriseCore persist | `enterprise/core.py:178,298,309` | EXISTS+NEEDS REFACTOR | Org/team/workspace store | Keep. Tests isolated to tmp. Stale local `agency_os_data` is dev data, gitignored. |
| ERP models | `enterprise/erp.py:42,52,90,128,207` Lead/Opp/Task/Invoice/Asset | EXISTS+NEEDS REFACTOR | Agency Reality model | Fixed IDs (opp_id/task_id/asset_id, lead_id link). Next: bind STATES/TRANSITIONS from schema. No orphan invoices/tasks. |
| AI-ERP | `enterprise/ai_erp.py:38,60,100,151,182,210,376` query/churn/forecast/capacity | PARTIAL | Business intel workers | Map to Pantheon Performance/Finance workers later. Read-only over ERP, proposals only. |
| Intelligence 6 | `aurora/intelligence/` narrative/visual/symbolism/design/marketing/psychological | EXISTS+CORRECT labor | Pantheon intel labor | Wrap as supervised workers: proposal shape + verification + escalation. No direct Reality writes. |
| MCP/A2A | `protocols/mcp_layer.py:70,115,260,319,338,355,376` call_tool/delegate/register | EXISTS+CORRECT | Tool substrate | Add allowlist/deny + idempotency envelope + scoped grants. `call_tool` is the only exec surface Operator uses. |
| AIOps ledger | `enterprise/aiops.py:60,134,199,220,238` RateCard/AICall/Budget/Ledger | PARTIAL | Economic observability | Bind to Operator receipts + loop health (cost per asset/plan, budget caps). |
| FastAPI | `api/server.py:252,276,283,355,375,419,457,470,589,626,696` 20+ routes | EXISTS+WRONG BOUNDARY | External surface | Add Sovereign middleware on mutating POST/DELETE (interpret, projects, observe, erp/*, batch, webhooks). Reads stay open per RBAC. |
| CLI | `aurora/cli.py`, entrypoints | EXISTS+CORRECT | Operator/dev interface | Keep `astra/astra-os` aliases. Add slice commands later. |
| Agency schema (new) | `aurora/agency/schema.py, messages.py` | STUB→NEEDS BIND | Contracts | Not a replacement store. Validation + envelopes only. Must be called by Graph/Runtime/API paths. |
| ALPHAs (new) | `aurora/alphas/sentinel.py, scribe.py, operator.py` | STUB→NEEDS BIND | Control-plane services | Must delegate to substrates above (Watcher, docs, CRP, MCP), not reimplement. TODO bindings explicit. |
| Event fabric | prints + lists (`watcher events:85`, audit `_audit`) | MISSING | Append-only bus/log | Decide: explicit `event.emit` to observation_log + History. No new infra in v1 (log convention). |

## Seam decisions (binding, not duplicating)
1. Identity: EnterpriseCore IDs + `ag_<kind>_*` ULIDs coexist via adapter (Enterprise objects get `ag_*` alias on promotion to graph). No dual primary keys for same fact.
2. Enforcement: `Sovereign.check()` → `GovernanceEngine.evaluate()` + `User.has_permission()`. One path. API + Operator + CRP all call it.
3. Execution: Operator builds Plan → `CRPRuntime.preflight(intent)` → `WorkflowEngine`/tools execute → Receipt → History. Operator never duplicates preflight logic.
4. Observation: `LiveObserver` events → `Sentinel.observe()` (subscription). No second watcher.
5. Synthesis: existing doc/synthesis → `Scribe.propose()` gate (evidence required) before human surface.
6. Tools: `MCPLayer.call_tool` sole exec. Allowlist per worker/ALPHA, idempotency keys, scoped grants.
7. Costs: `AIOpsLedger.record` on every Operator receipt + Aurora delegation. Budget caps enforced pre-flight.

## What we will NOT do (anti-fiction rules)
- No new graph store beside CreativeMemoryGraph. No new policy engine beside GovernanceEngine. No new orchestrator beside AuroraCore/CRP.
- New `aurora/agency/*` + `aurora/alphas/*` are contracts + services that delegate. Any file that duplicates substrate logic gets deleted or bound within one turn.
- Docs amended when they contradict code. Code refactored when it violates contracts. Neither drifts.

## Immediate TODOs (ordered)
1. [DONE] Bind Operator→CRP preflight — `aurora/alphas/operator.py:_get_runtime/execute_step Gate 0/preflight_via_crp` (shared runtime, single path; Sovereign version-pin retained for asset.publish).
2. [DONE] Bind Sentinel→LiveObserver subscription (`aurora/observation/watcher.py:subscribe_sentinel/_sentinel_sinks` fan-out; `Sentinel.ingest_event` owns hash/log/stage) + Scribe citation gates (`Scribe.propose_learning`, `gate_doc_cites`).
3. [DONE] Sovereign middleware for API mutating routes — `aurora/agency/api_guard.py:SOVEREIGN_ROUTE_MAP/action_for/guard_or_403` + `sovereign_gate` http middleware in `aurora/api/server.py` (reads open per RBAC, deny → 403 JSON).
4. [DONE] ERP STATES/TRANSITIONS binding — `aurora/agency/erp_bindings.py` (task/campaign/invoice adapters; `transition_erp_task`); enforced in API (`PATCH /api/v1/erp/tasks/{id}/state`, invoice linkage 422 on orphans).
5. [DONE] Amend frozen docs with substrate pointers (this file is the index) + `docs/architecture/authority-v1.md` (Authority Model v1: RBAC→ABAC→capability→approval→Sovereign→audit; `aurora/access/` canonical, `aurora/agency/access.py` shim).

## Documentation checkpoint (2026-09-08)
- Index: `docs/architecture/README.md` (read order; authority-model-v1 = design spec, authority-v1 = implementation record).
- Release notes: `CHANGELOG.md [Unreleased]` (added/fixed/verification: 245 passed / 73 skipped / 0 failed).
- Personal files never committed: `.mcp.json`, `ASTRA.md`, `SOUL.md`, `IDENTITY.md`, `USER.md`, `HEARTBEAT.md`, `Scripts/`, `Skills/`, `Tools/`, `Templates/`, `TOOLS.md`, media/data dirs (gitignore rooted).

## Documentation checkpoint 2 (2026-09-08) — full-service commercial
- Intake filled: `agency-intelligence-model.md` v1 findings (titles→capabilities, 17 sections with mapping targets).
- Research persisted: `agency-intelligence-research.md` (Enterprise OS north star + PHASE 0 per-concept classifications).
- Commercial ERP: Pitch/Scope/ChangeOrder/Retainer models (`enterprise/erp.py §1b`) + canonical transition adapters (`erp_bindings`: lead alias map, pitch/scope/retainer/launch/distribution gates).
- Sovereign gates: `preflight_scope_change` (numbered ChangeOrder + delta approval) + `preflight_launch` (QC + exact version + receipt path).
- Verification: 246 passed / 73 skipped / 0 failed. Index extended (README items 11–12).
