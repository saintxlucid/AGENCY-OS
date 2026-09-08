"""
Rituals as first-class graph objects (v1). Each ritual writes structured nodes:
briefing, kickoff, wip, creative_review, presentation, debrief, retrospective.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List


def _now() -> str:
    return datetime.now().isoformat()


def _id(prefix: str) -> str:
    return f"ag_ritual_{prefix}_{uuid.uuid4().hex[:8]}"


@dataclass
class Ritual:
    ritual_id: str
    kind: str  # briefing|kickoff|wip|creative_review|presentation|debrief|retrospective
    subject_id: str
    payload: Dict[str, Any] = field(default_factory=dict)
    decisions: List[str] = field(default_factory=list)
    next_actions: List[Dict[str, str]] = field(default_factory=list)
    created_at: str = field(default_factory=_now)


def briefing(subject_id: str, brief_id: str, clarifications: List[str]) -> Ritual:
    return Ritual(_id("briefing"), "briefing", subject_id,
                  {"brief_id": brief_id, "clarifications": clarifications})


def kickoff(subject_id: str, objective: str, team: List[str], timeline: str,
            risks: List[str], success: List[str]) -> Ritual:
    return Ritual(_id("kickoff"), "kickoff", subject_id,
                  {"objective": objective, "team": team, "timeline": timeline,
                   "risks": risks, "success": success})


def wip(subject_id: str, moving: List[str], blocked: List[str],
        late: List[str], needs_judgment: List[str]) -> Ritual:
    return Ritual(_id("wip"), "wip", subject_id,
                  {"moving": moving, "blocked": blocked, "late": late,
                   "needs_judgment": needs_judgment})


def creative_review(subject_id: str, concept_id: str, rationale: str,
                    feedback: List[str], decision: str) -> Ritual:
    return Ritual(_id("review"), "creative_review", subject_id,
                  {"concept_id": concept_id, "rationale": rationale,
                   "feedback": feedback, "decision": decision},
                  decisions=[decision])


def presentation(subject_id: str, narrative: str, objections: List[str],
                 response: str, decision: str, next_steps: List[str]) -> Ritual:
    return Ritual(_id("pres"), "presentation", subject_id,
                  {"narrative": narrative, "objections": objections,
                   "response": response, "decision": decision},
                  decisions=[decision],
                  next_actions=[{"action": s} for s in next_steps])


def debrief(subject_id: str, expected: str, actual: str, why: str, next_change: str) -> Ritual:
    return Ritual(_id("debrief"), "debrief", subject_id,
                  {"expected": expected, "actual": actual, "why": why,
                   "next_change": next_change})


def retrospective(subject_id: str, worked: List[str], failed: List[str],
                  unexpected: List[str], root_cause: str, action: str,
                  owner: str) -> Ritual:
    return Ritual(_id("retro"), "retrospective", subject_id,
                  {"worked": worked, "failed": failed, "unexpected": unexpected,
                   "root_cause": root_cause, "action": action},
                  next_actions=[{"action": action, "owner": owner}])
