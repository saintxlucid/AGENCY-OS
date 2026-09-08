# Agency Graph v1 — Canonical Spine (FROZEN)

Status: FROZEN checkpoint. Single graph. Typed nodes + edges. Explicit states.

## Principle
One graph. No silos. Every Reality node carries:
`id / org_id / state / owner / provenance / relationships / permissions_ref / history / evidence_refs`

- `id`: ULID `ag_<type>_<ulid>`, never reused.
- `org_id`: single value now (`org_saintlucid`), namespaced for multi-agency later. No logic forks in v1.
- `state`: closed enum per type. Transitions are events, not edits.
- `owner`: resolvable human/role. Empty owner = invalid.
- `provenance`: created_by, created_from, evidence_ids, decision_id.
- `history`: append-only. No in-place mutation of material facts.
- `evidence_refs`: artifacts, citations, performance, approvals justifying state.

## Nodes (Reality spine)
Client → Brand → Campaign → Brief → Strategy → Concept → Asset → Approval → Publication → Performance → Learning

- Client: prospect → active → paused → active | churned (terminal, Sovereign + reason). Owner: Account Director.
- Brand: draft → active → archived. Guidelines versioned. Owner: Brand Lead.
- Campaign: pitched → scoped → active → in_review → completed | killed. Budget immutable after active except via Change Order.
- Brief: draft → submitted → clarified → approved → superseded. Only approved unlocks Strategy. approved_by human in v1.
- Strategy: draft → proposed → selected | rejected. Every territory cites ≥1 evidence + brief criteria.
- Concept: draft → in_critique → revised → approved_for_production | killed. Structured eval vs brief+brand.
- Asset: wip → in_qc → qc_passed → approved | qc_failed → wip. Versions are new nodes + SUPERSEDES edge.
- Approval: requested → pending → decided (immutable). Must carry rationale + conditions on reject/changes.
- Publication: scheduled → published → taken_down. Requires receipt + exact-version Approval.
- Performance: collecting → reported → learned_from. Ingested/computed, no manual edits.
- Learning: draft → validated → embedded. Embedded = written to Knowledge Fabric.

Supporting: Person/Role, Proposal/Scope/Estimate/Retainer/Invoice (money chain, no orphan invoices), Task/Milestone/Blocker (always has parent_id + owner + due), Meeting/Message/Request (Request → Task/Revision, never disappears).

## Edges (typed, directed)
OWNS, HAS, ISSUES, GROUNDS, SELECTS, YIELDS, REALIZES, REQUIRES, AUTHORIZES, MEASURES, DISTILLS, EMBEDS_IN, INFORMS, SUPERSEDES, SUPERSEDED_BY, REJECTS, GOVERNED_BY, BLOCKED_BY, DELIVERS, TRIGGERS.
Single stored direction + inverse traversal. No hard deletes. Every state-changing edge appends History with actor + rationale + timestamp.

Canonical traversal must work in one walk:
Client → Brand → Campaign → Brief(v approved) → Strategy(territory selected) → Concept → Asset(v QC) → Approval(approved) → Publication(receipt) → Performance → Learning → Knowledge.

## Invariants
- No Campaign without active Client. No Strategy without approved Brief. No Publication without exact-version approved Approval. No Performance without publication_id. No Learning without performance + approval evidence.
- Invariants enforced at Reality write path + Operator pre-flight + Sovereign check.
