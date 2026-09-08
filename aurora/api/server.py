"""
AGENCY OS — FastAPI API Server
Central nervous system connecting all platform capabilities.
"""
from __future__ import annotations
import os, json, uuid, time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


# ─── Pydantic Models ───

class InterpretRequest(BaseModel):
    media_type: Optional[str] = None
    critique: bool = True
    improve: bool = True

class InterpretResponse(BaseModel):
    media_id: str
    media_type: str
    summary: str
    quality_score: float
    tags: List[str]
    insights: List[Dict]
    timestamp: str

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Project name")
    description: Optional[str] = Field(None, max_length=2000, description="Project description")
    client_id: Optional[str] = Field(None, description="Client ID")
    team_id: Optional[str] = Field(None, description="Team ID")
    brief: Optional[str] = Field(None, max_length=10000, description="Project brief")
    goals: List[str] = Field(default_factory=list, max_items=50, description="Project goals")
    due_date: Optional[str] = Field(None, description="Due date (ISO format)")

class ProjectResponse(BaseModel):
    project_id: str
    name: str
    status: str
    created_at: str

class QueryRequest(BaseModel):
    question: str
    domain: Optional[str] = None
    limit: int = 10

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict] = []
    confidence: float = 0.0

class ObserveRequest(BaseModel):
    targets: List[str]
    interval: float = 5.0
    auto_analyze: bool = True
    auto_critique: bool = True

class ObserveResponse(BaseModel):
    observation_id: str
    status: str
    targets: List[str]

class AIQueryRequest(BaseModel):
    question: str

class StatusResponse(BaseModel):
    version: str
    status: str
    uptime_seconds: float
    components: Dict[str, Any]
    stats: Dict[str, Any]

class ERPInvoiceCreate(BaseModel):
    client_id: str
    items: List[Dict]
    tax: float = 0.0
    due_date: Optional[str] = None
    notes: Optional[str] = None

class ERPTaskCreate(BaseModel):
    project_id: str
    title: str
    description: Optional[str] = None
    assignee_id: Optional[str] = None
    priority: str = "medium"
    estimated_hours: float = 0.0
    due_date: Optional[str] = None

class WebhookPayload(BaseModel):
    event: str
    data: Dict[str, Any]
    timestamp: Optional[str] = None
    signature: Optional[str] = None


# ─── App State ───

class AppState:
    """Shared application state."""
    def __init__(self):
        self.start_time = time.time()
        self.aurora = None
        self.enterprise_core = None
        self.erp_core = None
        self.ai_erp = None
        self.mcp_layer = None
        self.active_observations: Dict[str, Any] = {}
        self.websocket_connections: List[WebSocket] = []
        self.request_count = 0
        self.error_count = 0

state = AppState()


# ─── Lifespan ───

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    # Startup
    print("🌅 Starting AGENCY OS API Server...")

    try:
        from aurora.core import AuroraCore
        state.aurora = AuroraCore()
        await state.aurora.initialize()
        print("  ✅ AuroraCore initialized")
    except Exception as e:
        print(f"  ⚠️  AuroraCore: {e}")

    try:
        from aurora.enterprise.core import EnterpriseCore
        state.enterprise_core = EnterpriseCore()
        state.enterprise_core.load()
        print("  ✅ EnterpriseCore initialized")
    except Exception as e:
        print(f"  ⚠️  EnterpriseCore: {e}")

    try:
        from aurora.enterprise.erp import ERPCore
        state.erp_core = ERPCore()
        print("  ✅ ERPCore initialized")
    except Exception as e:
        print(f"  ⚠️  ERPCore: {e}")

    try:
        from aurora.enterprise.ai_erp import AIERPLayer
        if state.erp_core:
            state.ai_erp = AIERPLayer(state.erp_core, state.enterprise_core)
            print("  ✅ AIERPLayer initialized")
    except Exception as e:
        print(f"  ⚠️  AIERPLayer: {e}")

    print("🚀 AGENCY OS API Server ready")

    yield

    # Shutdown
    print("🌅 Shutting down...")
    if state.aurora:
        await state.aurora.shutdown()
    if state.enterprise_core:
        state.enterprise_core.save()
    print("✅ Shutdown complete")


# ─── App Creation ───

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title="AGENCY OS",
        description="AI-Native Agency ERP + Creative Intelligence Platform",
        version="1.0.0-alpha",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )

    # ─── Middleware ───

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure for production
    )

    @app.middleware("http")
    async def track_requests(request: Request, call_next):
        state.request_count += 1
        start = time.time()
        try:
            response = await call_next(request)
            response.headers["X-Process-Time"] = str(time.time() - start)
            response.headers["X-Request-ID"] = str(uuid.uuid4())[:12]
            return response
        except Exception as e:
            state.error_count += 1
            return JSONResponse(
                status_code=500,
                content={"error": str(e), "request_id": str(uuid.uuid4())[:12]}
            )

    # ─── Sovereign gate (PHASE 1 seam: mutating routes fail closed) ───
    # Reads stay open per RBAC. Deny → 403 JSON (returned, not raised:
    # raises inside http middleware bypass ExceptionMiddleware → 500).
    @app.middleware("http")
    async def sovereign_gate(request: Request, call_next):
        try:
            from aurora.agency.api_guard import action_for, guard_or_403
        except Exception:
            return await call_next(request)
        action = action_for(request.method, request.url.path)
        if action is None:
            return await call_next(request)
        is_human = request.headers.get("X-Human") == "true"
        approval = None
        decision = request.headers.get("X-Approval-Decision")
        if decision:
            approval = {"decision": decision, "expires_at": request.headers.get("X-Approval-Expires", "")}
        try:
            amount = float(request.headers.get("X-Amount-USD", "0") or 0)
        except ValueError:
            amount = 0.0
        try:
            guard_or_403(action, is_human=is_human, approval=approval, amount_usd=amount)
        except Exception as e:
            detail = getattr(e, "detail", None) or {"sovereign": "deny", "reason": str(e)}
            return JSONResponse(status_code=403, content={"detail": detail, "action": action})
        return await call_next(request)

    # ─── WebSocket Manager ───

    class ConnectionManager:
        def __init__(self):
            self.active: List[WebSocket] = []

        async def connect(self, websocket: WebSocket):
            await websocket.accept()
            self.active.append(websocket)

        def disconnect(self, websocket: WebSocket):
            self.active.remove(websocket)

        async def broadcast(self, message: Dict):
            for ws in self.active:
                try:
                    await ws.send_json(message)
                except:
                    pass

    manager = ConnectionManager()

    # ═══════════════════════════════════════════════════════════
    # ROUTES
    # ═══════════════════════════════════════════════════════════

    # ─── Health & Status ───

    @app.get("/api/v1/status", response_model=StatusResponse, tags=["System"])
    async def get_status():
        """Get system status and statistics."""
        return StatusResponse(
            version="1.0.0-alpha",
            status="healthy",
            uptime_seconds=time.time() - state.start_time,
            components={
                "aurora": "connected" if state.aurora else "disconnected",
                "enterprise": "connected" if state.enterprise_core else "disconnected",
                "erp": "connected" if state.erp_core else "disconnected",
                "ai_erp": "connected" if state.ai_erp else "disconnected",
                "observations": len(state.active_observations),
                "websockets": len(manager.active)
            },
            stats={
                "total_requests": state.request_count,
                "total_errors": state.error_count,
                "memory_nodes": state.aurora._memory.media_collection.count() if state.aurora and state.aurora._memory else 0,
                "projects": len(state.enterprise_core.projects) if state.enterprise_core else 0,
                "users": len(state.enterprise_core.users) if state.enterprise_core else 0
            }
        )

    @app.get("/api/v1/health", tags=["System"])
    async def health_check():
        """Simple health check."""
        return {"status": "ok", "timestamp": datetime.now().isoformat()}

    # ─── Interpret ───

    @app.post("/api/v1/interpret", response_model=InterpretResponse, tags=["Intelligence"])
    async def interpret_media(
        file: UploadFile = File(...),
        media_type: Optional[str] = None,
        critique: bool = True,
        improve: bool = True
    ):
        """Interpret a media file through the intelligence pipeline."""
        if not state.aurora:
            raise HTTPException(503, "AuroraCore not initialized")

        # Save uploaded file
        upload_dir = Path("./uploads")
        upload_dir.mkdir(exist_ok=True)
        file_path = upload_dir / f"{uuid.uuid4().hex}_{file.filename}"

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Determine media type
        mt = None
        if media_type:
            from aurora.core import MediaType
            try:
                mt = MediaType(media_type)
            except ValueError:
                pass

        # Interpret
        interpretation = await state.aurora.interpret(file_path, mt)

        # Optional critique and improvement
        if critique:
            critiques = await state.aurora.critique(interpretation)
            interpretation.insights.extend(critiques)

        if improve:
            improvements = await state.aurora.improve(interpretation)
            interpretation.insights.extend(improvements)

        return InterpretResponse(
            media_id=interpretation.media_id,
            media_type=interpretation.media_type.value if hasattr(interpretation.media_type, 'value') else str(interpretation.media_type),
            summary=interpretation.summary,
            quality_score=interpretation.quality_score,
            tags=interpretation.tags,
            insights=[{
                "domain": i.domain.value if hasattr(i.domain, 'value') else str(i.domain),
                "category": i.category,
                "finding": i.finding,
                "confidence": i.confidence,
                "evidence": i.evidence,
                "suggestions": i.suggestions
            } for i in interpretation.insights],
            timestamp=interpretation.timestamp
        )

    @app.get("/api/v1/interpret/{media_id}", tags=["Intelligence"])
    async def get_interpretation(media_id: str):
        """Get a stored interpretation by ID."""
        if not state.aurora or not state.aurora._memory:
            raise HTTPException(503, "Memory not initialized")

        result = await state.aurora._memory.get_media(media_id)
        if not result:
            raise HTTPException(404, "Interpretation not found")

        return result

    # ─── Query ───

    @app.post("/api/v1/query", response_model=QueryResponse, tags=["Intelligence"])
    async def query_memory(request: QueryRequest):
        """Query the creative memory graph with natural language."""
        if not state.aurora:
            raise HTTPException(503, "AuroraCore not initialized")

        domain = None
        if request.domain:
            from aurora.core import IntelligenceDomain
            try:
                domain = IntelligenceDomain(request.domain)
            except ValueError:
                pass

        answer = await state.aurora.query(request.question, domain)

        return QueryResponse(answer=answer, confidence=0.8)

    # ─── Projects ───

    @app.post("/api/v1/projects", response_model=ProjectResponse, tags=["Projects"])
    async def create_project(project: ProjectCreate):
        """Create a new project."""
        if not state.aurora:
            raise HTTPException(503, "AuroraCore not initialized")

        p = await state.aurora.create_project(
            name=project.name,
            description=project.description,
            brief=project.brief,
            goals=project.goals
        )

        return ProjectResponse(
            project_id=p.project_id,
            name=p.name,
            status=p.status,
            created_at=p.created_at
        )

    @app.get("/api/v1/projects", tags=["Projects"])
    async def list_projects():
        """List all projects."""
        if not state.aurora or not state.aurora._memory:
            raise HTTPException(503, "Memory not initialized")

        projects = []
        for pid, p in state.aurora._memory.projects.items():
            projects.append({"project_id": pid, **p})
        return projects

    @app.get("/api/v1/projects/{project_id}", tags=["Projects"])
    async def get_project(project_id: str):
        """Get project details."""
        if not state.aurora or not state.aurora._memory:
            raise HTTPException(503, "Memory not initialized")

        if project_id not in state.aurora._memory.projects:
            raise HTTPException(404, "Project not found")

        return {"project_id": project_id, **state.aurora._memory.projects[project_id]}

    # ─── Observe ───

    @app.post("/api/v1/observe", response_model=ObserveResponse, tags=["Observation"])
    async def start_observation(request: ObserveRequest):
        """Start live creative observation."""
        if not state.aurora:
            raise HTTPException(503, "AuroraCore not initialized")

        obs_id = f"obs_{uuid.uuid4().hex[:8]}"
        await state.aurora.start_observation(request.targets, request.interval)

        state.active_observations[obs_id] = {
            "targets": request.targets,
            "interval": request.interval,
            "started_at": datetime.now().isoformat()
        }

        return ObserveResponse(
            observation_id=obs_id,
            status="active",
            targets=request.targets
        )

    @app.delete("/api/v1/observe/{obs_id}", tags=["Observation"])
    async def stop_observation(obs_id: str):
        """Stop live observation."""
        if not state.aurora:
            raise HTTPException(503, "AuroraCore not initialized")

        await state.aurora.stop_observation()
        state.active_observations.pop(obs_id, None)
        return {"status": "stopped", "observation_id": obs_id}

    @app.get("/api/v1/observe", tags=["Observation"])
    async def list_observations():
        """List active observations."""
        return state.active_observations

    # ─── ERP: Finance ───

    @app.get("/api/v1/erp/invoices", tags=["ERP"])
    async def list_invoices(status: Optional[str] = None):
        """List invoices with optional status filter."""
        if not state.erp_core:
            raise HTTPException(503, "ERP not initialized")

        invoices = list(state.erp_core.invoices.values())
        if status:
            invoices = [i for i in invoices if i.status.value == status]

        return [{"id": i.invoice_id, "number": i.number, "status": i.status.value,
                 "total": i.total, "balance": i.balance} for i in invoices]

    @app.post("/api/v1/erp/invoices", tags=["ERP"])
    async def create_invoice(invoice: ERPInvoiceCreate):
        """Create a new invoice."""
        if not state.erp_core:
            raise HTTPException(503, "ERP not initialized")

        from aurora.enterprise.erp import Invoice, InvoiceStatus, Currency

        total = sum(i.get("quantity", 1) * i.get("rate", 0) for i in invoice.items) * (1 + invoice.tax)
        from aurora.agency.erp_bindings import assert_invoice_linkage

        try:
            assert_invoice_linkage(invoice.client_id, total)
        except ValueError as e:
            raise HTTPException(422, str(e))

        inv = Invoice(
            invoice_id=f"inv_{uuid.uuid4().hex[:10]}",
            org_id="org_default",
            client_id=invoice.client_id,
            number=f"INV-{len(state.erp_core.invoices)+1:04d}",
            items=invoice.items,
            tax=invoice.tax,
            total=total,
            due_date=invoice.due_date,
            notes=invoice.notes,
            status=InvoiceStatus.DRAFT,
            currency=Currency.USD
        )
        state.erp_core.invoices[inv.invoice_id] = inv
        return {"invoice_id": inv.invoice_id, "number": inv.number, "total": inv.total}

    @app.get("/api/v1/erp/finance/summary", tags=["ERP"])
    async def finance_summary():
        """Get financial summary."""
        if not state.erp_core:
            raise HTTPException(503, "ERP not initialized")

        return {
            "total_revenue": state.erp_core.get_org_revenue("org_default"),
            "outstanding": state.erp_core.get_org_outstanding("org_default"),
            "invoice_count": len(state.erp_core.invoices),
            "expense_count": len(state.erp_core.expenses)
        }

    # ─── ERP: Projects/Tasks ───

    @app.get("/api/v1/erp/tasks", tags=["ERP"])
    async def list_tasks(project_id: Optional[str] = None, status: Optional[str] = None):
        """List tasks with filters."""
        if not state.erp_core:
            raise HTTPException(503, "ERP not initialized")

        tasks = list(state.erp_core.tasks.values())
        if project_id:
            tasks = [t for t in tasks if t.project_id == project_id]
        if status:
            from aurora.enterprise.erp import TaskStatus
            tasks = [t for t in tasks if t.status.value == status]

        return [{"id": t.task_id, "title": t.title, "status": t.status.value,
                 "project_id": t.project_id, "assignee_id": t.assignee_id} for t in tasks]

    @app.post("/api/v1/erp/tasks", tags=["ERP"])
    async def create_task(task: ERPTaskCreate):
        """Create a new task."""
        if not state.erp_core:
            raise HTTPException(503, "ERP not initialized")

        from aurora.enterprise.erp import Task, TaskStatus

        t = Task(
            task_id=f"task_{uuid.uuid4().hex[:10]}",
            org_id="org_default",
            project_id=task.project_id,
            title=task.title,
            description=task.description,
            assignee_id=task.assignee_id,
            priority=task.priority,
            estimated_hours=task.estimated_hours,
            due_date=task.due_date,
            status=TaskStatus.TODO
        )
        state.erp_core.tasks[t.task_id] = t
        return {"task_id": t.task_id, "title": t.title, "status": t.status.value}

    @app.patch("/api/v1/erp/tasks/{task_id}/state", tags=["ERP"])
    async def transition_task_state(task_id: str, to_status: str):
        """Governed task transition (canonical TRANSITIONS via erp_bindings)."""
        if not state.erp_core:
            raise HTTPException(503, "ERP not initialized")
        if task_id not in state.erp_core.tasks:
            raise HTTPException(404, "Task not found")
        from aurora.agency.erp_bindings import transition_erp_task
        from aurora.enterprise.erp import TaskStatus

        try:
            target = TaskStatus(to_status)
        except ValueError:
            raise HTTPException(422, f"unknown task status {to_status}")
        t = state.erp_core.tasks[task_id]
        try:
            frm, to = transition_erp_task(t, target)
        except ValueError as e:
            raise HTTPException(422, str(e))
        return {"task_id": task_id, "from_agency": frm, "to_agency": to, "status": t.status.value}

    # ─── ERP: CRM ───

    @app.get("/api/v1/erp/crm/pipeline", tags=["ERP"])
    async def crm_pipeline():
        """Get CRM pipeline summary."""
        if not state.erp_core:
            raise HTTPException(503, "ERP not initialized")

        return state.erp_core.get_pipeline_value("org_default")

    @app.get("/api/v1/erp/crm/leads", tags=["ERP"])
    async def list_leads():
        """List all leads."""
        if not state.erp_core:
            raise HTTPException(503, "ERP not initialized")

        return [{"id": l.lead_id, "name": l.name, "status": l.status.value if hasattr(l.status, 'value') else str(l.status),
                 "value": l.value} for l in state.erp_core.leads.values()]

    # ─── ERP: HR ───

    @app.get("/api/v1/erp/hr/utilization", tags=["ERP"])
    async def hr_utilization():
        """Get team utilization metrics."""
        if not state.erp_core:
            raise HTTPException(503, "ERP not initialized")

        return state.erp_core.get_org_utilization("org_default")

    @app.get("/api/v1/erp/hr/employees", tags=["ERP"])
    async def list_employees():
        """List all employees."""
        if not state.erp_core:
            raise HTTPException(503, "ERP not initialized")

        return [{"id": e.employee_id, "name": e.name, "role": e.role,
                 "status": e.status.value if hasattr(e.status, 'value') else str(e.status)}
                for e in state.erp_core.employees.values()]

    # ─── AI ERP ───

    @app.post("/api/v1/ai/query", tags=["AI ERP"])
    async def ai_erp_query(request: AIQueryRequest):
        """AI-powered reasoning over all agency data."""
        if not state.ai_erp:
            raise HTTPException(503, "AI ERP not initialized")

        result = await state.ai_erp.query(request.question, "org_default")
        return result

    @app.get("/api/v1/ai/insights", tags=["AI ERP"])
    async def ai_insights():
        """Get auto-generated insights."""
        if not state.ai_erp:
            raise HTTPException(503, "AI ERP not initialized")

        insights = state.ai_erp.generate_insights("org_default")
        return [{"category": i.category, "title": i.title, "description": i.description,
                 "confidence": i.confidence, "severity": i.severity} for i in insights]

    @app.get("/api/v1/ai/forecast/revenue", tags=["AI ERP"])
    async def revenue_forecast():
        """Get revenue forecast."""
        if not state.ai_erp:
            raise HTTPException(503, "AI ERP not initialized")

        return await state.ai_erp.forecast_revenue("org_default")

    @app.get("/api/v1/ai/predict/churn", tags=["AI ERP"])
    async def churn_prediction():
        """Get churn prediction."""
        if not state.ai_erp:
            raise HTTPException(503, "AI ERP not initialized")

        return await state.ai_erp.predict_churn("org_default")

    # ─── Batch ───

    @app.post("/api/v1/batch", tags=["Batch"])
    async def batch_process(
        directory: str,
        extensions: str = "png,jpg,jpeg,webp",
        critique: bool = False,
        improve: bool = False
    ):
        """Batch process a directory of media files."""
        # Input validation first (404 precedes 503): bad path is client error
        # even when the service is down. Layer contract: fail-fast on inputs.
        path = Path(directory)
        if not path.exists():
            raise HTTPException(404, "Directory not found")

        if not state.aurora:
            raise HTTPException(503, "AuroraCore not initialized")

        ext_list = [e.strip() for e in extensions.split(",")]
        files = []
        for ext in ext_list:
            files.extend(path.rglob(f"*{ext}"))

        results = []
        for file_path in files:
            try:
                interp = await state.aurora.interpret(file_path)
                results.append({
                    "file": file_path.name,
                    "media_id": interp.media_id,
                    "quality": interp.quality_score
                })
            except Exception as e:
                results.append({"file": file_path.name, "error": str(e)})

        return {"total": len(files), "processed": len([r for r in results if "error" not in r]),
                "results": results}

    # ─── WebSocket ───

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket for real-time events."""
        await manager.connect(websocket)
        try:
            await websocket.send_json({"type": "connected", "timestamp": datetime.now().isoformat()})
            while True:
                data = await websocket.receive_text()
                msg = json.loads(data)
                if msg.get("action") == "subscribe":
                    await websocket.send_json({"type": "subscribed", "channel": msg.get("channel")})
                elif msg.get("action") == "ping":
                    await websocket.send_json({"type": "pong"})
        except WebSocketDisconnect:
            manager.disconnect(websocket)

    # ─── Webhooks ───

    @app.post("/api/v1/webhooks/{integration}", tags=["Webhooks"])
    async def receive_webhook(integration: str, payload: WebhookPayload):
        """Receive webhooks from external integrations."""
        # Broadcast to WebSocket clients
        await manager.broadcast({
            "type": "webhook",
            "integration": integration,
            "event": payload.event,
            "data": payload.data,
            "timestamp": datetime.now().isoformat()
        })
        return {"status": "received", "integration": integration}

    # ─── MCP ───

    @app.get("/api/v1/mcp/servers", tags=["MCP"])
    async def list_mcp_servers():
        """List configured MCP servers."""
        mcp_config = Path(".mcp.json")
        if mcp_config.exists():
            with open(mcp_config) as f:
                return json.load(f)
        return {"mcpServers": {}}

    @app.get("/api/v1/mcp/tools", tags=["MCP"])
    async def list_mcp_tools():
        """List available MCP tools."""
        if not state.mcp_layer:
            return {"tools": []}
        return {"tools": state.mcp_layer.get_available_tools()}

    # ─── Enterprise ───

    @app.get("/api/v1/enterprise/status", tags=["Enterprise"])
    async def enterprise_status():
        """Get enterprise status."""
        if not state.enterprise_core:
            raise HTTPException(503, "Enterprise not initialized")
        return state.enterprise_core.status()

    @app.get("/api/v1/enterprise/users", tags=["Enterprise"])
    async def list_users():
        """List all users."""
        if not state.enterprise_core:
            raise HTTPException(503, "Enterprise not initialized")
        return [{"id": u.user_id, "name": u.name, "email": u.email}
                for u in state.enterprise_core.users.values()]

    @app.get("/api/v1/enterprise/organizations", tags=["Enterprise"])
    async def list_organizations():
        """List all organizations."""
        if not state.enterprise_core:
            raise HTTPException(503, "Enterprise not initialized")
        return [{"id": o.org_id, "name": o.name, "plan": o.billing_plan,
                 "members": o.member_count} for o in state.enterprise_core.organizations.values()]

    return app


# ─── App Instance ───

app = create_app()


# ─── Run ───

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "aurora.api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )