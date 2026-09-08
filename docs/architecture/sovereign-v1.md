# Sovereign v1 — Kernel Authority (FROZEN)

Status: FROZEN. Unbypassable. Only path to mutation.

## Authority levels
- L0 Read: authenticated member with read on org/namespace.
- L1 Propose: agents + humans create drafts/proposals/critiques/tasks.
- L2 Approve-internal: Producers/Strategists approve internal (draft→in_review, wip→in_qc).
- L3 Approve-external (human-only v1): Brief approval, Concept→Production, Asset→Publication, send to client, performance reported.
- L4 Destructive/Financial (human-only + dual over threshold): budget/scope/retainer change, takedown, guideline change, client stage change, permission grants.

## Thresholds (defaults, locked)
- Client-visible send: L3 human. Publish: L3 human + exact version + unexpired Approval (72h).
- Spend: <$500 Producer L2, $500–5k AD L3, >$5k L4 dual (AD + owner).
- Brand guideline change: L4 + new version + re-eval flag on in-flight Concepts.
- Kill campaign / churn client: L4 + rationale + learning capture required.

## Destructive taxonomy (closed list)
archive, takedown, budget_change, scope_change, guideline_change, client_stage_change, retainer_change, delete_request (soft only), permission_grant, external_send.
Each requires: Approval node, actor, reason, before/after snapshot, undo plan where possible. No bulk destructives in v1.

## Escalation
- Agent blocked / confidence <0.65 / policy conflict → escalate to owner_role with context packet.
- Human reject → changes_requested + next-version expectations, auto-spawn Revision Task.
- Approval pending >48h → nudge → escalate to AD. Surfaced as Blocker, never silent.
- Tool failure → 3x backoff → escalate, never silent loop. Verification failure → block downstream + notify Producer.

## Audit
History on nodes + edges + actor + timestamp + rationale. Queryable: who approved what version on what evidence when. Exportable immutable log. No separate silo in v1.
