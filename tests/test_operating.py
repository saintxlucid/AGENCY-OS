"""Operating grammar + templates + rituals tests."""
from aurora.agency.grammar import parse_utterance
from aurora.agency.rituals import (
    briefing, creative_review, debrief, kickoff, presentation, retrospective, wip,
)
from aurora.agency.workflows import is_valid_template, template_gates, template_states


def test_grammar_routes():
    assert parse_utterance("Brief this.")["intent"] == "brief.create"
    assert parse_utterance("That wasn't in scope.")["intent"] == "scope.check"
    assert parse_utterance("Is this approved?")["intent"] == "approval.check"
    assert parse_utterance("What's the burn?")["intent"] == "scope.check"
    assert parse_utterance("What did we learn?")["intent"] == "knowledge.learnings"
    assert parse_utterance("blargle wobble")["confidence"] == 0.0


def test_templates_differ_by_type():
    assert "production" in template_states("tvc")
    assert "production" not in template_states("social_post")
    assert "won" in template_states("pitch")
    assert template_gates("tvc") != template_gates("social_post")
    assert is_valid_template("press_release") and not is_valid_template("nope")


def test_rituals_write_objects():
    b = briefing("ag_campaign_x", "ag_brief_1", ["audience?"])
    assert b.kind == "briefing" and b.payload["brief_id"] == "ag_brief_1"
    k = kickoff("c", "launch", ["sara"], "2w", ["risk"], ["ship"])
    assert k.payload["team"] == ["sara"]
    w = wip("c", ["a"], ["b"], ["c"], ["d"])
    assert w.payload["blocked"] == ["b"]
    r = creative_review("c", "concept_1", "why", ["fb"], "revise")
    assert r.decisions == ["revise"]
    p = presentation("c", "narr", ["obj"], "resp", "approved", ["ship it"])
    assert p.next_actions == [{"action": "ship it"}]
    d = debrief("c", "e", "a", "why", "next")
    assert d.payload["why"] == "why"
    assert retrospective("c", ["w"], ["f"], ["u"], "root", "fix", "sara").next_actions[0]["owner"] == "sara"
