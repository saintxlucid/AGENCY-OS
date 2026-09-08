# Getting Started Guide

**AGENCY OS — From Zero to First Insight**

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Your First Interpretation](#your-first-interpretation)
5. [Creating a Project](#creating-a-project)
6. [Using the CLI](#using-the-cli)
7. [Using the API](#using-the-api)
8. [Next Steps](#next-steps)

---

## Prerequisites

Before installing AGENCY OS, ensure you have:

- **Python 3.10+** installed
- **pip** or **uv** package manager
- API keys for at least one AI provider:
  - [OpenAI API Key](https://platform.openai.com/api-keys) (GPT-4o, DALL-E 3)
  - [Anthropic API Key](https://console.anthropic.com/) (Claude)
  - [Google AI Key](https://aistudio.google.com/) (Gemini)
- **8GB+ RAM** recommended
- **5GB+ disk space** for models and data

---

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/agency-os/agency-os.git
cd agency-os
```

### Step 2: Create Virtual Environment

```bash
# Using venv
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Or using uv (faster)
uv venv
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Verify Installation

```bash
python -c "from aurora.core import AuroraCore; print('✅ AGENCY OS installed')"
```

---

## Configuration

### Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your API keys:

```env
# ─── AI Provider Keys ───
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
GOOGLE_API_KEY=your-google-ai-key-here

# ─── Azure OpenAI (Optional) ───
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_DEPLOYMENT=

# ─── Google Cloud / Vertex AI (Optional) ───
GOOGLE_GENAI_USE_VERTEXAI=false
GOOGLE_CLOUD_PROJECT=
GOOGLE_CLOUD_LOCATION=us-central1

# ─── Studio Settings ───
STUDIO_OUTPUT_DIR=./output
STUDIO_TEMP_DIR=./tmp
STUDIO_LOG_LEVEL=INFO

# ─── Enterprise Settings ───
AGENCY_OS_DATA_DIR=./agency_os_data
AURORA_MEMORY_DIR=./aurora_memory
```

### MCP Server Configuration

Edit `.mcp.json` to configure external tool servers:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "./"]
    },
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp@latest"]
    }
  }
}
```

---

## Your First Interpretation

### Using Python

```python
import asyncio
from aurora.core import AuroraCore

async def main():
    # Initialize
    aurora = AuroraCore()
    await aurora.initialize()

    # Interpret an image
    interpretation = await aurora.interpret("path/to/your/image.png")

    # Print results
    print(f"Media ID: {interpretation.media_id}")
    print(f"Summary: {interpretation.summary}")
    print(f"Quality: {interpretation.quality_score}/10")
    print(f"Tags: {', '.join(interpretation.tags)}")

    for insight in interpretation.insights:
        print(f"  [{insight.domain.value}] {insight.finding}")

    await aurora.shutdown()

asyncio.run(main())
```

### Using CLI

```bash
# Interpret a single file
python aurora/cli.py interpret design.png --critique --improve

# Batch process a directory
python aurora/cli.py batch ./assets --extensions png,jpg,webp

# Query creative memory
python aurora/cli.py query "What colors work for tech brands?" --domain visual
```

---

## Creating a Project

### Step 1: Create Organization

```python
from aurora.enterprise.core import EnterpriseCore

core = EnterpriseCore()

# Create owner
owner = core.create_user("you@agency.com", "Your Name", "securepassword")

# Create organization
org = core.create_organization(
    name="Your Agency",
    owner_id=owner.user_id,
    plan="professional"
)
```

### Step 2: Create Project

```python
# Create team
team = core.create_team(org.org_id, "Design Team", owner.user_id)

# Create client
client = core.create_client(org.org_id, "Nike", industry="Sports")

# Create project
project = core.create_project(
    org_id=org.org_id,
    name="Q4 Campaign",
    client_id=client.client_id,
    team_id=team.team_id,
    brief="Holiday campaign for new shoe line",
    owner_id=owner.user_id
)
```

### Step 3: Set Up Workspace

```bash
# Create workspace
python aurora/cli.py project create "Q4 Campaign" \
    --audience "Athletes 18-35" \
    --goals "awareness,conversion,brand-loyalty"
```

---

## Using the CLI

### Core Commands

```bash
# Interpret media
python aurora/cli.py interpret <file> [--type TYPE] [--critique] [--improve]

# Project management
python aurora/cli.py project <action> [--name NAME] [--audience AUDIENCE]

# Live observation
python aurora/cli.py observe <targets...> [--interval SECONDS]

# Query memory
python aurora/cli.py query "question" [--domain DOMAIN]

# Batch processing
python aurora/cli.py batch <directory> [--extensions ext1,ext2]

# System status
python aurora/cli.py status
```

### Media Types

| Type | Extensions | Intelligence |
|------|-----------|--------------|
| Image | .png, .jpg, .webp, .gif | Visual, Symbolism, Design |
| Video | .mp4, .mov, .avi, .mkv | Narrative, Visual, Marketing |
| Audio | .mp3, .wav, .flac | Narrative, Marketing |
| Document | .pdf, .docx, .txt | Design, Marketing |
| Code | .py, .js, .ts, .html | Design |
| Design | .fig, .sketch, .xd | Visual, Symbolism, Design |
| 3D | .blend, .fbx, .obj | Visual |
| Project | .aep, .prproj, .flp | All domains |

### Intelligence Domains

| Domain | Question | Use Case |
|--------|----------|----------|
| Narrative | Story structure, pacing | Video, campaigns |
| Visual | Composition, color, lighting | Images, designs |
| Symbolism | Hidden meaning, archetypes | Brand assets |
| Design | Systems, accessibility | UI, web |
| Marketing | Positioning, conversion | Campaigns |
| Psychological | Persuasion, bias | Copy, ads |

---

## Using the API

### Initialize

```python
import asyncio
from aurora.core import AuroraCore

aurora = AuroraCore()
await aurora.initialize()
```

### Interpret Media

```python
result = await aurora.interpret("asset.png")
# Returns: MediaInterpretation with insights, tags, quality_score
```

### Query Memory

```python
answer = await aurora.query(
    "What color palettes worked for Nike campaigns?",
    domain=IntelligenceDomain.VISUAL
)
```

### Live Observation

```python
await aurora.start_observation(["./designs"], interval=5.0)
# Files are automatically interpreted on change
```

### AI ERP Reasoning

```python
from aurora.enterprise.ai_erp import AIERPLayer

ai = AIERPLayer(erp_core)
result = await ai.predict_churn("org_123")
result = await ai.forecast_revenue("org_123")
result = ai.analyze_capacity("org_123")
```

---

## Next Steps

1. **Explore Intelligence Engines** — See [Intelligence Guide](modules/intelligence.md)
2. **Set Up ERP Modules** — See [ERP Guide](modules/erp.md)
3. **Configure MCP Servers** — See [Integration Guide](../guides/integrations.md)
4. **Build Custom Agents** — See [Agent Instructions](../AGENTS.md)
5. **Deploy to Production** — See [Deployment Guide](../architecture/overview.md)

---

**Need Help?**

- [FAQ](faq.md)
- [Troubleshooting](troubleshooting.md)
- [API Reference](../api/reference.md)
- [Discord Community](https://discord.gg/agencyos)