"""
AGENCY OS — AI Operations (CRP Layer 2)

The cheapest module to build and the fastest to sell: nobody currently
knows what their AI actually costs per client, per campaign, per agent.

Design stance: this is an accounting ledger, not a dashboard. Every model
call is an immutable, append-only record attributable to an org, a client,
a project, and a creative object. If you cannot bill it, you cannot manage it.

Costs are computed from an explicit, versioned rate card rather than
scraped from provider invoices, so unit economics stay reproducible.
Rates ship as editable placeholders — verify against your provider's
current pricing before invoicing a client off these numbers.
"""
from __future__ import annotations

import json
import uuid
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _id(prefix: str = "ai_") -> str:
    return f"{prefix}{uuid.uuid4().hex[:12]}"


def _now() -> str:
    return datetime.now().isoformat()


# ═══════════════════════════════════════════════════════════════
# Rate card
# ═══════════════════════════════════════════════════════════════

@dataclass
class ModelRate:
    """
    Cost per unit for a model. USD.

    input_per_1k / output_per_1k for token models.
    per_call for image/video/audio endpoints.
    gpu_per_hour for self-hosted inference.
    """
    model: str
    provider: str
    input_per_1k: float = 0.0
    output_per_1k: float = 0.0
    cached_input_per_1k: float = 0.0
    per_call: float = 0.0
    gpu_per_hour: float = 0.0
    effective_from: str = field(default_factory=_now)
    note: str = ""


class RateCard:
    """Versioned pricing. Placeholder values — override at deploy time."""

    DEFAULTS: List[ModelRate] = [
        ModelRate("gpt-4o", "openai", 0.0025, 0.01, 0.00125, note="placeholder"),
        ModelRate("gpt-4o-mini", "openai", 0.00015, 0.0006, 0.000075, note="placeholder"),
        ModelRate("claude-sonnet", "anthropic", 0.003, 0.015, 0.0003, note="placeholder"),
        ModelRate("dall-e-3", "openai", per_call=0.04, note="placeholder, 1024x1024 std"),
        ModelRate("whisper-1", "openai", per_call=0.006, note="placeholder, per minute"),
        ModelRate("local-sdxl", "self", gpu_per_hour=1.20, note="placeholder, A10G spot"),
    ]

    def __init__(self, rates: Optional[List[ModelRate]] = None):
        self.rates: Dict[str, ModelRate] = {r.model: r for r in (rates or self.DEFAULTS)}
        self.unknown_models: set = set()

    def set_rate(self, rate: ModelRate) -> None:
        self.rates[rate.model] = rate

    def get(self, model: str) -> Optional[ModelRate]:
        rate = self.rates.get(model)
        if rate is None:
            self.unknown_models.add(model)
        return rate

    def price(
        self,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cached_tokens: int = 0,
        calls: int = 1,
        gpu_seconds: float = 0.0,
    ) -> Tuple[float, bool]:
        """
        Returns (usd, priced) — `priced=False` means the model was unknown and
        the cost is 0.0 by convention. Never silently guess a price.
        """
        rate = self.get(model)
        if rate is None:
            return 0.0, False
        usd = (
            (input_tokens / 1000.0) * rate.input_per_1k
            + (output_tokens / 1000.0) * rate.output_per_1k
            + (cached_tokens / 1000.0) * rate.cached_input_per_1k
            + calls * rate.per_call
            + (gpu_seconds / 3600.0) * rate.gpu_per_hour
        )
        return round(usd, 6), True


# ═══════════════════════════════════════════════════════════════
# The ledger record
# ═══════════════════════════════════════════════════════════════

class CallKind(Enum):
    COMPLETION = "completion"
    EMBEDDING = "embedding"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    TOOL = "tool"
    RETRIEVAL = "retrieval"


class Outcome(Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    REFUSED = "refused"
    BLOCKED_BY_POLICY = "blocked_by_policy"


@dataclass
class AICall:
    """
    One immutable inference record.

    `attributable` is the whole point: an unattributed call is overhead,
    an attributed call is cost of goods sold.
    """
    call_id: str
    org_id: str
    model: str
    kind: CallKind = CallKind.COMPLETION
    provider: str = ""

    # Attribution chain
    agent_id: Optional[str] = None
    user_id: Optional[str] = None
    client_id: Optional[str] = None
    project_id: Optional[str] = None
    campaign_id: Optional[str] = None
    object_id: Optional[str] = None      # -> creative.CreativeObject
    stage: Optional[str] = None

    # Usage
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0
    calls: int = 1
    gpu_seconds: float = 0.0
    latency_ms: float = 0.0

    # Economics
    cost_usd: float = 0.0
    priced: bool = True
    billable: bool = False

    # Quality / governance
    outcome: Outcome = Outcome.SUCCESS
    error: Optional[str] = None
    tools_called: List[str] = field(default_factory=list)
    human_reviewed: bool = False
    human_overridden: bool = False
    accepted: Optional[bool] = None       # did a human keep the output
    rating: Optional[float] = None        # 0..1, human or eval-assigned
    flagged: List[str] = field(default_factory=list)  # policy/eval flags

    prompt_hash: Optional[str] = None     # hash, not the prompt — PII discipline
    trace_id: Optional[str] = None
    at: str = field(default_factory=_now)

    @property
    def attributable(self) -> bool:
        return bool(self.client_id or self.project_id or self.campaign_id or self.object_id)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["kind"] = self.kind.value
        d["outcome"] = self.outcome.value
        return d


@dataclass
class Budget:
    """A spend ceiling with an enforcement mode."""
    budget_id: str
    org_id: str
    period: str                     # "2026-08" or "2026-Q3"
    limit_usd: float
    scope: str = "org"              # org | client | project | agent
    scope_id: Optional[str] = None
    warn_at: float = 0.8
    hard_stop: bool = False
    created_at: str = field(default_factory=_now)


class BudgetExceeded(Exception):
    """Raised when a hard-stop budget would be breached."""


# ═══════════════════════════════════════════════════════════════
# Ledger
# ═══════════════════════════════════════════════════════════════

class AIOpsLedger:
    """
    Append-only ledger of AI consumption with rollups.

    No ERP tracks this today, which is the arbitrage: agencies are currently
    eating model cost as undifferentiated overhead instead of passing it
    through as a line item.
    """

    def __init__(self, persist_dir: str = "./agency_os_data", rate_card: Optional[RateCard] = None):
        self.persist_dir = Path(persist_dir)
        self.rates = rate_card or RateCard()
        self.calls: List[AICall] = []
        self.budgets: Dict[str, Budget] = {}
        self._by_id: Dict[str, AICall] = {}

    # ─── Recording ───

    def record(
        self,
        org_id: str,
        model: str,
        kind: CallKind = CallKind.COMPLETION,
        enforce_budget: bool = True,
        **kwargs,
    ) -> AICall:
        """Price and append a call. Raises BudgetExceeded on hard-stop breach."""
        cost, priced = self.rates.price(
            model,
            input_tokens=kwargs.get("input_tokens", 0),
            output_tokens=kwargs.get("output_tokens", 0),
            cached_tokens=kwargs.get("cached_tokens", 0),
            calls=kwargs.get("calls", 1),
            gpu_seconds=kwargs.get("gpu_seconds", 0.0),
        )
        rate = self.rates.rates.get(model)
        call = AICall(
            call_id=_id(),
            org_id=org_id,
            model=model,
            kind=kind,
            provider=rate.provider if rate else "unknown",
            cost_usd=cost,
            priced=priced,
            **kwargs,
        )

        if enforce_budget:
            self._check_budgets(call)

        self.calls.append(call)
        self._by_id[call.call_id] = call
        return call

    def _check_budgets(self, call: AICall) -> None:
        period = call.at[:7]
        for b in self.budgets.values():
            if b.org_id != call.org_id or b.period != period:
                continue
            if b.scope != "org":
                scope_value = getattr(call, f"{b.scope}_id", None)
                if scope_value != b.scope_id:
                    continue
            spent = self._spend_for_budget(b)
            if b.hard_stop and spent + call.cost_usd > b.limit_usd:
                raise BudgetExceeded(
                    f"budget {b.budget_id} ({b.scope}:{b.scope_id or b.org_id}) "
                    f"would exceed ${b.limit_usd:.2f} — spent ${spent:.2f}, "
                    f"call ${call.cost_usd:.4f}"
                )

    def _spend_for_budget(self, b: Budget) -> float:
        total = 0.0
        for c in self.calls:
            if c.org_id != b.org_id or not c.at.startswith(b.period):
                continue
            if b.scope != "org" and getattr(c, f"{b.scope}_id", None) != b.scope_id:
                continue
            total += c.cost_usd
        return total

    def set_budget(self, org_id: str, period: str, limit_usd: float, **kwargs) -> Budget:
        b = Budget(budget_id=_id("bg_"), org_id=org_id, period=period,
                   limit_usd=limit_usd, **kwargs)
        self.budgets[b.budget_id] = b
        return b

    def annotate(
        self,
        call_id: str,
        accepted: Optional[bool] = None,
        rating: Optional[float] = None,
        human_overridden: Optional[bool] = None,
        flag: Optional[str] = None,
    ) -> AICall:
        """
        Post-hoc human feedback. This is the label source that makes any
        later predictive claim honest instead of vibes.
        """
        call = self._by_id[call_id]
        if accepted is not None:
            call.accepted = accepted
            call.human_reviewed = True
        if rating is not None:
            call.rating = rating
            call.human_reviewed = True
        if human_overridden is not None:
            call.human_overridden = human_overridden
            call.human_reviewed = True
        if flag:
            call.flagged.append(flag)
        return call

    # ─── Rollups ───

    def _scope(self, org_id: str, period: Optional[str] = None, **filters) -> List[AICall]:
        out = [c for c in self.calls if c.org_id == org_id]
        if period:
            out = [c for c in out if c.at.startswith(period)]
        for k, v in filters.items():
            if v is not None:
                out = [c for c in out if getattr(c, k, None) == v]
        return out

    def spend(self, org_id: str, period: Optional[str] = None, **filters) -> Dict[str, Any]:
        calls = self._scope(org_id, period, **filters)
        total = sum(c.cost_usd for c in calls)
        unpriced = [c for c in calls if not c.priced]
        return {
            "period": period or "all",
            "calls": len(calls),
            "total_usd": round(total, 4),
            "billable_usd": round(sum(c.cost_usd for c in calls if c.billable), 4),
            "unbillable_usd": round(sum(c.cost_usd for c in calls if not c.billable), 4),
            "tokens_in": sum(c.input_tokens for c in calls),
            "tokens_out": sum(c.output_tokens for c in calls),
            "gpu_hours": round(sum(c.gpu_seconds for c in calls) / 3600.0, 3),
            "unpriced_calls": len(unpriced),
            "unpriced_models": sorted({c.model for c in unpriced}),
        }

    def cost_per_client(self, org_id: str, period: Optional[str] = None) -> Dict[str, float]:
        agg: Dict[str, float] = defaultdict(float)
        for c in self._scope(org_id, period):
            agg[c.client_id or "_unattributed"] += c.cost_usd
        return {k: round(v, 4) for k, v in sorted(agg.items(), key=lambda x: -x[1])}

    def cost_per_campaign(self, org_id: str, period: Optional[str] = None) -> Dict[str, float]:
        agg: Dict[str, float] = defaultdict(float)
        for c in self._scope(org_id, period):
            agg[c.campaign_id or "_unattributed"] += c.cost_usd
        return {k: round(v, 4) for k, v in sorted(agg.items(), key=lambda x: -x[1])}

    def cost_per_model(self, org_id: str, period: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        agg: Dict[str, Dict[str, Any]] = {}
        for c in self._scope(org_id, period):
            e = agg.setdefault(c.model, {"calls": 0, "usd": 0.0, "tokens": 0, "errors": 0})
            e["calls"] += 1
            e["usd"] += c.cost_usd
            e["tokens"] += c.total_tokens
            if c.outcome is not Outcome.SUCCESS:
                e["errors"] += 1
        for e in agg.values():
            e["usd"] = round(e["usd"], 4)
        return dict(sorted(agg.items(), key=lambda x: -x[1]["usd"]))

    def attribution_gap(self, org_id: str, period: Optional[str] = None) -> Dict[str, Any]:
        """
        Share of spend that cannot be traced to a client. High values mean
        the ledger is decorative — fix instrumentation before trusting margins.
        """
        calls = self._scope(org_id, period)
        total = sum(c.cost_usd for c in calls) or 1e-9
        orphan = sum(c.cost_usd for c in calls if not c.attributable)
        return {
            "total_usd": round(total, 4),
            "unattributed_usd": round(orphan, 4),
            "unattributed_share": round(orphan / total, 4),
            "unattributed_calls": sum(1 for c in calls if not c.attributable),
        }

    def agent_scorecard(self, org_id: str, period: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Per-agent economics and reliability.

        `acceptance_rate` is computed only over reviewed calls, and
        `reviewed` is reported alongside it — a 100% acceptance rate on
        3 reviewed calls out of 4000 is noise, and the shape says so.
        """
        agg: Dict[str, Dict[str, Any]] = {}
        for c in self._scope(org_id, period):
            key = c.agent_id or "_unassigned"
            e = agg.setdefault(key, {
                "calls": 0, "usd": 0.0, "errors": 0, "reviewed": 0,
                "accepted": 0, "overridden": 0, "flags": 0,
                "latency_ms_total": 0.0, "ratings": [],
            })
            e["calls"] += 1
            e["usd"] += c.cost_usd
            e["latency_ms_total"] += c.latency_ms
            if c.outcome is not Outcome.SUCCESS:
                e["errors"] += 1
            if c.human_reviewed:
                e["reviewed"] += 1
            if c.accepted:
                e["accepted"] += 1
            if c.human_overridden:
                e["overridden"] += 1
            e["flags"] += len(c.flagged)
            if c.rating is not None:
                e["ratings"].append(c.rating)

        out: Dict[str, Dict[str, Any]] = {}
        for key, e in agg.items():
            reviewed = e["reviewed"]
            ratings = e["ratings"]
            out[key] = {
                "calls": e["calls"],
                "usd": round(e["usd"], 4),
                "usd_per_call": round(e["usd"] / e["calls"], 6) if e["calls"] else 0.0,
                "error_rate": round(e["errors"] / e["calls"], 4) if e["calls"] else 0.0,
                "avg_latency_ms": round(e["latency_ms_total"] / e["calls"], 1) if e["calls"] else 0.0,
                "reviewed": reviewed,
                "review_coverage": round(reviewed / e["calls"], 4) if e["calls"] else 0.0,
                "acceptance_rate": round(e["accepted"] / reviewed, 4) if reviewed else None,
                "override_rate": round(e["overridden"] / reviewed, 4) if reviewed else None,
                "avg_rating": round(sum(ratings) / len(ratings), 4) if ratings else None,
                "flags": e["flags"],
            }
        return dict(sorted(out.items(), key=lambda x: -x[1]["usd"]))

    def budget_status(self, org_id: str) -> List[Dict[str, Any]]:
        rows = []
        for b in self.budgets.values():
            if b.org_id != org_id:
                continue
            spent = self._spend_for_budget(b)
            pct = spent / b.limit_usd if b.limit_usd else 0.0
            rows.append({
                "budget_id": b.budget_id,
                "scope": f"{b.scope}:{b.scope_id or org_id}",
                "period": b.period,
                "limit_usd": b.limit_usd,
                "spent_usd": round(spent, 4),
                "utilization": round(pct, 4),
                "state": "over" if pct >= 1 else ("warning" if pct >= b.warn_at else "ok"),
                "hard_stop": b.hard_stop,
            })
        return sorted(rows, key=lambda r: -r["utilization"])

    def margin(
        self,
        org_id: str,
        project_id: str,
        revenue_usd: float,
        labor_cost_usd: float = 0.0,
    ) -> Dict[str, Any]:
        """AI cost as a real COGS line, not overhead."""
        ai_cost = sum(c.cost_usd for c in self._scope(org_id, project_id=project_id))
        cogs = ai_cost + labor_cost_usd
        profit = revenue_usd - cogs
        return {
            "project_id": project_id,
            "revenue_usd": round(revenue_usd, 2),
            "ai_cost_usd": round(ai_cost, 4),
            "labor_cost_usd": round(labor_cost_usd, 2),
            "gross_profit_usd": round(profit, 2),
            "gross_margin": round(profit / revenue_usd, 4) if revenue_usd else None,
            "ai_share_of_cogs": round(ai_cost / cogs, 4) if cogs else None,
        }

    # ─── Persistence ───

    def save(self, filename: str = "aiops_ledger.json") -> Path:
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        path = self.persist_dir / filename
        payload = {
            "calls": [c.to_dict() for c in self.calls],
            "budgets": {k: asdict(v) for k, v in self.budgets.items()},
            "rates": {k: asdict(v) for k, v in self.rates.rates.items()},
            "saved_at": _now(),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)
        return path

    def load(self, filename: str = "aiops_ledger.json") -> None:
        path = self.persist_dir / filename
        if not path.exists():
            return
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        for r in data.get("rates", {}).values():
            self.rates.set_rate(ModelRate(**r))
        for b in data.get("budgets", {}).values():
            self.budgets[b["budget_id"]] = Budget(**b)
        for c in data.get("calls", []):
            c["kind"] = CallKind(c["kind"])
            c["outcome"] = Outcome(c["outcome"])
            call = AICall(**c)
            self.calls.append(call)
            self._by_id[call.call_id] = call
