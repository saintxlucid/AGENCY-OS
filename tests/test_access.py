"""Authority fabric tests (separation laws + purpose limits)."""
from aurora.agency.access import PROFILES, AccessProfile, CapabilityToken, decide


def test_profiles_enumerated():
    assert {"maintainer", "security_admin", "analyst", "client"} <= set(PROFILES)


def test_maintainer_cannot_carry_business_approve():
    p = AccessProfile(principal="human", profile="maintainer",
                      actions=["READ", "APPROVE"])
    assert any("APPROVE" in e for e in p.validate())


def test_client_needs_organization():
    p = AccessProfile(principal="client", profile="client", actions=["read"])
    assert any("organization" in e for e in p.validate())


def test_analyst_denied_highly_restricted_salary():
    a = AccessProfile(principal="human", profile="analyst", department="intelligence",
                      resource_scope=["organization"],
                      actions=["read", "query", "aggregate"],
                      data_classification=["PUBLIC", "INTERNAL"])
    r = decide(a, "query", "HIGHLY-RESTRICTED", purpose="capacity analysis")
    assert not r["allowed"] and r["code"] == "deny_classification"


def test_purpose_limits_intelligence():
    a = AccessProfile(principal="human", profile="analyst", department="intelligence",
                      actions=["query"], data_classification=["SENSITIVE"])
    r = decide(a, "query", "SENSITIVE", purpose="capacity analysis",
               is_sensitive_purpose_mismatch=True)
    assert not r["allowed"] and r["code"] == "deny_purpose"


def test_capability_expiry():
    t = CapabilityToken(subject="Asset:x", action="update", version=7,
                        expires_at="2000-01-01T00:00:00", purpose="rev", issued_by="Operator")
    assert t.expired()
