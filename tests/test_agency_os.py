# AGENCY OS — Test Suite
# Comprehensive tests for all platform components

import pytest
import asyncio
import uuid
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

# ─── Fixtures ───

@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def aurora_core():
    """Create AuroraCore instance for testing."""
    from aurora.core import AuroraCore
    core = AuroraCore()
    yield core
    await core.shutdown()

@pytest.fixture
def enterprise_core():
    """Create EnterpriseCore instance for testing."""
    from aurora.enterprise.core import EnterpriseCore
    core = EnterpriseCore(persist_dir="./test_data")
    yield core
    # Cleanup
    import shutil
    if Path("./test_data").exists():
        shutil.rmtree("./test_data")

@pytest.fixture
def erp_core():
    """Create ERPCore instance for testing."""
    from aurora.enterprise.erp import ERPCore
    return ERPCore()

@pytest.fixture
def sample_user(enterprise_core):
    """Create a sample user."""
    return enterprise_core.create_user("test@agency.com", "Test User", "password123")

@pytest.fixture
def sample_org(enterprise_core, sample_user):
    """Create a sample organization."""
    return enterprise_core.create_org("Test Agency", sample_user.user_id, "professional")

@pytest.fixture
def sample_project(enterprise_core, sample_org, sample_user):
    """Create a sample project."""
    return enterprise_core.create_project(
        sample_org.org_id, "Test Project", owner_id=sample_user.user_id
    )


# ═══════════════════════════════════════════════════════════
# CORE PLATFORM TESTS
# ═══════════════════════════════════════════════════════════

class TestAuroraCore:
    """Tests for AuroraCore orchestration engine."""

    def test_initialization(self):
        from aurora.core import AuroraCore
        core = AuroraCore()
        assert core.session_id is not None
        assert core.started_at is not None
        assert core.observation_active is False

    @pytest.mark.asyncio
    async def test_full_lifecycle(self):
        from aurora.core import AuroraCore
        core = AuroraCore()
        await core.initialize()
        assert core._memory is not None
        assert len(core._intelligence_engines) == 6
        await core.shutdown()

    @pytest.mark.asyncio
    async def test_create_project(self, aurora_core):
        project = await aurora_core.create_project(
            name="Test Campaign",
            description="Test description",
            goals=["awareness"]
        )
        assert project.project_id is not None
        assert project.name == "Test Campaign"
        assert project.status == "planning"

    def test_media_type_detection(self, aurora_core):
        from aurora.core import MediaType
        assert aurora_core._detect_media_type(Path("test.png")) == MediaType.IMAGE
        assert aurora_core._detect_media_type(Path("test.mp4")) == MediaType.VIDEO
        assert aurora_core._detect_media_type(Path("test.mp3")) == MediaType.AUDIO
        assert aurora_core._detect_media_type(Path("test.pdf")) == MediaType.DOCUMENT
        assert aurora_core._detect_media_type(Path("test.py")) == MediaType.CODE
        assert aurora_core._detect_media_type(Path("test.fig")) == MediaType.DESIGN
        assert aurora_core._detect_media_type(Path("test.blend")) == MediaType.MODEL_3D

    def test_quality_score_calculation(self, aurora_core):
        from aurora.core import CreativeInsight, IntelligenceDomain
        insights = [
            CreativeInsight(IntelligenceDomain.VISUAL, "test", "finding", 0.9),
            CreativeInsight(IntelligenceDomain.DESIGN, "test", "finding", 0.7),
        ]
        score = aurora_core._calculate_quality_score(insights)
        assert 0 <= score <= 10

    def test_summary_generation(self, aurora_core):
        from aurora.core import CreativeInsight, IntelligenceDomain
        insights = [
            CreativeInsight(IntelligenceDomain.VISUAL, "composition", "Strong composition", 0.9),
        ]
        summary = aurora_core._generate_summary(insights)
        assert "Visual" in summary
        assert "Strong composition" in summary


# ═══════════════════════════════════════════════════════════
# ENTERPRISE CORE TESTS
# ═══════════════════════════════════════════════════════════

class TestEnterpriseCore:
    """Tests for multi-tenant enterprise core."""

    def test_create_user(self, enterprise_core):
        user = enterprise_core.create_user("user@test.com", "Test User", "pass123")
        assert user.user_id is not None
        assert user.email == "user@test.com"
        assert user.status == "active"

    def test_duplicate_user(self, enterprise_core, sample_user):
        with pytest.raises(ValueError):
            enterprise_core.create_user("test@agency.com", "Another", "pass123")

    def test_authenticate(self, enterprise_core, sample_user):
        token = enterprise_core.authenticate("test@agency.com", "password123")
        assert token is not None
        assert len(token) > 20

    def test_authenticate_wrong_password(self, enterprise_core, sample_user):
        token = enterprise_core.authenticate("test@agency.com", "wrongpass")
        assert token is None

    def test_create_organization(self, enterprise_core, sample_user):
        org = enterprise_core.create_org("Test Co", sample_user.user_id, "starter")
        assert org.org_id is not None
        assert org.slug == "test-co"
        assert org.billing_plan == "starter"
        assert org.member_count == 1

    def test_organization_limits(self, enterprise_core, sample_user):
        org = enterprise_core.create_org("Test Co", sample_user.user_id, "starter")
        assert org.max_projects == 10
        assert org.can_create_project() is True

    def test_create_team(self, enterprise_core, sample_org):
        team = enterprise_core.create_team(sample_org.org_id, "Design Team")
        assert team.team_id is not None
        assert team.name == "Design Team"

    def test_create_workspace(self, enterprise_core, sample_org):
        ws = enterprise_core.create_workspace(sample_org.org_id, "Main Workspace")
        assert ws.workspace_id is not None
        assert ws.type == "creative"

    def test_create_project(self, enterprise_core, sample_org, sample_user):
        project = enterprise_core.create_project(
            sample_org.org_id, "Test Project", owner_id=sample_user.user_id
        )
        assert project.project_id is not None
        assert project.status == "planning"

    def test_create_client(self, enterprise_core, sample_org):
        client = enterprise_core.create_client(sample_org.org_id, "Nike", industry="Sports")
        assert client.client_id is not None
        assert client.name == "Nike"

    def test_rbac_permissions(self, enterprise_core, sample_user):
        from aurora.enterprise.core import Role, Permission
        sample_user.add_to_org("org1", Role.DESIGNER)
        assert sample_user.has_permission("org1", Permission.ASSET_CREATE) is True
        assert sample_user.has_permission("org1", Permission.ASSET_DELETE) is False
        assert sample_user.has_permission("org1", Permission.ADMIN_FULL) is False

    def test_role_permissions(self):
        from aurora.enterprise.core import Role, Permission
        owner_perms = Role.permissions(Role.OWNER)
        assert Permission.ADMIN_FULL in owner_perms
        assert len(owner_perms) == len(Permission)

        designer_perms = Role.permissions(Role.DESIGNER)
        assert Permission.ASSET_CREATE in designer_perms
        assert Permission.ADMIN_FULL not in designer_perms

    def test_audit_logging(self, enterprise_core, sample_user):
        enterprise_core._audit("test_action", sample_user.user_id, {"key": "value"})
        assert len(enterprise_core._audit_log) > 0
        assert enterprise_core._audit_log[-1]["action"] == "test_action"

    def test_persistence(self, enterprise_core, sample_user, sample_org):
        enterprise_core.save()
        assert Path("./agency_os_data/core.json").exists()

        # Load into new instance
        from aurora.enterprise.core import EnterpriseCore
        new_core = EnterpriseCore()
        new_core.load()
        assert len(new_core.users) == len(enterprise_core.users)
        assert len(new_core.organizations) == len(enterprise_core.organizations)

    def test_status(self, enterprise_core, sample_user, sample_org):
        status = enterprise_core.status()
        assert status["users"] >= 1
        assert status["orgs"] >= 1


# ═══════════════════════════════════════════════════════════
# ERP MODULE TESTS
# ═══════════════════════════════════════════════════════════

class TestERPCore:
    """Tests for all 10 ERP modules."""

    # ─── CRM ───

    def test_create_lead(self, erp_core):
        from aurora.enterprise.erp import Lead, LeadStatus
        lead = Lead(lead_id="l1", org_id="org1", name="Test Lead", email="lead@test.com",
                    value=50000, status=LeadStatus.NEW)
        erp_core.leads[lead.lead_id] = lead
        assert len(erp_core.leads) == 1

    def test_create_opportunity(self, erp_core):
        from aurora.enterprise.erp import Opportunity
        opp = Opportunity(lead_id="opp1", org_id="org1", name="Big Deal", value=100000, probability=0.5)
        erp_core.opportunities[opp.opp_id] = opp
        assert len(erp_core.opportunities) == 1

    # ─── Finance ───

    def test_create_invoice(self, erp_core):
        from aurora.enterprise.erp import Invoice, InvoiceStatus, Currency
        inv = Invoice(invoice_id="inv1", org_id="org1", client_id="c1", number="INV-001",
                      total=25000, amount_paid=10000, status=InvoiceStatus.SENT)
        erp_core.invoices[inv.invoice_id] = inv
        assert inv.balance == 15000

    def test_revenue_calculation(self, erp_core):
        from aurora.enterprise.erp import Invoice, InvoiceStatus
        erp_core.invoices["i1"] = Invoice(invoice_id="i1", org_id="org1", client_id="c1",
                                           total=50000, status=InvoiceStatus.PAID)
        erp_core.invoices["i2"] = Invoice(invoice_id="i2", org_id="org1", client_id="c2",
                                           total=30000, status=InvoiceStatus.SENT)
        assert erp_core.get_org_revenue("org1") == 50000
        assert erp_core.get_org_outstanding("org1") == 30000

    # ─── Projects ───

    def test_create_task(self, erp_core):
        from aurora.enterprise.erp import Task, TaskStatus
        task = Task(invoice_id="t1", org_id="org1", project_id="p1", title="Design",
                     status=TaskStatus.IN_PROGRESS, actual_hours=10, cost=1000)
        erp_core.tasks[task.task_id] = task
        assert len(erp_core.tasks) == 1

    def test_task_filtering(self, erp_core):
        from aurora.enterprise.erp import Task, TaskStatus
        erp_core.tasks["t1"] = Task(invoice_id="t1", org_id="org1", project_id="p1",
                                      title="Task 1", status=TaskStatus.TODO)
        erp_core.tasks["t2"] = Task(invoice_id="t2", org_id="org1", project_id="p1",
                                      title="Task 2", status=TaskStatus.DONE)
        todo_tasks = erp_core.get_org_tasks("org1", status=TaskStatus.TODO)
        assert len(todo_tasks) == 1

    # ─── HR ───

    def test_create_employee(self, erp_core):
        from aurora.enterprise.erp import Employee, EmployeeStatus
        emp = Employee(employee_id="e1", org_id="org1", name="John", email="john@agency.com",
                        role="Designer", salary=85000, status=EmployeeStatus.ACTIVE)
        erp_core.employees[emp.employee_id] = emp
        assert len(erp_core.employees) == 1

    def test_utilization(self, erp_core):
        from aurora.enterprise.erp import Employee, EmployeeStatus
        erp_core.employees["e1"] = Employee(employee_id="e1", org_id="org1", name="John",
                                             email="john@agency.com", status=EmployeeStatus.ACTIVE)
        util = erp_core.get_org_utilization("org1")
        assert "utilization_rate" in util
        assert "total_employees" in util

    # ─── Sales ───

    def test_pipeline_value(self, erp_core):
        from aurora.enterprise.erp import SalesDeal
        erp_core.sales_deals["d1"] = SalesDeal(deal_id="d1", org_id="org1", name="Deal A",
                                                 value=50000, probability=0.6)
        erp_core.sales_deals["d2"] = SalesDeal(deal_id="d2", org_id="org1", name="Deal B",
                                                 value=80000, probability=0.8)
        pipeline = erp_core.get_pipeline_value("org1")
        assert pipeline["total_value"] == 130000
        assert pipeline["weighted_value"] == 50000*0.6 + 80000*0.8

    # ─── Assets ───

    def test_create_asset(self, erp_core):
        from aurora.enterprise.erp import Asset, AssetType, AssetStatus
        asset = Asset(invoice_id="a1", org_id="org1", name="Canon C70",
                       asset_type=AssetType.HARDWARE, purchase_price=5500,
                       current_value=4200, status=AssetStatus.AVAILABLE)
        erp_core.assets[asset.asset_id] = asset
        assert len(erp_core.assets) == 1

    # ─── Summary ───

    def test_erp_summary(self, erp_core):
        summary = erp_core.summary()
        assert "crm" in summary
        assert "projects" in summary
        assert "finance" in summary
        assert "hr" in summary
        assert "sales" in summary


# ═══════════════════════════════════════════════════════════
# AI ERP LAYER TESTS
# ═══════════════════════════════════════════════════════════

class TestAIERP:
    """Tests for AI reasoning over ERP data."""

    @pytest.fixture
    def ai_erp(self, erp_core):
        from aurora.enterprise.ai_erp import AIERPLayer
        return AIERPLayer(erp_core)

    @pytest.mark.asyncio
    async def test_churn_prediction(self, ai_erp):
        from aurora.enterprise.erp import Invoice, InvoiceStatus
        ai_erp.erp.invoices["i1"] = Invoice(invoice_id="i1", org_id="org1", client_id="c1",
                                              total=40000, status=InvoiceStatus.OVERDUE, amount_paid=0)
        result = await ai_erp.predict_churn("org1")
        assert result["type"] == "churn_prediction"
        assert result["risk_count"] >= 1

    @pytest.mark.asyncio
    async def test_revenue_forecast(self, ai_erp):
        result = await ai_erp.forecast_revenue("org1")
        assert result["type"] == "revenue_forecast"
        assert "forecasts" in result

    def test_capacity_analysis(self, ai_erp):
        result = ai_erp.analyze_capacity("org1")
        assert result["type"] == "capacity_analysis"
        assert "utilization_rate" in result

    def test_profitability(self, ai_erp):
        result = ai_erp.analyze_profitability("org1")
        assert result["type"] == "profitability_analysis"
        assert "total_profit" in result

    def test_sales_forecast(self, ai_erp):
        result = ai_erp.forecast_sales("org1")
        assert result["type"] == "sales_forecast"
        assert "total_pipeline" in result

    def test_team_performance(self, ai_erp):
        result = ai_erp.analyze_team_performance("org1")
        assert result["type"] == "team_performance"
        assert "team_size" in result

    def test_generate_insights(self, ai_erp):
        insights = ai_erp.generate_insights("org1")
        assert isinstance(insights, list)


# ═══════════════════════════════════════════════════════════
# INTELLIGENCE ENGINE TESTS
# ═══════════════════════════════════════════════════════════

class TestIntelligenceEngines:
    """Tests for all 6 intelligence engines."""

    @pytest.fixture
    def sample_interpretation(self):
        from aurora.core import MediaInterpretation, MediaType, CreativeInsight, IntelligenceDomain
        return MediaInterpretation(
            media_id="test_001",
            media_type=MediaType.IMAGE,
            source_path="test.png",
            timestamp=datetime.now().isoformat(),
            insights=[
                CreativeInsight(IntelligenceDomain.VISUAL, "composition",
                                "Strong rule-of-thirds composition", 0.85),
            ],
            summary="Test image with strong composition",
            quality_score=8.0,
            metadata_graph={"format": "png", "size": 1024},
            tags=["image", "test"]
        )

    @pytest.mark.asyncio
    async def test_narrative_engine(self, sample_interpretation):
        from aurora.intelligence.narrative import NarrativeIntelligence
        engine = NarrativeIntelligence()
        insights = await engine.analyze(sample_interpretation)
        assert isinstance(insights, list)

    @pytest.mark.asyncio
    async def test_visual_engine(self, sample_interpretation):
        from aurora.intelligence.visual import VisualIntelligence
        engine = VisualIntelligence()
        insights = await engine.analyze(sample_interpretation)
        assert isinstance(insights, list)

    @pytest.mark.asyncio
    async def test_symbolism_engine(self, sample_interpretation):
        from aurora.intelligence.symbolism import SymbolismIntelligence
        engine = SymbolismIntelligence()
        insights = await engine.analyze(sample_interpretation)
        assert isinstance(insights, list)

    @pytest.mark.asyncio
    async def test_design_engine(self, sample_interpretation):
        from aurora.intelligence.design import DesignIntelligence
        engine = DesignIntelligence()
        insights = await engine.analyze(sample_interpretation)
        assert isinstance(insights, list)

    @pytest.mark.asyncio
    async def test_marketing_engine(self, sample_interpretation):
        from aurora.intelligence.marketing import MarketingIntelligence
        engine = MarketingIntelligence()
        insights = await engine.analyze(sample_interpretation)
        assert isinstance(insights, list)

    @pytest.mark.asyncio
    async def test_psychological_engine(self, sample_interpretation):
        from aurora.intelligence.psychological import PsychologicalIntelligence
        engine = PsychologicalIntelligence()
        insights = await engine.analyze(sample_interpretation)
        assert isinstance(insights, list)

    @pytest.mark.asyncio
    async def test_critique_generation(self, sample_interpretation):
        from aurora.intelligence.visual import VisualIntelligence
        engine = VisualIntelligence()
        critiques = await engine.critique(sample_interpretation)
        assert isinstance(critiques, list)
        assert len(critiques) > 0

    @pytest.mark.asyncio
    async def test_improvement_generation(self, sample_interpretation):
        from aurora.intelligence.visual import VisualIntelligence
        engine = VisualIntelligence()
        improvements = await engine.improve(sample_interpretation)
        assert isinstance(improvements, list)
        assert len(improvements) > 0


# ═══════════════════════════════════════════════════════════
# INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════

class TestIntegrations:
    """Tests for external integration connectors."""

    @pytest.mark.asyncio
    async def test_figma_integration(self):
        from aurora.integrations.connectors import FigmaIntegration
        figma = FigmaIntegration({"access_token": "test_token"})
        assert figma.name == "figma"
        assert figma.is_connected is False

    @pytest.mark.asyncio
    async def test_github_integration(self):
        from aurora.integrations.connectors import GitHubIntegration
        gh = GitHubIntegration({"token": "test_token"})
        assert gh.name == "github"

    @pytest.mark.asyncio
    async def test_slack_integration(self):
        from aurora.integrations.connectors import SlackIntegration
        slack = SlackIntegration({"bot_token": "xoxb-test"})
        assert slack.name == "slack"

    @pytest.mark.asyncio
    async def test_integration_manager(self):
        from aurora.integrations.connectors import IntegrationManager
        manager = IntegrationManager()
        assert manager.list_integrations() == []


# ═══════════════════════════════════════════════════════════
# WORKFLOW ENGINE TESTS
# ═══════════════════════════════════════════════════════════

class TestWorkflowEngine:
    """Tests for workflow builder engine."""

    @pytest.fixture
    def engine(self):
        from aurora.workflows.engine import WorkflowEngine
        return WorkflowEngine()

    def test_create_workflow(self, engine):
        wf = engine.create_workflow("org1", "Test Workflow")
        assert wf.workflow_id is not None
        assert wf.name == "Test Workflow"
        assert wf.status.value == "draft"

    def test_add_node(self, engine):
        wf = engine.create_workflow("org1", "Test")
        from aurora.workflows.engine import NodeType
        node = engine.add_node(wf.workflow_id, NodeType.ACTION, "Test Action")
        assert node is not None
        assert node.name == "Test Action"
        assert len(wf.nodes) == 1

    def test_connect_nodes(self, engine):
        wf = engine.create_workflow("org1", "Test")
        from aurora.workflows.engine import NodeType
        n1 = engine.add_node(wf.workflow_id, NodeType.TRIGGER, "Start")
        n2 = engine.add_node(wf.workflow_id, NodeType.ACTION, "Action")
        result = engine.connect_nodes(wf.workflow_id, n1.node_id, n2.node_id)
        assert result is True
        assert n2.node_id in n1.connections

    def test_list_workflows(self, engine):
        engine.create_workflow("org1", "WF1")
        engine.create_workflow("org1", "WF2")
        engine.create_workflow("org2", "WF3")
        wfs = engine.list_workflows("org1")
        assert len(wfs) == 2

    def test_delete_workflow(self, engine):
        wf = engine.create_workflow("org1", "Test")
        result = engine.delete_workflow(wf.workflow_id)
        assert result is True
        assert wf.workflow_id not in engine.workflows


# ═══════════════════════════════════════════════════════════
# EXPORT PIPELINE TESTS
# ═══════════════════════════════════════════════════════════

class TestExportPipeline:
    """Tests for export and publishing pipeline."""

    @pytest.fixture
    def pipeline(self, tmp_path):
        from aurora.export.pipeline import ExportPipeline
        return ExportPipeline(output_dir=str(tmp_path))

    def test_export_json(self, pipeline):
        from aurora.export.pipeline import ExportFormat
        data = {"test": "data", "nested": {"key": "value"}}
        path = pipeline.export(data, ExportFormat.JSON, "test")
        assert path.exists()
        assert path.suffix == ".json"

    def test_export_markdown(self, pipeline):
        from aurora.export.pipeline import ExportFormat
        data = {"title": "Test", "content": "Hello world"}
        path = pipeline.export(data, ExportFormat.MARKDOWN, "test")
        assert path.exists()
        assert path.suffix == ".md"

    def test_export_html(self, pipeline):
        from aurora.export.pipeline import ExportFormat
        data = {"title": "Test", "content": "Hello world"}
        path = pipeline.export(data, ExportFormat.HTML, "test")
        assert path.exists()
        assert path.suffix == ".html"


# ═══════════════════════════════════════════════════════════
# PROMPT ENGINEERING TESTS
# ═══════════════════════════════════════════════════════════

class TestPromptEngineering:
    """Tests for prompt engineering system."""

    @pytest.fixture
    def prompt_system(self, tmp_path):
        from aurora.agents.prompts import PromptEngineeringSystem
        return PromptEngineeringSystem(persist_dir=str(tmp_path))

    def test_create_prompt(self, prompt_system):
        from aurora.agents.prompts import PromptType
        prompt = prompt_system.create_prompt(
            "org1", "Test Prompt", "Analyze {image}", PromptType.ANALYSIS,
            variables=[{"name": "image", "description": "Image to analyze"}]
        )
        assert prompt.prompt_id is not None
        assert prompt.name == "Test Prompt"

    def test_render_prompt(self, prompt_system):
        from aurora.agents.prompts import PromptType
        prompt = prompt_system.create_prompt(
            "org1", "Test", "Analyze {image} for {style}", PromptType.ANALYSIS,
            variables=[{"name": "image", "description": "Image"}, {"name": "style", "description": "Style"}]
        )
        rendered = prompt_system.render_prompt(prompt.prompt_id, {"image": "photo.jpg", "style": "modern"})
        assert "photo.jpg" in rendered
        assert "modern" in rendered

    def test_list_prompts(self, prompt_system):
        from aurora.agents.prompts import PromptType
        prompt_system.create_prompt("org1", "P1", "Content", PromptType.ANALYSIS)
        prompt_system.create_prompt("org1", "P2", "Content", PromptType.GENERATION)
        prompts = prompt_system.list_prompts("org1")
        assert len(prompts) == 2

    def test_duplicate_prompt(self, prompt_system):
        from aurora.agents.prompts import PromptType
        original = prompt_system.create_prompt("org1", "Original", "Content", PromptType.ANALYSIS)
        dup = prompt_system.duplicate_prompt(original.prompt_id, "Copy")
        assert dup.prompt_id != original.prompt_id
        assert dup.name == "Copy"
        assert dup.parent_id == original.prompt_id

    def test_evaluate_prompt(self, prompt_system):
        from aurora.agents.prompts import PromptType
        prompt = prompt_system.create_prompt("org1", "Test", "Content", PromptType.ANALYSIS)
        eval_result = prompt_system.evaluate_prompt(
            prompt.prompt_id, "test case", "output", "expected output"
        )
        assert eval_result.evaluation_id is not None
        assert 0 <= eval_result.score <= 1

    def test_optimize_prompt(self, prompt_system):
        from aurora.agents.prompts import PromptType
        prompt = prompt_system.create_prompt("org1", "Test", "Analyze this image please", PromptType.ANALYSIS)
        result = prompt_system.optimize_prompt(prompt.prompt_id, "all")
        assert "suggestions" in result
        assert len(result["suggestions"]) > 0


# ═══════════════════════════════════════════════════════════
# INDUSTRY PACKS TESTS
# ═══════════════════════════════════════════════════════════

class TestIndustryPacks:
    """Tests for industry pack registry."""

    @pytest.fixture
    def registry(self):
        from aurora.integrations.industry_packs import IndustryPackRegistry
        return IndustryPackRegistry()

    def test_list_packs(self, registry):
        packs = registry.list_packs()
        assert len(packs) == 15

    def test_get_pack(self, registry):
        pack = registry.get_pack("advertising")
        assert pack is not None
        assert pack.name == "Advertising Agency"

    def test_pack_has_workflows(self, registry):
        pack = registry.get_pack("advertising")
        assert len(pack.workflows) > 0

    def test_pack_has_kpis(self, registry):
        pack = registry.get_pack("advertising")
        assert len(pack.kpis) > 0

    def test_enable_pack(self, registry):
        result = registry.enable_pack("org1", "advertising")
        assert result["status"] == "enabled"
        assert result["pack_id"] == "advertising"

    def test_all_packs_valid(self, registry):
        for pack in registry.list_packs():
            assert pack.pack_id is not None
            assert pack.name is not None
            assert pack.industry is not None
            assert len(pack.kpis) > 0


# ═══════════════════════════════════════════════════════════
# API SERVER TESTS
# ═══════════════════════════════════════════════════════════

class TestAPIServer:
    """Tests for FastAPI server endpoints."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from aurora.api.server import app
        return TestClient(app)

    def test_health_check(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_status(self, client):
        response = client.get("/api/v1/status")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "components" in data
        assert "stats" in data

    def test_404(self, client):
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404

    def test_mcp_servers(self, client):
        response = client.get("/api/v1/mcp/servers")
        assert response.status_code == 200

    def test_batch_missing_dir(self, client):
        response = client.post("/api/v1/batch", params={"directory": "/nonexistent"})
        assert response.status_code == 404


# ═══════════════════════════════════════════════════════════
# END-TO-END TESTS
# ═══════════════════════════════════════════════════════════

class TestEndToEnd:
    """End-to-end integration tests."""

    @pytest.mark.asyncio
    async def test_full_interpretation_pipeline(self, tmp_path):
        """Test complete interpretation pipeline from file to insight."""
        from aurora.core import AuroraCore, MediaType, CreativeInsight, IntelligenceDomain
        from aurora.interpreters.universal import UniversalInterpreter

        # Create interpreter
        interpreter = UniversalInterpreter(MediaType.IMAGE)

        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        # Interpret
        interpretation = await interpreter.interpret(test_file)

        assert interpretation.media_id is not None
        assert interpretation.media_type == MediaType.IMAGE
        assert len(interpretation.tags) > 0

    def test_full_erp_workflow(self, erp_core):
        """Test complete ERP workflow from lead to invoice."""
        from aurora.enterprise.erp import (
            Lead, LeadStatus, Opportunity, Invoice, InvoiceStatus,
            Task, TaskStatus, Employee, EmployeeStatus, SalesDeal
        )

        # Create lead
        lead = Lead(lead_id="l1", org_id="org1", name="Nike", email="brand@nike.com", value=50000)
        erp_core.leads[lead.lead_id] = lead

        # Convert to opportunity
        opp = Opportunity(lead_id="opp1", org_id="org1", name="Nike Campaign", value=75000, probability=0.6)
        erp_core.opportunities[opp.opp_id] = opp

        # Create project task
        task = Task(invoice_id="t1", org_id="org1", project_id="p1", title="Design", status=TaskStatus.TODO)
        erp_core.tasks[task.task_id] = task

        # Create invoice
        inv = Invoice(invoice_id="inv1", org_id="org1", client_id="nike", number="INV-001",
                      total=25000, status=InvoiceStatus.SENT)
        erp_core.invoices[inv.invoice_id] = inv

        # Verify pipeline
        assert len(erp_core.leads) == 1
        assert len(erp_core.opportunities) == 1
        assert len(erp_core.tasks) == 1
        assert len(erp_core.invoices) == 1
        assert erp_core.get_org_outstanding("org1") == 25000

    def test_full_enterprise_workflow(self, enterprise_core):
        """Test complete enterprise workflow from user to project."""
        # Create user
        user = enterprise_core.create_user("test@agency.com", "Test User", "pass123")

        # Create org
        org = enterprise_core.create_org("Test Agency", user.user_id, "professional")

        # Create team
        team = enterprise_core.create_team(org.org_id, "Design", user.user_id)

        # Create client
        client = enterprise_core.create_client(org.org_id, "Nike", industry="Sports")

        # Create project
        project = enterprise_core.create_project(
            org.org_id, "Q4 Campaign", client_id=client.client_id,
            team_id=team.team_id, owner_id=user.user_id
        )

        # Verify
        assert len(enterprise_core.users) == 1
        assert len(enterprise_core.organizations) == 1
        assert len(enterprise_core.teams) == 1
        assert len(enterprise_core.clients) == 1
        assert len(enterprise_core.projects) == 1
        assert org.project_count == 1