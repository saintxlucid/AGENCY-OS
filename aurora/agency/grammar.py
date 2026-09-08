"""
Operating grammar router (v1). Agency phrases → graph intents. Rule-based, no LLM.
Each phrase resolves to {intent, subject_kind, params} for Operator/Sovereign paths.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

PATTERNS: List[Tuple[str, str, str]] = [
    (r"brief this", "brief.create", "request"),
    (r"action brief", "brief.create", "request"),
    (r"route .* to creative", "work.route", "concept"),
    (r"debrief", "work.debrief", "campaign"),
    (r"status", "work.status", "campaign"),
    (r"waiting on .*feedback", "approval.awaiting", "asset"),
    (r"not in scope|out of scope", "scope.check", "scope"),
    (r"another route|other route", "concept.variant", "concept"),
    (r"another round|one more round", "asset.revise", "asset"),
    (r"is .* approved", "approval.check", "asset"),
    (r"latest version", "asset.latest", "asset"),
    (r"who dificil|who is on|who's on", "work.assignments", "task"),
    (r"who.*on it", "work.assignments", "task"),
    (r"capacit", "capacity.check", "task"),
    (r"deadline|make the", "delivery.check", "campaign"),
    (r"brief changed", "brief.supersede", "brief"),
    (r"push .*production", "asset.to_production", "asset"),
    (r"sign-?off|sign off", "approval.request", "asset"),
    (r"burn|overservicing|retainer left|charge this", "scope.check", "scope"),
    (r"what did we learn", "knowledge.learnings", "campaign"),
]


def parse_utterance(text: str) -> Dict[str, Any]:
    t = text.strip().lower()
    for pattern, intent, subject in PATTERNS:
        if re.search(pattern, t):
            return {"intent": intent, "subject_kind": subject,
                    "utterance": text, "confidence": 0.8}
    return {"intent": "unknown", "subject_kind": "",
            "utterance": text, "confidence": 0.0}
