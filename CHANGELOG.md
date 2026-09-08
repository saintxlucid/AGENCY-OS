# Changelog

**AGENCY OS — Version History**

---

## [1.0.0-alpha] — 2026-08-07

### Added

#### Core Platform
- Multi-tenant architecture with Organizations, Teams, Workspaces, Projects, Clients
- RBAC permission system with 11 roles (Owner, Admin, Manager, Creative Director, Designer, Developer, Editor, Researcher, Client, Viewer, Billing)
- Session and API key authentication
- Complete audit logging
- Plan-based limits (Starter, Professional, Enterprise)
- Data persistence and loading

#### Creative Intelligence
- **Narrative Intelligence** — Story structure, character arcs, emotional arcs, themes, pacing
- **Visual Intelligence** — Composition, color theory, lighting, hierarchy, typography
- **Symbolism Intelligence** — Cultural symbols, brand archetypes, luxury cues, hidden meaning
- **Design Intelligence** — Design systems, WCAG compliance, UI patterns, tokens
- **Marketing Intelligence** — Positioning, audience alignment, messaging, funnel stage
- **Psychological Intelligence** — Cognitive biases, persuasion principles, attention, memory, ethics

#### Memory System
- CreativeMemoryGraph with ChromaDB vector search
- NetworkX knowledge graph for relationship mapping
- Auto-linking of similar media
- Semantic search across all interpretations
- Project timeline tracking
- Persistent storage

#### Media Processing
- Universal Media Interpreter supporting 9 media types
- Image analysis (PNG, JPG, WEBP, GIF, TIFF, SVG)
- Video analysis (MP4, MOV, AVI, MKV, WEBM)
- Audio analysis (MP3, WAV, FLAC, AAC, OGG)
- Document analysis (PDF, DOCX, TXT, MD)
- Code analysis (PY, JS, TS, HTML, CSS)
- Design file support (FIG, SKETCH, XD, PSD, AI)
- 3D model support (BLEND, FBX, OBJ, STL)
- Project file support (AEPPRPROJ, DRP, FLP)

#### Live Observation
- File system watching with watchdog
- Debounced change detection
- Real-time critique and improvement
- Application-level observation (extensible)
- Event history and callbacks

#### MCP/A2A Protocol Layer
- MCP client supporting stdio, HTTP, and WebSocket transports
- Tool registry and auto-discovery
- Resource and prompt templates
- A2A agent registration and delegation
- JSON-RPC 2.0 communication

#### ERP Modules (10 modules, 30+ entities)
- **CRM** — Leads, Opportunities, Contacts, Meetings
- **Project ERP** — Tasks, Campaigns, Time Entries, Milestones
- **Finance ERP** — Invoices, Expenses, Quotes, Purchase Orders
- **HR** — Employees, Candidates, Leave Requests, Performance
- **Asset ERP** — Digital/Physical assets, maintenance, QR tracking
- **Production ERP** — Productions, Shoot Days, Crew, Equipment
- **Procurement** — Vendors, Purchase Orders, Inventory
- **Knowledge ERP** — SOPs, Playbooks, Lessons, Templates
- **Sales ERP** — Deals, Pipeline, Scoring, Forecasting
- **Operations ERP** — Capacity Plans, Risks, KPIs

#### AI ERP Layer
- Natural language reasoning over all agency data
- Churn prediction (payment delays, engagement patterns)
- Revenue forecasting (historical + pipeline)
- Capacity analysis (utilization, overload detection)
- Profitability analysis (per-project, per-client)
- Sales forecasting (win probability, pipeline value)
- Team performance (completion rates, hours, skills)
- Auto-generated insights (financial, operational, risk)

#### CLI
- `interpret` — Media interpretation with critique/improvement
- `project` — Project creation and management
- `observe` — Live creative observation
- `query` — Natural language memory queries
- `batch` — Directory batch processing
- `status` — System status and diagnostics
- `export` — Data export to external formats
- `mcp` — MCP server management

#### Prompts & Templates
- Brand Identity prompt template
- Design System prompt template
- Image Generation prompt builder
- Design Critique framework
- Research & Trend Analysis template

### Technical
- Python 3.10+ compatibility
- Async/await throughout
- ChromaDB for vector storage
- NetworkX for knowledge graph
- Sentence Transformers for embeddings
- Watchdog for file monitoring
- MCP SDK for protocol support
- Pandas-compatible data models
- JSON serialization throughout
- Modular architecture (each engine independent)

### Dependencies
- openai>=2.53.0
- anthropic>=0.120.2
- google-adk>=2.6.2
- mcp>=1.29.0
- chromadb>=1.5.9
- sentence-transformers>=5.7.0
- networkx>=3.6
- pillow>=12.3.0
- python-dotenv>=1.2.2
- httpx>=0.28.1
- websockets>=15.0.1
- watchdog>=6.0.0

---

## [0.9.0-beta] — 2026-08-06

### Added
- Initial intelligence engines (Visual, Narrative)
- Basic memory graph with ChromaDB
- First CLI commands (interpret, query)
- MCP protocol layer foundation
- Studio agent with image generation

---

## [0.8.0-alpha] — 2026-08-05

### Added
- AuroraCore orchestration engine
- Universal Media Interpreter prototype
- Basic file type detection
- First intelligence engine (Visual)

---

## Release Cycle

AGENCY OS follows semantic versioning:

- **Patch (0.0.x):** Bug fixes, documentation
- **Minor (0.x.0):** New features, modules, engines
- **Major (x.0.0):** Breaking changes, major releases

### Support

| Version | Status | Support Until |
|---------|--------|---------------|
| 1.0.0-alpha | Current | Active development |
| 0.9.0-beta | Legacy | 2026-09-01 |
| 0.8.0-alpha | Legacy | 2026-08-15 |

---

## Upcoming

### Beta (Planned)
- REST API (FastAPI)
- GraphQL API
- Web UI (React)
- Real-time collaboration (WebSocket)
- Figma integration
- Adobe Creative Cloud integration
- Advanced workflow builder
- Agent marketplace
- SSO / SAML / OAuth2

### v1.0 (Planned)
- Production-ready release
- Mobile companion app
- Desktop app (Electron)
- Industry packs (15 verticals)
- SOC 2 compliance
- Kubernetes deployment
- GPU scheduling

### Enterprise (Planned)
- Private deployments
- White labeling
- Advanced security (SOC 2, GDPR, HIPAA)
- Global CDN
- Dedicated support

---

**Full documentation at [docs/](.)**