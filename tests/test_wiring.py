"""Operator↔Pantheon wiring + API read helpers (no Reality writes)."""
import pytest

from aurora.alphas.operator import Operator
from aurora.api.pantheon import account_queue_snapshot, project_delivery_snapshot
from aurora.enterprise.erp import ERPCore


def test_operator_records_pantheon_escalation_as_blocker():
    from aurora.pantheon.domain import AccountWorker
    ops = Operator()
    res = AccountWorker().triage([{"request_id": "r1", "age_hours": 72}])
    assert "escalate" in res.escalation
    rc = ops.execute_step("act_triage", "account.triage", None, 1,
                          approval=None, evidence_ids=["r1"],
                          executor=lambda: res.recommendation)
    assert rc.status == "ok" and rc.result_ref.startswith("triage")


def test_api_delivery_snapshot_reads_erp():
    snap = project_delivery_snapshot(ERPCore(), "org1")
    assert snap["org_id"] == "org1" and "done" in snap["recommendation"]


def test_api_account_snapshot_flags_stale():
    snap = account_queue_snapshot([{"request_id": "r1", "age_hours": 1}])
    assert snap["metric"]["stale"] == 0
    snap2 = account_queue_snapshot([{"request_id": "r2", "age_hours": 99}])
    assert "escalate" in snap2["escalation"]
