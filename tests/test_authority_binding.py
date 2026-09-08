"""Sovereign + ABAC + RBAC binding tests (Authority Model v1 enforcement)."""
from aurora.agency.access import AccessProfile
from aurora.agency.sovereign import Sovereign
from aurora.api.sovereign_map import check_mutating_route


def _analyst():
    return AccessProfile(principal="human", profile="analyst", department="intelligence",
                         resource_scope=["organization"],
                         actions=["read", "query", "aggregate"],
                         data_classification=["PUBLIC", "INTERNAL"])


def test_sovereign_denies_highly_restricted_for_analyst():
    s = Sovereign()
    r = s.check("intel.query", access_profile=_analyst(),
                classification="HIGHLY-RESTRICTED", purpose="capacity analysis")
    assert not r.allowed and r.code == "deny_classification"


def test_sovereign_denies_purpose_mismatch():
    s = Sovereign()
    p = AccessProfile(principal="human", profile="analyst", department="intelligence",
                      actions=["query"], data_classification=["SENSITIVE"])
    r = s.check("intel.query", access_profile=p, classification="SENSITIVE",
                purpose="capacity analysis", purpose_mismatch=True)
    assert not r.allowed and r.code == "deny_purpose"


def test_sovereign_rbac_false_denies():
    s = Sovereign()
    r = s.check("project.create", rbac_allowed=False)
    assert not r.allowed and r.code == "deny_permission"


def test_sovereign_backward_compatible_without_profile():
    s = Sovereign()
    r = s.check("asset.publish", is_human=False, approval={"decision": "approved"})
    assert r.allowed


def test_api_map_forwards_abac_and_rbac():
    # Analyst CAN query, but NOT HIGHLY-RESTRICTED → classification denial (not action).
    r = check_mutating_route("POST", "/api/v1/ai/query", access_profile=_analyst(),
                             classification="HIGHLY-RESTRICTED")
    assert r["gated"] and not r["allowed"] and r["code"] == "deny_classification"
    r2 = check_mutating_route("POST", "/api/v1/erp/tasks", rbac_allowed=False)
    assert not r2["allowed"] and r2["code"] == "deny_permission"
    r3 = check_mutating_route("GET", "/api/v1/health")
    assert r3["gated"] is False
