"""
CRP test suite — Creative Object Model, AI Ops ledger, Governance, Runtime.

CRP = Creative Resource Planning. See docs/architecture/crp.md.

Stdlib unittest, no third-party dependencies, so it runs anywhere the
package imports. Table-driven where the surface is combinatorial (state
machine transitions, policy matching), example-driven where behaviour is
about sequencing (approval gates, workflow suspension).

Run:  python -m unittest tests.test_crp -v
"""
from __future__ import annotations

import asyncio
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aurora.enterprise.creative import (
    Actor, ActorType, CreativeGraph, CreativeObject, EdgeType, GATED_STAGES,
    ObjectKind, Stage, TRANSITIONS, TransitionError,
)
from aurora.enterprise.aiops import (
    AICall, AIOpsLedger, Budget, BudgetExceeded, CallKind, ModelRate,
    Outcome, RateCard,
)
from aurora.enterprise.governance import (
    ApprovalState, AuditChain, Decision, Effect, GovernanceEngine, Policy,
    PolicyContext, Severity, default_policies,
)
from aurora.enterprise.runtime import (
    ARPRuntime, CARPRuntime, CRPRuntime, ECRPRuntime, Intent, Result,
    RuntimeBlocked, RuntimeState, Usage,
)
from aurora.workflows.engine import (
    ExecutionStatus, NodeType, WorkflowEngine, WorkflowStatus, _safe_condition,
)

ORG = "org_test"


def run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


# ═══════════════════════════════════════════════════════════════
# Creative Object Model
# ═══════════════════════════════════════════════════════════════

class TestLifecycleStateMachine(unittest.TestCase):
    """Table-driven: the transition table is the contract."""

    def _obj(self, stage: Stage) -> CreativeObject:
        return CreativeObject("o1", ORG, ObjectKind.DESIGN, "t", stage=stage)

    def test_every_declared_transition_is_permitted(self):
        for src, targets in TRANSITIONS.items():
            for dst in targets:
                with self.subTest(src=src.value, dst=dst.value):
                    obj = self._obj(src)
                    obj.advance(dst, "u1", ActorType.HUMAN, allow_gated=True)
                    self.assertIs(obj.stage, dst)

    def test_every_undeclared_transition_is_rejected(self):
        for src in Stage:
            allowed = TRANSITIONS.get(src, set())
            for dst in Stage:
                if dst in allowed:
                    continue
                with self.subTest(src=src.value, dst=dst.value):
                    obj = self._obj(src)
                    with self.assertRaises(TransitionError):
                        obj.advance(dst, "u1", allow_gated=True)

    def test_terminal_stages_have_no_exits(self):
        for terminal in (Stage.ARCHIVED, Stage.KILLED):
            self.assertEqual(TRANSITIONS[terminal], set())

    def test_every_stage_except_terminals_can_be_killed_or_completed(self):
        for src, targets in TRANSITIONS.items():
            if src in (Stage.ARCHIVED, Stage.KILLED):
                continue
            with self.subTest(stage=src.value):
                self.assertTrue(targets, f"{src.value} is a dead end")

    def test_agent_blocked_from_gated_stages(self):
        for gated in GATED_STAGES:
            sources = [s for s, t in TRANSITIONS.items() if gated in t]
            for src in sources:
                with self.subTest(src=src.value, gated=gated.value):
                    obj = self._obj(src)
                    with self.assertRaises(TransitionError):
                        obj.advance(gated, "agent1", ActorType.AGENT)

    def test_agent_allowed_into_gated_stage_with_clearance(self):
        obj = self._obj(Stage.REVIEW)
        obj.advance(Stage.APPROVAL, "agent1", ActorType.AGENT, allow_gated=True)
        self.assertIs(obj.stage, Stage.APPROVAL)

    def test_human_ungated_stages_need_no_clearance(self):
        obj = self._obj(Stage.CONCEPT)
        obj.advance(Stage.DESIGN, "u1", ActorType.AGENT)
        self.assertIs(obj.stage, Stage.DESIGN)

    def test_history_records_each_hop(self):
        obj = self._obj(Stage.CONCEPT)
        obj.advance(Stage.DESIGN, "u1")
        obj.advance(Stage.REVIEW, "u2")
        self.assertEqual(len(obj.history), 2)
        self.assertEqual(obj.history[0].from_stage, "concept")
        self.assertEqual(obj.history[1].to_stage, "review")
        self.assertEqual(obj.history[1].actor_id, "u2")

    def test_revision_count_and_touched_by(self):
        obj = self._obj(Stage.REVIEW)
        obj.advance(Stage.REVISION, "cd")
        obj.advance(Stage.REVIEW, "designer")
        obj.advance(Stage.REVISION, "cd")
        self.assertEqual(obj.revision_count(), 2)
        self.assertEqual(obj.touched_by(), {"cd", "designer"})


class TestSignals(unittest.TestCase):

    def test_signal_carries_provenance_and_prior_value(self):
        obj = CreativeObject("o1", ORG, ObjectKind.DESIGN, "t")
        obj.set_signal("brand_fit", 0.7, source="agent:qa", confidence=0.8)
        obj.set_signal("brand_fit", 0.4, source="human:cd")
        s = obj.signals["brand_fit"]
        self.assertEqual(s["value"], 0.4)
        self.assertEqual(s["previous"], 0.7)
        self.assertEqual(s["source"], "human:cd")
        self.assertEqual(obj.signal("brand_fit"), 0.4)

    def test_missing_signal_returns_default(self):
        obj = CreativeObject("o1", ORG, ObjectKind.DESIGN, "t")
        self.assertIsNone(obj.signal("nope"))
        self.assertEqual(obj.signal("nope", 0.5), 0.5)


class TestGraph(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.g = CreativeGraph(self.tmp)
        self.g.add_actor(Actor("cd", ORG, "CD", ActorType.HUMAN))
        self.g.add_actor(Actor("ai", ORG, "Agent", ActorType.AGENT))

    def test_link_rejects_unknown_nodes(self):
        a = self.g.create_object(ORG, ObjectKind.DESIGN, "a")
        with self.assertRaises(KeyError):
            self.g.link(a.object_id, "ghost", EdgeType.REFERENCES)
        with self.assertRaises(KeyError):
            self.g.link("ghost", a.object_id, EdgeType.REFERENCES)

    def test_version_fork_inherits_ai_provenance(self):
        a = self.g.create_object(ORG, ObjectKind.DESIGN, "a", ai_generated=True)
        v2 = self.g.new_version(a.object_id, "cd")
        self.assertTrue(v2.ai_generated, "generated flag must not launder through a fork")
        self.assertTrue(v2.ai_assisted)
        self.assertEqual(v2.version, 2)
        self.assertFalse(a.is_canonical)
        self.assertTrue(v2.is_canonical)

    def test_human_edit_on_generated_work_stays_assisted(self):
        a = self.g.create_object(ORG, ObjectKind.DESIGN, "a", ai_generated=True)
        v2 = self.g.new_version(a.object_id, "cd", ai_generated=False)
        self.assertFalse(v2.ai_generated)
        self.assertTrue(v2.ai_assisted, "human-edited AI work is still AI-assisted")

    def test_provenance_spans_full_ancestry(self):
        a = self.g.create_object(ORG, ObjectKind.DESIGN, "a", created_by="ai")
        a.advance(Stage.RESEARCH, "researcher")
        v2 = self.g.new_version(a.object_id, "cd")
        v3 = self.g.new_version(v2.object_id, "designer")
        prov = self.g.provenance(v3.object_id)
        self.assertEqual(len(prov["lineage"]), 3)
        for who in ("ai", "cd", "designer", "researcher"):
            self.assertIn(who, prov["actors"], f"{who} missing from provenance")

    def test_lineage_ordered_oldest_first(self):
        a = self.g.create_object(ORG, ObjectKind.DESIGN, "a")
        v2 = self.g.new_version(a.object_id, "cd")
        chain = self.g.lineage(v2.object_id)
        self.assertEqual([c.version for c in chain], [1, 2])

    def test_traverse_respects_depth_and_edge_filter(self):
        a = self.g.create_object(ORG, ObjectKind.BRIEF, "a")
        b = self.g.create_object(ORG, ObjectKind.MOODBOARD, "b")
        c = self.g.create_object(ORG, ObjectKind.DESIGN, "c")
        self.g.link(b.object_id, a.object_id, EdgeType.FULFILLS)
        self.g.link(c.object_id, b.object_id, EdgeType.REFERENCES)
        deep = self.g.traverse(c.object_id, max_depth=2)
        self.assertEqual(len(deep), 2)
        shallow = self.g.traverse(c.object_id, max_depth=1)
        self.assertEqual(len(shallow), 1)
        filtered = self.g.traverse(c.object_id, max_depth=3, edge_types=[EdgeType.FULFILLS])
        self.assertEqual(filtered, [])

    def test_bottlenecks_measure_dwell_time(self):
        o = self.g.create_object(ORG, ObjectKind.DESIGN, "a", stage=Stage.CONCEPT)
        o.advance(Stage.DESIGN, "u")
        o.advance(Stage.REVIEW, "u")
        bn = self.g.bottlenecks(ORG)
        self.assertIn("design", bn)
        self.assertGreaterEqual(bn["design"]["samples"], 1)

    def test_funnel_counts_all_stages(self):
        self.g.create_object(ORG, ObjectKind.IDEA, "a", stage=Stage.IDEA)
        self.g.create_object(ORG, ObjectKind.DESIGN, "b", stage=Stage.DESIGN)
        f = self.g.funnel(ORG)
        self.assertEqual(f["idea"], 1)
        self.assertEqual(f["design"], 1)
        self.assertEqual(len(f), len(Stage))

    def test_org_isolation(self):
        self.g.create_object(ORG, ObjectKind.DESIGN, "mine")
        self.g.create_object("other_org", ObjectKind.DESIGN, "theirs")
        self.assertEqual(len(self.g.by_kind(ORG, ObjectKind.DESIGN)), 1)
        self.assertEqual(len(self.g.funnel(ORG)), len(Stage))
        self.assertEqual(sum(self.g.funnel(ORG).values()), 1)

    def test_persistence_roundtrip_preserves_enums_and_history(self):
        o = self.g.create_object(ORG, ObjectKind.VIDEO, "clip", stage=Stage.CONCEPT)
        o.advance(Stage.DESIGN, "u1")
        o.set_signal("brand_fit", 0.9, source="qa")
        self.g.link(o.object_id, "cd", EdgeType.PRODUCED_BY)
        self.g.save()

        g2 = CreativeGraph(self.tmp)
        g2.load()
        r = g2.objects[o.object_id]
        self.assertIs(r.kind, ObjectKind.VIDEO)
        self.assertIs(r.stage, Stage.DESIGN)
        self.assertEqual(len(r.history), 1)
        self.assertEqual(r.signal("brand_fit"), 0.9)
        self.assertEqual(len(g2.edges), 1)
        self.assertIs(list(g2.edges.values())[0].edge_type, EdgeType.PRODUCED_BY)
        self.assertEqual(len(g2.neighbors(o.object_id, EdgeType.PRODUCED_BY)), 1)

    def test_stalled_ignores_terminal_stages(self):
        o = self.g.create_object(ORG, ObjectKind.DESIGN, "old", stage=Stage.ARCHIVED)
        o.created_at = "2020-01-01T00:00:00"
        self.assertEqual(self.g.stalled(ORG, threshold_seconds=1), [])

    def test_ai_attribution_only_counts_shipped(self):
        self.g.create_object(ORG, ObjectKind.DESIGN, "wip",
                             stage=Stage.DESIGN, ai_generated=True)
        self.g.create_object(ORG, ObjectKind.DESIGN, "out",
                             stage=Stage.DELIVERY, ai_generated=True)
        a = self.g.ai_attribution(ORG)
        self.assertEqual(a["shipped"], 1)
        self.assertEqual(a["ai_generated"], 1)


# ═══════════════════════════════════════════════════════════════
# AI Ops
# ═══════════════════════════════════════════════════════════════

class TestRateCard(unittest.TestCase):

    def test_token_pricing_arithmetic(self):
        rc = RateCard([ModelRate("m", "p", input_per_1k=1.0, output_per_1k=2.0)])
        usd, priced = rc.price("m", input_tokens=1000, output_tokens=500)
        self.assertTrue(priced)
        self.assertAlmostEqual(usd, 2.0)

    def test_per_call_and_gpu_pricing(self):
        rc = RateCard([ModelRate("img", "p", per_call=0.04),
                       ModelRate("gpu", "self", gpu_per_hour=3.60)])
        self.assertAlmostEqual(rc.price("img", calls=5)[0], 0.20)
        self.assertAlmostEqual(rc.price("gpu", gpu_seconds=1800)[0], 1.80)

    def test_unknown_model_is_not_guessed(self):
        rc = RateCard([])
        usd, priced = rc.price("ghost", input_tokens=999999)
        self.assertEqual(usd, 0.0)
        self.assertFalse(priced)
        self.assertIn("ghost", rc.unknown_models)


class TestLedger(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.led = AIOpsLedger(self.tmp, RateCard([
            ModelRate("m", "p", input_per_1k=1.0, output_per_1k=1.0),
        ]))

    def _period(self):
        from datetime import datetime
        return datetime.now().isoformat()[:7]

    def test_attribution_flag(self):
        a = self.led.record(ORG, "m", client_id="c1", input_tokens=1000)
        b = self.led.record(ORG, "m", input_tokens=1000)
        self.assertTrue(a.attributable)
        self.assertFalse(b.attributable)
        gap = self.led.attribution_gap(ORG)
        self.assertAlmostEqual(gap["unattributed_share"], 0.5)

    def test_hard_stop_budget_blocks_before_append(self):
        self.led.set_budget(ORG, self._period(), 1.0, hard_stop=True)
        self.led.record(ORG, "m", input_tokens=900)
        before = len(self.led.calls)
        with self.assertRaises(BudgetExceeded):
            self.led.record(ORG, "m", input_tokens=900)
        self.assertEqual(len(self.led.calls), before,
                         "blocked call must not be recorded")

    def test_soft_budget_warns_but_allows(self):
        self.led.set_budget(ORG, self._period(), 1.0, hard_stop=False, warn_at=0.5)
        self.led.record(ORG, "m", input_tokens=800)
        status = self.led.budget_status(ORG)[0]
        self.assertEqual(status["state"], "warning")

    def test_scoped_budget_only_applies_to_its_scope(self):
        self.led.set_budget(ORG, self._period(), 0.001, scope="client",
                            scope_id="c1", hard_stop=True)
        self.led.record(ORG, "m", client_id="c2", input_tokens=5000)
        with self.assertRaises(BudgetExceeded):
            self.led.record(ORG, "m", client_id="c1", input_tokens=5000)

    def test_scorecard_reports_coverage_alongside_acceptance(self):
        calls = [self.led.record(ORG, "m", agent_id="a1", input_tokens=100)
                 for _ in range(10)]
        self.led.annotate(calls[0].call_id, accepted=True)
        sc = self.led.agent_scorecard(ORG)["a1"]
        self.assertEqual(sc["acceptance_rate"], 1.0)
        self.assertEqual(sc["review_coverage"], 0.1,
                         "a perfect score on 1/10 reviewed must be visible as such")

    def test_scorecard_none_when_nothing_reviewed(self):
        self.led.record(ORG, "m", agent_id="a1", input_tokens=100)
        sc = self.led.agent_scorecard(ORG)["a1"]
        self.assertIsNone(sc["acceptance_rate"])
        self.assertIsNone(sc["avg_rating"])

    def test_error_rate(self):
        self.led.record(ORG, "m", agent_id="a1", input_tokens=100)
        self.led.record(ORG, "m", agent_id="a1", input_tokens=100,
                        outcome=Outcome.ERROR)
        self.assertEqual(self.led.agent_scorecard(ORG)["a1"]["error_rate"], 0.5)

    def test_margin_treats_ai_as_cogs(self):
        self.led.record(ORG, "m", project_id="p1", input_tokens=1000)
        m = self.led.margin(ORG, "p1", revenue_usd=100.0, labor_cost_usd=49.0)
        self.assertAlmostEqual(m["gross_profit_usd"], 50.0)
        self.assertAlmostEqual(m["gross_margin"], 0.5)

    def test_unpriced_models_surface_in_spend(self):
        self.led.record(ORG, "ghost", input_tokens=1000)
        s = self.led.spend(ORG)
        self.assertEqual(s["unpriced_calls"], 1)
        self.assertIn("ghost", s["unpriced_models"])

    def test_persistence_roundtrip(self):
        self.led.record(ORG, "m", client_id="c1", input_tokens=1000,
                        kind=CallKind.IMAGE, outcome=Outcome.ERROR)
        self.led.save()
        led2 = AIOpsLedger(self.tmp)
        led2.load()
        self.assertEqual(len(led2.calls), 1)
        self.assertIs(led2.calls[0].kind, CallKind.IMAGE)
        self.assertIs(led2.calls[0].outcome, Outcome.ERROR)


# ═══════════════════════════════════════════════════════════════
# Governance
# ═══════════════════════════════════════════════════════════════

class TestPolicyMatching(unittest.TestCase):
    """Table-driven: glob semantics are easy to get subtly wrong."""

    CASES = [
        ("*",            "asset.publish",       True),
        ("*",            "anything",            True),
        ("asset.*",      "asset.publish",       True),
        ("asset.*",      "agent.execute",       False),
        ("*.delete",     "asset.delete",        True),
        ("*.delete",     "project.delete",      True),
        ("*.delete",     "asset.publish",       False),
        ("*.delete",     "delete",              False),
        ("asset.publish", "asset.publish",      True),
        ("asset.publish", "asset.publishing",   False),
    ]

    def test_patterns(self):
        for pattern, action, expected in self.CASES:
            with self.subTest(pattern=pattern, action=action):
                p = Policy("p", ORG, "n", pattern, Effect.DENY)
                self.assertEqual(p.matches(action), expected)


class TestPolicyEngine(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.gov = GovernanceEngine(self.tmp)
        self.gov.install_defaults(ORG)

    def test_agent_delete_denied(self):
        d = self.gov.evaluate(PolicyContext(ORG, "asset.delete",
                                            actor_id="a", actor_type="agent"))
        self.assertIs(d.effect, Effect.DENY)
        self.assertFalse(d.allowed)

    def test_human_delete_allowed(self):
        d = self.gov.evaluate(PolicyContext(ORG, "asset.delete",
                                            actor_id="u", actor_type="human"))
        self.assertTrue(d.allowed)

    def test_deny_beats_approval(self):
        self.gov.add_policy(Policy(
            "p_deny", ORG, "hard no", "asset.publish", Effect.DENY,
            severity=Severity.CRITICAL, priority=2000))
        d = self.gov.evaluate(PolicyContext(ORG, "asset.publish", ai_generated=True,
                                            external_facing=True))
        self.assertIs(d.effect, Effect.DENY)
        self.assertIsNone(d.approval_id)

    def test_strictest_effect_wins_regardless_of_order(self):
        self.gov.add_policy(Policy("p_low", ORG, "allow", "custom.act",
                                   Effect.ALLOW, priority=999))
        self.gov.add_policy(Policy("p_hi", ORG, "gate", "custom.act",
                                   Effect.REQUIRE_APPROVAL, priority=1))
        d = self.gov.evaluate(PolicyContext(ORG, "custom.act"))
        self.assertIs(d.effect, Effect.REQUIRE_APPROVAL)

    def test_broken_condition_fails_closed(self):
        def boom(ctx):
            raise RuntimeError("bad rule")
        self.gov.add_policy(Policy("p_boom", ORG, "broken", "custom.act",
                                   Effect.DENY, condition=boom, priority=500))
        d = self.gov.evaluate(PolicyContext(ORG, "custom.act"))
        self.assertIs(d.effect, Effect.DENY, "a broken rule must not fail open")

    def test_disabled_policy_ignored(self):
        p = Policy("p_off", ORG, "off", "custom.act", Effect.DENY, enabled=False)
        self.gov.add_policy(p)
        self.assertTrue(self.gov.evaluate(PolicyContext(ORG, "custom.act")).allowed)

    def test_org_isolation(self):
        d = self.gov.evaluate(PolicyContext("other_org", "asset.delete",
                                            actor_type="agent"))
        self.assertTrue(d.allowed, "policies must not leak across tenants")

    def test_conditions_accumulate(self):
        d = self.gov.evaluate(PolicyContext(
            ORG, "asset.publish", external_facing=True, accessibility_score=0.5))
        self.assertIs(d.effect, Effect.ALLOW_WITH_CONDITIONS)
        self.assertTrue(d.conditions)

    def test_explanation_names_the_blocker(self):
        d = self.gov.evaluate(PolicyContext(ORG, "asset.delete", actor_type="agent"))
        self.assertIn("Agents may not delete", d.explanation)

    def test_risk_score_tracks_severity(self):
        low = self.gov.evaluate(PolicyContext(ORG, "asset.deliver", ai_generated=True))
        high = self.gov.evaluate(PolicyContext(ORG, "model.finetune",
                                               contains_client_ip=True))
        self.assertLess(low.risk_score, high.risk_score)


class TestApprovals(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.gov = GovernanceEngine(self.tmp)
        self.gov.install_defaults(ORG)
        self.d = self.gov.evaluate(PolicyContext(
            ORG, "asset.publish", actor_id="requester", actor_type="agent",
            ai_generated=True, external_facing=True))
        self.aid = self.d.approval_id

    def test_gate_created(self):
        self.assertIsNotNone(self.aid)
        self.assertFalse(self.gov.is_cleared(self.aid))

    def test_self_approval_blocked(self):
        with self.assertRaises(PermissionError):
            self.gov.decide(self.aid, "requester", True)

    def test_wrong_role_blocked(self):
        with self.assertRaises(PermissionError):
            self.gov.decide(self.aid, "someone", True, approver_role="viewer")

    def test_correct_role_approves(self):
        a = self.gov.decide(self.aid, "cd", True, approver_role="creative_director")
        self.assertIs(a.state, ApprovalState.APPROVED)
        self.assertTrue(self.gov.is_cleared(self.aid))

    def test_rejection_does_not_clear(self):
        self.gov.decide(self.aid, "cd", False, approver_role="creative_director")
        self.assertFalse(self.gov.is_cleared(self.aid))

    def test_double_decision_blocked(self):
        self.gov.decide(self.aid, "cd", True, approver_role="creative_director")
        with self.assertRaises(PermissionError):
            self.gov.decide(self.aid, "cd2", True, approver_role="owner")

    def test_expired_approval_rejected_and_never_clears(self):
        a = self.gov.approvals[self.aid]
        a.expires_at = "2020-01-01T00:00:00"
        self.assertTrue(a.is_expired)
        with self.assertRaises(PermissionError):
            self.gov.decide(self.aid, "cd", True, approver_role="creative_director")
        self.assertFalse(self.gov.is_cleared(self.aid))

    def test_is_cleared_false_for_none_and_unknown(self):
        self.assertFalse(self.gov.is_cleared(None))
        self.assertFalse(self.gov.is_cleared("ap_nonexistent"))

    def test_pending_filtered_by_role(self):
        self.assertEqual(len(self.gov.pending(ORG, "creative_director")), 1)
        self.assertEqual(len(self.gov.pending(ORG, "viewer")), 0)


class TestAuditChain(unittest.TestCase):

    def test_empty_chain_valid(self):
        c = AuditChain()
        self.assertTrue(c.verify()["valid"])
        self.assertEqual(c.head(), AuditChain.GENESIS)

    def test_chain_links(self):
        c = AuditChain()
        e1 = c.append(ORG, "a", "ok")
        e2 = c.append(ORG, "b", "ok")
        self.assertEqual(e1.prev_hash, AuditChain.GENESIS)
        self.assertEqual(e2.prev_hash, e1.hash)
        self.assertTrue(c.verify()["valid"])

    def test_content_tamper_detected(self):
        c = AuditChain()
        c.append(ORG, "a", "ok")
        c.append(ORG, "b", "ok")
        c.events[0].outcome = "tampered"
        v = c.verify()
        self.assertFalse(v["valid"])
        self.assertEqual(v["broken_at"], 0)

    def test_deletion_detected(self):
        c = AuditChain()
        for i in range(4):
            c.append(ORG, f"a{i}", "ok")
        del c.events[1]
        self.assertFalse(c.verify()["valid"])

    def test_reorder_detected(self):
        c = AuditChain()
        for i in range(3):
            c.append(ORG, f"a{i}", "ok")
        c.events[0], c.events[1] = c.events[1], c.events[0]
        self.assertFalse(c.verify()["valid"])


# ═══════════════════════════════════════════════════════════════
# Runtime — the chokepoint
# ═══════════════════════════════════════════════════════════════

class TestRuntime(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.rt = CRPRuntime(persist_dir=self.tmp, strict_mode=True)
        self.rt.bootstrap(ORG)
        self.rt.ledger.rates.set_rate(
            ModelRate("m", "p", input_per_1k=1.0, output_per_1k=1.0))
        self.rt.graph.add_actor(Actor("cd", ORG, "CD", ActorType.HUMAN))
        self.rt.graph.add_actor(Actor("ai", ORG, "Agent", ActorType.AGENT))
        self.obj = self.rt.graph.create_object(
            ORG, ObjectKind.DESIGN, "hero", stage=Stage.REVIEW,
            client_id="c1", project_id="p1", ai_generated=True)

    def test_strict_mode_denies_unknown_action(self):
        r = run(self.rt.execute(Intent(ORG, "totally.made.up")))
        self.assertIs(r.state, RuntimeState.DENIED)
        self.assertIn("unknown action", r.error)

    def test_permissive_mode_allows_unknown_action(self):
        rt = CRPRuntime(persist_dir=self.tmp, strict_mode=False)
        rt.bootstrap(ORG)
        r = run(rt.execute(Intent(ORG, "totally.made.up")))
        self.assertIs(r.state, RuntimeState.EXECUTED)

    def test_handler_not_invoked_when_denied(self):
        calls = []
        r = run(self.rt.execute(
            Intent(ORG, "asset.delete", actor_id="ai", actor_type=ActorType.AGENT),
            lambda: calls.append(1)))
        self.assertIs(r.state, RuntimeState.DENIED)
        self.assertEqual(calls, [], "denied work must never run")

    def test_handler_not_invoked_when_awaiting_approval(self):
        calls = []
        r = run(self.rt.execute(
            Intent(ORG, "asset.publish", actor_id="ai", actor_type=ActorType.AGENT,
                   object_id=self.obj.object_id, ai_generated=True,
                   external_facing=True),
            lambda: calls.append(1)))
        self.assertIs(r.state, RuntimeState.AWAITING_APPROVAL)
        self.assertEqual(calls, [])
        self.assertIsNotNone(r.approval_id)

    def test_approved_run_executes_and_advances(self):
        r1 = run(self.rt.publish(self.obj.object_id, "ai", ActorType.AGENT))
        self.assertIs(r1.state, RuntimeState.AWAITING_APPROVAL)
        self.rt.gov.decide(r1.approval_id, "cd", True,
                           approver_role="creative_director")
        r2 = run(self.rt.advance(self.obj.object_id, Stage.APPROVAL, "cd",
                                 approval_id=r1.approval_id))
        self.assertIs(r2.state, RuntimeState.EXECUTED)
        self.assertEqual(r2.stage_after, "approval")

    def test_gated_stage_refused_without_clearance(self):
        r = run(self.rt.advance(self.obj.object_id, Stage.APPROVAL, "ai",
                                ActorType.AGENT))
        self.assertIsNot(r.state, RuntimeState.EXECUTED)

    def test_illegal_transition_returns_failed_not_raises(self):
        r = run(self.rt.advance(self.obj.object_id, Stage.DELIVERY, "cd"))
        self.assertIs(r.state, RuntimeState.FAILED)
        self.assertIn("not a legal transition", r.error)
        self.assertEqual(self.obj.stage, Stage.REVIEW, "stage must not move")

    def test_signals_read_from_graph_not_caller(self):
        self.obj.set_signal("brand_fit", 0.1, source="qa")
        d = self.rt.preflight(Intent(
            ORG, "asset.publish", actor_id="cd", object_id=self.obj.object_id,
            external_facing=True))
        self.assertIs(d.state, RuntimeState.AWAITING_APPROVAL,
                      "low brand_fit in the graph must gate regardless of caller claims")

    def test_metering_records_cost_and_attribution(self):
        async def work():
            return "done", Usage(input_tokens=1000, output_tokens=1000, model="m")
        r = run(self.rt.execute(
            Intent(ORG, "agent.execute", actor_id="ai", actor_type=ActorType.AGENT,
                   object_id=self.obj.object_id, model="m", billable=True),
            work))
        self.assertIs(r.state, RuntimeState.EXECUTED)
        self.assertAlmostEqual(r.cost_usd, 2.0)
        self.assertEqual(r.call.client_id, "c1")
        self.assertEqual(r.call.project_id, "p1")
        self.assertTrue(r.call.billable)

    def test_budget_blocks_before_handler_runs(self):
        from datetime import datetime
        self.rt.ledger.set_budget(ORG, datetime.now().isoformat()[:7], 0.01,
                                  hard_stop=True)
        calls = []
        r = run(self.rt.execute(
            Intent(ORG, "agent.execute", actor_id="ai", actor_type=ActorType.AGENT,
                   model="m", estimated_cost_usd=5.0),
            lambda: calls.append(1)))
        self.assertIs(r.state, RuntimeState.BUDGET_BLOCKED)
        self.assertEqual(calls, [], "budget must block before spending compute")

    def test_handler_exception_becomes_failed_result(self):
        def boom():
            raise ValueError("kaboom")
        r = run(self.rt.execute(
            Intent(ORG, "agent.execute", actor_id="ai", actor_type=ActorType.AGENT,
                   model="m"), boom))
        self.assertIs(r.state, RuntimeState.FAILED)
        self.assertIn("kaboom", r.error)
        self.assertIs(r.call.outcome, Outcome.ERROR)

    def test_misdeclaration_flagged(self):
        async def work():
            return "x", Usage(model="m", actual_ai_generated=True)
        r = run(self.rt.execute(
            Intent(ORG, "agent.execute", actor_id="ai", actor_type=ActorType.AGENT,
                   object_id=self.obj.object_id, model="m", ai_generated=False),
            work))
        self.assertIn("ai_generated", r.declared_vs_actual)
        self.assertIn("intent_misdeclaration", r.call.flagged)

    def test_agent_execution_marks_object_ai_assisted(self):
        obj = self.rt.graph.create_object(ORG, ObjectKind.DESIGN, "x")
        self.assertFalse(obj.ai_assisted)
        run(self.rt.execute(Intent(ORG, "agent.execute", actor_id="ai",
                                   actor_type=ActorType.AGENT,
                                   object_id=obj.object_id)))
        self.assertTrue(obj.ai_assisted)

    def test_unwrap_raises_on_block(self):
        r = run(self.rt.execute(Intent(ORG, "asset.delete", actor_id="ai",
                                       actor_type=ActorType.AGENT)))
        with self.assertRaises(RuntimeBlocked):
            r.unwrap()

    def test_unmetered_actions_surface_in_health(self):
        run(self.rt.execute(Intent(ORG, "asset.create", actor_id="cd"),
                            lambda: "no model"))
        self.assertIn("asset.create", self.rt.health(ORG)["unmetered_actions"])

    def test_every_run_is_audited(self):
        before = len(self.rt.gov.audit.events)
        run(self.rt.execute(Intent(ORG, "asset.create", actor_id="cd")))
        run(self.rt.execute(Intent(ORG, "asset.delete", actor_id="ai",
                                   actor_type=ActorType.AGENT)))
        self.assertGreater(len(self.rt.gov.audit.events), before + 1)
        self.assertTrue(self.rt.gov.audit.verify()["valid"])

    def test_health_reports_chain_and_counts(self):
        run(self.rt.execute(Intent(ORG, "asset.create", actor_id="cd")))
        h = self.rt.health(ORG)
        self.assertEqual(h["executed"], 1)
        self.assertTrue(h["strict_mode"])
        self.assertTrue(h["governance"]["chain"]["valid"])

    def test_preflight_does_not_execute(self):
        calls = []
        self.rt.preflight(Intent(ORG, "asset.create", actor_id="cd"))
        self.assertEqual(calls, [])
        self.assertEqual(len(self.rt.runs), 0)


# ═══════════════════════════════════════════════════════════════
# Workflow engine
# ═══════════════════════════════════════════════════════════════

class TestCategoryAliases(unittest.TestCase):
    """
    CRP is canonical. CARP and ARP are supported aliases so that a
    reasonable import guess does not fail. They must stay the *same class* —
    a subclass would silently fork behaviour and break isinstance().
    """

    def test_aliases_are_the_same_class(self):
        for alias in (CARPRuntime, ARPRuntime, ECRPRuntime):
            with self.subTest(alias=alias.__name__):
                self.assertIs(alias, CRPRuntime)

    def test_isinstance_holds_across_all_names(self):
        rt = CARPRuntime(persist_dir=tempfile.mkdtemp(), strict_mode=False)
        for alias in (CRPRuntime, CARPRuntime, ARPRuntime, ECRPRuntime):
            with self.subTest(alias=alias.__name__):
                self.assertIsInstance(rt, alias)

    def test_alias_instance_is_fully_functional(self):
        rt = ARPRuntime(persist_dir=tempfile.mkdtemp(), strict_mode=True)
        rt.bootstrap(ORG)
        r = run(rt.execute(Intent(ORG, "asset.delete", actor_id="a",
                                  actor_type=ActorType.AGENT)))
        self.assertIs(r.state, RuntimeState.DENIED,
                      "governance must work identically regardless of import name")


class TestSafeCondition(unittest.TestCase):

    CASES = [
        ("score > 5",            {"score": 10},            True),
        ("score > 5",            {"score": 1},             False),
        ("score >= 10",          {"score": 10},            True),
        ("name == 'nike'",       {"name": "nike"},         True),
        ("name != 'nike'",       {"name": "nike"},         False),
        ("flag",                 {"flag": True},           True),
        ("flag",                 {"flag": False},          False),
        ("score > 5 and flag",   {"score": 9, "flag": 1},  True),
        ("score > 5 and flag",   {"score": 1, "flag": 1},  False),
        ("score > 5 or flag",    {"score": 1, "flag": 1},  True),
        ("missing > 5",          {},                       False),
        ("title contains 'lux'", {"title": "luxury"},      True),
    ]

    def test_grammar(self):
        for expr, data, expected in self.CASES:
            with self.subTest(expr=expr):
                self.assertEqual(_safe_condition(expr, data), expected)

    def test_no_code_execution(self):
        data = {}
        for hostile in ("__import__('os').system('echo pwned')",
                        "().__class__.__bases__[0]"):
            with self.subTest(expr=hostile):
                self.assertFalse(_safe_condition(hostile, data))


class TestWorkflowValidation(unittest.TestCase):

    def setUp(self):
        self.e = WorkflowEngine()
        self.wf = self.e.create_workflow(ORG, "w")

    def test_cycle_detected(self):
        a = self.e.add_node(self.wf.workflow_id, NodeType.ACTION, "a")
        b = self.e.add_node(self.wf.workflow_id, NodeType.ACTION, "b")
        self.e.connect_nodes(self.wf.workflow_id, a.node_id, b.node_id)
        self.e.connect_nodes(self.wf.workflow_id, b.node_id, a.node_id)
        report = self.e.validate(self.wf.workflow_id)
        self.assertFalse(report["valid"])
        self.assertTrue(any("cycle" in x for x in report["errors"]))

    def test_activation_refused_when_invalid(self):
        a = self.e.add_node(self.wf.workflow_id, NodeType.ACTION, "a")
        self.e.connect_nodes(self.wf.workflow_id, a.node_id, a.node_id)
        self.e.activate(self.wf.workflow_id)
        self.assertIs(self.wf.status, WorkflowStatus.DRAFT)

    def test_cyclic_workflow_refused_at_execution(self):
        a = self.e.add_node(self.wf.workflow_id, NodeType.ACTION, "a")
        b = self.e.add_node(self.wf.workflow_id, NodeType.ACTION, "b")
        self.e.connect_nodes(self.wf.workflow_id, a.node_id, b.node_id)
        self.e.connect_nodes(self.wf.workflow_id, b.node_id, a.node_id)
        self.wf.status = WorkflowStatus.ACTIVE
        r = run(self.e.execute(self.wf.workflow_id))
        self.assertIn("cycle", r["error"])

    def test_agent_node_without_agent_is_error(self):
        self.e.add_node(self.wf.workflow_id, NodeType.AGENT, "a", {})
        self.assertFalse(self.e.validate(self.wf.workflow_id)["valid"])

    def test_dangling_edge_is_error(self):
        a = self.e.add_node(self.wf.workflow_id, NodeType.ACTION, "a")
        a.connections.append("ghost")
        self.assertFalse(self.e.validate(self.wf.workflow_id)["valid"])

    def test_orphan_is_warning_not_error(self):
        t = self.e.add_node(self.wf.workflow_id, NodeType.TRIGGER, "t")
        self.e.add_node(self.wf.workflow_id, NodeType.ACTION, "orphan")
        report = self.e.validate(self.wf.workflow_id)
        self.assertTrue(report["valid"])
        self.assertTrue(any("unreachable" in w for w in report["warnings"]))


class TestWorkflowExecution(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.rt = CRPRuntime(persist_dir=self.tmp, strict_mode=False)
        self.rt.bootstrap(ORG)
        self.e = WorkflowEngine(runtime=self.rt)

    def test_approval_node_suspends_execution(self):
        wf = self.e.create_workflow(ORG, "w")
        t = self.e.add_node(wf.workflow_id, NodeType.TRIGGER, "t")
        ap = self.e.add_node(wf.workflow_id, NodeType.APPROVAL, "gate",
                             {"approver_roles": ["owner"]})
        after = self.e.add_node(wf.workflow_id, NodeType.ACTION, "after",
                                {"action_type": "noop"})
        self.e.connect_nodes(wf.workflow_id, t.node_id, ap.node_id)
        self.e.connect_nodes(wf.workflow_id, ap.node_id, after.node_id)
        self.e.activate(wf.workflow_id)

        ex = run(self.e.execute(wf.workflow_id))
        self.assertEqual(ex["status"], ExecutionStatus.SUSPENDED.value)
        self.assertNotIn(after.node_id, ex["completed_nodes"],
                         "downstream nodes must not run before approval")

    def test_resume_refused_without_approval(self):
        wf = self.e.create_workflow(ORG, "w")
        t = self.e.add_node(wf.workflow_id, NodeType.TRIGGER, "t")
        ap = self.e.add_node(wf.workflow_id, NodeType.APPROVAL, "gate",
                             {"approver_roles": ["owner"]})
        self.e.connect_nodes(wf.workflow_id, t.node_id, ap.node_id)
        self.e.activate(wf.workflow_id)
        ex = run(self.e.execute(wf.workflow_id))
        out = run(self.e.resume(ex["execution_id"]))
        self.assertIn("error", out)

    def test_resume_after_approval_completes(self):
        wf = self.e.create_workflow(ORG, "w")
        t = self.e.add_node(wf.workflow_id, NodeType.TRIGGER, "t")
        ap = self.e.add_node(wf.workflow_id, NodeType.APPROVAL, "gate",
                             {"approver_roles": ["owner"]})
        after = self.e.add_node(wf.workflow_id, NodeType.ACTION, "after",
                                {"action_type": "noop"})
        self.e.connect_nodes(wf.workflow_id, t.node_id, ap.node_id)
        self.e.connect_nodes(wf.workflow_id, ap.node_id, after.node_id)
        self.e.activate(wf.workflow_id)

        ex = run(self.e.execute(wf.workflow_id))
        self.rt.gov.decide(ex["pending_approval"], "owner_user", True,
                           approver_role="owner")
        ex2 = run(self.e.resume(ex["execution_id"]))
        self.assertEqual(ex2["status"], ExecutionStatus.COMPLETED.value)
        self.assertIn(after.node_id, ex2["completed_nodes"])

    def test_two_gates_require_two_approvals(self):
        """Regression: one clearance must not satisfy a later, distinct gate."""
        wf = self.e.create_workflow(ORG, "w")
        t = self.e.add_node(wf.workflow_id, NodeType.TRIGGER, "t")
        g1 = self.e.add_node(wf.workflow_id, NodeType.APPROVAL, "gate1",
                             {"approver_roles": ["owner"]})
        g2 = self.e.add_node(wf.workflow_id, NodeType.APPROVAL, "gate2",
                             {"approver_roles": ["owner"]})
        end = self.e.add_node(wf.workflow_id, NodeType.ACTION, "end",
                              {"action_type": "noop"})
        for a, b in ((t, g1), (g1, g2), (g2, end)):
            self.e.connect_nodes(wf.workflow_id, a.node_id, b.node_id)
        self.e.activate(wf.workflow_id)

        ex = run(self.e.execute(wf.workflow_id))
        first = ex["pending_approval"]
        self.rt.gov.decide(first, "owner_user", True, approver_role="owner")

        ex = run(self.e.resume(ex["execution_id"]))
        self.assertEqual(ex["status"], ExecutionStatus.SUSPENDED.value,
                         "second gate must suspend independently")
        second = ex["pending_approval"]
        self.assertNotEqual(first, second)

        self.rt.gov.decide(second, "owner_user", True, approver_role="owner")
        ex = run(self.e.resume(ex["execution_id"]))
        self.assertEqual(ex["status"], ExecutionStatus.COMPLETED.value)
        self.assertIn(end.node_id, ex["completed_nodes"])

    def test_approval_node_blocks_without_runtime(self):
        e = WorkflowEngine(runtime=None)
        wf = e.create_workflow(ORG, "w")
        t = e.add_node(wf.workflow_id, NodeType.TRIGGER, "t")
        ap = e.add_node(wf.workflow_id, NodeType.APPROVAL, "gate",
                        {"approver_roles": ["owner"]})
        e.connect_nodes(wf.workflow_id, t.node_id, ap.node_id)
        e.activate(wf.workflow_id)
        ex = run(e.execute(wf.workflow_id))
        self.assertEqual(ex["status"], ExecutionStatus.BLOCKED.value)
        self.assertFalse(ex["governed"])

    def test_denied_action_blocks_workflow(self):
        rt = CRPRuntime(persist_dir=self.tmp, strict_mode=False)
        rt.bootstrap(ORG)
        e = WorkflowEngine(runtime=rt)
        wf = e.create_workflow(ORG, "w")
        t = e.add_node(wf.workflow_id, NodeType.TRIGGER, "t")
        d = e.add_node(wf.workflow_id, NodeType.ACTION, "del",
                       {"action_type": "delete"})
        e.connect_nodes(wf.workflow_id, t.node_id, d.node_id)
        e.activate(wf.workflow_id)
        # Workflow actions run as SYSTEM, which the agent-delete rule permits;
        # add an explicit deny to prove the block path works end to end.
        rt.gov.add_policy(Policy("p_nodel", ORG, "no deletes", "asset.delete",
                                 Effect.DENY, priority=2000))
        ex = run(e.execute(wf.workflow_id))
        self.assertEqual(ex["status"], ExecutionStatus.BLOCKED.value)

    def test_condition_branches(self):
        wf = self.e.create_workflow(ORG, "w")
        t = self.e.add_node(wf.workflow_id, NodeType.TRIGGER, "t")
        c = self.e.add_node(wf.workflow_id, NodeType.CONDITION, "c",
                            {"condition": "score > 5"})
        yes = self.e.add_node(wf.workflow_id, NodeType.ACTION, "yes", {"action_type": "noop"})
        no = self.e.add_node(wf.workflow_id, NodeType.ACTION, "no", {"action_type": "noop"})
        self.e.connect_nodes(wf.workflow_id, t.node_id, c.node_id)
        self.e.connect_nodes(wf.workflow_id, c.node_id, yes.node_id, branch="true")
        self.e.connect_nodes(wf.workflow_id, c.node_id, no.node_id, branch="false")
        self.e.activate(wf.workflow_id)

        ex = run(self.e.execute(wf.workflow_id, {"score": 10}))
        self.assertIn(yes.node_id, ex["completed_nodes"])
        self.assertNotIn(no.node_id, ex["completed_nodes"])

        ex2 = run(self.e.execute(wf.workflow_id, {"score": 1}))
        self.assertIn(no.node_id, ex2["completed_nodes"])
        self.assertNotIn(yes.node_id, ex2["completed_nodes"])

    def test_template_workflow_is_registered_and_valid(self):
        wf = self.e.create_campaign_workflow(ORG)
        self.assertIn(wf.workflow_id, self.e.workflows)
        report = self.e.validate(wf.workflow_id)
        self.assertTrue(report["valid"], report["errors"])

    def test_template_suspends_at_first_gate(self):
        wf = self.e.create_campaign_workflow(ORG)
        self.e.activate(wf.workflow_id)
        ex = run(self.e.execute(wf.workflow_id))
        self.assertEqual(ex["status"], ExecutionStatus.SUSPENDED.value)
        names = [wf.node(n).name for n in ex["completed_nodes"]]
        self.assertNotIn("Publish", names)

    def test_persistence_roundtrip_rehydrates_objects(self):
        wf = self.e.create_campaign_workflow(ORG)
        d = Path(self.tmp) / "wf"
        self.e.save(str(d))
        e2 = WorkflowEngine()
        e2.load(str(d))
        loaded = e2.workflows[wf.workflow_id]
        self.assertEqual(loaded.name, wf.name)
        self.assertEqual(len(loaded.nodes), len(wf.nodes))
        self.assertIs(loaded.nodes[0].type, NodeType.TRIGGER)
        self.assertTrue(e2.validate(wf.workflow_id)["valid"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
