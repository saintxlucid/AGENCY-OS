# Architecture Overview

**AGENCY OS — System Architecture**
Version 1.0.0-alpha

---

## System Design

AGENCY OS follows a **layered microservices architecture** with clear separation of concerns. Each layer can be scaled independently.

### Layer Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                             │
│                                                                         │
│   CLI              Web UI           Mobile         Desktop             │
│   (Python)         (React)          (React Native)  (Electron)          │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                          GATEWAY LAYER                                  │
│                                                                         │
│   API Gateway  │  Auth  │  Rate Limiting  │  Load Balancing            │
│   REST API     │  JWT   │  Throttling     │  Routing                   │
│   GraphQL      │  OAuth │  Caching        │  WebSocket                 │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                       INTELLIGENCE LAYER                                │
│                                                                         │
│   ┌──────────────────────────────────────────────────────────────┐     │
│   │              Multi-Agent Orchestration                        │     │
│   │  Planning │ Reflection │ Critique │ Self-Correction          │     │
│   └──────────────────────────────────────────────────────────────┘     │
│                                                                         │
│   ┌──────────────────────────────────────────────────────────────┐     │
│   │              6 Intelligence Engines                           │     │
│   │  Narrative │ Visual │ Symbolism │ Design │ Marketing │ Psych │     │
│   └──────────────────────────────────────────────────────────────┘     │
│                                                                         │
│   ┌──────────────────────────────────────────────────────────────┐     │
│   │              AI ERP Layer                                     │     │
│   │  Churn Prediction │ Revenue Forecast │ Capacity Analysis     │     │
│   │  Profitability    │ Sales Forecast   │ Risk Assessment       │     │
│   └──────────────────────────────────────────────────────────────┘     │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                          ERP LAYER                                     │
│                                                                         │
│   CRM │ Projects │ Finance │ HR │ Assets │ Production │ Sales        │
│   Operations │ Procurement │ Knowledge                               │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                         CORE LAYER                                     │
│                                                                         │
│   Organizations │ Teams │ Workspaces │ Projects │ Clients            │
│   RBAC │ Audit │ Auth │ Billing │ Notifications                     │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                         MEMORY LAYER                                   │
│                                                                         │
│   ChromaDB (Vector Search) │ NetworkX (Knowledge Graph)               │
│   SQLite (Metadata)        │ Object Storage (Assets)                  │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                      INTEGRATION LAYER                                 │
│                                                                         │
│   MCP Protocol │ A2A Protocol │ REST APIs │ Webhooks │ SDKs          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### Presentation Layer

| Component | Technology | Status |
|-----------|-----------|--------|
| CLI | Python (Click) | ✅ Implemented |
| Web UI | React + TypeScript | 🚧 Planned |
| Desktop | Electron | 📋 Planned |
| Mobile | React Native | 📋 Planned |

### Gateway Layer

| Component | Technology | Status |
|-----------|-----------|--------|
| REST API | FastAPI | 🚧 Planned |
| GraphQL | Strawberry | 📋 Planned |
| WebSocket | FastAPI WS | 📋 Planned |
| Auth | JWT + OAuth2 | 🚧 Planned |

### Intelligence Layer

| Component | File | Status |
|-----------|------|--------|
| Narrative Engine | `intelligence/narrative.py` | ✅ |
| Visual Engine | `intelligence/visual.py` | ✅ |
| Symbolism Engine | `intelligence/symbolism.py` | ✅ |
| Design Engine | `intelligence/design.py` | ✅ |
| Marketing Engine | `intelligence/marketing.py` | ✅ |
| Psychological Engine | `intelligence/psychological.py` | ✅ |
| AI ERP Layer | `enterprise/ai_erp.py` | ✅ |

### Memory Layer

| Component | Technology | Status |
|-----------|-----------|--------|
| Vector Store | ChromaDB | ✅ |
| Knowledge Graph | NetworkX | ✅ |
| Metadata | SQLite | ✅ |
| Object Storage | Local/S3 | 🚧 |

---

## Data Flow

### Interpretation Pipeline

```
Input → Detect Type → Extract Content → Intelligence Engines → Insights
                                                          ↓
                                                    Memory Store
                                                          ↓
                                                    Auto-Linking
                                                          ↓
                                                    Knowledge Graph
```

### ERP Reasoning Pipeline

```
Question → Intent Detection → Data Aggregation → AI Reasoning → Insight
                                                              ↓
                                                        Actions
                                                              ↓
                                                        Notification
```

### Observation Pipeline

```
File Change → Debounce → Interpret → Critique → Improve → Notify
                                                    ↓
                                              Memory Update
```

---

## Scalability

### Horizontal Scaling

```
                    Load Balancer
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   API Server 1   API Server 2   API Server N
        │                │                │
        └────────────────┼────────────────┘
                         │
                    Redis Cache
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   Worker 1        Worker 2        Worker N
        │                │                │
        └────────────────┼────────────────┘
                         │
              PostgreSQL + ChromaDB
```

### Multi-Tenancy

- **Organization Isolation:** Each org has separate data namespace
- **Team Isolation:** Teams within org have scoped access
- **Workspace Isolation:** Workspaces contain project-specific data

---

## Security Architecture

```
┌─────────────────────────────────────────────┐
│                 User Request                 │
└───────────────────┬─────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│              API Gateway                     │
│  ┌─────────┐ ┌─────────┐ ┌──────────────┐  │
│  │   JWT   │ │  OAuth  │ │  API Key     │  │
│  │  Auth   │ │  2.0    │ │  Validation  │  │
│  └─────────┘ └─────────┘ └──────────────┘  │
└───────────────────┬─────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│            RBAC/ABAC Engine                  │
│  ┌──────────────┐ ┌────────────────────┐    │
│  │  Role Check  │ │  Attribute Check   │    │
│  └──────────────┘ └────────────────────┘    │
└───────────────────┬─────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│             Service Layer                    │
│  ┌──────────────┐ ┌────────────────────┐    │
│  │ Permission   │ │  Data Isolation    │    │
│  │ Enforcement  │ │  (Org/Team/WS)     │    │
│  └──────────────┘ └────────────────────┘    │
└─────────────────────────────────────────────┘
```

---

## Deployment Architecture

### Development

```
Local Machine
├── Python 3.10+
├── ChromaDB (local)
├── SQLite (local)
└── .env (API keys)
```

### Production (Docker)

```
Docker Compose / Kubernetes
├── API Servers (FastAPI + Uvicorn)
├── Workers (Celery / ARQ)
├── PostgreSQL (primary DB)
├── ChromaDB (vector store)
├── Redis (cache + queue)
├── Object Storage (S3/MinIO)
├── Monitoring (Prometheus + Grafana)
└── Log Aggregation (Loki / ELK)
```

### Production (Cloud)

```
Cloud Provider (AWS/GCP/Azure)
├── EKS/GKE/AKS (Kubernetes)
├── RDS/Cloud SQL (PostgreSQL)
├── ElastiCache/Memorystore (Redis)
├── S3/GCS (Object Storage)
├── CloudFront/CDN (CDN)
├── CloudWatch/Stackdriver (Monitoring)
└── Secrets Manager (Secrets)
```