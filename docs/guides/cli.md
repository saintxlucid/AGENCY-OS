# CLI Reference

**AGENCY OS — Command Line Interface**

---

## Global Options

```
aurora [-h] [--version] [--verbose] [--quiet]
       {interpret, project, observe, query, batch, status, export, mcp}
       ...
```

| Option | Description |
|--------|-------------|
| `--version` | Show version |
| `-v, --verbose` | Verbose output |
| `-q, --quiet` | Minimal output |

---

## Commands

### interpret (i)

Interpret media files through the intelligence pipeline.

```
aurora interpret FILE [FILE ...] [-t TYPE] [-c] [--improve] [-o OUTPUT]
```

**Arguments:**
| Arg | Description |
|-----|-------------|
| `FILE` | Media file(s) to interpret |
| `-t, --type` | Media type (image, video, audio, document, code, design, 3d, project) |
| `-c, --critique` | Generate constructive critique |
| `--improve` | Generate improvement suggestions |
| `-o, --output` | Output format (json, markdown, text) |

**Examples:**
```bash
# Interpret image
python aurora/cli.py interpret design.png

# Full analysis
python aurora/cli.py interpret ad.png --critique --improve

# Video analysis
python aurora/cli.py interpret commercial.mp4 --type video

# Multiple files
python aurora/cli.py interpret *.png --critique

# JSON output
python aurora/cli.py interpret asset.png -o json
```

**Output:**
```
🔍 Interpreting: design.png
  ✅ Media ID: media_abc123
  📝 Summary: Modern minimalist design with warm amber palette
  ⭐ Quality: 8.4/10
  🏷️  Tags: image, design, minimalist, warm
  💡 Insights (12):
    • [visual] Strong rule-of-thirds composition
    • [design] WCAG AA contrast compliance verified
    • [marketing] Clear hierarchy, CTA prominent
    • [symbolism] Explorer archetype detected

  📋 Critique:
    • [visual] Consider more negative space around CTA
    • [design] Mobile breakpoint not optimized

  🚀 Improvements:
    • [visual] Add depth with subtle shadow layers
    • [marketing] Strengthen value proposition headline
```

---

### project (p)

Manage projects and project context.

```
aurora project ACTION [-n NAME] [-d DESCRIPTION] [-b BRIEF] [-a AUDIENCE] [-g GOALS]
```

**Actions:**
| Action | Description |
|--------|-------------|
| `create` | Create new project |
| `list` | List all projects |
| `show` | Show project details |
| `switch` | Switch active project |
| `archive` | Archive project |

**Examples:**
```bash
# Create project
python aurora/cli.py project create "Q4 Campaign" \
    --audience "Urban professionals 25-40" \
    --goals "awareness,conversion"

# List projects
python aurora/cli.py project list

# Switch context
python aurora/cli.py project switch "Q4 Campaign"
```

---

### observe (o, watch)

Start live creative observation on files/directories.

```
aurora observe TARGET [TARGET ...] [-i INTERVAL]
```

**Arguments:**
| Arg | Description |
|-----|-------------|
| `TARGET` | File or directory to watch |
| `-i, --interval` | Check interval in seconds (default: 5.0) |

**Examples:**
```bash
# Watch directory
python aurora/cli.py observe ./designs --interval 3

# Watch multiple targets
python aurora/cli.py observe ./designs ./assets ./src

# Watch single file
python aurora/cli.py observe hero-image.png
```

**Output:**
```
👁️  Starting observation on 3 targets (interval: 3.0s)
   Press Ctrl+C to stop

🔄 Change detected: hero-v2.png (modified)
  📝 Live critique for hero-v2.png:
    • [visual] Contrast ratio dropped to 3.8:1 (below WCAG AA)
    • [design] Spacing inconsistent with v1 (16px vs 24px)
    • [marketing] CTA below fold on mobile
```

---

### query (q, ask)

Query the creative memory graph with natural language.

```
aurora query QUESTION [-d DOMAIN] [-l LIMIT]
```

**Arguments:**
| Arg | Description |
|-----|-------------|
| `QUESTION` | Natural language question |
| `-d, --domain` | Focus domain (narrative, visual, symbolism, design, marketing, psychological) |
| `-l, --limit` | Max results (default: 10) |

**Examples:**
```bash
# Visual query
python aurora/cli.py query "What color palettes work for fintech?" --domain visual

# Marketing query
python aurora/cli.py query "Best CTAs for SaaS landing pages?" --domain marketing

# General query
python aurora/cli.py query "What worked for Nike campaigns?"
```

---

### batch

Batch process a directory of media files.

```
aurora batch DIRECTORY [-e EXTENSIONS] [--critique] [--improve]
```

**Arguments:**
| Arg | Description |
|-----|-------------|
| `DIRECTORY` | Directory to process |
| `-e, --extensions` | Comma-separated extensions (default: png,jpg,jpeg,webp) |
| `--critique` | Generate critique for each file |
| `--improve` | Generate improvements for each file |

**Examples:**
```bash
# Process all images
python aurora/cli.py batch ./assets

# Specific extensions
python aurora/cli.py batch ./assets --extensions png,jpg,mp4,mov

# Full analysis
python aurora/cli.py batch ./assets --critique --improve
```

---

### status (s)

Show system status and statistics.

```
aurora status [--org ORG_ID] [--detailed]
```

**Examples:**
```bash
# Platform status
python aurora/cli.py status

# Organization status
python aurora/cli.py status --org org_123

# Detailed
python aurora/cli.py status --detailed
```

**Output:**
```
📊 AGENCY OS Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Version:        1.0.0-alpha
Users:          12
Organizations:  3
Projects:       28
Assets:         1,247
Memory Nodes:   3,891

🧠 Intelligence Engines: 6/6 active
📚 ERP Modules: 10/10 active
🔗 MCP Servers: 2/12 connected
👁️  Observation: Inactive

💰 Finance:
  Revenue (MTD):    $125,000
  Outstanding:      $45,000
  Pipeline:         $340,000

👥 Team:
  Total Members:    12
  Active:           10
  Utilization:      78%
```

---

### export (e)

Export interpretation to external format/tool.

```
aurora export --media-id ID [--target TARGET] [--format FORMAT]
```

**Arguments:**
| Arg | Description |
|-----|-------------|
| `--media-id` | Media ID to export |
| `--target` | Target tool (figma, webflow, framer, notion, json) |
| `--format` | Export format (json, markdown, html, csv) |

**Examples:**
```bash
# Export to JSON
python aurora/cli.py export --media-id abc123 --format json

# Export to Figma
python aurora/cli.py export --media-id abc123 --target figma

# Export to Webflow
python aurora/cli.py export --media-id abc123 --target webflow
```

---

### mcp

Manage MCP server connections.

```
mcp {list, start, stop, status} [SERVER_NAME]
```

**Examples:**
```bash
# List available servers
python aurora/cli.py mcp list

# Start a server
python aurora/cli.py mcp start filesystem

# Check status
python aurora/cli.py mcp status
```

---

## Configuration File

Create `~/.agencyos/config.yaml` for persistent settings:

```yaml
# Default organization
default_org: org_abc123

# Default model
default_model: gpt-4o

# Output preferences
output:
  format: text  # text, json, markdown
  color: true
  emoji: true

# Intelligence engine settings
intelligence:
  auto_critique: true
  auto_improve: true
  min_confidence: 0.6

# Observation settings
observation:
  interval: 5.0
  debounce: 2.0
  auto_analyze: true

# API settings
api:
  timeout: 30
  retries: 3
  rate_limit: 100

# Cache settings
cache:
  enabled: true
  ttl: 3600  # seconds
  max_size: 1000
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AGENCY_OS_HOME` | Data directory | `~/.agencyos` |
| `AGENCY_OS_LOG_LEVEL` | Log level | `INFO` |
| `AGENCY_OS_MODEL` | Default AI model | `gpt-4o` |
| `AGENCY_OS_OUTPUT` | Default output format | `text` |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `ANTHROPIC_API_KEY` | Anthropic API key | - |
| `GOOGLE_API_KEY` | Google AI key | - |

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | File not found |
| 4 | Permission denied |
| 5 | API error |
| 6 | Configuration error |
| 7 | Memory/storage error |

---

## Tips & Tricks

### Shell Aliases

```bash
# Add to .bashrc/.zshrc
alias aos='python aurora/cli.py'
alias aosi='python aurora/cli.py interpret'
alias aoso='python aurora/cli.py observe'
alias aosq='python aurora/cli.py query'
```

### Batch with Watch

```bash
# Observe and batch process
python aurora/cli.py observe ./incoming --interval 10 &
python aurora/cli.py batch ./incoming --extensions png,jpg
```

### JSON Pipeline

```bash
# Export to JSON for processing
python aurora/cli.py interpret ad.png -o json | jq '.insights[] | select(.domain=="visual")'
```