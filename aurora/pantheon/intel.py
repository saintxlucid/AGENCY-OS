"""
Intel workers — wrap 6 existing engines as supervised Pantheon labor.
Engines judge (analyze/critique); worker shapes Proposal with evidence + escalation.
No Reality writes. No approval. Delegates to Scribe citation rules.
"""
from __future__ import annotations

from typing import Any, Dict, List

from aurora.pantheon.base import PantheonWorker, WorkerResult


class IntelWorker(PantheonWorker):
    def __init__(self, engine: Any, owner_role: str = "Strategy Owner"):
        self.engine = engine
        self.owner_role = owner_role
        domain = getattr(engine, "domain", None)
        self.mandate = f"supervised {getattr(domain, 'value', domain)} intelligence"

    async def propose(self, media: Any, context: Any = None,
                      evidence_ids: List[str] | None = None) -> WorkerResult:
        evs = evidence_ids or []
        self._require_evidence(evs)
        insights = await self.engine.analyze(media, context)
        findings = "; ".join(getattr(i, "finding", "") for i in insights[:3]) or "no findings"
        confs = [getattr(i, "confidence", 0.0) for i in insights] or [0.0]
        conf = round(sum(confs) / len(confs), 3)
        return WorkerResult(
            worker=type(self.engine).__name__,
            subject_id=getattr(media, "media_id", "unknown"),
            recommendation=findings[:500],
            rationale=f"engine {type(self.engine).__name__} over {len(insights)} insights",
            confidence=conf,
            evidence_ids=evs,
            verification="citation_check",
            escalation=self._escalate_if(conf),
            metric={"insights": len(insights)},
        )


def build_intel_pantheon() -> Dict[str, IntelWorker]:
    """Lazily wrap all six engines. Import-safe (no torch at module load)."""
    from aurora.intelligence.design import DesignIntelligence
    from aurora.intelligence.marketing import MarketingIntelligence
    from aurora.intelligence.narrative import NarrativeIntelligence
    from aurora.intelligence.psychological import PsychologicalIntelligence
    from aurora.intelligence.symbolism import SymbolismIntelligence
    from aurora.intelligence.visual import VisualIntelligence

    return {
        "narrative": IntelWorker(NarrativeIntelligence()),
        "visual": IntelWorker(VisualIntelligence()),
        "symbolism": IntelWorker(SymbolismIntelligence()),
        "design": IntelWorker(DesignIntelligence()),
        "marketing": IntelWorker(MarketingIntelligence()),
        "psychological": IntelWorker(PsychologicalIntelligence()),
    }
