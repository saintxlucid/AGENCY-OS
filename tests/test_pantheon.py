"""ASTRA OS — Pantheon contract tests (supervised labor, no Reality writes)."""
import pytest

from aurora.enterprise.erp import ERPCore
from aurora.pantheon.base import PantheonWorker
from aurora.pantheon.domain import AccountWorker, DeliveryWorker, PerformanceWorker
from aurora.pantheon.intel import build_intel_pantheon


def test_pantheon_has_no_write_surface():
    for cls in (PantheonWorker, AccountWorker, DeliveryWorker, PerformanceWorker):
        for attr in ("graph", "save", "publish", "send", "approve", "spend"):
            assert not hasattr(cls, attr), f"{cls.__name__} must not expose {attr}"


def test_intel_pantheon_wraps_six():
    pantheon = build_intel_pantheon()
    assert set(pantheon) == {"narrative", "visual", "symbolism", "design",
                             "marketing", "psychological"}
    assert all(w.authority == "L1-propose-only" for w in pantheon.values())


async def _dummy_media():
    from aurora.core import MediaInterpretation, MediaType
    return MediaInterpretation(media_id="m1", media_type=MediaType.IMAGE,
                               source_path="x.png", timestamp="t",
                               insights=[], summary="s", quality_score=5.0,
                               metadata_graph={})


@pytest.mark.asyncio
async def test_intel_proposal_requires_evidence():
    pantheon = build_intel_pantheon()
    media = await _dummy_media()
    with pytest.raises(ValueError):
        await pantheon["narrative"].propose(media, None, [])


@pytest.mark.asyncio
async def test_intel_proposal_happy_path():
    pantheon = build_intel_pantheon()
    media = await _dummy_media()
    r = await pantheon["visual"].propose(media, None, ["ag_ev_1"])
    assert r.evidence_ids == ["ag_ev_1"] and r.verification == "citation_check"


def test_account_escalates_stale():
    w = AccountWorker()
    r = w.triage([{"request_id": "r1", "age_hours": 72}])
    assert "escalate" in r.escalation and r.metric["stale"] == 1


def test_delivery_reads_erp():
    w = DeliveryWorker()
    r = w.health(ERPCore(), "org1")
    assert r.subject_id == "org1" and "done" in r.recommendation
