# Configuration Guide

**AGENCY OS — Complete Configuration Reference**

---

## Table of Contents

1. [Environment Variables](#environment-variables)
2. [MCP Server Configuration](#mcp-server-configuration)
3. [AI Provider Configuration](#ai-provider-configuration)
4. [Enterprise Settings](#enterprise-settings)
5. [Module Configuration](#module-configuration)
6. [Security Configuration](#security-configuration)
7. [Integration Configuration](#integration-configuration)
8. [Performance Tuning](#performance-tuning)

---

## Environment Variables

### Core Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `AGENCY_OS_HOME` | Data directory | `~/.agencyos` | No |
| `AGENCY_OS_LOG_LEVEL` | Log level | `INFO` | No |
| `AGENCY_OS_MODEL` | Default AI model | `gpt-4o` | No |
| `AGENCY_OS_OUTPUT` | Default output format | `text` | No |
| `AGENCY_OS_DATA_DIR` | Enterprise data directory | `./agency_os_data` | No |
| `AURORA_MEMORY_DIR` | Memory storage directory | `./aurora_memory` | No |

### AI Provider Keys

| Variable | Description | Provider |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key | OpenAI (GPT-4o, DALL-E 3, Whisper) |
| `OPENAI_ORG_ID` | OpenAI organization ID | OpenAI |
| `OPENAI_PROJECT_ID` | OpenAI project ID | OpenAI |
| `ANTHROPIC_API_KEY` | Anthropic API key | Anthropic (Claude) |
| `GOOGLE_API_KEY` | Google AI Studio key | Google (Gemini) |
| `GOOGLE_GENAI_API_KEY` | Google GenAI key | Google (Gemini) |
| `GOOGLE_GENAI_USE_VERTEXAI` | Use Vertex AI | Google |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID | Google Vertex |
| `GOOGLE_CLOUD_LOCATION` | GCP region | `us-central1` |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI key | Azure |
| `AZURE_OPENAI_ENDPOINT` | Azure endpoint URL | Azure |
| `AZURE_OPENAI_DEPLOYMENT` | Azure deployment name | Azure |
| `MISTRAL_API_KEY` | Mistral API key | Mistral |
| `XAI_API_KEY` | xAI API key | xAI (Grok) |

### Studio Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `STUDIO_OUTPUT_DIR` | Output directory | `./output` |
| `STUDIO_TEMP_DIR` | Temporary files directory | `./tmp` |
| `STUDIO_LOG_LEVEL` | Log level | `INFO` |

---

## MCP Server Configuration

### Config File: `.mcp.json`

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "./"],
      "transport": "stdio"
    },
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp@latest"],
      "transport": "stdio"
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "transport": "stdio",
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_xxx"
      }
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "transport": "stdio",
      "env": {
        "POSTGRESQL_CONNECTION_STRING": "postgresql://user:pass@localhost/db"
      }
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"],
      "transport": "stdio"
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"],
      "transport": "stdio"
    },
    "fetch": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-fetch"],
      "transport": "stdio"
    },
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "transport": "stdio",
      "env": {
        "BRAVE_API_KEY": "your-brave-key"
      }
    },
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
      "transport": "stdio"
    },
    "slack": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-slack"],
      "transport": "stdio",
      "env": {
        "SLACK_BOT_TOKEN": "xoxb-xxx",
        "SLACK_TEAM_ID": "T00000000"
      }
    }
  }
}
```

### Transport Types

| Transport | Description | Use Case |
|-----------|-------------|----------|
| `stdio` | Standard input/output | Local servers |
| `http` | HTTP endpoints | Remote servers |
| `websocket` | WebSocket connections | Real-time servers |

---

## AI Provider Configuration

### Model Selection

Default model routing by task:

| Task | Primary | Fallback |
|------|---------|----------|
| Image Analysis | GPT-4o | Claude 3.5 Sonnet |
| Text Generation | GPT-4o | Claude 3.5 Sonnet |
| Image Generation | DALL-E 3 | - |
| Audio Transcription | Whisper | - |
| Vector Embeddings | text-embedding-3-small | all-MiniLM-L6-v2 |
| Video Analysis | GPT-4o | Gemini 1.5 Pro |

### Custom Model Routing

Create `~/.agencyos/models.yaml`:

```yaml
models:
  default: gpt-4o
  fallback: claude-3-5-sonnet

  routing:
    image_analysis:
      primary: gpt-4o
      fallback: claude-3-5-sonnet
    text_generation:
      primary: gpt-4o
      fallback: claude-3-5-sonnet
    image_generation:
      primary: dall-e-3
    transcription:
      primary: whisper-1
    embeddings:
      primary: text-embedding-3-small
      local: all-MiniLM-L6-v2

  providers:
    openai:
      api_key: ${OPENAI_API_KEY}
      org_id: ${OPENAI_ORG_ID}
    anthropic:
      api_key: ${ANTHROPIC_API_KEY}
    google:
      api_key: ${GOOGLE_API_KEY}
```

---

## Enterprise Settings

### Plan Limits

| Plan | Projects | Storage | Members | Workflows | Agents |
|------|----------|---------|---------|-----------|--------|
| Starter | 10 | 50GB | 10 | 20 | 10 |
| Professional | 50 | 500GB | 50 | 100 | 50 |
| Enterprise | Unlimited | Unlimited | Unlimited | Unlimited | Unlimited |

### RBAC Configuration

```yaml
roles:
  owner:
    permissions: ["*"]
  admin:
    permissions:
      - "org:*"
      - "project:*"
      - "asset:*"
      - "workflow:*"
      - "agent:*"
  manager:
    permissions:
      - "org:read"
      - "project:*"
      - "asset:*"
      - "workflow:*"
  designer:
    permissions:
      - "org:read"
      - "project:read"
      - "asset:create"
      - "asset:read"
      - "asset:write"
```

---

## Module Configuration

### Intelligence Engines

```yaml
intelligence:
  engines:
    narrative:
      enabled: true
      model: gpt-4o
      min_confidence: 0.6
    visual:
      enabled: true
      model: gpt-4o
      min_confidence: 0.6
    symbolism:
      enabled: true
      model: gpt-4o
      min_confidence: 0.5
    design:
      enabled: true
      model: gpt-4o
      accessibility_level: AA
    marketing:
      enabled: true
      model: gpt-4o
    psychological:
      enabled: true
      model: gpt-4o
      ethics_check: true

  auto_critique: true
  auto_improve: true
  batch_size: 10
```

### Observation

```yaml
observation:
  enabled: true
  interval: 5.0        # Check interval in seconds
  debounce: 2.0        # Debounce time in seconds
  auto_analyze: true
  auto_critique: true
  auto_improve: true
  watch_patterns:
    - "*.png"
    - "*.jpg"
    - "*.mp4"
    - "*.fig"
  ignore_patterns:
    - "node_modules/*"
    - ".git/*"
    - "tmp/*"
```

### Memory

```yaml
memory:
  persist_dir: ./aurora_memory
  vector_store: chromadb
  embedding_model: all-MiniLM-L6-v2
  auto_link: true
  similarity_threshold: 0.75
  max_results: 10
  ttl: null  # null = never expire
```

---

## Security Configuration

### Authentication

```yaml
auth:
  session_ttl: 604800  # 7 days in seconds
  refresh_ttl: 2592000  # 30 days
  max_sessions: 5
  mfa_required: false
  password_min_length: 8
  password_require_uppercase: true
  password_require_numbers: true
  password_require_symbols: false
```

### Encryption

```yaml
encryption:
  at_rest: AES-256
  in_transit: TLS-1.3
  key_rotation_days: 90
```

### Rate Limiting

```yaml
rate_limit:
  requests_per_minute: 60
  burst: 100
  per_user: true
  per_org: true
```

---

## Integration Configuration

### Adobe Creative Cloud

```yaml
adobe:
  client_id: your-adobe-client-id
  client_secret: your-adobe-client-secret
  scopes:
    - "openid"
    - "creative_sdk"
  services:
    - photoshop
    - illustrator
    - premiere
    - after_effects
```

### Figma

```yaml
figma:
  access_token: your-figma-token
  team_id: your-team-id
  webhook_enabled: true
```

### GitHub

```yaml
github:
  token: ghp_xxx
  org: your-org
  webhook_secret: your-secret
```

### Slack

```yaml
slack:
  bot_token: xoxb-xxx
  app_token: xapp-xxx
  signing_secret: your-secret
```

---

## Performance Tuning

### Caching

```yaml
cache:
  enabled: true
  backend: memory  # memory, redis
  ttl: 3600  # seconds
  max_size: 1000
  redis_url: redis://localhost:6379
```

### Workers

```yaml
workers:
  count: 4
  max_concurrent: 10
  timeout: 300  # seconds
  retry_count: 3
```

### Database

```yaml
database:
  url: sqlite:///agency_os.db
  # For PostgreSQL:
  # url: postgresql://user:pass@localhost/agency_os
  pool_size: 10
  max_overflow: 20
  echo: false
```

### GPU (for local models)

```yaml
gpu:
  enabled: false
  device: cuda  # cuda, mps, cpu
  memory_limit: 8192  # MB
  batch_size: 4
```

---

## Complete Example Configuration

```yaml
# ~/.agencyos/config.yaml

# Core
home: ~/.agencyos
log_level: INFO
default_model: gpt-4o

# Intelligence
intelligence:
  auto_critique: true
  auto_improve: true
  min_confidence: 0.6

# Memory
memory:
  persist_dir: ~/.agencyos/memory
  auto_link: true
  similarity_threshold: 0.75

# Observation
observation:
  interval: 5.0
  debounce: 2.0
  auto_analyze: true

# Security
auth:
  session_ttl: 604800
  mfa_required: false

# Performance
cache:
  enabled: true
  ttl: 3600
workers:
  count: 4
```

---

**For environment-specific configuration, see [Getting Started](../guides/getting-started.md).**