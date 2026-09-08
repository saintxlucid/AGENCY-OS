"""
AGENCY OS — AI-Native Agency ERP + Creative Intelligence Platform
Enterprise Resource Planning Layer
"""
from __future__ import annotations
import os, json, uuid, re, hashlib, secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path


# ─── Shared Types ───

class Currency(Enum):
    USD = "USD"; EUR = "EUR"; GBP = "GBP"; JPY = "JPY"; CAD = "CAD"; AUD = "AUD"

class Status(Enum):
    ACTIVE = "active"; ARCHIVED = "archived"; DELETED = "deleted"; DRAFT = "draft"

@dataclass
class Address:
    street: str = ""; city: str = ""; state: str = ""
    zip: str = ""; country: str = ""

def _id(prefix: str = "") -> str:
    return f"{prefix}{uuid.uuid4().hex[:10]}"

def _now() -> str:
    return datetime.now().isoformat()


# ═══════════════════════════════════════════════════════════════
# 1. CRM — Customer Relationship Management
# ═══════════════════════════════════════════════════════════════

class LeadStatus(Enum):
    NEW = "new"; QUALIFIED = "qualified"; CONTACTED = "contacted"
    PROPOSAL = "proposal"; NEGOTIATION = "negotiation"; WON = "won"; LOST = "lost"

@dataclass
class Lead:
    lead_id: str; org_id: str; name: str; email: str
    company: Optional[str] = None; phone: Optional[str] = None
    source: Optional[str] = None; status: LeadStatus = LeadStatus.NEW
    score: float = 0.0; value: float = 0.0
    owner_id: Optional[str] = None; notes: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now)

@dataclass
class Opportunity:
    opp_id: str; org_id: str; name: str; contact_id: Optional[str] = None
    stage: str = "discovery"; value: float = 0.0; probability: float = 0.0
    expected_close: Optional[str] = None; actual_close: Optional[str] = None
    owner_id: Optional[str] = None; source: Optional[str] = None
    notes: Optional[str] = None; tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now)

@dataclass
class Contact:
    contact_id: str; org_id: str; name: str; email: str
    phone: Optional[str] = None; company: Optional[str] = None
    title: Optional[str] = None; linkedin: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    last_contact: Optional[str] = None; notes: Optional[str] = None
    created_at: str = field(default_factory=_now)

@dataclass
class Meeting:
    meeting_id: str; org_id: str; title: str
    date: str; duration_min: int = 60
    attendees: List[str] = field(default_factory=list)
    notes: Optional[str] = None; ai_summary: Optional[str] = None
    action_items: List[str] = field(default_factory=list)
    recording_url: Optional[str] = None
    project_id: Optional[str] = None
    created_at: str = field(default_factory=_now)


# ═══════════════════════════════════════════════════════════════
# 2. PROJECT ERP — Campaigns, Tasks, Resources
# ═══════════════════════════════════════════════════════════════

class TaskStatus(Enum):
    TODO = "todo"; IN_PROGRESS = "in_progress"; REVIEW = "review"; DONE = "done"

@dataclass
class Task:
    task_id: str; org_id: str; project_id: str; title: str
    description: Optional[str] = None; status: TaskStatus = TaskStatus.TODO
    priority: str = "medium"; assignee_id: Optional[str] = None
    due_date: Optional[str] = None; estimated_hours: float = 0.0
    actual_hours: float = 0.0; budget: float = 0.0; cost: float = 0.0
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now)

@dataclass
class Campaign:
    campaign_id: str; org_id: str; name: str
    client_id: Optional[str] = None; project_id: Optional[str] = None
    status: str = "planning"; budget: float = 0.0; spent: float = 0.0
    start_date: Optional[str] = None; end_date: Optional[str] = None
    goals: List[str] = field(default_factory=list)
    channels: List[str] = field(default_factory=list)
    kpis: Dict[str, float] = field(default_factory=dict)
    created_at: str = field(default_factory=_now)

@dataclass
class TimeEntry:
    entry_id: str; org_id: str; user_id: str
    project_id: Optional[str] = None; task_id: Optional[str] = None
    date: str = ""; hours: float = 0.0; billable: bool = True
    rate: float = 0.0; description: Optional[str] = None
    created_at: str = field(default_factory=_now)


# ═══════════════════════════════════════════════════════════════
# 3. FINANCE ERP — Quotes, Invoices, Expenses, Payroll
# ═══════════════════════════════════════════════════════════════

class InvoiceStatus(Enum):
    DRAFT = "draft"; SENT = "sent"; PAID = "paid"; OVERDUE = "overdue"; CANCELLED = "cancelled"

@dataclass
class Invoice:
    invoice_id: str; org_id: str; client_id: str
    number: str = ""; status: InvoiceStatus = InvoiceStatus.DRAFT
    issue_date: str = ""; due_date: str = ""
    items: List[Dict] = field(default_factory=list)
    subtotal: float = 0.0; tax: float = 0.0; total: float = 0.0
    amount_paid: float = 0.0; currency: Currency = Currency.USD
    notes: Optional[str] = None; project_id: Optional[str] = None
    created_at: str = field(default_factory=_now)

    @property
    def balance(self) -> float:
        return self.total - self.amount_paid

@dataclass
class Expense:
    expense_id: str; org_id: str; amount: float; description: str
    category: str = ""; vendor: Optional[str] = None
    date: str = ""; user_id: Optional[str] = None
    project_id: Optional[str] = None; receipt_url: Optional[str] = None
    approved: bool = False; billable: bool = False
    created_at: str = field(default_factory=_now)

@dataclass
class Quote:
    quote_id: str; org_id: str; client_id: str; name: str
    status: str = "draft"; items: List[Dict] = field(default_factory=list)
    subtotal: float = 0.0; tax: float = 0.0; total: float = 0.0
    valid_until: Optional[str] = None; notes: Optional[str] = None
    created_at: str = field(default_factory=_now)


# ═══════════════════════════════════════════════════════════════
# 4. HUMAN RESOURCES — Employees, Recruitment, Performance
# ═══════════════════════════════════════════════════════════════

class EmployeeStatus(Enum):
    ACTIVE = "active"; ON_LEAVE = "on_leave"; TERMINATED = "terminated"; PROBATION = "probation"

@dataclass
class Employee:
    employee_id: str; org_id: str; name: str; email: str
    role: str = ""; department: Optional[str] = None
    status: EmployeeStatus = EmployeeStatus.ACTIVE
    salary: float = 0.0; hourly_rate: float = 0.0
    skills: List[str] = field(default_factory=list)
    start_date: Optional[str] = None; end_date: Optional[str] = None
    manager_id: Optional[str] = None; location: Optional[str] = None
    created_at: str = field(default_factory=_now)

@dataclass
class Candidate:
    candidate_id: str; org_id: str; name: str; email: str
    position: str = ""; stage: str = "applied"
    rating: float = 0.0; notes: Optional[str] = None
    resume_url: Optional[str] = None
    created_at: str = field(default_factory=_now)

@dataclass
class LeaveRequest:
    leave_id: str; org_id: str; employee_id: str
    type: str = ""; start_date: str = ""; end_date: str = ""
    days: float = 0.0; status: str = "pending"
    reason: Optional[str] = None
    created_at: str = field(default_factory=_now)


# ═══════════════════════════════════════════════════════════════
# 5. ASSET ERP — Digital & Physical Assets
# ═══════════════════════════════════════════════════════

class AssetType(Enum):
    DIGITAL = "digital"; HARDWARE = "hardware"; LICENSE = "license"
    VEHICLE = "vehicle"; FURNITURE = "furniture"

class AssetStatus(Enum):
    AVAILABLE = "available"; IN_USE = "in_use"; MAINTENANCE = "maintenance"; RETIRED = "retired"

@dataclass
class Asset:
    asset_id: str; org_id: str; name: str; asset_type: AssetType
    status: AssetStatus = AssetStatus.AVAILABLE
    serial_number: Optional[str] = None; purchase_price: float = 0.0
    current_value: float = 0.0; purchase_date: Optional[str] = None
    assigned_to: Optional[str] = None; location: Optional[str] = None
    warranty_expiry: Optional[str] = None
    maintenance_schedule: Optional[str] = None
    qr_code: Optional[str] = None; notes: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now)


# ═══════════════════════════════════════════════════════════════
# 6. PRODUCTION ERP — Pre/Post Production Workflows
# ═══════════════════════════════════════════════════════════════

@dataclass
class Production:
    production_id: str; org_id: str; name: str
    client_id: Optional[str] = None; project_id: Optional[str] = None
    status: str = "pre_production"
    budget: float = 0.0; spent: float = 0.0
    start_date: Optional[str] = None; end_date: Optional[str] = None
    director: Optional[str] = None; producer: Optional[str] = None
    crew: List[str] = field(default_factory=list)
    equipment: List[str] = field(default_factory=list)
    location: Optional[str] = None
    created_at: str = field(default_factory=_now)

@dataclass
class ShootDay:
    shoot_id: str; org_id: str; production_id: str
    date: str = ""; location: Optional[str] = None
    call_time: str = ""; wrap_time: str = ""
    crew: List[str] = field(default_factory=list)
    equipment: List[str] = field(default_factory=list)
    notes: Optional[str] = None; status: str = "scheduled"
    created_at: str = field(default_factory=_now)


# ═══════════════════════════════════════════════════════════════
# 7. PROCUREMENT — Vendors, Purchase Orders
# ═══════════════════════════════════════════════════════════════

@dataclass
class Vendor:
    vendor_id: str; org_id: str; name: str
    contact_name: Optional[str] = None; email: Optional[str] = None
    phone: Optional[str] = None; address: Optional[Address] = None
    category: Optional[str] = None; rating: float = 0.0
    notes: Optional[str] = None; tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now)

@dataclass
class PurchaseOrder:
    po_id: str; org_id: str; vendor_id: str
    number: str = ""; status: str = "draft"
    items: List[Dict] = field(default_factory=list)
    subtotal: float = 0.0; tax: float = 0.0; total: float = 0.0
    order_date: str = ""; expected_delivery: Optional[str] = None
    project_id: Optional[str] = None; notes: Optional[str] = None
    created_at: str = field(default_factory=_now)


# ═══════════════════════════════════════════════════════════════
# 8. KNOWLEDGE ERP — SOPs, Playbooks, Lessons
# ═══════════════════════════════════════════════════════════════

@dataclass
class KnowledgeItem:
    item_id: str; org_id: str; title: str; content: str
    category: str = ""  # policy, sop, playbook, guideline, lesson
    tags: List[str] = field(default_factory=list)
    author_id: Optional[str] = None
    version: str = "1.0"; parent_id: Optional[str] = None
    attachments: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)


# ═══════════════════════════════════════════════════════════════
# 9. SALES ERP — Pipeline, Scoring, Proposals
# ═══════════════════════════════════════════════════════════════

@dataclass
class SalesDeal:
    deal_id: str; org_id: str; name: str
    contact_id: Optional[str] = None; company: Optional[str] = None
    stage: str = "prospecting"; value: float = 0.0
    probability: float = 0.0; score: float = 0.0
    source: Optional[str] = None; owner_id: Optional[str] = None
    next_step: Optional[str] = None
    expected_close: Optional[str] = None
    notes: Optional[str] = None; tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now)


# ═══════════════════════════════════════════════════════════════
# 10. OPERATIONS ERP — Capacity, Utilization, Risk
# ═══════════════════════════════════════════════════════════════

@dataclass
class CapacityPlan:
    plan_id: str; org_id: str; period: str  # e.g., "2026-Q1"
    team_id: Optional[str] = None
    total_hours: float = 0.0; allocated_hours: float = 0.0
    utilization_target: float = 0.8

    @property
    def available_hours(self) -> float:
        return self.total_hours - self.allocated_hours

    @property
    def utilization_rate(self) -> float:
        return self.allocated_hours / self.total_hours if self.total_hours > 0 else 0.0

@dataclass
class RiskItem:
    risk_id: str; org_id: str; title: str
    category: str = ""; probability: float = 0.0; impact: float = 0.0
    mitigation: Optional[str] = None; owner_id: Optional[str] = None
    status: str = "open"; project_id: Optional[str] = None
    created_at: str = field(default_factory=_now)

    @property
    def risk_score(self) -> float:
        return self.probability * self.impact


# ═══════════════════════════════════════════════════════════════
# ERP MODULE REGISTRY — Central Data Store
# ═══════════════════════════════════════════════════════════════

class ERPCore:
    """
    Central ERP data store for AGENCY OS.
    Holds all module data with query capabilities.
    """

    def __init__(self):
        # CRM
        self.leads: Dict[str, Lead] = {}
        self.opportunities: Dict[str, Opportunity] = {}
        self.contacts: Dict[str, Contact] = {}
        self.meetings: Dict[str, Meeting] = {}

        # Project ERP
        self.tasks: Dict[str, Task] = {}
        self.campaigns: Dict[str, Campaign] = {}
        self.time_entries: Dict[str, TimeEntry] = {}

        # Finance ERP
        self.invoices: Dict[str, Invoice] = {}
        self.expenses: Dict[str, Expense] = {}
        self.quotes: Dict[str, Quote] = {}

        # HR
        self.employees: Dict[str, Employee] = {}
        self.candidates: Dict[str, Candidate] = {}
        self.leave_requests: Dict[str, LeaveRequest] = {}

        # Asset ERP
        self.assets: Dict[str, Asset] = {}

        # Production ERP
        self.productions: Dict[str, Production] = {}
        self.shoot_days: Dict[str, ShootDay] = {}

        # Procurement
        self.vendors: Dict[str, Vendor] = {}
        self.purchase_orders: Dict[str, PurchaseOrder] = {}

        # Knowledge ERP
        self.knowledge_items: Dict[str, KnowledgeItem] = {}

        # Sales ERP
        self.sales_deals: Dict[str, SalesDeal] = {}

        # Operations ERP
        self.capacity_plans: Dict[str, CapacityPlan] = {}
        self.risks: Dict[str, RiskItem] = {}

    # ─── Query Helpers ───

    def get_org_invoices(self, org_id: str) -> List[Invoice]:
        return [v for v in self.invoices.values() if v.org_id == org_id]

    def get_org_revenue(self, org_id: str) -> float:
        return sum(i.total for i in self.get_org_invoices(org_id) if i.status == InvoiceStatus.PAID)

    def get_org_outstanding(self, org_id: str) -> float:
        return sum(i.balance for i in self.get_org_invoices(org_id) if i.status in (InvoiceStatus.SENT, InvoiceStatus.OVERDUE))

    def get_org_tasks(self, org_id: str, status: Optional[TaskStatus] = None) -> List[Task]:
        tasks = [t for t in self.tasks.values() if t.org_id == org_id]
        if status: tasks = [t for t in tasks if t.status == status]
        return tasks

    def get_org_utilization(self, org_id: str) -> Dict:
        employees = [e for e in self.employees.values() if e.org_id == org_id and e.status == EmployeeStatus.ACTIVE]
        total_capacity = sum(160 for e in employees)  # ~160h/month per employee
        allocated = sum(te.hours for te in self.time_entries.values() if te.org_id == org_id)
        return {
            "total_employees": len(employees),
            "total_capacity_hours": total_capacity,
            "allocated_hours": allocated,
            "utilization_rate": allocated / total_capacity if total_capacity > 0 else 0.0
        }

    def get_pipeline_value(self, org_id: str) -> Dict:
        deals = [d for d in self.sales_deals.values() if d.org_id == org_id]
        total = sum(d.value for d in deals)
        weighted = sum(d.value * d.probability for d in deals)
        return {"total_value": total, "weighted_value": weighted, "deal_count": len(deals)}

    def get_profitability(self, org_id: str, project_id: str) -> Dict:
        project_tasks = [t for t in self.tasks.values() if t.project_id == project_id]
        costs = sum(t.cost for t in project_tasks)
        hours = sum(t.actual_hours for t in project_tasks)
        revenue = sum(i.total for i in self.invoices.values() if i.project_id == project_id)
        return {"revenue": revenue, "costs": costs, "profit": revenue - costs, "hours": hours}

    def summary(self) -> Dict:
        return {
            "crm": {"leads": len(self.leads), "opportunities": len(self.opportunities),
                     "contacts": len(self.contacts), "meetings": len(self.meetings)},
            "projects": {"tasks": len(self.tasks), "campaigns": len(self.campaigns),
                         "time_entries": len(self.time_entries)},
            "finance": {"invoices": len(self.invoices), "expenses": len(self.expenses),
                         "quotes": len(self.quotes)},
            "hr": {"employees": len(self.employees), "candidates": len(self.candidates),
                    "leave_requests": len(self.leave_requests)},
            "assets": len(self.assets),
            "production": {"productions": len(self.productions), "shoot_days": len(self.shoot_days)},
            "procurement": {"vendors": len(self.vendors), "purchase_orders": len(self.purchase_orders)},
            "knowledge": len(self.knowledge_items),
            "sales": len(self.sales_deals),
            "operations": {"capacity_plans": len(self.capacity_plans), "risks": len(self.risks)},
        }