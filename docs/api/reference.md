# API Reference

**AGENCY OS — REST & GraphQL API**

---

## Base URL

```
http://localhost:8000/api/v1
```

---

## Authentication

All API requests require authentication via Bearer token or API key.

```bash
# Bearer token
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/status

# API key
curl -H "X-API-Key: ao_xxxxx" http://localhost:8000/api/v1/status
```

---

## REST Endpoints

### Interpret

#### POST /interpret

Interpret a media file through the intelligence pipeline.

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/interpret \
  -H "Authorization: Bearer <token>" \
  -F "file=@design.png" \
  -F "media_type=image" \
  -F "critique=true" \
  -F "improve=true"
```

**Response:**
```json
{
  "media_id": "media_abc123",
  "media_type": "image",
  "summary": "Modern minimalist design with warm amber palette",
  "quality_score": 8.4,
  "tags": ["image", "design", "minimalist", "warm"],
  "insights": [
    {
      "domain": "visual",
      "category": "composition",
      "finding": "Strong rule-of-thirds composition",
      "confidence": 0.85,
      "evidence": ["Focal point at intersection"],
      "suggestions": ["Maintain current composition"]
    }
  ],
  "timestamp": "2026-08-07T19:54:57Z"
}
```

#### GET /interpret/{media_id}

Retrieve a stored interpretation.

**Response:**
```json
{
  "media_id": "media_abc123",
  "media_type": "image",
  "summary": "Modern minimalist design",
  "quality_score": 8.4,
  "insights": [...],
  "tags": [...],
  "timestamp": "2026-08-07T19:54:57Z"
}
```

---

### Projects

#### POST /projects

Create a new project.

**Request:**
```json
{
  "name": "Q4 Campaign",
  "description": "Holiday brand refresh",
  "client_id": "client_123",
  "team_id": "team_456",
  "brief": "Campaign brief text...",
  "goals": ["awareness", "conversion"],
  "due_date": "2026-12-31"
}
```

**Response:**
```json
{
  "project_id": "proj_789",
  "name": "Q4 Campaign",
  "status": "planning",
  "created_at": "2026-08-07T19:54:57Z"
}
```

#### GET /projects

List all projects.

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `status` | string | Filter by status |
| `client_id` | string | Filter by client |
| `team_id` | string | Filter by team |
| `limit` | int | Max results (default: 50) |
| `offset` | int | Pagination offset |

#### GET /projects/{project_id}

Get project details.

#### PUT /projects/{project_id}

Update project.

#### DELETE /projects/{project_id}

Archive project.

---

### Query

#### POST /query

Query the creative memory graph.

**Request:**
```json
{
  "question": "What color palettes work for fintech?",
  "domain": "visual",
  "limit": 10
}
```

**Response:**
```json
{
  "answer": "Based on creative memory analysis...",
  "sources": [
    {
      "media_id": "media_abc",
      "relevance": 0.92,
      "summary": "Fintech app with blue/teal palette"
    }
  ],
  "confidence": 0.85
}
```

---

### Observe

#### POST /observe

Start live observation.

**Request:**
```json
{
  "targets": ["./designs", "./assets"],
  "interval": 5.0,
  "auto_analyze": true,
  "auto_critique": true
}
```

**Response:**
```json
{
  "observation_id": "obs_001",
  "status": "active",
  "targets": ["./designs", "./assets"],
  "started_at": "2026-08-07T19:54:57Z"
}
```

#### DELETE /observe/{observation_id}

Stop observation.

#### GET /observe/{observation_id}/events

Get observation events.

---

### ERP

#### GET /erp/invoices

List invoices.

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `status` | string | draft, sent, paid, overdue |
| `client_id` | string | Filter by client |
| `min_amount` | float | Minimum amount |
| `max_amount` | float | Maximum amount |

#### POST /erp/invoices

Create invoice.

**Request:**
```json
{
  "client_id": "client_123",
  "items": [
    {"description": "Design work", "quantity": 1, "rate": 5000}
  ],
  "tax": 0.08,
  "due_date": "2026-09-07"
}
```

#### GET /erp/finance/summary

Get financial summary.

**Response:**
```json
{
  "total_revenue": 125000.00,
  "outstanding": 45000.00,
  "overdue": 15000.00,
  "pipeline_value": 340000.00,
  "weighted_pipeline": 180000.00,
  "monthly_recurring": 35000.00
}
```

#### GET /erp/crm/pipeline

Get CRM pipeline.

**Response:**
```json
{
  "stages": {
    "prospecting": {"count": 5, "value": 250000},
    "proposal": {"count": 3, "value": 180000},
    "negotiation": {"count": 2, "value": 120000},
    "won": {"count": 8, "value": 450000}
  },
  "total_value": 1000000,
  "weighted_value": 485000
}
```

#### GET /erp/hr/utilization

Get team utilization.

**Response:**
```json
{
  "total_employees": 12,
  "active_employees": 10,
  "total_capacity_hours": 1920,
  "allocated_hours": 1536,
  "utilization_rate": 0.80,
  "overloaded_members": []
}
```

#### POST /erp/ai/query

AI-powered ERP reasoning.

**Request:**
```json
{
  "question": "Which clients are likely to churn?"
}
```

**Response:**
```json
{
  "type": "churn_prediction",
  "at_risk_clients": [
    {
      "client_id": "client_456",
      "risk_score": 0.75,
      "signals": ["Overdue invoice", "Low payment ratio"],
      "recommended_action": "Schedule check-in call"
    }
  ],
  "total_clients": 25,
  "risk_count": 3
}
```

---

### Batch

#### POST /batch

Batch process a directory.

**Request:**
```json
{
  "directory": "./assets",
  "extensions": ["png", "jpg", "webp"],
  "critique": true,
  "improve": true
}
```

**Response:**
```json
{
  "batch_id": "batch_001",
  "total_files": 45,
  "processed": 45,
  "failed": 0,
  "results": [
    {"file": "design1.png", "media_id": "media_001", "quality": 8.2}
  ]
}
```

---

### Status

#### GET /status

Get system status.

**Response:**
```json
{
  "version": "1.0.0-alpha",
  "status": "healthy",
  "uptime": "2d 5h 30m",
  "components": {
    "memory": "connected",
    "intelligence_engines": "6/6 active",
    "erp_modules": "10/10 active",
    "mcp_servers": "2/12 connected"
  },
  "stats": {
    "total_interpretations": 1247,
    "total_projects": 28,
    "total_assets": 3891
  }
}
```

---

## GraphQL API

### Endpoint

```
http://localhost:8000/graphql
```

### Schema

```graphql
type Query {
  # Interpretation
  interpretation(id: ID!): Interpretation
  interpretations(limit: Int, offset: Int): [Interpretation!]!

  # Projects
  project(id: ID!): Project
  projects(status: String, limit: Int): [Project!]!

  # Memory
  query(question: String!, domain: String, limit: Int): QueryResult!

  # ERP
  invoices(status: String, clientId: String): [Invoice!]!
  contacts(limit: Int): [Contact!]!
  opportunities(stage: String): [Opportunity!]!

  # Status
  status: SystemStatus!
}

type Mutation {
  # Interpretation
  interpret(file: Upload!, mediaType: String, critique: Boolean): Interpretation!

  # Projects
  createProject(input: ProjectInput!): Project!
  updateProject(id: ID!, input: ProjectInput!): Project!

  # Observation
  startObservation(targets: [String!]!, interval: Float): Observation!
  stopObservation(id: ID!): Boolean!

  # ERP
  createInvoice(input: InvoiceInput!): Invoice!
  createContact(input: ContactInput!): Contact!
  createLead(input: LeadInput!): Lead!
}

type Interpretation {
  id: ID!
  mediaType: String!
  summary: String!
  qualityScore: Float!
  tags: [String!]!
  insights: [Insight!]!
  timestamp: String!
}

type Insight {
  domain: String!
  category: String!
  finding: String!
  confidence: Float!
  evidence: [String!]!
  suggestions: [String!]!
}

type Project {
  id: ID!
  name: String!
  description: String
  status: String!
  progress: Float!
  assets: [Interpretation!]!
  tasks: [Task!]!
  createdAt: String!
}

type Invoice {
  id: ID!
  number: String!
  status: String!
  total: Float!
  amountPaid: Float!
  balance: Float!
  dueDate: String
}

type SystemStatus {
  version: String!
  status: String!
  components: JSON!
  stats: JSON!
}

type QueryResult {
  answer: String!
  sources: [Source!]!
  confidence: Float!
}

type Source {
  mediaId: ID!
  relevance: Float!
  summary: String!
}
```

### Example Queries

```graphql
# Get project with assets
query {
  project(id: "proj_123") {
    name
    status
    assets {
      id
      summary
      qualityScore
      insights {
        domain
        finding
        confidence
      }
    }
  }
}

# Query memory
query {
  query(question: "Best colors for fintech?", domain: "visual", limit: 5) {
    answer
    sources {
      mediaId
      relevance
      summary
    }
  }
}

# Get invoices
query {
  invoices(status: "sent") {
    id
    number
    total
    balance
    dueDate
  }
}
```

### Example Mutations

```graphql
# Create project
mutation {
  createProject(input: {
    name: "Q4 Campaign"
    description: "Holiday brand refresh"
    goals: ["awareness", "conversion"]
  }) {
    id
    name
    status
  }
}

# Interpret media
mutation {
  interpret(file: "design.png", critique: true) {
    id
    summary
    qualityScore
    insights {
      domain
      finding
    }
  }
}
```

---

## WebSocket API

### Endpoint

```
ws://localhost:8000/ws
```

### Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `observation.event` | Server → Client | File change detected |
| `interpretation.complete` | Server → Client | Interpretation finished |
| `insight.generated` | Server → Client | New insight available |
| `subscribe` | Client → Server | Subscribe to channel |
| `unsubscribe` | Client → Server | Unsubscribe |

### Example

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'observation.event') {
    console.log('File changed:', data.file);
    console.log('Insights:', data.insights);
  }
};

// Subscribe to observation events
ws.send(JSON.stringify({
  action: 'subscribe',
  channel: 'observation.obs_001'
}));
```

---

## Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| 200 | OK | Success |
| 201 | Created | Resource created |
| 400 | Bad Request | Invalid input |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Permission denied |
| 404 | Not Found | Resource not found |
| 429 | Rate Limited | Too many requests |
| 500 | Server Error | Internal error |

### Error Response Format

```json
{
  "error": {
    "code": 400,
    "message": "Invalid media type",
    "details": "Unsupported file format: .xyz",
    "request_id": "req_abc123"
  }
}
```

---

## Rate Limits

| Plan | Requests/Minute | Burst |
|------|-----------------|-------|
| Starter | 60 | 100 |
| Professional | 300 | 500 |
| Enterprise | Unlimited | Unlimited |

---

**For implementation details, see the [Source Code](../aurora/api/).**