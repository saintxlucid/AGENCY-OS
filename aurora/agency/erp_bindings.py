"""ASTRA OS — ERP ↔ Agency Graph state bindings (PHASE 1 seam).

ERP vocabularies predate the canonical schema. This module is the single
adapter: ERP writes validate against canonical TRANSITIONS via mapping.
No orphan invoices/tasks: helpers require parent linkage where mandated.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from aurora.agency.schema import TRANSITIONS, can_transition

# ─── Task: ERP TaskStatus ⇄ canonical task states ───
# ERP: todo | in_progress | review | done
# Canonical: todo | doing | blocked | done  (review folds to doing; blocked has no ERP enum)

ERP_TASK_TO_AGENCY: Dict[str, str] = {
    "todo": "todo",
    "in_progress": "doing",
    "review": "doing",
    "done": "done",
}

AGENCY_TO_ERP_TASK: Dict[str, str] = {
    "todo": "todo",
    "doing": "in_progress",
    "blocked": "in_progress",  # lossy: ERP cannot represent blocked; caller must set flag/tag
    "done": "done",
}


def erp_task_to_agency(status: str) -> str:
    key = status.value if hasattr(status, "value") else str(status)
    return ERP_TASK_TO_AGENCY.get(key, key)


def agency_to_erp_task(state: str) -> str:
    return AGENCY_TO_ERP_TASK.get(state, state)


def legal_task_transitions() -> List[Tuple[str, str]]:
    return list(TRANSITIONS.get("task", []))


def assert_legal_task_transition(frm_erp: str, to_erp: str) -> Tuple[str, str]:
    frm = erp_task_to_agency(frm_erp)
    to = erp_task_to_agency(to_erp)
    # review is a refinement of doing: doing→doing via review is always legal internally
    if frm == to and {frm_erp, to_erp} <= {"in_progress", "review", "doing"}:
        return frm, to
    if not can_transition("task", frm, to):
        raise ValueError(f"illegal task transition {frm_erp}→{to_erp} (canonical {frm}→{to})")
    return frm, to


def transition_erp_task(task, to_status) -> Tuple[str, str]:
    """Validate then mutate task.status. Returns (frm_agency, to_agency)."""
    frm_raw = task.status.value if hasattr(task.status, "value") else str(task.status)
    to_raw = to_status.value if hasattr(to_status, "value") else str(to_status)
    frm, to = assert_legal_task_transition(frm_raw, to_raw)
    task.status = to_status
    return frm, to


# ─── Campaign: free-string status → canonical ───

CAMPAIGN_ALIASES: Dict[str, str] = {
    "planning": "pitched",
    "pitched": "pitched",
    "scoped": "scoped",
    "active": "active",
    "in_review": "in_review",
    "completed": "completed",
    "killed": "killed",
}

CAMPAIGN_TRANSITIONS: List[Tuple[str, str]] = [
    ("pitched", "scoped"), ("scoped", "active"), ("active", "in_review"),
    ("in_review", "active"), ("in_review", "completed"), ("active", "completed"),
    ("pitched", "killed"), ("scoped", "killed"), ("active", "killed"),
]


def normalize_campaign_status(status: str) -> str:
    return CAMPAIGN_ALIASES.get(status, status)


def assert_legal_campaign_transition(frm: str, to: str) -> None:
    f, t = normalize_campaign_status(frm), normalize_campaign_status(to)
    if (f, t) not in CAMPAIGN_TRANSITIONS:
        raise ValueError(f"illegal campaign transition {frm}→{to} (canonical {f}→{t})")


# ─── Invoice: v1 closed transitions (no orphans: client_id + total required) ───

INVOICE_TRANSITIONS: List[Tuple[str, str]] = [
    ("draft", "sent"), ("sent", "paid"), ("sent", "overdue"),
    ("overdue", "paid"), ("draft", "cancelled"), ("sent", "cancelled"),
    ("overdue", "cancelled"),
]


def assert_legal_invoice_transition(frm: str, to: str) -> None:
    f = frm.value if hasattr(frm, "value") else str(frm)
    t = to.value if hasattr(to, "value") else str(to)
    if (f, t) not in INVOICE_TRANSITIONS:
        raise ValueError(f"illegal invoice transition {f}→{t}")


def assert_invoice_linkage(client_id: str | None, total: float) -> None:
    if not client_id:
        raise ValueError("orphan invoice blocked: client_id required")
    if total <= 0:
        raise ValueError("orphan invoice blocked: total must be > 0")
