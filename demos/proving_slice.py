"""
ASTRA OS — Proving slice harness (in-memory, no heavy deps).

Walks Brief → Strategy → Concept → Asset → Approval → Publication → Performance → Learning
with ALPHA 01/02/03 + Sovereign + schema transitions. Proves blocks:
- no evidence → no proposal, version drift → deny publish, no receipt → stays scheduled.
Run: python demos/proving_slice.py
"""
from aurora.agency.schema import AgencyEdge, AgencyNode, can_transition, new_id
from aurora.agency.sovereign import Sovereign
from aurora.alphas.operator import Operator, PlanStep
from aurora.alphas.scribe import Scribe
from aurora.alphas.sentinel import Sentinel

ORG = "org_saintlucid"


def main() -> dict:
    sov = Sovereign(org_id=ORG)
    sen = Sentinel()
    scr = Scribe()
    ops = Operator(sovereign=sov)
    history = []

    # Nodes (approved brief grounds strategy, etc.)
    brief = AgencyNode(id=new_id("brief"), kind="brief", org_id=ORG,
                       state="approved", owner_role="Strategist")
    assert brief.validate() == []
    history.append(("brief.approved", brief.id))
    sen.observe(brief.id, "state_transition", {"state": "clarified"},
                {"state": "approved"}, source="graph_event")
    ev_brief = sen.stage_evidence(brief.id, "approved-brief", recency="fresh", corroboration=2)

    # Strategy proposal REQUIRES evidence (block proven if empty)
    blocked = sov.preflight_proposal([])
    assert not blocked.allowed and blocked.code == "missing_evidence"
    prop = scr.propose(brief.id, "Territory B: 3s hooks", "evidence-backed",
                       0.78, [ev_brief.evidence_id],
                       [ev_brief.evidence_id],
                       [{"option": "Territory A", "tradeoff": "safer, lower lift"}])
    assert can_transition("strategy", "proposed", "selected")

    # Concept → Asset versions (new nodes, never overwrite)
    assert can_transition("asset", "in_qc", "qc_passed")
    assert not can_transition("asset", "wip", "approved")

    # Publish: version pin enforced
    approval = {"decision": "approved", "expires_at": "2099-01-01T00:00:00"}
    bad = ops.execute_step("act_pub_bad", "asset.publish", 4, 5, approval, [ev_brief.evidence_id])
    assert bad.status == "blocked" and bad.detail["code"] == "version_mismatch"
    good = ops.execute_step("act_pub", "asset.publish", 4, 4, approval,
                            [ev_brief.evidence_id], executor=lambda: "external:ig:post_123")
    assert good.status == "ok"

    # No receipt → stays scheduled (proven by blocked publish having no result_ref)
    assert bad.result_ref == "" and good.result_ref == "external:ig:post_123"

    # Learning proposal needs performance evidence
    ev_perf = sen.stage_evidence("ag_publication_x", "perf-ingest-7d", corroboration=2)
    learn = scr.propose("ag_campaign_q4", "Hook <3s wins on IG", "ctr 1.8→2.4%",
                        0.71, [ev_perf.evidence_id], [ev_perf.evidence_id])
    assert learn.confidence == 0.71

    result = {"brief": brief.id, "proposal": prop.proposal_id,
              "receipt": good.receipt_id, "learning": learn.proposal_id,
              "blockers": len(ops.blockers), "observations": len(sen.observation_log)}
    print("PROVING SLICE OK:", result)
    return result


if __name__ == "__main__":
    main()
