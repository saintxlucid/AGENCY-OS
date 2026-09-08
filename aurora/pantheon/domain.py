"""
Domain workers — Account / Delivery / Performance over existing ERP + AI-ERP seams.
Read substrates, propose only. No state writes, no sends, no embeds.
"""
from __future__ import annotations

from typing import Any, Dict, List

from aurora.pantheon.base import PantheonWorker, WorkerResult


class AccountWorker(PantheonWorker):
    mandate = "triage requests → tasks, draft status with evidence"
    owner_role = "Account Director"

    def triage(self, requests: List[Dict[str, Any]]) -> WorkerResult:
        self._require_evidence([r.get("request_id", "") for r in requests if r.get("request_id")])
        stale = [r for r in requests if r.get("age_hours", 0) > 48]
        esc = f"escalate to {self.owner_role}: {len(stale)} stale requests" if stale else ""
        return WorkerResult(worker="AccountWorker", subject_id="account-queue",
                            recommendation=f"triage {len(requests)} requests → tasks",
                            rationale=f"{len(stale)} stale >48h",
                            confidence=0.8 if not stale else 0.55,
                            evidence_ids=[r.get("request_id", "") for r in requests],
                            verification="request→task linkage",
                            escalation=esc or self._escalate_if(0.8),
                            metric={"requests": len(requests), "stale": len(stale)})


class DeliveryWorker(PantheonWorker):
    mandate = "plan health from tasks/milestones, surface blockers"
    owner_role = "Producer"

    def health(self, erp_core: Any, org_id: str) -> WorkerResult:
        tasks = erp_core.get_org_tasks(org_id) if hasattr(erp_core, "get_org_tasks") else []
        blocked = [t for t in tasks if str(getattr(t, "status", "")) not in ("done", "TaskStatus.DONE")
                   and getattr(t, "status", "") in ("blocked",)]
        # Generic: count non-done as at-risk signal without overclaiming statuses
        total, done = len(tasks), sum(1 for t in tasks if "done" in str(getattr(t, "status", "")).lower())
        conf = 0.85 if total == 0 or done / max(total, 1) >= 0.5 else 0.6
        esc = f"escalate to {self.owner_role}: {len(blocked)} blocked" if blocked else self._escalate_if(conf)
        return WorkerResult(worker="DeliveryWorker", subject_id=org_id,
                            recommendation=f"{done}/{total} done",
                            rationale="erp task states",
                            confidence=conf, evidence_ids=[f"erp:{org_id}:tasks"],
                            verification="every task has parent+owner+due (caller checks)",
                            escalation=esc, metric={"total": total, "done": done})


class PerformanceWorker(PantheonWorker):
    mandate = "report + learning proposals from AI-ERP, never declare truth"
    owner_role = "Performance Owner"

    async def report(self, ai_erp: Any, org_id: str, evidence_ids: List[str]) -> WorkerResult:
        self._require_evidence(evidence_ids)
        try:
            insights = ai_erp.generate_insights(org_id) if hasattr(ai_erp, "generate_insights") else []
        except Exception:
            insights = []
        return WorkerResult(worker="PerformanceWorker", subject_id=org_id,
                            recommendation=f"{len(insights)} insights proposed",
                            rationale="ai-erp over performance rows",
                            confidence=0.72, evidence_ids=evidence_ids,
                            verification="attribution window stated",
                            escalation=self._escalate_if(0.72),
                            metric={"insights": len(insights)})
