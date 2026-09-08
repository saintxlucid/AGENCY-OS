"""AGENCY OS — Agent Development Kit (ADK) over OpenAI Agents SDK + Claude.

- OpenAI path uses the `agents` package (openai-agents): Agent / Runner / function_tool.
- Claude path uses ClaudeClient with a tool-loop over TOOL_SPECS/HANDLERS.
- Google ADK (`google.adk`) is optional: exposed via try_import_google_adk()
  so installs without that extra keep working.

No network at import. Missing keys raise only when an agent is run.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .config import LLMConfig, load_llm_config
from .tools import HANDLERS, TOOL_SPECS

DESIGN_STUDIO_INSTRUCTIONS = """You are DAIRA Design Studio — an AI-powered creative intelligence system.

Capabilities: generate_image, analyze_image_openai, analyze_image_claude,
process_image, research_topic, save_project_brief.

Workflow: research first if needed, then generate, then analyze/refine.
Always save important outputs to the project brief.
Be concise but thorough — creative professionals value speed."""

RESEARCH_INSTRUCTIONS = """You are the Research agent. Use research_topic for trends,
tools, competitors. Cite what you found, flag uncertainty, propose next steps."""

CRITIC_INSTRUCTIONS = """You are the Critic agent. Review creative work for design,
accessibility, brand fit, and clarity. Be specific and actionable."""


@dataclass
class AgentSpec:
    name: str
    instructions: str
    provider: str = "auto"  # openai | claude | auto
    model: Optional[str] = None
    tools: List[str] = field(default_factory=lambda: [t.name for t in TOOL_SPECS])


def _require_agents_sdk():
    try:
        import agents as _agents  # type: ignore  # openai-agents package
    except ImportError as e:
        raise RuntimeError("openai-agents package not installed. pip install openai-agents>=0.19") from e
    # Guard against namespace shadowing (e.g. another `agents` package on sys.path).
    # The real openai-agents SDK exposes Agent + Runner + function_tool.
    missing = [a for a in ("Agent", "Runner", "function_tool") if not hasattr(_agents, a)]
    if missing:
        raise RuntimeError(
            f"imported `agents` from {_agents.__file__} lacks {missing} — "
            "wrong `agents` package shadowed openai-agents on sys.path. "
            "pip install openai-agents>=0.19 and remove shadowing path."
        )
    return _agents


def openai_agents_status() -> Dict[str, Any]:
    """Availability probe that never raises (for tests and health checks)."""
    try:
        mod = _require_agents_sdk()
        return {"available": True, "package": getattr(mod, "__file__", "agents")}
    except Exception as e:
        return {"available": False, "error": str(e)}


def build_openai_sdk_tools(tool_names: Optional[List[str]] = None):
    """Wrap canonical handlers as openai-agents function_tool objects."""
    agents = _require_agents_sdk()
    names = tool_names or [t.name for t in TOOL_SPECS]
    wrapped = []
    for spec in TOOL_SPECS:
        if spec.name not in names:
            continue
        handler = HANDLERS[spec.name]

        # Create a closure with the right signature metadata for function_tool.
        # function_tool inspects the function; keep names explicit per tool.
        if spec.name == "generate_image":
            async def _generate_image(prompt: str, size: str = "1024x1024", quality: str = "standard", style: str = "vivid") -> str:
                """Generate an image with DALL-E 3."""
                return await HANDLERS["generate_image"](prompt, size=size, quality=quality, style=style)

            wrapped.append(agents.function_tool(_generate_image))
        elif spec.name == "analyze_image_openai":
            async def _analyze_openai(image_path_or_url: str, analysis_type: str = "general") -> str:
                """Analyze an image with GPT-4o vision."""
                return await HANDLERS["analyze_image_openai"](image_path_or_url, analysis_type)

            wrapped.append(agents.function_tool(_analyze_openai))
        elif spec.name == "analyze_image_claude":
            async def _analyze_claude(image_path_or_url: str, question: str = "Describe this image in detail.") -> str:
                """Analyze an image with Claude vision."""
                return await HANDLERS["analyze_image_claude"](image_path_or_url, question)

            wrapped.append(agents.function_tool(_analyze_claude))
        elif spec.name == "research_topic":
            async def _research(query: str, focus: str = "general", provider: str = "auto") -> str:
                """Research a topic."""
                return await HANDLERS["research_topic"](query, focus, provider)

            wrapped.append(agents.function_tool(_research))
        elif spec.name == "save_project_brief":
            async def _save_brief(project_name: str, brief: str, tags: str = "") -> str:
                """Save a project brief."""
                return await HANDLERS["save_project_brief"](project_name, brief, tags)

            wrapped.append(agents.function_tool(_save_brief))
        elif spec.name == "process_image":
            async def _process(image_path: str, operation: str = "info", width: int = 512, height: int = 512, size: int = 256, quality: int = 85) -> str:
                """Local image ops."""
                return await HANDLERS["process_image"](image_path, operation, width, height, size, quality)

            wrapped.append(agents.function_tool(_process))
    return wrapped


def create_openai_agent(spec: AgentSpec, config: LLMConfig | None = None):
    """Build an openai-agents Agent (does not call the network)."""
    agents = _require_agents_sdk()
    config = config or load_llm_config()
    if not config.openai_available:
        raise RuntimeError("OPENAI_API_KEY missing — cannot build OpenAI agent.")
    return agents.Agent(
        name=spec.name,
        instructions=spec.instructions,
        tools=build_openai_sdk_tools(spec.tools),
        model=spec.model or config.openai_model,
    )


async def run_openai_agent(agent, user_input: str) -> str:
    agents = _require_agents_sdk()
    result = await agents.Runner.run(agent, input=user_input)
    return result.final_output


async def run_claude_tool_loop(prompt: str, system: Optional[str] = None, max_turns: int = 4, config: LLMConfig | None = None, model: Optional[str] = None) -> str:
    """Minimal Claude agentic loop: chat -> execute tool_use -> feed results -> final text."""
    from .claude import ClaudeClient
    from .types import ChatMessage

    config = config or load_llm_config()
    client = ClaudeClient(config)
    messages: List[Dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    tools = [t.to_claude() for t in TOOL_SPECS]
    last_text = ""
    for _ in range(max_turns):
        resp = await client.chat([ChatMessage(role=m["role"], content=m["content"]) for m in messages], model=model, tools=tools)
        last_text = resp.text or last_text
        if not resp.tool_calls:
            return last_text or "(empty response)"
        # Execute tools, append as user context for next turn
        results = []
        for tc in resp.tool_calls:
            handler = HANDLERS.get(tc["name"])
            if handler is None:
                results.append(f"[{tc['name']}] unknown tool")
                continue
            try:
                args = tc.get("input", {}) or {}
                results.append(f"[{tc['name']}] " + str(await handler(**args)))
            except Exception as e:
                results.append(f"[{tc['name']}] error: {e}")
        messages.append({"role": "user", "content": "Tool results:\n" + "\n".join(results)})
    return last_text or "(empty response)"


async def run_agent(spec: AgentSpec, user_input: str, config: LLMConfig | None = None, session_context: Dict | None = None) -> str:
    """Provider-agnostic entry: picks OpenAI Agents SDK or Claude tool-loop."""
    from .factory import pick_provider

    config = config or load_llm_config()
    provider = spec.provider
    if provider == "auto":
        provider = pick_provider(config, "auto")
    ctx = f"\n\n[Session Context]\n{json.dumps(session_context, indent=2, default=str)}" if session_context else ""
    full_input = user_input + ctx
    if provider == "claude":
        return await run_claude_tool_loop(full_input, system=spec.instructions, config=config, model=spec.model)
    agent = create_openai_agent(spec, config)
    return await run_openai_agent(agent, full_input)


def try_import_google_adk():
    """Optional Google ADK bridge. Returns module or None (never raises)."""
    try:
        import google.adk as adk  # type: ignore
        return adk
    except Exception:
        return None


def adk_status() -> Dict[str, Any]:
    mod = try_import_google_adk()
    return {"available": mod is not None, "package": "google-adk" if mod else None}


PREBUILT_SPECS: Dict[str, AgentSpec] = {
    "design_studio": AgentSpec(name="DesignStudio", instructions=DESIGN_STUDIO_INSTRUCTIONS, provider="auto"),
    "researcher": AgentSpec(name="Researcher", instructions=RESEARCH_INSTRUCTIONS, provider="auto",
                            tools=["research_topic", "save_project_brief"]),
    "critic": AgentSpec(name="Critic", instructions=CRITIC_INSTRUCTIONS, provider="auto",
                        tools=["analyze_image_openai", "analyze_image_claude", "research_topic"]),
}
