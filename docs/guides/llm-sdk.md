# LLM SDK Guide — Unified Claude + OpenAI/ADK Layer

Canonical package: `aurora/llm/`. Provider-agnostic agents: `aurora/agents/`.
Provider integrations: `aurora/integrations/llm.py`. No network at import;
missing keys raise only when a call is attempted (fail-fast, no retry on
missing key).

## Environment

Copy `.env.example` → `.env` (never commit `.env`). At least one provider key:

| Variable | Default | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | — | OpenAI SDK + Agents SDK |
| `OPENAI_MODEL` | `gpt-4o` | Chat default |
| `OPENAI_IMAGE_MODEL` | `dall-e-3` | Image generation |
| `OPENAI_EMBED_MODEL` | `text-embedding-3-small` | Embeddings |
| `ANTHROPIC_API_KEY` | — | Claude SDK |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-6` | Messages default |
| `LLM_DEFAULT_PROVIDER` | `openai` | `openai` \| `claude` \| `auto` |
| `LLM_MAX_TOKENS` | `1500` | Per-call cap |
| `LLM_TEMPERATURE` | `0.7` | Sampling |

Dependencies (core): `openai>=2.53.0`, `openai-agents>=0.19.0`,
`anthropic>=0.120.2`, `tenacity` (retry). Heavy ML stays under `[local]`.

## Modules (`aurora/llm/`)

| Module | Contents |
|---|---|
| `types.py` | `ChatMessage`, `ToolSpec` (→ OpenAI/Claude/MCP shapes), `LLMResponse` |
| `config.py` | `LLMConfig`, `load_llm_config(overrides)` |
| `claude.py` | `ClaudeClient` — chat, tool-use loop input, async vision `analyze_image` |
| `openai_llm.py` | `OpenAIClient` — chat, vision, `generate_image`, `embed` |
| `tools.py` | 6 canonical tools + `HANDLERS`: `generate_image`, `analyze_image_openai`, `analyze_image_claude`, `research_topic`, `save_project_brief`, `process_image`; `openai_tools()` / `claude_tools()` / `mcp_tools()` |
| `factory.py` | `pick_provider()`, `chat_auto()`, `chat_with_provider()`, `create_clients()` |
| `agents_sdk.py` | ADK: `AgentSpec`, `PREBUILT_SPECS` (design_studio/researcher/critic), `create_openai_agent()`, `run_openai_agent()`, `run_claude_tool_loop()`, `run_agent()`, `adk_status()` (optional `google-adk` bridge) |

## Usage

```python
from aurora.llm import load_llm_config, chat_auto
from aurora.llm.tools import openai_tools, claude_tools

cfg = load_llm_config()
print(cfg.status())  # per-provider availability, no network

text = await chat_auto("Summarize this brief", provider="auto")

from aurora.agents.studio import run_studio, run_research, run_critique
result = await run_studio("Design a hero image for Q4", provider="auto")
print(result.output, result.provider)
```

Direct clients (fail fast without key, retry transient errors ×3):

```python
from aurora.llm import OpenAIClient, ClaudeClient
await OpenAIClient().ask("Hello", system="You are concise.")
await ClaudeClient().analyze_image("asset.png", "Describe the composition.")
```

## Agents SDK / ADK pattern

- OpenAI path uses the `agents` package (`openai-agents`): `Agent` + `Runner` +
  `function_tool` wrappers built from `TOOL_SPECS`/`HANDLERS` (`build_openai_sdk_tools()`).
- Claude path runs `run_claude_tool_loop()`: chat → execute `tool_use` via
  `HANDLERS` → feed results → final text (max 4 turns).
- `run_agent(spec, ...)` picks by `spec.provider` (`auto` → configured default
  with fallback). Google ADK is optional: `try_import_google_adk()` returns the
  module or `None`; `adk_status()` reports availability.

## Platform wiring

- `AuroraCore.initialize()` loads LLM config, connects `claude` + `openai`
  integrations (never fatal without keys), registers the 6 tools into the MCP
  layer (`register_llm_tools()`), and exposes `aurora.chat()` / `aurora.run_agent()`.
  `aurora.status()` includes an `llm` block.
- `MCPLayer.register_llm_tools()` mirrors handlers as local MCP tools.
- Legacy entry points (`studio_agents/studio_agent.py`, `studio_scripts/media_pipeline.py`)
  still work; new code should consume `aurora.llm` / `aurora.agents`.

## Tests

`tests/test_llm_sdk.py` — hermetic (explicit key overrides, no network):
config defaults, tool-shape conversion, handler registry, fail-fast on missing
keys, agent build, integration health without keys, MCP registration, agent describe.
