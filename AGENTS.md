# AGENTS.md — AI Agent Instructions for AGENCY OS

**Version:** 1.0.0-alpha
**Last Updated:** 2026-08-07
**Classification:** Agent Runtime Documentation

---

## Table of Contents

1. [Platform Overview](#platform-overview)
2. [Agent Architecture](#agent-architecture)
3. [Agent Lifecycle](#agent-lifecycle)
4. [Available Agents](#available-agents)
5. [Agent Communication](#agent-communication)
6. [Memory & Context](#memory--context)
7. [Tool Access](#tool-access)
8. [Permission Model](#permission-model)
9. [Safety & Guardrails](#safety--guardrails)
10. [Development Guide](#development-guide)
11. [Code Conventions](#code-conventions)
12. [Module Reference](#module-reference)

---

## Platform Overview

AGENCY OS is an AI-Native Agency ERP + Creative Intelligence Platform. As an AI agent operating within this platform, you have access to:

- **Creative Intelligence Layer** — 6 intelligence engines that understand meaning, not just pixels
- **ERP Layer** — 10 enterprise modules covering all agency operations
- **Memory Layer** — Semantic knowledge graph connecting all projects, assets, and decisions
- **Integration Layer** — MCP/A2A protocols for tool communication

### Core Principles

1. **Understand Creative Intent** — Don't just detect objects; understand narrative, symbolism, and meaning
2. **Reason Over Data** — Use AI ERP capabilities to provide insights, not just reports
3. **Continuous Observation** — Monitor work in progress, not just completed assets
4. **Cross-Domain Intelligence** — Combine insights from multiple intelligence domains
5. **Ethical AI** — Always check for bias, accessibility, and ethical implications

---

## Agent Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENT ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  AGENT CORE                           │   │
│  │  Planning │ Reflection │ Critique │ Self-Correction  │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              INTELLIGENCE LAYER                       │   │
│  │  Narrative │ Visual │ Symbolism │ Design │ Marketing │   │
│  │  Psychological                                            │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                 MEMORY LAYER                          │   │
│  │  Short-term │ Long-term │ Semantic │ Episodic       │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                 TOOL LAYER                            │   │
│  │  Internal │ MCP │ A2A │ API │ CLI │ SDK             │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Agent Types

| Type | Description | Autonomy Level |
|------|-------------|----------------|
| **Specialist** | Domain-specific (design, video, copy) | Medium |
| **Orchestrator** | Coordinates multiple agents | High |
| **Analyst** | Data analysis and insights | Medium |
| **Assistant** | User-facing helper | Low |
| **Autonomous** | Self-directed task execution | High |

---

## Agent Lifecycle

### 1. Initialization
```python
from aurora.core import AuroraCore

aurora = AuroraCore()
await aurora.initialize()
```

### 2. Context Loading
```python
# Set active project for context
aurora.set_active_project(project)

# Load relevant memory
relevant = await aurora.find_similar(media_id)
```

### 3. Task Execution
```python
# Interpret media
interpretation = await aurora.interpret("path/to/asset.png")

# Generate critique
critiques = await aurora.critique(interpretation)

# Generate improvements
improvements = await aurora.improve(interpretation)
```

### 4. Memory Storage
```python
# Store interpretation in memory graph
await aurora.memory.store(interpretation)

# Link to project
await aurora.memory.link_to_project(media_id, project_id)
```

### 5. Observation (Optional)
```python
# Start live observation
await aurora.start_observation(["path/to/directory"])

# Stop observation
await aurora.stop_observation()
```

---

## Available Agents

### Creative Director Agent
- **Domain:** All creative domains
- **Capabilities:** Strategy, quality assessment, brand alignment
- **Tools:** All intelligence engines, project management
- **Autonomy:** High — can delegate to specialist agents

### Researcher Agent
- **Domain:** Intelligence Suite
- **Capabilities:** Market research, competitor analysis, trend detection
- **Tools:** Web search, academic databases, social listening
- **Autonomy:** Medium

### Copywriter Agent
- **Domain:** Narrative + Marketing Intelligence
- **Capabilities:** Copy generation, brand voice, messaging strategy
- **Tools:** LLM generation, tone analysis, A/B testing
- **Autonomy:** Medium

### Art Director Agent
- **Domain:** Visual + Symbolism Intelligence
- **Capabilities:** Visual direction, composition, color strategy
- **Tools:** Image generation, style analysis, brand guidelines
- **Autonomy:** Medium

### Developer Agent
- **Domain:** Code + Design Intelligence
- **Capabilities:** Front-end development, design-to-code, prototyping
- **Tools:** Code generation, component libraries, Figma API
- **Autonomy:** High

### Video Editor Agent
- **Domain:** Narrative + Visual Intelligence
- **Capabilities:** Video editing, story analysis, pacing
- **Tools:** Timeline editing, scene detection, color grading
- **Autonomy:** Medium

### Music Producer Agent
- **Domain:** Audio Intelligence
- **Capabilities:** Music generation, mix analysis, sound design
- **Tools:** DAW integration, stem separation, mastering
- **Autonomy:** Medium

### Business Strategist Agent
- **Domain:** Marketing + Psychological Intelligence
- **Capabilities:** Campaign strategy, positioning, audience analysis
- **Tools:** Market data, competitor analysis, forecasting
- **Autonomy:** Medium

### QA Agent
- **Domain:** All Intelligence Engines
- **Capabilities:** Quality assurance, accessibility checks, brand compliance
- **Tools:** WCAG validator, brand guidelines, design systems
- **Autonomy:** High

### Automation Engineer Agent
- **Domain:** Workflow + Process
- **Capabilities:** Workflow design, process automation, integration
- **Tools:** n8n, Zapier, custom APIs, MCP servers
- **Autonomy:** High

---

## Agent Communication

### A2A (Agent-to-Agent Protocol)

```python
from aurora.protocols.mcp_layer import A2AAgent

# Register agent
agent = A2AAgent(
    agent_id="creative_director_001",
    name="Creative Director",
    description="Lead creative strategy and quality",
    url="http://localhost:8001",
    version="1.0",
    capabilities=["strategy", "critique", "delegation"]
)
await mcp_layer.register_a2a_agent(agent)

# Delegate task to another agent
result = await mcp_layer.delegate_to_agent(
    agent_id="copywriter_001",
    task="Write headline for Nike campaign",
    context={"brand": "Nike", "tone": "energetic", "audience": "athletes"}
)
```

### MCP (Model Context Protocol)

```python
from aurora.protocols.mcp_layer import MCPLayer

# Connect to MCP server
await mcp_layer.connect_server("filesystem")

# Call tool
result = await mcp_layer.call_tool("filesystem", "read_file", {
    "path": "/path/to/file.png"
})

# Read resource
resource = await mcp_layer.read_resource("filesystem", "file:///path/to/file.png")
```

---

## Memory & Context

### Memory Types

| Type | Storage | Access | Use Case |
|------|---------|--------|----------|
| **Short-term** | Session cache | Immediate | Current task context |
| **Long-term** | ChromaDB | Semantic search | Historical knowledge |
| **Semantic** | Knowledge Graph | Graph traversal | Relationships |
| **Episodic** | SQLite | Time-based query | Past experiences |

### Context Management

```python
# Set project context
aurora.set_active_project(project)

# Load relevant memory
similar = await aurora.find_similar(media_id, limit=5)

# Query memory
result = await aurora.query(
    "What color palettes worked for Nike campaigns?",
    domain=IntelligenceDomain.VISUAL
)
```

---

## Tool Access

### Internal Tools

| Tool | Function | Module |
|------|----------|--------|
| `generate_image` | DALL-E 3 image generation | studio_agent |
| `analyze_image` | GPT-4o vision analysis | studio_agent |
| `process_image` | Resize, convert, compress | studio_agent |
| `research_topic` | Web research via GPT-4o | studio_agent |
| `save_project_brief` | Save project context | studio_agent |

### MCP Tools (External)

| Server | Tools | Category |
|--------|-------|----------|
| filesystem | read, write, search | Productivity |
| github | repos, PRs, issues | Development |
| postgres | query, schema | Database |
| playwright | browser automation | Testing |
| memory | remember, recall | AI Memory |
| sequential-thinking | structured reasoning | AI Reasoning |

### Tool Selection Logic

```
1. Is it a creative analysis task? → Use Intelligence Engines
2. Is it a media generation task? → Use generation tools
3. Is it a data query? → Use ERP modules
4. Is it an external tool? → Use MCP
5. Is it an agent delegation? → Use A2A
```

---

## Permission Model

### Role-Based Access Control (RBAC)

| Role | Permissions |
|------|-------------|
| Owner | All permissions |
| Admin | Organization management, all modules |
| Manager | Project management, team oversight |
| Creative Director | Creative approval, strategy |
| Designer | Asset creation, design tools |
| Developer | Code, integrations, API |
| Editor | Content editing, publishing |
| Researcher | Research, analysis |
| Client | View, approve |
| Viewer | Read-only |

### Attribute-Based Access Control (ABAC)

```python
# Check permission
if user.has_permission(org_id, Permission.ASSET_CREATE):
    # Allow asset creation
    pass

# Check role
if user.roles.get(org_id) == Role.DESIGNER:
    # Apply designer-specific logic
    pass
```

---

## Safety & Guardrails

### Content Safety
- All generated content is screened for harmful material
- Brand guidelines are enforced automatically
- Accessibility standards (WCAG 2.1 AA) are checked
- Cultural sensitivity is evaluated by Symbolism Intelligence

### AI Ethics
- No dark patterns in psychological persuasion
- Transparent AI decision-making
- User consent for observation features
- Data privacy and GDPR compliance

### Operational Safety
- Human approval checkpoints for critical actions
- Audit logging for all operations
- Rate limiting for API calls
- Error recovery and self-healing

### Guardrails Checklist
- [ ] Check permission before any write operation
- [ ] Validate content against brand guidelines
- [ ] Verify accessibility compliance
- [ ] Log all actions to audit trail
- [ ] Respect user privacy settings
- [ ] Provide transparent AI reasoning
- [ ] Offer human override for critical decisions

---

## Development Guide

### Creating a New Agent

```python
from aurora.core import IntelligenceEngine, IntelligenceDomain, CreativeInsight

class MyCustomAgent(IntelligenceEngine):
    def __init__(self):
        super().__init__(IntelligenceDomain.DESIGN)
    
    async def analyze(self, media, context=None):
        # Your analysis logic
        return [CreativeInsight(
            domain=self.domain,
            category="custom",
            finding="Your finding",
            confidence=0.85,
            evidence=["Evidence 1", "Evidence 2"],
            suggestions=["Suggestion 1"]
        )]
    
    async def critique(self, media, context=None):
        # Your critique logic
        return []
    
    async def improve(self, media, context=None):
        # Your improvement suggestions
        return []
```

### Creating a New Integration

```python
from aurora.protocols.mcp_layer import MCPLayer

# Register custom MCP server
await mcp_layer.connect_server("my_custom_server")

# Use custom tool
result = await mcp_layer.call_tool("my_custom_server", "my_tool", {
    "param1": "value1"
})
```

### Creating a New ERP Module

```python
from aurora.enterprise.erp import ERPCore

# Add custom data model
@dataclass
class CustomEntity:
    entity_id: str
    org_id: str
    name: str
    # ... custom fields

# Register with ERP core
erp.custom_entities = {}
erp.custom_entities["id"] = CustomEntity(...)
```

---

## Code Conventions

### File Naming
- Use lowercase with underscores: `creative_director.py`
- One class per file (generally)
- Test files: `test_creative_director.py`

### Code Style
```python
# Type hints required
async def analyze(self, media: MediaInterpretation, context: Optional[ProjectContext] = None) -> List[CreativeInsight]:
    """Analyze media and return insights."""
    pass

# Dataclasses for data models
@dataclass
class MyModel:
    field: str
    optional_field: Optional[str] = None

# Enums for fixed values
class Status(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
```

### Documentation
- All public functions must have docstrings
- Complex logic must have inline comments
- API endpoints must have OpenAPI specs
- Modules must have README files

### Testing
- Unit tests for all functions
- Integration tests for all modules
- E2E tests for critical workflows
- Minimum 80% code coverage

---

## Module Reference

### Core Modules

| Module | File | Purpose |
|--------|------|---------|
| AuroraCore | `aurora/core.py` | Central orchestration |
| CLI | `aurora/cli.py` | Command-line interface |
| Enterprise Core | `aurora/enterprise/core.py` | Multi-tenant + RBAC |
| ERP Core | `aurora/enterprise/erp.py` | 10 ERP modules |
| AI ERP | `aurora/enterprise/ai_erp.py` | AI reasoning |

### Intelligence Modules

| Module | File | Domain |
|--------|------|--------|
| Narrative | `aurora/intelligence/narrative.py` | Story, theme, structure |
| Visual | `aurora/intelligence/visual.py` | Composition, color, lighting |
| Symbolism | `aurora/intelligence/symbolism.py` | Cultural symbols, archetypes |
| Design | `aurora/intelligence/design.py` | Systems, accessibility |
| Marketing | `aurora/intelligence/marketing.py` | Positioning, funnel |
| Psychological | `aurora/intelligence/psychological.py` | Biases, persuasion |

### Infrastructure Modules

| Module | File | Purpose |
|--------|------|---------|
| Memory Graph | `aurora/memory/graph.py` | Knowledge storage |
| Universal Interpreter | `aurora/interpreters/universal.py` | Media ingestion |
| Live Observer | `aurora/observation/watcher.py` | Real-time monitoring |
| MCP Layer | `aurora/protocols/mcp_layer.py` | Tool integration |

---

## Quick Reference

### Common Operations

```python
# Initialize
aurora = AuroraCore()
await aurora.initialize()

# Create project
project = await aurora.create_project(name="Campaign", description="Q4 brand refresh")

# Interpret media
result = await aurora.interpret("asset.png")

# Query memory
answer = await aurora.query("What worked for Nike?")

# Start observation
await aurora.start_observation(["./designs"])

# Shutdown
await aurora.shutdown()
```

### CLI Commands

```bash
# Interpret media
python aurora/cli.py interpret asset.png --critique --improve

# Create project
python aurora/cli.py project create "Campaign" --audience "Gen Z"

# Live observation
python aurora/cli.py observe ./designs --interval 3

# Query memory
python aurora/cli.py query "Best color palettes for fintech?"

# Batch process
python aurora/cli.py batch ./assets --extensions png,jpg

# System status
python aurora/cli.py status
```

---

**Document Version:** 1.0.0-alpha
**Last Updated:** 2026-08-07
**Maintainer:** AGENCY OS Core Team