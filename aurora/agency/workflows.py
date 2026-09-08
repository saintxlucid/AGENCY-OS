"""
Workflow templates (v1). Per-type ordered states + gate kinds. Executable domain knowledge.
TVC ≠ social ≠ pitch ≠ press: each template is a subset path over canonical states.
"""
from __future__ import annotations

from typing import Dict, List

TEMPLATES: Dict[str, Dict[str, List[str]]] = {
    "tvc": {"states": ["briefed", "strategy", "creative", "internal_review",
                       "client_review", "revision", "qc", "approval",
                       "production", "published", "learning"],
            "gates": ["brief.approved", "concept.approved_for_production",
                      "asset.qc_passed", "approval.exact_version", "receipt"]},
    "social_post": {"states": ["briefed", "creative", "internal_review",
                               "approval", "scheduled", "published", "learning"],
                    "gates": ["brief.approved", "approval.exact_version", "receipt"]},
    "pitch": {"states": ["lead", "pitched", "strategy", "creative",
                         "client_review", "won", "learning"],
              "gates": ["pitch.submitted", "decision.recorded"]},
    "press_release": {"states": ["briefed", "creative", "internal_review",
                                 "client_review", "approval", "published", "learning"],
                      "gates": ["brief.approved", "approval.exact_version"]},
    "always_on": {"states": ["briefed", "creative", "qc", "approval",
                             "scheduled", "monitoring", "analysis", "learning"],
                  "gates": ["approval.exact_version", "receipt", "performance.window"]},
}


def template_states(work_type: str) -> List[str]:
    return list(TEMPLATES.get(work_type, {}).get("states", []))


def template_gates(work_type: str) -> List[str]:
    return list(TEMPLATES.get(work_type, {}).get("gates", []))


def is_valid_template(work_type: str) -> bool:
    return work_type in TEMPLATES
