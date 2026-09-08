# AGENCY OS — Workspace Navigation

**Master map for finding anything in the platform.**

---

## Quick Lookup

| What are you looking for? | Where to go |
|--------------------------|-------------|
| Platform overview & setup | `README.md` |
| AI agent instructions | `AGENTS.md` |
| Getting started guide | `docs/guides/getting-started.md` |
| CLI reference | `docs/guides/cli.md` |
| Configuration | `docs/guides/configuration.md` |
| Troubleshooting | `docs/guides/troubleshooting.md` |
| Architecture diagrams | `docs/architecture/overview.md` |
| API reference | `docs/api/reference.md` |
| Module documentation | `docs/modules/index.md` |
| Changelog | `CHANGELOG.md` |
| This navigation map | `WORKSPACE.md` |
| Package configuration | `pyproject.toml` |
| Docker deployment | `docker-compose.yml` |

---

## Directory Map

```
X:\Playground\
│
├── 📄 README.md .......................... Platform overview, quick start
├── 📄 AGENTS.md .......................... AI agent instructions
├── 📄 CHANGELOG.md ...................... Version history
├── 📄 WORKSPACE.md ....................... This file (navigation map)
├── 📄 pyproject.toml ..................... Python package config
├── 📄 Dockerfile ......................... Docker build config
├── 📄 docker-compose.yml ................. Full stack deployment
├── 📄 .env ............................... Environment variables
├── 📄 .env.example ....................... Environment template
├── 📄 .mcp.json .......................... MCP server config
├── 📄 .gitignore ......................... Git ignore rules
│
├── 📁 aurora/ ............................ Core platform package
│   │
│   ├── 📄 core.py ........................ AuroraCore orchestration
│   ├── 📄 cli.py ......................... CLI entry point
│   │
│   ├── 📁 intelligence/ .................. 6 Intelligence Engines
│   │   ├── 📄 narrative.py ............... Story, character, theme
│   │   ├── 📄 visual.py .................. Composition, color, lighting
│   │   ├── 📄 symbolism.py ............... Cultural symbols, archetypes
│   │   ├── 📄 design.py .................. Design systems, accessibility
│   │   ├── 📄 marketing.py ............... Positioning, funnel
│   │   └── 📄 psychological.py ........... Cognitive biases, persuasion
│   │
│   ├── 📁 memory/ ........................ Creative Memory Graph
│   │   └── 📄 graph.py ................... ChromaDB + NetworkX
│   │
│   ├── 📁 interpreters/ .................. Universal Media Interpreter
│   │   └── 📄 universal.py ............... 9 media types
│   │
│   ├── 📁 observation/ ................... Live Observation
│   │   └── 📄 watcher.py ................. File watching + critique
│   │
│   ├── 📁 protocols/ ..................... MCP/A2A Protocol Layer
│   │   └── 📄 mcp_layer.py ............... Tool integration
│   │
│   ├── 📁 enterprise/ .................... Enterprise + ERP + AI
│   │   ├── 📄 core.py .................... Multi-tenant + RBAC
│   │   ├── 📄 erp.py ..................... 10 ERP modules
│   │   └── 📄 ai_erp.py .................. AI reasoning layer
│   │
│   ├── 📁 integrations/ .................. Connectors + Industry Packs
│   │   ├── 📄 connectors.py .............. Figma, Adobe, GitHub, Slack
│   │   └── 📄 industry_packs.py .......... 15 vertical solutions
│   │
│   ├── 📁 workflows/ ..................... Workflow Builder
│   │   └── 📄 engine.py .................. Node-based automation
│   │
│   ├── 📁 agents/ ........................ AI Agents + Prompts
│   │   └── 📄 prompts.py ................. Prompt engineering system
│   │
│   ├── 📁 export/ ........................ Export & Publishing
│   │   └── 📄 pipeline.py ................ Multi-format export
│   │
│   ├── 📁 api/ ........................... API Server
│   │   ├── 📄 server.py .................. FastAPI + WebSocket
│   │   └── 📄 auth.py .................... JWT + API key auth
│   │
│   └── 📁 ui/ ............................ Web UI
│       └── 📄 foundation.py .............. React + TypeScript
│
├── 📁 docs/ .............................. Documentation
│   ├── 📁 architecture/
│   │   └── 📄 overview.md ................ System architecture
│   ├── 📁 api/
│   │   └── 📄 reference.md ............... REST/GraphQL reference
│   ├── 📁 modules/
│   │   └── 📄 index.md ................... Module documentation
│   ├── 📁 guides/
│   │   ├── 📄 getting-started.md .......... Installation & setup
│   │   ├── 📄 cli.md ..................... CLI reference
│   │   ├── 📄 configuration.md ........... All config options
│   │   └── 📄 troubleshooting.md ......... FAQ & debugging
│   └── 📁 images/ ........................ Diagrams
│
├── 📁 tests/ ............................. Test Suite
│   └── 📄 test_agency_os.py .............. Comprehensive tests
│
├── 📁 studio_agents/ ..................... Design Studio
│   ├── 📄 studio_agent.py ................ Studio agent (OpenAI)
│   └── 📄 __init__.py
│
├── 📁 studio_scripts/ .................... Utility Scripts
│   ├── 📄 media_pipeline.py .............. DALL-E pipeline
│   └── 📄 mcp_manager.py ................. MCP server management
│
├── 📁 prompts/templates/ ................. Prompt Templates
│   ├── 📄 brand_identity.txt
│   ├── 📄 design_system.txt
│   ├── 📄 image_prompt.txt
│   ├── 📄 design_critique.txt
│   └── 📄 research.txt
│
├── 📁 projects/ .......................... Project Storage
├── 📁 output/ ............................ Generated Assets
├── 📁 tmp/ ............................... Temporary Files
├── 📁 aurora_memory/ ..................... Memory Persistence
└── 📁 agency_os_data/ .................... Enterprise Data
```

---

## Task-Based Navigation

### "I want to interpret media..."
1. CLI: `python aurora/cli.py interpret <file>`
2. Python: `aurora.interpret("file.png")`
3. API: `POST /api/v1/interpret`
4. Code: `aurora/interpreters/universal.py`

### "I want to manage projects..."
1. CLI: `python aurora/cli.py project create "Name"`
2. Python: `aurora.create_project(name="...")`
3. API: `POST /api/v1/projects`
4. Code: `aurora/enterprise/core.py` → `create_project()`

### "I want to run ERP operations..."
1. Python: `erp = ERPCore()` then `erp.invoices["id"] = Invoice(...)`
2. API: `GET /api/v1/erp/invoices`
3. Code: `aurora/enterprise/erp.py`

### "I want to ask AI about my data..."
1. Python: `ai = AIERPLayer(erp)` then `ai.predict_churn("org1")`
2. API: `POST /api/v1/ai/query`
3. Code: `aurora/enterprise/ai_erp.py`

### "I want to integrate Figma..."
1. Python: `figma = FigmaIntegration(config)` then `figma.get_files()`
2. Code: `aurora/integrations/connectors.py`

### "I want to build a workflow..."
1. Python: `engine = WorkflowEngine()` then `engine.create_workflow(...)`
2. Code: `aurora/workflows/engine.py`

### "I want to manage prompts..."
1. Python: `ps = PromptEngineeringSystem()` then `ps.create_prompt(...)`
2. Code: `aurora/agents/prompts.py`

### "I want to run the API server..."
1. Direct: `python aurora/api/server.py`
2. Docker: `docker-compose up -d`
3. Code: `aurora/api/server.py`

### "I want to run tests..."
1. `pytest tests/ -v`
2. With coverage: `pytest tests/ --cov=aurora`

---

## Module Dependency Graph

```
                    ┌─────────────┐
                    │  AuroraCore │
                    │  core.py    │
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼────┐      ┌──────▼──────┐    ┌──────▼──────┐
   │ Memory  │      │ Intelligence│    │ Interpreters│
   │ graph   │      │ 6 engines   │    │ universal   │
   └─────────┘      └─────────────┘    └─────────────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                    ┌──────▼──────┐
                    │ Enterprise  │
                    │ core + ERP  │
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼────┐      ┌──────▼──────┐    ┌──────▼──────┐
   │AI ERP   │      │Integrations │    │  Workflows  │
   │ ai_erp  │      │ connectors  │    │  engine     │
   └─────────┘      └─────────────┘    └─────────────┘
```

---

## Key Files by Role

| Role | Primary Files |
|------|--------------|
| **Developer** | `aurora/core.py`, `aurora/enterprise/*.py`, `aurora/api/server.py` |
| **Designer** | `aurora/intelligence/visual.py`, `aurora/integrations/connectors.py` |
| **Data Analyst** | `aurora/enterprise/erp.py`, `aurora/enterprise/ai_erp.py` |
| **DevOps** | `Dockerfile`, `docker-compose.yml`, `pyproject.toml` |
| **QA** | `tests/test_agency_os.py` |
| **Product** | `README.md`, `docs/modules/index.md` |
| **AI/ML** | `aurora/intelligence/*.py`, `aurora/agents/prompts.py` |
| **Manager** | `aurora/enterprise/erp.py`, `aurora/enterprise/ai_erp.py` |

---

## Configuration Files

| File | Purpose | Edit When |
|------|---------|-----------|
| `.env` | API keys, settings | Adding/changing API keys |
| `.mcp.json` | MCP servers | Adding external tools |
| `pyproject.toml` | Python package | Adding dependencies |
| `Dockerfile` | Docker build | Changing runtime |
| `docker-compose.yml` | Deployment | Adding services |

---

## Quick Start Commands

```bash
# Setup
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add your API keys

# CLI
python aurora/cli.py --help
python aurora/cli.py interpret image.png --critique --improve
python aurora/cli.py query "best colors for fintech?"

# API Server
python aurora/api/server.py
# → http://localhost:8000/docs

# Docker
docker-compose up -d
# → http://localhost:8000

# Tests
pytest tests/ -v

# Python REPL
python -c "from aurora.core import AuroraCore; ..."
```

---

**Last Updated:** 2026-08-07
**Platform Version:** 1.0.0-alpha
**Total Files:** 40+ Python files, 10 docs, 4 config files