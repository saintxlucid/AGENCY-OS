# Layer Contracts — Reality / Intelligence / Action / Decision (FROZEN)

Status: FROZEN. Enforceable contracts, not aspirations.

Loop: Reality → Intelligence → Decision → Action → Result → Learning → Reality.

## Reality (system of record)
CAN: store typed nodes + edges + history. Serve reads per permission. Emit events.
CANNOT: infer, judge, recommend, auto-transition. No implicit status edits.
Contract: writes arrive as Action {actor, intent, subject_id, payload, evidence_ids[], idempotency_key}. Validate schema + state-machine legality, append history. Invalid = rejected with reason, logged.

## Intelligence (understanding)
CAN: read Reality + external sources. Produce Observation → Evidence → Synthesis → Proposal.
CANNOT: mutate Reality. Cannot approve/publish/spend/send. Cannot present synthesis without evidence_ids. Cannot hide uncertainty.
Proposal shape fixed: proposal_id, subject_id, kind, recommendation, rationale, confidence 0-1, evidence_ids[], alternatives[], verification_required, escalation_if_rejected, owner_role, measurable_outcome. Missing field = Sovereign rejects before human sees.

## Action (doing)
CAN: execute approved Proposals via tools (create/modify/send/publish/schedule/analyze/produce/escalate) only with valid Approval where required.
CANNOT: self-authorize. Cannot chain destructives without re-auth per step. Cannot publish version ≠ approved version.
Contract: Decision → Approval → Execution → Receipt → History. No receipt = not done.

## Decision (bridge)
Human or delegated authority resolving Proposal → approved / rejected / changes_requested with rationale. Stored as Approval node. Accountability lives here.

## Loop invariant
Result must link back. Performance without publication_id = orphan. Learning without performance + approval evidence = opinion. Knowledge embed without validated Learning = pollution.
