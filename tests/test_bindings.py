"""ASTRA OS — PHASE 1 binding tests (seams, not duplicates)."""
from aurora.agency.sovereign import Sovereign
from aurora.alphas.operator import Operator
from aurora.alphas.sentinel import Sentinel
from aurora.api.sovereign_map import MUTATING_ROUTES, check_mutating_route


def test_operator_prefers_crp_with_fallback():
    ops = Operator(sovereign=Sovereign())
    r = ops.preflight_via_crp("asset.publish", estimated_cost_usd=10)
    assert r["via"] in ("crp", "sovereign-fallback")
    assert "allowed" in r and "state" in r


def test_sentinel_ingests_live_observer_event():
    from aurora.observation.watcher import ObservationEvent

    sen = Sentinel()
    ev = ObservationEvent(event_id="e1", target_id="t1", event_type="modified",
                          timestamp="2026-09-08T00:00:00", file_path="/tmp/a.png")
    rec = sen.ingest_event(ev)
    assert rec.subject_id == "/tmp/a.png"
    assert len(sen.observation_log) == 1
    assert len(sen.evidence_staging) == 1


def test_api_mutating_map_covers_writes():
    assert ("POST", "/api/v1/erp/invoices") in MUTATING_ROUTES
    assert ("POST", "/api/v1/erp/tasks") in MUTATING_ROUTES
    assert ("POST", "/api/v1/projects") in MUTATING_ROUTES
    r = check_mutating_route("POST", "/api/v1/erp/invoices")
    assert r["gated"] and r["action"] == "finance.invoice_create"
    assert check_mutating_route("GET", "/api/v1/health")["gated"] is False
