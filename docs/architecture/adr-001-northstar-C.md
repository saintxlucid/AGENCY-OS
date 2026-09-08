# ADR-001 — North Star C: Internal Weapon First, Productizable by Architecture

Status: ACCEPTED. Date: 2026-09-08. Owner: Saint Lucid + ASTRA.

## Decision
C. Build insanely good internal agency OS first. Architecture deliberately capable of becoming product later. No SaaS poison in v1.

## Context
Options: A internal-only, B general SaaS now, C internal-first productizable-later. Recommendation C accepted.

## Consequences
- Single-agency deployment first, multi-agency by namespace (org_id everywhere, no logic forks in v1).
- Reference implementation = Saint Lucid / EAR-style agency reality.
- V1 exclusions: no multi-tenant UI, white-label, per-tenant metering, generic workflow builder (3 campaign templates max), autonomous publishing/sending.
- Every core object carries org_id + provenance + history + evidence from day one. Productization = deployment decision, not rewrite.
- Gates: no Pantheon proliferation, no god-agent, no ambient autonomy, no Sovereign bypass.

## Implementation order
Architecture → implementation plan → schemas/contracts → kernel (Sovereign + Graph) → ALPHAs → proving slice → verification.
Frozen checkpoint: agency-graph-v1, layer-contracts, sovereign-v1, builtin-agents, proving-slice, this ADR.
