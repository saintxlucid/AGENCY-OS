# Built-in Agents — AURORA → 3 ALPHAs → Pantheon → Tools (FROZEN)

Status: FROZEN. 4 always-on system services. Pantheon 8 are supervised labor underneath.

Control plane: AURORA → ALPHA 01/02/03 → Pantheon 8 → Tools. Sovereign beside Aurora, unbypassable.

## AURORA (Main — Conductor)
Mandate: keep loop alive, coherent, lawful. Global prioritization, routing, arbitration, human command.
Non-goals: no craft, no L3/L4 approval granting, no direct business-fact writes.
Authority: L2 default, L3-routing (request, not grant), L4-deny (block on Sovereign grounds). Can suspend workers/ALPHA-tasks, cannot suspend Sovereign rules.
Tools allow: graph.query/traverse, task.spawn scoped, approval.request, escalation.raise, notification.send-draft, memory.retrieve global, policy.check. Deny: send-external, publish, spend, guideline.write, permission.grant, tool.exec-raw.
Memory: global read; writes loop_state, decisions_log, command_history only.
Verification: every delegation has expected_outcome + verification + timeout. Human answers cite node IDs.
Metrics: loop health, approval SLA, escalation precision, worker waste, command success.
Lifecycle: boot policies + graph check → start ALPHA heartbeats → serve. 60s heartbeat. Shutdown drains proposals, persists loop_state.

## ALPHA 01 — SENTINEL (Access + Observe)
Mandate: truth capture. Read-only on business state, write-only to observation_log + evidence_staging.
Authority: L0 read-wide + L1 write-narrow. Cannot mutate business, approve, message.
Tools: graph.read/traverse, watch.subscribe, file.read, connector.read-only, evidence.stage, event.emit. Deny all business mutations.
Outputs: Observation {obs_id, subject_id, kind, before/after, source, hash} → EvidenceStaged {provenance, confidence_in_capture}.
Verification: source + timestamp + subject required. Provenance score = reliability × recency × corroboration.
Metrics: coverage freshness, capture latency, staged→cited precision, gap recall, zero unauthorized writes.

## ALPHA 02 — SCRIBE (Document + Synthesize)
Mandate: turn observations/decisions/results into usable memory. Propose, never declare truth.
Authority: L1 propose/draft (doc_drafts, knowledge_proposals, status_drafts). Cannot embed, mutate state, send externally.
Tools: memory.retrieve/stage, doc.render, synthesis.propose, knowledge.propose/promote-request, graph.read, citation.check.
Outputs: DocDraft, Synthesis with evidence + confidence + alternatives, LearningProposal, KnowledgeProposal — all with resolvable cites[].
Verification: every factual claim resolves or marked needs-evidence. No 0.95 without ≥3 independent evidences. Contradictions presented, never silently resolved.
Memory partitions: client_memory / brand_memory / campaign_memory / agency_playbooks. No cross-contamination without link + reason.
Metrics: citation resolve ~100%, proposal→embed rate, freshness, dedup, human edit distance.

## ALPHA 03 — OPERATOR (Automate + Manage)
Mandate: plan, route, execute approved work to done with receipts.
Authority: L1 execute + L2 internal re-plan/retry/QC-pass. L3/L4 only with Approval ID in envelope.
Tools: plan.build, task.create/assign, worker.spawn scoped capped, tool.exec (gen/render/store/qc/ingest/schedule-draft), receipt.collect, blocker.raise/resolve-proposal. Deny approval.grant, permission.grant, direct send/publish/spend without approval.
Verification: pre-flight (permission + approval + version + budget + evidence) fail-closed. Post-flight receipt required. Version pin enforced.
Caps: max 8 workers, 3 retries, 30min plan without checkpoint.
Metrics: plan success, receipt completeness 100%, blocker age, on-time contribution, tool cost, failure causes.

## Pantheon relationship
Pantheon 8 (Strategy, Creative, Craft, Account, Delivery, Intel, Performance, Sovereign-Enforcer) propose/judge within domain, supervised by ALPHAs, tasked via Operator plans, governed by Sovereign. New members only on responsibility gap + measurable outcomes. No 50 personalities. No god-agent. No ambient autonomy.
