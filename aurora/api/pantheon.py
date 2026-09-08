"""
ASTRA OS — Pantheon read helpers (no new routes mounted).
Pure functions over ERP/AI-ERP + Pantheon workers for API read paths.
"""
from __future__ import annotations

from typing import Any, Dict


def project_delivery_snapshot(erp_core: Any, org_id: str) -> Dict[str, Any]:
    from aurora.pantheon.domain import DeliveryWorker
    r = DeliveryWorker().health(erp_core, org_id)
    return {"org_id": org_id, "recommendation": r.recommendation,
            "confidence": r.confidence, "escalation": r.escalation,
            "metric": r.metric, "evidence": r.evidence_ids}


def account_queue_snapshot(requests: list) -> Dict[str, Any]:
    from aurora.pantheon.domain import AccountWorker
    r = AccountWorker().triage(requests)
    return {"recommendation": r.recommendation, "escalation": r.escalation,
            "metric": r.metric, "evidence": r.evidence_ids}


async def performance_snapshot(ai_erp: Any, org_id: str, evidence_ids: list) -> Dict[str, Any]:
    from aurora.pantheon.domain import PerformanceWorker
    r = await PerformanceWorker().report(ai_erp, org_id, evidence_ids)
    return {"recommendation": r.recommendation, "confidence": r.confidence,
            "metric": r.metric, "evidence": r.evidence_ids}
