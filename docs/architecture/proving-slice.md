# Proving Slice — Brief → Learning in One Loop (FROZEN)

Scope: One brand, one campaign (Q4 Brand Sprint Test Brand). Full chain, no skips.

Chain: Brief v1 approved → Strategy 3 territories → 1 selected → Concept 2 variants → 1 approved for production → Asset copy+visual v1→v2 QC passed → Approval exact version human → Publication 1 channel + receipt → Performance 7-day → Learning 1 validated → embedded.

## Swimlanes
Human (CD/AD/Producer): approve Brief, select Territory, approve Concept, approve Asset version, validate Learning.
Aurora: truth (Sentinel) + context (Scribe) → route via Operator → request Decisions → close loop.
Sentinel: observe transitions, stage evidence, emit gaps/divergence.
Scribe: render docs, propose syntheses/learnings with citations.
Operator: plan, spawn scoped workers, execute tools, collect receipts, manage Tasks/Blockers.
Pantheon: judge within domain, propose only. Sovereign: allow/deny/need-approval. Graph+Tools: truth + execution.

## Steps + blocks
1. Brief: Scribe renders, Aurora requests L3. Block: unapproved Brief → Strategy rejected.
2. Strategy: 3 territories evidenced. Block: missing evidence_ids → refused.
3. Concept: 2 variants evaluated vs brief+brand. Block: off-brand/unevaluated → blocked.
4. Asset: v1→v2 new nodes + SUPERSEDES, QC report + AI provenance. Block: qc_failed → frozen + Revision Task.
5. Approval: exact asset version + channel + QC + 72h expiry, human. Block: version drift → Operator denies publish.
6. Publication: exact version, receipt required. No receipt = scheduled + Blocker.
7. Performance: 7-day ingest, attribution window stated. Report cites publication + approval.
8. Learning: finding + evidence (performance+asset+approval) + applicability + confidence. Human validates → embedded with validator + INFORMS next Brief.

Rejection anywhere → changes_requested + expectations + Revision Task owned + due. Blocker >24h → Producer + Account. Tool 3x fail → freeze branch, preserve receipts.

## Message schemas (frozen shapes)
Action {action_id, intent, subject{type,id,version}, payload, approval_ref, evidence_ids[], preflight{permission,policy_version}, idempotency_key, actor, trace_id, org_id}.
Proposal {proposal_id, subject_id, kind, recommendation, rationale, confidence, evidence_ids[], alternatives[], verification_required, owner_role, measurable_outcome}.
Observation {obs_id, subject_id, kind, before/after, source, timestamp, hash}.
ApprovalRequest {request_id, subject{type,id,version}, requested_by, approver_role, context{proposal_id,evidence_ids,diff}, expires_at} → Decision {approval_id, decision approved/rejected/changes_requested, approver_user_id, rationale, conditions[], timestamp}.
Plan {plan_id, goal, steps[{step_id,op,owner,verifies,needs_approval}], deps, caps} + Receipt {receipt_id, action_id, result_ref, status ok/failed, timestamp}.
LearningProposal {learning_id, campaign_id, finding, evidence_ids[], applicability{brands,channels}, confidence, validator_required:true}.

Pre-flight every mutating step: permission? approval_if_needed? version_match? budget_threshold? evidence_present? Any no → deny with code + remediation, logged, no partials.

Pass criteria: one-walk traversal, actor+rationale+timestamp everywhere, blocks enforced, learning citable by next Brief, humans only where L3/L4 requires.
