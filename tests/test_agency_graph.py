"""ASTRA OS — Agency Graph schema tests (frozen v1 contracts)."""
from aurora.agency.schema import (
    AgencyEdge,
    AgencyNode,
    EdgeKind,
    NodeKind,
    can_transition,
    new_id,
)


def test_ids_are_namespaced():
    nid = new_id("brief")
    assert nid.startswith("ag_brief_")


def test_brief_states_closed():
    n = AgencyNode(id=new_id("brief"), kind="brief", org_id="org_saintlucid",
                   state="approved", owner_role="Strategist")
    assert n.validate() == []
    bad = AgencyNode(id=n.id, kind="brief", org_id=n.org_id, state="published")
    assert any("state" in e for e in bad.validate())


def test_owner_required_on_reality_nodes():
    n = AgencyNode(id=new_id("concept"), kind="concept", org_id="o", state="draft")
    assert any("owner" in e for e in n.validate())


def test_legal_transitions():
    assert can_transition("brief", "submitted", "approved")
    assert not can_transition("brief", "draft", "approved")
    assert can_transition("asset", "in_qc", "qc_passed")
    assert not can_transition("asset", "wip", "approved")
    assert can_transition("approval", "pending", "decided")
    assert not can_transition("publication", "scheduled", "taken_down")


def test_edges_typed():
    e = AgencyEdge(source_id="ag_brief_x", target_id="ag_strategy_y", kind="grounds",
                   actor="aurora", rationale="approved brief grounds strategy")
    assert e.validate() == []
    bad = AgencyEdge(source_id="a", target_id="b", kind="vibes")
    assert any("edge" in x for x in bad.validate())


def test_chain_shape():
    # Spine must be expressible: client -owns-> brand -has-> campaign -issues-> brief
    kinds = [NodeKind.CLIENT.value, NodeKind.BRAND.value, NodeKind.CAMPAIGN.value, NodeKind.BRIEF.value]
    assert kinds == ["client", "brand", "campaign", "brief"]


def test_full_service_extension_additive():
    # New nodes validate; old transitions untouched (backward compatible).
    lead = AgencyNode(id=new_id("lead"), kind="lead", org_id="o", state="qualified",
                      owner_role="New Business")
    assert lead.validate() == []
    assert can_transition("lead", "qualified", "pitched")
    assert not can_transition("lead", "new", "won")
    assert can_transition("scope", "approved", "changed")
    assert can_transition("distribution", "live", "paused")
    assert can_transition("retainer", "active", "renewed")
    assert can_transition("launch", "planned", "released")
    # Old spine still enforced
    assert can_transition("brief", "submitted", "approved")
    assert not can_transition("asset", "wip", "approved")
    e = AgencyEdge(source_id="a", target_id="b", kind="converts_to")
    assert e.validate() == []
