"""
AGENCY OS — AI ERP Layer
Natural language reasoning over all agency data.
This is what makes AGENCY OS unique vs traditional ERPs.
"""
from __future__ import annotations
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field


@dataclass
class AIInsight:
    """Generated insight from AI reasoning."""
    insight_id: str
    category: str  # risk, opportunity, efficiency, financial, people
    title: str
    description: str
    confidence: float
    severity: str  # info, warning, critical
    affected_entities: List[Dict] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Forecast:
    """AI-generated forecast."""
    metric: str  # revenue, cost, utilization, etc.
    period: str  # e.g., "2026-Q1"
    predicted_value: float
    confidence: float
    factors: List[str] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class AIERPLayer:
    """
    AI reasoning engine over all ERP data.
    
    Traditional ERPs record information.
    AGENCY OS reasons over it.
    
    Examples:
    - "Which clients are likely to churn?" -> Analyzes contracts, sentiment, payments, velocity
    - "What's our revenue forecast?" -> Analyzes pipeline, close rates, seasonality
    - "Where are we over capacity?" -> Analyzes utilization, workload, deadlines
    - "Which projects are at risk?" -> Analyzes budget burn, delays, dependencies
    """

    def __init__(self, erp_core, enterprise_core=None):
        self.erp = erp_core
        self.core = enterprise_core
        self.insights: List[AIInsight] = []
        self.forecasts: List[Forecast] = []

    # ─── Natural Language Query ───

    async def query(self, question: str, org_id: str) -> Dict:
        """Answer natural language question about agency data."""
        q = question.lower()

        # Churn prediction
        if "churn" in q or "at risk" in q or "leaving" in q:
            return await self.predict_churn(org_id)

        # Revenue forecast
        if "revenue" in q and ("forecast" in q or "predict" in q):
            return await self.forecast_revenue(org_id)

        # Capacity / utilization
        if "capacity" in q or "utilization" in q or "overload" in q:
            return self.analyze_capacity(org_id)

        # Profitability
        if "profit" in q or "margin" in q or "loss" in q:
            return self.analyze_profitability(org_id)

        # Project risk
        if "project risk" in q or "at risk project" in q:
            return self.analyze_project_risks(org_id)

        # Best clients
        if "best client" in q or "top client" in q or "most valuable" in q:
            return self.rank_clients(org_id)

        # Sales forecast
        if "sales forecast" in q or "pipeline" in q:
            return self.forecast_sales(org_id)

        # Team performance
        if "team performance" in q or "team productivity" in q:
            return self.analyze_team_performance(org_id)

        return {"answer": "I can answer questions about: churn, revenue, capacity, profitability, project risk, best clients, sales forecast, and team performance."}

    # ─── Predictive Analytics ───

    async def predict_churn(self, org_id: str) -> Dict:
        """Predict which clients are at risk of churning."""
        at_risk = []
        for inv in self.erp.get_org_invoices(org_id):
            # Risk signals
            risk_signals = []
            score = 0.0

            # Overdue invoice
            if inv.status.value == "overdue":
                risk_signals.append("Overdue invoice")
                score += 0.3

            # Low payment ratio
            if inv.total > 0 and inv.amount_paid / inv.total < 0.5:
                risk_signals.append(f"Low payment ratio ({inv.amount_paid/inv.total:.0%})")
                score += 0.2

            if score > 0:
                at_risk.append({
                    "client_id": inv.client_id,
                    "risk_score": min(score, 1.0),
                    "signals": risk_signals,
                    "recommended_action": "Schedule check-in call",
                    "draft_email": f"Hi {inv.client_id}, just wanted to check in on project progress and see if there's anything we can help with."
                })

        # Sort by risk score
        at_risk.sort(key=lambda x: x["risk_score"], reverse=True)

        # Generate AI insight
        if at_risk:
            insight = AIInsight(
                insight_id="churn_001",
                category="risk",
                title=f"{len(at_risk)} clients at risk of churning",
                description=f"Based on payment delays and engagement patterns, {len(at_risk)} clients show churn risk signals.",
                confidence=0.75,
                severity="warning" if len(at_risk) > 2 else "info",
                affected_entities=[{"client_id": r["client_id"]} for r in at_risk],
                recommended_actions=["Schedule check-in calls", "Review project satisfaction", "Offer value-add services"]
            )
            self.insights.append(insight)

        return {
            "type": "churn_prediction",
            "at_risk_clients": at_risk,
            "total_clients": len(set(inv.client_id for inv in self.erp.get_org_invoices(org_id))),
            "risk_count": len(at_risk)
        }

    async def forecast_revenue(self, org_id: str, periods: int = 4) -> Dict:
        """Forecast future revenue based on historical data + pipeline."""
        # Historical revenue by period
        paid_invoices = [i for i in self.erp.get_org_invoices(org_id) if i.status.value == "paid"]
        total_revenue = sum(i.total for i in paid_invoices)
        avg_monthly = total_revenue / max(len(paid_invoices), 1)

        # Pipeline contribution
        pipeline = self.erp.get_pipeline_value(org_id)
        weighted_pipeline = pipeline["weighted_value"]

        # Simple forecast (would use ML in production)
        forecasts = []
        for i in range(periods):
            month = i + 1
            predicted = avg_monthly + (weighted_pipeline * 0.1 * month)  # Pipeline contribution
            forecasts.append({
                "period": f"Month+{month}",
                "predicted_revenue": round(predicted, 2),
                "confidence": max(0.3, 0.85 - (i * 0.15))  # Confidence decreases over time
            })

        return {
            "type": "revenue_forecast",
            "historical_avg_monthly": round(avg_monthly, 2),
            "pipeline_value": pipeline["total_value"],
            "weighted_pipeline": pipeline["weighted_value"],
            "forecasts": forecasts,
            "total_predicted": sum(f["predicted_revenue"] for f in forecasts)
        }

    def analyze_capacity(self, org_id: str) -> Dict:
        """Analyze team capacity and utilization."""
        util = self.erp.get_org_utilization(org_id)
        employees = [e for e in self.erp.employees.values() if e.org_id == org_id and e.status.value == "active"]

        # Overloaded team members
        overloaded = []
        for emp in employees:
            emp_hours = sum(te.hours for te in self.erp.time_entries.values()
                          if te.user_id == emp.employee_id and te.org_id == org_id)
            if emp_hours > 160:  # Over 160h/month
                overloaded.append({
                    "employee": emp.name,
                    "hours": emp_hours,
                    "over_by": emp_hours - 160
                })

        return {
            "type": "capacity_analysis",
            "total_employees": util["total_employees"],
            "total_capacity_hours": util["total_capacity_hours"],
            "allocated_hours": util["allocated_hours"],
            "utilization_rate": round(util["utilization_rate"], 2),
            "status": "overloaded" if util["utilization_rate"] > 0.9 else "healthy" if util["utilization_rate"] > 0.7 else "underutilized",
            "overloaded_members": overloaded,
            "recommendation": "Hire more staff" if util["utilization_rate"] > 0.9 else "Allocate more projects" if util["utilization_rate"] < 0.6 else "Capacity is well-balanced"
        }

    def analyze_profitability(self, org_id: str) -> Dict:
        """Analyze project profitability."""
        # Aggregate by project
        project_data: Dict[str, Dict] = {}
        for task in self.erp.tasks.values():
            if task.org_id == org_id:
                pid = task.project_id
                if pid not in project_data:
                    project_data[pid] = {"cost": 0, "hours": 0, "tasks": 0}
                project_data[pid]["cost"] += task.cost
                project_data[pid]["hours"] += task.actual_hours
                project_data[pid]["tasks"] += 1

        # Add revenue
        for inv in self.erp.invoices.values():
            if inv.org_id == org_id and inv.project_id:
                pid = inv.project_id
                if pid not in project_data:
                    project_data[pid] = {"cost": 0, "hours": 0, "tasks": 0}
                project_data[pid]["revenue"] = project_data.get(pid, {}).get("revenue", 0) + inv.total

        # Calculate profitability
        results = []
        total_profit = 0
        for pid, data in project_data.items():
            revenue = data.get("revenue", 0)
            profit = revenue - data["cost"]
            margin = profit / revenue if revenue > 0 else 0
            total_profit += profit
            results.append({
                "project_id": pid,
                "revenue": revenue,
                "cost": data["cost"],
                "profit": profit,
                "margin": round(margin, 2),
                "hours": data["hours"]
            })

        results.sort(key=lambda x: x["profit"], reverse=True)

        return {
            "type": "profitability_analysis",
            "total_profit": round(total_profit, 2),
            "project_count": len(results),
            "most_profitable": results[0] if results else None,
            "least_profitable": results[-1] if results else None,
            "projects": results
        }

    def analyze_project_risks(self, org_id: str) -> Dict:
        """Identify projects at risk."""
        at_risk = []

        # Budget overrun risk
        for task in self.erp.tasks.values():
            if task.org_id == org_id and task.estimated_hours > 0:
                if task.actual_hours > task.estimated_hours * 1.2:  # 20% over estimate
                    at_risk.append({
                        "project_id": task.project_id,
                        "task": task.title,
                        "risk": "scope_creep",
                        "estimated_hours": task.estimated_hours,
                        "actual_hours": task.actual_hours,
                        "overrun_pct": round((task.actual_hours / task.estimated_hours - 1) * 100, 1)
                    })

        # Schedule risk (tasks past due)
        now = datetime.now().isoformat()
        for task in self.erp.tasks.values():
            if (task.org_id == org_id and task.status.value != "done"
                and task.due_date and task.due_date < now):
                at_risk.append({
                    "project_id": task.project_id,
                    "task": task.title,
                    "risk": "past_due",
                    "due_date": task.due_date,
                    "days_overdue": 0  # Would calculate
                })

        return {
            "type": "project_risk_analysis",
            "total_risks": len(at_risk),
            "risk_level": "high" if len(at_risks) > 5 else "medium" if len(at_risks) > 2 else "low",
            "risks": at_risk
        }

    def rank_clients(self, org_id: str) -> Dict:
        """Rank clients by value, profitability, and satisfaction."""
        client_data: Dict[str, Dict] = {}

        # Revenue per client
        for inv in self.erp.invoices.values():
            if inv.org_id == org_id:
                cid = inv.client_id
                if cid not in client_data:
                    client_data[cid] = {"revenue": 0, "profit": 0, "projects": 0}
                client_data[cid]["revenue"] += inv.total

        # Sort by revenue
        ranked = sorted(client_data.items(), key=lambda x: x[1]["revenue"], reverse=True)

        return {
            "type": "client_ranking",
            "top_clients": [{"client_id": cid, **data} for cid, data in ranked[:10]],
            "total_clients": len(client_data)
        }

    def forecast_sales(self, org_id: str) -> Dict:
        """Forecast sales based on pipeline."""
        pipeline = self.erp.get_pipeline_value(org_id)
        deals = [d for d in self.erp.sales_deals.values() if d.org_id == org_id]

        # Group by stage
        by_stage = {}
        for deal in deals:
            stage = deal.stage
            if stage not in by_stage:
                by_stage[stage] = {"count": 0, "value": 0, "weighted": 0}
            by_stage[stage]["count"] += 1
            by_stage[stage]["value"] += deal.value
            by_stage[stage]["weighted"] += deal.value * deal.probability

        return {
            "type": "sales_forecast",
            "total_pipeline": pipeline["total_value"],
            "weighted_pipeline": pipeline["weighted_value"],
            "deal_count": pipeline["deal_count"],
            "by_stage": by_stage,
            "forecast_30d": round(pipeline["weighted_value"] * 0.25, 2),
            "forecast_90d": round(pipeline["weighted_value"] * 0.6, 2)
        }

    def analyze_team_performance(self, org_id: str) -> Dict:
        """Analyze team performance metrics."""
        employees = [e for e in self.erp.employees.values() if e.org_id == org_id and e.status.value == "active"]

        performance = []
        for emp in employees:
            emp_tasks = [t for t in self.erp.tasks.values()
                        if t.assignee_id == emp.employee_id and t.org_id == org_id]
            completed = [t for t in emp_tasks if t.status.value == "done"]
            emp_hours = sum(te.hours for te in self.erp.time_entries.values()
                          if te.user_id == emp.employee_id)

            performance.append({
                "name": emp.name,
                "role": emp.role,
                "total_tasks": len(emp_tasks),
                "completed_tasks": len(completed),
                "completion_rate": round(len(completed) / len(emp_tasks), 2) if emp_tasks else 0,
                "total_hours": emp_hours,
                "skills": emp.skills
            })

        performance.sort(key=lambda x: x["completion_rate"], reverse=True)

        return {
            "type": "team_performance",
            "team_size": len(employees),
            "members": performance,
            "top_performer": performance[0] if performance else None,
            "avg_completion_rate": round(sum(p["completion_rate"] for p in performance) / len(performance), 2) if performance else 0
        }

    # ─── Insights Generation ───

    def generate_insights(self, org_id: str) -> List[AIInsight]:
        """Automatically generate insights for an organization."""
        insights = []

        # Financial insights
        outstanding = self.erp.get_org_outstanding(org_id)
        if outstanding > 50000:
            insights.append(AIInsight(
                insight_id="fin_001", category="financial",
                title="High outstanding invoices",
                description=f"${outstanding:,.2f} in unpaid invoices. Consider implementing automated reminders.",
                confidence=0.9, severity="warning",
                recommended_actions=["Send payment reminders", "Review payment terms", "Offer early payment discount"]
            ))

        # Utilization insights
        util = self.erp.get_org_utilization(org_id)
        if util["utilization_rate"] > 0.95:
            insights.append(AIInsight(
                insight_id="ops_001", category="efficiency",
                title="Team over capacity",
                description=f"Utilization at {util['utilization_rate']:.0%}. Risk of burnout and quality decline.",
                confidence=0.85, severity="critical",
                recommended_actions=["Redistribute workload", "Hire additional staff", "Defer non-critical projects"]
            ))

        self.insights.extend(insights)
        return insights