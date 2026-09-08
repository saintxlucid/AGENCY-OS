"""
AGENCY OS — Comprehensive End-to-End Demo
Exercises every part of the platform with realistic data.
Run: python demos/full_demo.py
"""
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))


def header(text):
    print(f"\n{'═' * 70}")
    print(f"  {text}")
    print(f"{'═' * 70}")


def subheader(text):
    print(f"\n── {text} {'─' * (60 - len(text))}")


def ok(text):
    print(f"  ✅ {text}")


def info(text):
    print(f"  ℹ️  {text}")


async def main():
    header("AGENCY OS — Full Platform Demo")
    print("  AI-Native Agency ERP + Creative Intelligence Platform")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # ══════════════════════════════════════════════════════════
    # 1. ENTERPRISE SETUP
    # ══════════════════════════════════════════════════════════
    header("1. Enterprise Setup")

    from aurora.enterprise.core import EnterpriseCore, Role, Permission

    core = EnterpriseCore(persist_dir="./demo_data")

    # Create team
    admin = core.create_user("jane@neondesign.com", "Jane Creative", "secure123")
    designer = core.create_user("john@neondesign.com", "John Designer", "secure123")
    developer = core.create_user("mia@neondesign.com", "Mia Developer", "secure123")
    ok(f"Created 3 users: Jane (Owner), John (Designer), Mia (Developer)")

    # Create organization
    org = core.create_org("Neon Design Co.", admin.user_id, "professional",
                           "Award-winning creative agency specializing in brand identity")
    ok(f"Organization: {org.name} ({org.slug}) — Plan: {org.billing_plan}")

    # Add members
    core.invite_member(org.org_id, "john@neondesign.com", Role.DESIGNER, admin.user_id)
    core.invite_member(org.org_id, "mia@neondesign.com", Role.DEVELOPER, admin.user_id)
    org.member_count = 3
    ok(f"Added John as Designer, Mia as Developer")

    # Verify RBAC
    admin_user = core.users[admin.user_id]
    designer_user = core.users[designer.user_id]
    assert admin_user.has_permission(org.org_id, Permission.ADMIN_FULL)
    assert designer_user.has_permission(org.org_id, Permission.ASSET_CREATE)
    assert not designer_user.has_permission(org.org_id, Permission.ADMIN_FULL)
    ok("RBAC verified: Owner has full access, Designer has limited access")

    # Create team
    design_team = core.create_team(org.org_id, "Design Team", admin.user_id)
    core.create_team(org.org_id, "Development Team", admin.user_id)
    ok(f"Created teams: Design Team, Development Team")

    # Create workspaces
    core.create_workspace(org.org_id, "Brand Studio", "creative")
    core.create_workspace(org.org_id, "Dev Lab", "creative")
    ok("Created workspaces: Brand Studio, Dev Lab")

    # Create clients
    nike = core.create_client(org.org_id, "Nike", industry="Sports",
                               description="Global sportswear brand", target_audience="Athletes 18-35")
    adidas = core.create_client(org.org_id, "Adidas", industry="Sports",
                                 description="Performance sportswear", target_audience="Runners 20-40")
    apple = core.create_client(org.org_id, "Apple", industry="Technology",
                                description="Consumer electronics giant", target_audience="Tech-savvy 25-50")
    ok(f"Created clients: Nike, Adidas, Apple")

    # Create projects
    proj1 = core.create_project(org.org_id, "Nike Q4 Campaign",
                                 description="Holiday campaign for new shoe line",
                                 client_id=nike.client_id, team_id=design_team.team_id,
                                 brief="Create a holiday campaign that captures the spirit of athletic achievement",
                                 owner_id=admin.user_id, due_date="2026-12-15")
    proj2 = core.create_project(org.org_id, "Adidas Rebrand",
                                 description="Complete visual identity overhaul",
                                 client_id=adidas.client_id, team_id=design_team.team_id,
                                 brief="Refresh the brand while maintaining heritage",
                                 owner_id=designer.user_id, due_date="2026-11-30")
    proj3 = core.create_project(org.org_id, "Apple WWDC Site",
                                 description="Microsite for developer conference",
                                 client_id=apple.client_id,
                                 brief="Design a stunning microsite for WWDC 2026",
                                 owner_id=developer.user_id, due_date="2027-06-01")
    ok(f"Created 3 projects: Nike Q4, Adidas Rebrand, Apple WWDC")

    # ══════════════════════════════════════════════════════════
    # 2. ERP MODULES
    # ══════════════════════════════════════════════════════════
    header("2. ERP Modules")

    from aurora.enterprise.erp import (
        ERPCore, Lead, LeadStatus, SalesDeal, Invoice, InvoiceStatus,
        Task, TaskStatus, Employee, EmployeeStatus, TimeEntry
    )

    erp = core.erp_core if hasattr(core, 'erp_core') else ERPCore()
    core.erp_core = erp

    # CRM
    subheader("CRM")
    lead1 = Lead(lead_id="lead_001", org_id=org.org_id, name="Puma Marketing",
                 email="brand@puma.com", company="Puma", value=75000, source="website",
                 status=LeadStatus.QUALIFIED)
    erp.leads[lead1.lead_id] = lead1
    deal1 = SalesDeal(deal_id="deal_001", org_id=org.org_id, name="Nike Expansion",
                      company="Nike", stage="negotiation", value=150000, probability=0.7, score=85)
    deal2 = SalesDeal(deal_id="deal_002", org_id=org.org_id, name="Adidas Digital",
                      company="Adidas", stage="proposal", value=95000, probability=0.5, score=72)
    deal3 = SalesDeal(deal_id="deal_003", org_id=org.org_id, name="Apple Vision",
                      company="Apple", stage="discovery", value=250000, probability=0.2, score=60)
    erp.sales_deals[deal1.deal_id] = deal1
    erp.sales_deals[deal2.deal_id] = deal2
    erp.sales_deals[deal3.deal_id] = deal3
    ok("Created 3 sales deals worth $495,000 total pipeline")

    # Finance
    subheader("Finance")
    inv1 = Invoice(invoice_id="inv_001", org_id=org.org_id, client_id=nike.client_id,
                   number="INV-2026-001", status=InvoiceStatus.SENT,
                   total=25000, amount_paid=10000, due_date="2026-09-15")
    inv2 = Invoice(invoice_id="inv_002", org_id=org.org_id, client_id=adidas.client_id,
                   number="INV-2026-002", status=InvoiceStatus.OVERDUE,
                   total=40000, amount_paid=0, due_date="2026-07-01")
    inv3 = Invoice(invoice_id="inv_003", org_id=org.org_id, client_id=apple.client_id,
                   number="INV-2026-003", status=InvoiceStatus.PAID,
                   total=60000, amount_paid=60000, due_date="2026-08-01")
    erp.invoices[inv1.invoice_id] = inv1
    erp.invoices[inv2.invoice_id] = inv2
    erp.invoices[inv3.invoice_id] = inv3
    ok(f"Revenue=${erp.get_org_revenue(org.org_id):,.0f}, Outstanding=${erp.get_org_outstanding(org.org_id):,.0f}")

    # Projects/Tasks
    subheader("Projects")
    tasks = [
        Task("task_001", org.org_id, proj1.project_id, "Moodboard", TaskStatus.DONE, actual_hours=8, cost=800),
        Task("task_002", org.org_id, proj1.project_id, "Concept Design", TaskStatus.IN_PROGRESS, actual_hours=16, cost=1600),
        Task("task_003", org.org_id, proj1.project_id, "Photo Shoot", TaskStatus.TODO, estimated_hours=24, budget=5000),
        Task("task_004", org.org_id, proj1.project_id, "Video Edit", TaskStatus.TODO, estimated_hours=20, budget=4000),
        Task("task_005", org.org_id, proj2.project_id, "Brand Audit", TaskStatus.DONE, actual_hours=12, cost=1200),
        Task("task_006", org.org_id, proj2.project_id, "Logo Concepts", TaskStatus.IN_PROGRESS, actual_hours=20, cost=2000, estimated_hours=16),
    ]
    for t in tasks:
        erp.tasks[t.task_id] = t
    ok(f"Created {len(tasks)} tasks across 3 projects")

    # HR
    subheader("HR")
    emp1 = Employee("emp_001", org.org_id, "John Designer", "john@neondesign.com",
                    "Senior Designer", EmployeeStatus.ACTIVE, salary=85000, hourly_rate=85,
                    skills=["Photoshop", "Illustrator", "Figma", "Branding"])
    emp2 = Employee("emp_002", org.org_id, "Mia Developer", "mia@neondesign.com",
                    "Full-Stack Developer", EmployeeStatus.ACTIVE, salary=95000, hourly_rate=95,
                    skills=["React", "TypeScript", "Node.js", "Three.js"])
    emp3 = Employee("emp_003", org.org_id, "Sam Researcher", "sam@neondesign.com",
                    "UX Researcher", EmployeeStatus.ACTIVE, salary=75000, hourly_rate=75,
                    skills=["User Research", "Analytics", "A/B Testing"])
    for e in [emp1, emp2, emp3]:
        erp.employees[e.employee_id] = e
    te1 = TimeEntry("te_001", org.org_id, emp1.employee_id, proj1.project_id, "2026-08-01", 40, True, 85)
    te2 = TimeEntry("te_002", org.org_id, emp1.employee_id, proj1.project_id, "2026-08-02", 35, True, 85)
    te3 = TimeEntry("te_003", org.org_id, emp2.employee_id, proj3.project_id, "2026-08-01", 45, True, 95)
    for te in [te1, te2, te3]:
        erp.time_entries[te.entry_id] = te
    ok(f"Created 3 employees, 3 time entries")

    # Save enterprise data
    core.save()
    ok("Enterprise data saved to disk")

    # ══════════════════════════════════════════════════════════
    # 3. AI ERP REASONING
    # ══════════════════════════════════════════════════════════
    header("3. AI ERP Reasoning")

    from aurora.enterprise.ai_erp import AIERPLayer

    ai = AIERPLayer(erp, core)

    # Churn prediction
    subheader("Churn Prediction")
    churn = await ai.predict_churn(org.org_id)
    info(f"At-risk clients: {churn['risk_count']} of {churn['total_clients']}")
    for client in churn.get('at_risk_clients', []):
        info(f"  • {client['client_id']}: risk={client['risk_score']:.0%}")

    # Revenue forecast
    subheader("Revenue Forecast")
    forecast = await ai.forecast_revenue(org.org_id, periods=4)
    info(f"Historical avg monthly: ${forecast['historical_avg_monthly']:,.0f}")
    info(f"Pipeline value: ${forecast['pipeline_value']:,.0f}")
    for f in forecast['forecasts']:
        info(f"  • {f['period']}: ${f['predicted_revenue']:,.0f} (conf: {f['confidence']:.0%})")

    # Capacity analysis
    subheader("Capacity Analysis")
    capacity = ai.analyze_capacity(org.org_id)
    info(f"Team size: {capacity['total_employees']}")
    info(f"Utilization rate: {capacity['utilization_rate']:.0%}")
    info(f"Status: {capacity['status']}")

    # Profitability
    subheader("Profitability Analysis")
    profit = ai.analyze_profitability(org.org_id)
    info(f"Total profit: ${profit['total_profit']:,.0f}")

    # Sales forecast
    subheader("Sales Forecast")
    sales = ai.forecast_sales(org.org_id)
    info(f"Total pipeline: ${sales['total_pipeline']:,.0f}")
    info(f"30-day forecast: ${sales['forecast_30d']:,.0f}")

    # Auto insights
    subheader("Auto-Generated Insights")
    insights = ai.generate_insights(org.org_id)
    for insight in insights:
        info(f"  • [{insight.severity.upper()}] {insight.title}")

    # ══════════════════════════════════════════════════════════
    # 4. INTELLIGENCE ENGINES
    # ══════════════════════════════════════════════════════════
    header("4. Intelligence Engines")

    from aurora.intelligence.narrative import NarrativeIntelligence
    from aurora.intelligence.visual import VisualIntelligence
    from aurora.intelligence.symbolism import SymbolismIntelligence
    from aurora.intelligence.design import DesignIntelligence
    from aurora.intelligence.marketing import MarketingIntelligence
    from aurora.intelligence.psychological import PsychologicalIntelligence
    from aurora.core import MediaInterpretation, MediaType, CreativeInsight, IntelligenceDomain

    sample_interp = MediaInterpretation(
        media_id="demo_001",
        media_type=MediaType.IMAGE,
        source_path="demo/nike_holiday_ad.png",
        timestamp=datetime.now().isoformat(),
        insights=[
            CreativeInsight(IntelligenceDomain.VISUAL, "composition",
                            "Strong rule-of-thirds composition with dynamic diagonal lines", 0.92),
            CreativeInsight(IntelligenceDomain.VISUAL, "color_theory",
                            "Warm amber and gold palette evoking holiday warmth", 0.88),
            CreativeInsight(IntelligenceDomain.MARKETING, "cta",
                            "Clear value proposition with prominent CTA", 0.85),
        ],
        summary="Nike holiday campaign featuring dynamic athlete imagery",
        quality_score=8.7,
        metadata_graph={"brand": "Nike", "campaign": "Q4 Holiday"},
        tags=["nike", "campaign", "holiday", "digital"]
    )

    engines = {
        "Narrative": NarrativeIntelligence(),
        "Visual": VisualIntelligence(),
        "Symbolism": SymbolismIntelligence(),
        "Design": DesignIntelligence(),
        "Marketing": MarketingIntelligence(),
        "Psychological": PsychologicalIntelligence(),
    }

    total_insights = 0
    for name, engine in engines.items():
        subheader(f"{name} Engine")
        result = await engine.analyze(sample_interp)
        total_insights += len(result)
        ok(f"Generated {len(result)} insights")
        for i in result[:2]:
            info(f"  • [{i.category}] {i.finding[:50]}...")

    ok(f"Total insights across all engines: {total_insights}")

    # ══════════════════════════════════════════════════════════
    # 5. WORKFLOW ENGINE
    # ══════════════════════════════════════════════════════════
    header("5. Workflow Engine")

    from aurora.workflows.engine import WorkflowEngine, NodeType

    wf_engine = WorkflowEngine()
    wf = wf_engine.create_workflow(org.org_id, "Campaign Production",
                                    "End-to-end campaign production pipeline")
    n1 = wf_engine.add_node(wf.workflow_id, NodeType.AGENT, "Market Research",
                             {"agent": "researcher"})
    n2 = wf_engine.add_node(wf.workflow_id, NodeType.AGENT, "Creative Brief",
                             {"agent": "creative_director"})
    n3 = wf_engine.add_node(wf.workflow_id, NodeType.AGENT, "Concept Design",
                             {"agent": "art_director"})
    n4 = wf_engine.add_node(wf.workflow_id, NodeType.APPROVAL, "Creative Review")
    n5 = wf_engine.add_node(wf.workflow_id, NodeType.AGENT, "Produce Assets",
                             {"agent": "designer"})
    n6 = wf_engine.add_node(wf.workflow_id, NodeType.APPROVAL, "Client Approval")
    n7 = wf_engine.add_node(wf.workflow_id, NodeType.ACTION, "Publish")

    wf_engine.connect_nodes(wf.workflow_id, n1.node_id, n2.node_id)
    wf_engine.connect_nodes(wf.workflow_id, n2.node_id, n3.node_id)
    wf_engine.connect_nodes(wf.workflow_id, n3.node_id, n4.node_id)
    wf_engine.connect_nodes(wf.workflow_id, n4.node_id, n5.node_id)
    wf_engine.connect_nodes(wf.workflow_id, n5.node_id, n6.node_id)
    wf_engine.connect_nodes(wf.workflow_id, n6.node_id, n7.node_id)
    ok(f"Created workflow '{wf.name}' with {len(wf.nodes)} nodes")

    # ══════════════════════════════════════════════════════════
    # 6. PROMPT ENGINEERING
    # ══════════════════════════════════════════════════════════
    header("6. Prompt Engineering")

    from aurora.agents.prompts import PromptEngineeringSystem, PromptType

    ps = PromptEngineeringSystem(persist_dir="./demo_data/prompts")
    p1 = ps.create_prompt(org.org_id, "Brand Analysis",
                          "Analyze the brand identity of {brand} in {industry}.",
                          PromptType.ANALYSIS,
                          variables=[{"name": "brand", "description": "Brand name"},
                                     {"name": "industry", "description": "Industry"}])
    p2 = ps.create_prompt(org.org_id, "Campaign Brief",
                          "Create a creative brief for {client}. Goals: {goals}.",
                          PromptType.GENERATION,
                          variables=[{"name": "client", "description": "Client"},
                                     {"name": "goals", "description": "Goals"}])
    ok(f"Created {len(ps.prompts)} prompt templates")

    rendered = ps.render_prompt(p1.prompt_id, {"brand": "Nike", "industry": "Sports"})
    ok(f"Rendered: '{rendered[:50]}...'")

    chain = ps.create_chain(org.org_id, "Campaign Pipeline", "Full campaign chain")
    ps.add_chain_step(chain.chain_id, p1.prompt_id, {"brand": "Nike", "industry": "Sports"})
    ps.add_chain_step(chain.chain_id, p2.prompt_id, {"client": "Nike", "goals": "awareness"})
    ok(f"Created chain '{chain.name}' with {len(chain.steps)} steps")

    eval_result = ps.evaluate_prompt(p1.prompt_id, "Test", "output here", "expected output")
    ok(f"Evaluation score: {eval_result.score:.2f}")

    opt = ps.optimize_prompt(p1.prompt_id, "all")
    ok(f"Generated {len(opt['suggestions'])} optimization suggestions")

    # ══════════════════════════════════════════════════════════
    # 7. EXPORT PIPELINE
    # ══════════════════════════════════════════════════════════
    header("7. Export Pipeline")

    from aurora.export.pipeline import ExportPipeline, ExportFormat

    exporter = ExportPipeline(output_dir="./demo_output")

    data = {
        "media_id": sample_interp.media_id,
        "summary": sample_interp.summary,
        "quality_score": sample_interp.quality_score,
        "tags": sample_interp.tags,
        "insights": [{"domain": i.domain.value, "category": i.category, "finding": i.finding, "confidence": i.confidence} for i in sample_interp.insights]
    }
    json_path = exporter.export(data, ExportFormat.JSON, "demo_report")
    ok(f"Exported JSON: {json_path}")

    md_path = exporter.export(data, ExportFormat.MARKDOWN, "demo_report")
    ok(f"Exported Markdown: {md_path}")

    html_path = exporter.export(data, ExportFormat.HTML, "demo_report")
    ok(f"Exported HTML: {html_path}")

    # ══════════════════════════════════════════════════════════
    # 8. INDUSTRY PACKS
    # ══════════════════════════════════════════════════════════
    header("8. Industry Packs")

    from aurora.integrations.industry_packs import IndustryPackRegistry

    registry = IndustryPackRegistry()
    packs = registry.list_packs()
    ok(f"Available industry packs: {len(packs)}")
    for pack in packs[:5]:
        info(f"  • {pack.name} ({pack.industry}) — {len(pack.kpis)} KPIs")

    # Enable a pack
    result = registry.enable_pack(org.org_id, "advertising")
    ok(f"Enabled '{result['pack_id']}' pack: {result['workflows']} workflows")

    # ══════════════════════════════════════════════════════════
    # SUMMARY
    # ══════════════════════════════════════════════════════════
    header("Demo Complete — Summary")
    info(f"Organization: {org.name} ({org.billing_plan})")
    info(f"Users: {len(core.users)} | Teams: {len(core.teams)} | Clients: {len(core.clients)}")
    info(f"Projects: {len(core.projects)} | Workspaces: {len(core.workspaces)}")
    info(f"ERP: {len(erp.invoices)} invoices, {len(erp.tasks)} tasks, {len(erp.employees)} employees")
    info(f"AI Insights: {len(insights)} auto-generated")
    info(f"Intelligence Engines: 6 active, {total_insights} total insights")
    info(f"Industry Packs: {len(packs)} available")
    info(f"Data saved to: ./demo_data/")
    info(f"Reports exported to: ./demo_output/")
    print(f"\n{'═' * 70}")
    print("  AGENCY OS Demo Complete!")
    print(f"{'═' * 70}\n")


if __name__ == "__main__":
    asyncio.run(main())