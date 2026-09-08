<div align="center">

# 🏢 AGENCY OS®

**The Operating System for Creative Intelligence**

*AI-Native Agency ERP + Creative Intelligence Platform*

[![Version](https://img.shields.io/badge/version-1.0.0--alpha-blue)](https://github.com/agency-os/agency-os)
[![Python](https://img.shields.io/badge/python-3.10+-green)](https://python.org)
[![License](https://img.shields.io/badge/license-enterprise-red)](LICENSE)

<br/>

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   🧠 Creative Intelligence  🤖 Agentic Automation             │
│   🔌 Universal Integrations   📚 Organizational Memory         │
│   🧩 Modular Workspace       🚀 Enterprise Ready               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

<br/>

**One intelligence. Every creative tool. Every medium. Every workflow.**

[Getting Started](docs/guides/getting-started.md) •
[Architecture](docs/architecture/overview.md) •
[API Reference](docs/api/reference.md) •
[Modules](docs/modules/index.md) •
[CLI](docs/guides/cli.md)

</div>

---

## Table of Contents

- [What is AGENCY OS?](#what-is-agency-os)
- [Vision](#vision)
- [Key Differentiators](#key-differentiators)
- [Architecture Overview](#architecture-overview)
- [Product Pillars](#product-pillars)
- [SaaS Modules](#saas-modules)
- [Intelligence Engines](#intelligence-engines)
- [ERP Modules](#erp-modules)
- [Target Customers](#target-customers)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [Roadmap](#roadmap)
- [License](#license)

---

## What is AGENCY OS?

AGENCY OS is an **AI-native operating system for creative agencies, marketing teams, production studios, freelancers, and enterprise brands**. It unifies strategy, research, design, content, video, development, automation, and business operations into one intelligent platform.

Rather than replacing existing software, AGENCY OS **orchestrates applications, AI models, people, knowledge, and workflows** through a unified cognitive layer, enabling agencies to research, create, edit, analyze, automate, and deliver work faster, with greater quality and consistency.

### Positioning

```
                    AGENCY OS
        Creative Intelligence Platform
──────────────────────────────────────────────
        Adobe CC  Figma  Canva  Blender
        DaVinci   Premiere  Runway  Higgsfield
        VS Code   Office  Webflow  Notion
        GitHub    Slack   Discord  n8n
──────────────────────────────────────────────
        OpenAI  Anthropic  Google  Mistral
        Local LLMs  ComfyUI  Stable Diffusion
──────────────────────────────────────────────
            Windows  macOS  Linux
──────────────────────────────────────────────
```

---

## Vision

> **AGENCY OS transforms every creative tool into part of a single intelligent workspace.**

The long-term objective is for AGENCY OS to become the **AI-native ERP for the creative economy**. Traditional ERPs like SAP, Oracle, and NetSuite excel at structured business operations but have little understanding of creative workflows. Creative platforms like Adobe and Figma excel at content creation but don't manage the business behind it.

AGENCY OS bridges those worlds by combining **creative production, business operations, organizational knowledge, and AI reasoning** into one unified platform.

---

## Key Differentiators

| Differentiator | Description |
|---------------|-------------|
| **Creative Cognition** | Understands narrative, symbolism, aesthetics, branding, psychology, and design—not just pixels |
| **AI ERP Layer** | Natural language reasoning over all agency data (churn prediction, revenue forecasting, capacity analysis) |
| **Semantic Knowledge Graph** | Every project, asset, campaign, client, and decision becomes connected |
| **Live Creative Observation** | Continuous creative review (not just post-hoc analysis) |
| **6 Intelligence Domains** | Narrative, Visual, Symbolism, Design, Marketing, Psychological |
| **Multi-tenant RBAC** | Enterprise-ready with organizations, teams, workspaces, roles |
| **MCP/A2A Protocol** | Universal tool integration (50+ integrations) |
| **Modular Architecture** | Install only the modules your organization needs |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        AGENCY OS PLATFORM                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     GATEWAY LAYER                                │   │
│  │  CLI  │  Web UI  │  REST API  │  GraphQL  │  WebSocket  │  SDK  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                  CREATIVE INTELLIGENCE LAYER                     │   │
│  │  ┌─────────┐ ┌────────┐ ┌──────────┐ ┌───────┐ ┌───────────┐  │   │
│  │  │Narrative│ │ Visual │ │Symbolism │ │Design │ │ Marketing │  │   │
│  │  └─────────┘ └────────┘ └──────────┘ └───────┘ └───────────┘  │   │
│  │  ┌──────────────┐ ┌──────────────────────────────────────────┐ │   │
│  │  │Psychological │ │           AI ERP LAYER                  │ │   │
│  │  └──────────────┘ └──────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      ERP LAYER                                   │   │
│  │  CRM │ Projects │ Finance │ HR │ Assets │ Production │ Sales  │   │
│  │  Operations │ Procurement │ Knowledge                           │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                   CORE PLATFORM                                  │   │
│  │  Organizations │ Teams │ Workspaces │ Projects │ Clients       │   │
│  │  RBAC │ Audit │ Auth │ Billing │ Notifications                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    MEMORY LAYER                                  │   │
│  │  ChromaDB (Vectors) │ NetworkX (Graph) │ SQLite (Metadata)      │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                 INTEGRATION LAYER                                │   │
│  │  MCP Protocol │ A2A Protocol │ REST APIs │ Webhooks │ SDKs     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Product Pillars

### 🧠 Creative Intelligence
Understands narrative, symbolism, aesthetics, branding, psychology, and design—not just pixels. Six intelligence engines analyze every creative deliverable.

### 🤖 Agentic Automation
Specialized AI agents collaborate, delegate work, critique outputs, and automate end-to-end workflows.

### 🔌 Universal Integrations
Native connectivity with creative software, developer tools, cloud services, MCP servers, APIs, and local applications.

### 🧩 Modular Workspace
Every organization builds its own operating system by enabling only the modules it needs.

### 📚 Organizational Memory
A semantic knowledge graph that learns from every project, asset, client, workflow, and decision.

### 🚀 Enterprise Ready
Multi-tenant architecture, governance, permissions, audit trails, security, compliance, and scalability.

---

## SaaS Modules

### AGENCY OS Core
- Organizations • Teams • Workspaces • Projects • Clients
- Authentication • RBAC • Audit • Billing • Notifications

### Creative Suite
- Design Studio • Image Studio • Video Studio • Motion Studio
- Audio Studio • Copy Studio • 3D Studio

### Intelligence Suite
- Research • Creative Analysis • Competitor Intelligence
- Trend Analysis • Predictive Insights • Quality Assurance

### Business Suite
- CRM • Proposals • Contracts • Invoicing
- Resource Planning • Time Tracking • Reporting

### Automation Suite
- Agent Builder • Workflow Builder • MCP Orchestrator
- API Integrations • Scheduled Tasks • Event Automation

### Developer Suite
- CLI • SDK • REST API • GraphQL API • Plugin SDK • Custom MCP Connectors

### Enterprise Suite
- SSO • RBAC • Audit Logs • Compliance • Security Policies • Private Deployments

---

## Intelligence Engines

| Engine | Analyzes | Output |
|--------|----------|--------|
| **Narrative** | Story structure, character arcs, themes, pacing, emotional arcs | Story quality score, structural patterns, tension analysis |
| **Visual** | Composition, color theory, lighting, hierarchy, typography | Visual balance, color harmony, focal points |
| **Symbolism** | Cultural symbols, brand archetypes, luxury cues, hidden meaning | Symbolic coherence, archetype alignment, semiotic analysis |
| **Design** | Design systems, WCAG compliance, UI patterns, tokens | Accessibility score, system maturity, token structure |
| **Marketing** | Positioning, audience alignment, messaging, funnel stage | Conversion potential, message clarity, CTA effectiveness |
| **Psychological** | Cognitive biases, persuasion principles, attention, memory | Ethical assessment, persuasion score, engagement prediction |

---

## ERP Modules

| Module | Entities | AI Reasoning |
|--------|----------|--------------|
| **CRM** | Leads, Opportunities, Contacts, Meetings | Churn prediction, relationship scoring |
| **Projects** | Tasks, Campaigns, Time Entries | Scope creep detection, schedule risk |
| **Finance** | Invoices, Expenses, Quotes | Revenue forecasting, cash flow analysis |
| **HR** | Employees, Candidates, Leave | Capacity analysis, utilization optimization |
| **Assets** | Digital/Physical assets, maintenance | Depreciation tracking, utilization |
| **Production** | Productions, Shoot Days | Schedule optimization, resource allocation |
| **Procurement** | Vendors, Purchase Orders | Price comparison, vendor scoring |
| **Knowledge** | SOPs, Playbooks, Lessons | Semantic search, knowledge gaps |
| **Sales** | Deals, Pipeline, Scoring | Win probability, revenue forecasting |
| **Operations** | Capacity Plans, Risks | Risk scoring, utilization analysis |

---

## Target Customers

| Segment | Use Case |
|---------|----------|
| **Creative Agencies** | Full agency operations, client management, creative production |
| **Enterprise Marketing** | In-house teams, brand consistency, campaign management |
| **Production Studios** | Video/film production, scheduling, resource planning |
| **Freelancers** | Project management, invoicing, creative tools |
| **Education** | Design schools, media programs, creative bootcamps |

---

## Quick Start

### Prerequisites
- Python 3.10+
- pip or uv package manager
- API keys for AI providers (OpenAI, Anthropic, Google)

### Installation

```bash
# Clone the repository
git clone https://github.com/agency-os/agency-os.git
cd agency-os

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run the CLI
python aurora/cli.py --help

# Run the API server
python aurora/api/server.py
```

### First Steps

```python
import asyncio
from aurora.core import AuroraCore

async def main():
    # Initialize the platform
    aurora = AuroraCore()
    await aurora.initialize()

    # Create a project
    project = await aurora.create_project(
        name="Brand Campaign 2026",
        description="Q4 brand refresh campaign",
        target_audience="Urban professionals 25-40",
        goals=["Increase brand awareness", "Drive conversions"]
    )

    # Interpret media
    interpretation = await aurora.interpret("path/to/asset.png")

    # Query creative memory
    result = await aurora.query("What color palettes work for fintech?")

    await aurora.shutdown()

asyncio.run(main())
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [Getting Started](docs/guides/getting-started.md) | Installation, setup, first steps |
| [CLI Guide](docs/guides/cli.md) | Command-line interface reference |
| [Configuration](docs/guides/configuration.md) | Environment variables, settings |
| [Architecture Overview](docs/architecture/overview.md) | System architecture, data flow |
| [Architecture Diagrams](docs/architecture/diagrams.md) | Visual architecture diagrams |
| [API Reference](docs/api/reference.md) | REST API endpoints |
| [Module Reference](docs/modules/index.md) | All SaaS modules |
| [Intelligence Engines](docs/modules/intelligence.md) | Creative cognition system |
| [ERP Modules](docs/modules/erp.md) | Enterprise resource planning |
| [Integration Guide](docs/guides/integrations.md) | MCP, A2A, third-party tools |
| [Agent Instructions](AGENTS.md) | AI agent guidelines |
| [Contributing](CONTRIBUTING.md) | Development guidelines |
| [Changelog](CHANGELOG.md) | Version history |

---

## File Structure

```
AGENCY OS/
├── aurora/                          # Core platform package
│   ├── __init__.py
│   ├── core.py                      # AuroraCore — central orchestration
│   ├── cli.py                       # CLI entry point
│   ├── intelligence/                # 6 Intelligence Engines
│   │   ├── narrative.py             # Story, character, theme analysis
│   │   ├── visual.py                # Composition, color, lighting
│   │   ├── symbolism.py             # Cultural symbols, archetypes
│   │   ├── design.py                # Design systems, accessibility
│   │   ├── marketing.py             # Positioning, audience, funnel
│   │   └── psychological.py         # Cognitive biases, persuasion
│   ├── memory/
│   │   └── graph.py                 # CreativeMemoryGraph
│   ├── interpreters/
│   │   └── universal.py             # Universal media interpreter
│   ├── observation/
│   │   └── watcher.py               # LiveObserver
│   ├── protocols/
│   │   └── mcp_layer.py             # MCP/A2A protocol layer
│   ├── enterprise/
│   │   ├── core.py                  # Multi-tenant core + RBAC
│   │   ├── erp.py                   # 10 ERP modules
│   │   └── ai_erp.py                # AI reasoning over ERP data
│   ├── integrations/                # Third-party integrations
│   ├── api/                         # REST/GraphQL API
│   ├── ui/                          # Web UI components
│   ├── agents/                      # AI agent definitions
│   └── workflows/                   # Workflow engine
├── docs/                            # Documentation
│   ├── architecture/                # Architecture docs
│   ├── modules/                     # Module docs
│   ├── api/                         # API reference
│   ├── guides/                      # User guides
│   └── images/                      # Diagrams, screenshots
├── studio_agents/                   # Design studio agent
├── studio_scripts/                  # Media pipeline scripts
├── prompts/templates/               # Prompt templates
├── projects/                        # Project storage
├── output/                          # Generated assets
├── tests/                           # Test suite
├── requirements.txt                 # Python dependencies
├── .env                             # Environment configuration
├── .mcp.json                        # MCP server configuration
├── README.md                        # This file
├── AGENTS.md                        # AI agent instructions
└── CHANGELOG.md                     # Version history
```

---

## Roadmap

### Alpha (Current) ✅
- [x] Core platform with multi-tenant architecture
- [x] 6 Intelligence Engines
- [x] Creative Memory Graph (ChromaDB + NetworkX)
- [x] Universal Media Interpreter (9 types)
- [x] Live Observation System
- [x] MCP/A2A Protocol Layer
- [x] 10 ERP Modules
- [x] AI ERP Layer (predictive analytics)
- [x] CLI Interface
- [x] Enterprise Core (RBAC, audit, auth)

### Beta (Next) 🚧
- [ ] REST API + GraphQL
- [ ] Web UI (React)
- [ ] Real-time collaboration
- [ ] Advanced workflow builder
- [ ] Agent marketplace
- [ ] Figma integration
- [ ] Adobe Creative Cloud integration

### v1.0 📋
- [ ] SSO / SAML / OAuth2
- [ ] Mobile companion
- [ ] Desktop app (Electron)
- [ ] Industry packs (15 verticals)
- [ ] Marketplace launch
- [ ] SOC 2 compliance

### Enterprise 🏢
- [ ] Kubernetes deployment
- [ ] GPU scheduling
- [ ] Private deployments
- [ ] White labeling
- [ ] Global CDN

---

## License

AGENCY OS is proprietary software. Contact licensing for enterprise use.

---

<div align="center">

**[⬆ Back to Top](#-agency-os)**

</div>