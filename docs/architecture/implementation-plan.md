# Implementation Plan — From Frozen Architecture to Proving Slice

Source: frozen docs/architecture/*-v1.md + adr-001-northstar-C.md. Docs-only freeze respected. Now buildable steps.

## Reuse map (do not rewrite)
- `aurora/enterprise/governance.py` (PolicyEngine, ApprovalGate, AuditChain, 622 lines) → Sovereign v1 enforcement. Wrap, don't fork. Add L0-L4 presets + thresholds + destructive taxonomy as policy pack.
- `aurora/memory/graph.py` (Chroma + NetworkX, lazy embedder + hash fallback) → Agency Graph prototype. Add typed node/edge validation + history append + ULID ids.
- `aurora/core.py` (AuroraCore, ProjectContext, memory_dir overridable) → Reality kernel primitives + loop_state. Add status field + transition helpers.
- `aurora/api/server.py` (20 routes) → Action gateway. Add Sovereign middleware on mutating routes next phase.
- `aurora/workers/settings.py` (ARQ stub) → Operator execution entry. Keep.

## Phases
1. Schemas/contracts (this turn): `aurora/agency/` — ids, nodes, edges, messages, transitions. Pydantic-free dataclasses + enums to avoid new deps. Unit-tested state machines.
2. Kernel: Sovereign policy pack (L0-L4 + thresholds + destructive list) over governance.py + Graph history wrapper (append-only, provenance required).
3. ALPHAs scaffold: Sentinel (observe/stage), Scribe (cite/propose), Operator (pre-flight/receipt) as service classes with caps + logs, supervised by Aurora conductor methods.
4. Proving slice harness: `demos/proving_slice.py` walking Brief→Learning with fixtures, asserting blocks (no evidence→no proposal, version drift→deny, no receipt→scheduled).
5. Verification: `tests/test_agency_graph.py` + `tests/test_sovereign.py` + slice test green. Then commit.

## Acceptance (slice)
One-walk traversal query works. Every transition has actor+rationale+timestamp. Blocks enforced with codes. Learning citable. Humans only where L3/L4 requires.
No Pantheon proliferation. No god-agent. No Sovereign bypass. No ambient autonomy.

## Out of scope v1
Multi-tenant UI, white-label, metering, generic workflow builder (>3 templates), autonomous publish/send, free-form agent creation.
