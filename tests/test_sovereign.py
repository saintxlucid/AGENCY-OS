"""ASTRA OS — Sovereign gate tests (frozen v1: fail-closed, human-only, version pin)."""
from aurora.agency.sovereign import Sovereign


def test_human_only_blocked_for_agents():
    s = Sovereign()
    r = s.check("asset.publish", actor_type="agent", is_human=False, approval=None)
    assert not r.allowed and r.code == "need_approval"


def test_human_only_allowed_with_approval():
    s = Sovereign()
    r = s.check("asset.publish", actor_type="agent", is_human=False,
                approval={"decision": "approved"})
    assert r.allowed and r.code == "ok"


def test_version_pin_enforced():
    s = Sovereign()
    r = s.preflight_publish(4, 5, {"decision": "approved"})
    assert not r.allowed and r.code == "version_mismatch"
    r2 = s.preflight_publish(4, 4, {"decision": "approved"})
    assert r2.allowed


def test_destructive_needs_approval():
    s = Sovereign()
    r = s.check("budget_change", actor_type="agent", is_human=True, approval=None)
    assert not r.allowed and r.code == "need_approval"


def test_spend_thresholds():
    s = Sovereign()
    r = s.check("spend.commit", actor_role="Craft", is_human=False,
                approval=None, amount_usd=6000)
    assert not r.allowed
    r2 = s.check("spend.commit", actor_role="Craft", is_human=False,
                 approval={"decision": "approved"}, amount_usd=6000)
    assert r2.allowed


def test_proposal_needs_evidence():
    s = Sovereign()
    assert not s.preflight_proposal([]).allowed
    assert s.preflight_proposal(["ag_ev_1"]).allowed
