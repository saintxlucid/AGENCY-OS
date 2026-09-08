"""Tests for Authority & Access Fabric v1. No network. Fail-closed assertions."""
from __future__ import annotations

from datetime import datetime, timedelta


def _op_t2(actions, **kw):
    d = {"principal": "human", "profile": "operator_t2", "department": "creative",
         "resource_scope": ["assigned_projects"], "actions": actions,
         "data_classification": ["INTERNAL", "CLIENT-CONFIDENTIAL"], **kw}
    return d


def test_maintainer_has_no_business_approve():
    from aurora.access import AccessProfile

    p = AccessProfile(principal="human", profile="maintainer",
                      actions=["READ", "EXECUTE", "APPROVE"])
    assert any("APPROVE" in e for e in p.validate())


def test_security_admin_has_no_publish_approve():
    from aurora.access import AccessProfile

    p = AccessProfile(principal="human", profile="security_admin",
                      actions=["READ", "PUBLISH"])
    assert p.validate()


def test_t2_is_not_admin_zone():
    from aurora.access import pre_check

    # operator_t2 default zones are Z2/Z1 — Z5 (security) must deny
    r = pre_check(_op_t2(["READ"]), "READ", "INTERNAL", zone="Z5")
    assert not r["allowed"] and r["code"] == "deny_zone"


def test_cross_department_viewer_read_only():
    from aurora.access import pre_check

    viewer = {"principal": "human", "profile": "viewer", "actions": ["READ"],
              "data_classification": ["INTERNAL"]}
    assert pre_check(viewer, "READ", "INTERNAL")["allowed"]
    r = pre_check(viewer, "EDIT", "INTERNAL")
    assert not r["allowed"] and r["code"] == "deny_action"


def test_hr_salary_boundary_and_redaction():
    from aurora.access import filter_query_result

    rows = [{"name": "A", "department": "creative", "salary": 90000,
             "classification": "HIGHLY-RESTRICTED"}]
    analyst = {"principal": "human", "profile": "analyst", "actions": ["READ", "QUERY"],
               "data_classification": ["INTERNAL", "RESTRICTED"]}
    out = filter_query_result(rows, analyst)
    assert out == []  # ceiling RESTRICTED < HIGHLY-RESTRICTED
    hr = {"principal": "human", "profile": "hr", "actions": ["READ", "QUERY"],
          "data_classification": ["INTERNAL", "HIGHLY-RESTRICTED"]}
    out2 = filter_query_result(rows, hr)
    assert out2 and out2[0]["salary"] == 90000


def test_analyst_purpose_cap_and_no_direct_db():
    from aurora.access import AccessProfile, pre_check

    p = AccessProfile(principal="human", profile="analyst", actions=["QUERY"],
                      database_direct_access=True)
    assert any("database_direct_access" in e for e in p.validate())
    prof = {"principal": "human", "profile": "analyst", "actions": ["QUERY", "READ"],
            "data_classification": ["INTERNAL", "SENSITIVE", "RESTRICTED"]}
    r = pre_check(prof, "QUERY", "SENSITIVE", purpose="capacity_analysis")
    assert not r["allowed"] and r["code"] == "deny_purpose"


def test_client_scoping_and_row_policy():
    from aurora.access import filter_query_result

    client = {"principal": "client", "profile": "client", "organization": "client_001",
              "actions": ["READ", "COMMENT"], "data_classification": ["CLIENT-CONFIDENTIAL"]}
    rows = [{"campaign": "a", "client_id": "client_001", "classification": "CLIENT-CONFIDENTIAL"},
            {"campaign": "b", "client_id": "client_002", "classification": "CLIENT-CONFIDENTIAL"},
            {"campaign": "c", "classification": "CLIENT-CONFIDENTIAL"}]
    out = filter_query_result(rows, client)
    assert [r["campaign"] for r in out] == ["a"]


def test_delegation_expiry_and_scope():
    from aurora.access import Delegation, pre_check

    profile = {"principal": "human", "profile": "operator_t1",
               "actions": ["READ"], "data_classification": ["INTERNAL"],
               "expires_at": (datetime.now() - timedelta(hours=1)).isoformat()}
    # expired base + no grant → expired (not silent allow)
    r = pre_check(profile, "READ", "INTERNAL")
    assert not r["allowed"] and r["code"] == "expired"
    # live delegation widens the missing action within ceilings
    live = Delegation(granted_by="cd", granted_to="senior", capabilities=["REVIEW"],
                      resources=["campaign_x"],
                      expires_at=(datetime.now() + timedelta(hours=48)).isoformat())
    r2 = pre_check({**profile, "expires_at": ""}, "REVIEW", "INTERNAL", delegation=live)
    assert r2["allowed"] and r2.get("widened_by", "").startswith("delegation:")


def test_break_glass_expiry():
    from aurora.access import BreakGlassGrant, pre_check

    expired = BreakGlassGrant(granted_to="ops", reason="2am outage", scopes=["EXECUTE"],
                              minutes=-1)
    assert not expired.active()
    prof = {"principal": "human", "profile": "operator_t1",
            "actions": ["READ"], "data_classification": ["INTERNAL"]}
    r = pre_check(prof, "EXECUTE", "INTERNAL", break_glass=expired)
    assert not r["allowed"]


def test_capability_token_scoping_and_version_pin():
    from aurora.access import CapabilityToken

    tok = CapabilityToken(subject="Asset:abc123", action="update", version=7,
                          purpose="production_revision", issued_to="producer-agent")
    assert tok.covers("Asset:abc123", "update", version=7)
    assert not tok.covers("Asset:abc123", "update", version=8)
    assert not tok.covers("Asset:other", "update")


def test_agent_identity_chain_required():
    from aurora.access import AgentIdentityChain, pre_check

    prof = {"principal": "agent", "profile": "operator_t1", "actions": ["READ"],
            "data_classification": ["INTERNAL"]}
    r = pre_check(prof, "READ", "INTERNAL")
    assert not r["allowed"] and r["code"] == "deny_agent_identity"
    chain = AgentIdentityChain(human_actor="karim", agent_actor="producer-1", tool_actor="render")
    r2 = pre_check(prof, "READ", "INTERNAL", agent_chain=chain)
    assert r2["allowed"]


def test_sovereign_final_adjudication_still_blocks():
    from aurora.agency.sovereign import Sovereign

    s = Sovereign()
    prof = {"principal": "human", "profile": "operator_t2",
            "actions": ["PUBLISH"], "data_classification": ["CLIENT-CONFIDENTIAL"]}
    # fabric pre-check passes (action present) but human-only publish without approval → Sovereign denies
    r = s.check("asset.publish", access_profile=prof, classification="CLIENT-CONFIDENTIAL")
    assert not r.allowed and r.code == "need_approval"


def test_rbac_is_only_baseline():
    from aurora.access import rbac_baseline_allowed

    # designer baseline allows asset:read; unknown permission → False (never grants)
    assert rbac_baseline_allowed("designer", "asset:read", "org1", {"org1": "designer"})
    assert not rbac_baseline_allowed("designer", "admin:full", "org1", {"org1": "designer"})
    assert not rbac_baseline_allowed("designer", "asset:read", "org2", {"org1": "designer"})


def test_simulate_is_side_effect_free_with_alternative():
    from aurora.access import simulate

    analyst = {"principal": "human", "profile": "analyst", "actions": ["QUERY", "EXPORT"],
               "data_classification": ["INTERNAL", "RESTRICTED"]}
    r = simulate(analyst, "EXPORT", classification="HIGHLY-RESTRICTED",
                 purpose="capacity_analysis")
    assert r["simulation"] and not r["allowed"] and "alternative" in r


def test_api_guard_fabric_headers_deny_and_allow():
    from aurora.agency.api_guard import action_for, guard_or_403

    assert action_for("POST", "/api/v1/erp/tasks") == "task.create"
    assert action_for("GET", "/api/v1/erp/tasks") is None  # reads open per RBAC
    # maintainer attempting business approve → fabric deny (not Sovereign approval path)
    prof = {"principal": "human", "profile": "maintainer", "actions": ["READ", "EXECUTE"]}
    try:
        guard_or_403("task.create", access_profile=prof, classification="INTERNAL")
        raise AssertionError("should deny")
    except Exception as e:
        assert getattr(e, "status_code", 0) == 403
    # operator_t1 create task → allowed (no approval needed for non-human-only action)
    ok_prof = {"principal": "human", "profile": "operator_t1",
               "actions": ["CREATE", "READ"], "data_classification": ["INTERNAL"]}
    guard_or_403("task.create", access_profile=ok_prof, classification="INTERNAL")
