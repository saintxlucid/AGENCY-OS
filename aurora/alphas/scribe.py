"""
ALPHA 02 — SCRIBE. The Librarian.
Documents + proposes with citations. Never executes, never embeds without validation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class DocDraft:
    draft_id: str
    subject_id: str
    body: str
    cites: List[str] = field(default_factory=list)
    expired: bool = False


@dataclass
class SynthesisProposal:
    proposal_id: str
    subject_id: str
    recommendation: str
    rationale: str
    confidence: float
    evidence_ids: List[str] = field(default_factory=list)
    alternatives: List[Dict[str, str]] = field(default_factory=list)


class Scribe:
    def __init__(self):
        self.drafts: List[DocDraft] = []
        self.proposals: List[SynthesisProposal] = []
        self._n = 0

    def _check_cites(self, cites: List[str], known_evidence: List[str]) -> List[str]:
        return [c for c in cites if c not in known_evidence]

    def render_draft(self, subject_id: str, body: str, cites: List[str],
                     known_evidence: List[str]) -> DocDraft:
        missing = self._check_cites(cites, known_evidence)
        if missing:
            raise ValueError(f"unresolvable cites: {missing}")
        self._n += 1
        d = DocDraft(draft_id=f"ag_draft_{self._n:04d}", subject_id=subject_id,
                     body=body, cites=cites)
        self.drafts.append(d)
        return d

    def propose(self, subject_id: str, recommendation: str, rationale: str,
                confidence: float, evidence_ids: List[str],
                known_evidence: List[str],
                alternatives: List[Dict[str, str]] | None = None) -> SynthesisProposal:
        if not evidence_ids:
            raise ValueError("proposal requires ≥1 evidence_id")
        missing = self._check_cites(evidence_ids, known_evidence)
        if missing:
            raise ValueError(f"unresolvable evidence: {missing}")
        if confidence >= 0.95 and len(evidence_ids) < 3:
            raise ValueError("confidence ≥0.95 needs ≥3 independent evidences")
        self._n += 1
        p = SynthesisProposal(
            proposal_id=f"ag_prop_{self._n:04d}", subject_id=subject_id,
            recommendation=recommendation, rationale=rationale,
            confidence=confidence, evidence_ids=evidence_ids,
            alternatives=alternatives or [],
        )
        self.proposals.append(p)
        return p

    def propose_learning(self, campaign_id: str, finding: str, rationale: str,
                         confidence: float, performance_evidence_id: str,
                         approval_evidence_id: str, known_evidence: List[str],
                         alternatives: List[Dict[str, str]] | None = None) -> SynthesisProposal:
        """Learning gate: performance + approval evidence required (invariant)."""
        evs = [performance_evidence_id, approval_evidence_id]
        if not performance_evidence_id or not approval_evidence_id:
            raise ValueError("learning requires performance_evidence_id + approval_evidence_id")
        return self.propose(campaign_id, finding, rationale, confidence, evs, known_evidence, alternatives)

    @staticmethod
    def gate_doc_cites(cites: List[str], known_evidence: List[str]) -> None:
        """Doc-path binding: call before surfacing any synthesis/doc to humans."""
        missing = [c for c in cites if c not in known_evidence]
        if missing:
            raise ValueError(f"doc blocked: unresolvable cites {missing}")
