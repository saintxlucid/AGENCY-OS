# Architecture — Canonical Index (FROZEN checkpoints + live evolution)

Read order for new engineers:
1. `adr-001-northstar-C.md` — north star C (internal weapon first, productizable by namespace).
2. `reconciliation.md` — substrate → canonical map (PHASE 0). Start here before any implementation.
3. `agency-graph-v1.md` — nodes, edges, states, invariants (the spine).
4. `layer-contracts.md` — Reality / Intelligence / Action / Decision contracts + loop.
5. `sovereign-v1.md` — L0-L4, thresholds, destructive taxonomy, escalation, audit.
6. `authority-model-v1.md` — design spec: multi-surface fabric (profiles, verbs, zones, classifications, purpose, delegation, break-glass, agent identity, capabilities, monitoring).
7. `authority-v1.md` — implementation record: exact modules (access/model, policy, decide, api_guard headers, server endpoints) as built. Design above, code here.
8. `builtin-agents.md` — AURORA → ALPHA 01/02/03 → Pantheon → Tools (mandates, authority, verification).
9. `proving-slice.md` — Brief→Learning slice: swimlanes + message schemas + pass criteria.
10. `implementation-plan.md` — reuse map + 5 phases + acceptance + out-of-scope.

Related (non-frozen context): `overview.md`, `crp.md`, `pdftool.md`.

Amendment rule: docs amended when they contradict code; code refactored when it violates contracts. Neither drifts. Parallel tracks reconcile via `reconciliation.md`, never via duplicate stores/engines/orchestrators.

Checkpoints: 318 passed (+316 subtests) / 0 failed (2026-09-08). Chain: Sovereign→Aurora+Identity→Decision→scopes→Approval→Execution→Operator→CRP.
