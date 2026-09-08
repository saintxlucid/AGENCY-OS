"""
Pantheon base contract (PHASE 2). Supervised labor: propose + judge within domain.
Authority L1 propose only. No graph writes, no approvals, no sends. Escalation explicit.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class WorkerResult:
    worker: str
    subject_id: str
    recommendation: str
    rationale: str
    confidence: float
    evidence_ids: List[str] = field(default_factory=list)
    alternatives: List[Dict[str, str]] = field(default_factory=list)
    verification: str = ""
    escalation: str = ""  # non-empty = needs human/owner
    metric: Dict[str, Any] = field(default_factory=dict)


class PantheonWorker:
    mandate: str = ""
    owner_role: str = ""
    authority: str = "L1-propose-only"

    def _require_evidence(self, evidence_ids: List[str]) -> None:
        if not evidence_ids:
            raise ValueError(f"{self.__class__.__name__} requires ≥1 evidence_id")

    def _escalate_if(self, confidence: float, threshold: float = 0.65) -> str:
        if confidence < threshold:
            return f"escalate to {self.owner_role}: confidence {confidence} < {threshold}"
        return ""
