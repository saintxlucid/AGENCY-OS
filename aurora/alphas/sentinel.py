"""
ALPHA 01 — SENTINEL. The Witness.
Read-only on business state. Write-only to observation_log + evidence_staging.
Observations extracted, never generated. No judgment, no action.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List


def _hash(payload: str) -> str:
    return "sha256:" + hashlib.sha256(payload.encode()).hexdigest()[:16]


@dataclass
class ObservationRecord:
    obs_id: str
    subject_id: str
    kind: str
    before: Dict[str, Any] = field(default_factory=dict)
    after: Dict[str, Any] = field(default_factory=dict)
    source: str = ""
    content_hash: str = ""


@dataclass
class StagedEvidence:
    evidence_id: str
    subject_id: str
    provenance: str = ""
    recency: str = ""
    corroboration: int = 1
    score: float = 0.0


class Sentinel:
    def __init__(self):
        self.observation_log: List[ObservationRecord] = []
        self.evidence_staging: List[StagedEvidence] = []
        self._n = 0

    def observe(self, subject_id: str, kind: str, before: Dict[str, Any],
                after: Dict[str, Any], source: str) -> ObservationRecord:
        if not subject_id or not source:
            raise ValueError("observation requires subject_id + source")
        self._n += 1
        rec = ObservationRecord(
            obs_id=f"ag_obs_{self._n:04d}",
            subject_id=subject_id, kind=kind,
            before=before, after=after, source=source,
            content_hash=_hash(subject_id + kind + source),
        )
        self.observation_log.append(rec)
        return rec

    def stage_evidence(self, subject_id: str, provenance: str,
                       recency: str = "fresh", corroboration: int = 1) -> StagedEvidence:
        score = min(1.0, 0.4 + 0.2 * corroboration + (0.2 if recency == "fresh" else 0.0))
        ev = StagedEvidence(
            evidence_id=f"ag_ev_{len(self.evidence_staging)+1:04d}",
            subject_id=subject_id, provenance=provenance,
            recency=recency, corroboration=corroboration, score=score,
        )
        self.evidence_staging.append(ev)
        return ev

    def gaps(self, expected_subjects: List[str]) -> List[str]:
        seen = {o.subject_id for o in self.observation_log}
        return [s for s in expected_subjects if s not in seen]
