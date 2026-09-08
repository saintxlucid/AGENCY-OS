"""Tests for unified LLM SDK layer (Claude + OpenAI/ADK). No network calls."""
from __future__ import annotations


def test_llm_config_defaults(monkeypatch):
    # Hermetic: process env (e.g. OPENAI_MODEL=llama) must not override contract defaults.
    for var in ("OPENAI_MODEL", "ANTHROPIC_MODEL", "LLM_DEFAULT_PROVIDER",
                "OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    from aurora.llm.config import load_llm_config

    cfg = load_llm_config({"openai_api_key": "", "anthropic_api_key": ""})
    assert cfg.openai_model == "gpt-4o"
    assert cfg.anthropic_model == "claude-sonnet-4-6"
    assert cfg.providers() == []
    st = cfg.status()
    assert st["openai"]["available"] is False
    assert st["claude"]["available"] is False


def test_tool_specs_convert():
    from aurora.llm.tools import TOOL_SPECS

    names = {t.name for t in TOOL_SPECS}
    assert {"generate_image", "research_topic", "save_project_brief", "process_image"} <= names
    for t in TOOL_SPECS:
        assert t.to_openai()["type"] == "function"
        assert "input_schema" in t.to_claude()
        assert "inputSchema" in t.to_mcp()


def test_handlers_registry():
    from aurora.llm.tools import HANDLERS, TOOL_SPECS

    for spec in TOOL_SPECS:
        assert spec.name in HANDLERS


def test_unavailable_clients_raise():
    import asyncio

    from aurora.llm.claude import ClaudeClient
    from aurora.llm.config import load_llm_config
    from aurora.llm.openai_llm import OpenAIClient
    from aurora.llm.types import ChatMessage

    cfg = load_llm_config({"openai_api_key": "", "anthropic_api_key": ""})
    assert OpenAIClient(cfg).is_available() is False
    assert ClaudeClient(cfg).is_available() is False

    async def _go():
        import tenacity
        try:
            await OpenAIClient(cfg).chat([ChatMessage(role="user", content="hi")])
            raise AssertionError("should have raised")
        except (RuntimeError, tenacity.RetryError):
            pass
        try:
            await ClaudeClient(cfg).chat([ChatMessage(role="user", content="hi")])
            raise AssertionError("should have raised")
        except (RuntimeError, tenacity.RetryError):
            pass

    asyncio.run(_go())


def test_openai_agent_build_and_adk_status():
    import pytest
    from aurora.llm.agents_sdk import PREBUILT_SPECS, adk_status, create_openai_agent, openai_agents_status
    from aurora.llm.config import load_llm_config

    assert "design_studio" in PREBUILT_SPECS
    st = adk_status()
    assert "available" in st

    sdk = openai_agents_status()
    if not sdk["available"]:
        pytest.skip(f"openai-agents SDK unavailable: {sdk.get('error')}")

    cfg = load_llm_config({"openai_api_key": "test-key", "anthropic_api_key": ""})
    agent = create_openai_agent(PREBUILT_SPECS["design_studio"], cfg)
    assert agent.name == "DesignStudio"
    assert len(agent.tools) == 6


def test_integrations_health_without_keys():
    import asyncio

    from aurora.integrations.llm import ClaudeIntegration, OpenAIIntegration

    async def _go():
        c = ClaudeIntegration({"anthropic_api_key": ""})
        assert await c.connect() is False
        h = await c.health()
        assert h["name"] == "claude" and h["connected"] is False

        o = OpenAIIntegration({"openai_api_key": ""})
        assert await o.connect() is False
        ho = await o.health()
        assert ho["name"] == "openai" and ho["connected"] is False

    asyncio.run(_go())


def test_mcp_registers_llm_tools():
    from aurora.protocols.mcp_layer import MCPLayer

    layer = MCPLayer(aurora_core=None)
    n = layer.register_llm_tools()
    assert n == 6
    tools = layer.get_available_tools()
    names = {t["name"] for t in tools}
    assert "generate_image" in names and "research_topic" in names


def test_base_agent_describe():
    from aurora.agents.studio import design_studio
    from aurora.llm.config import load_llm_config

    cfg = load_llm_config({"openai_api_key": "k", "anthropic_api_key": ""})
    agent = design_studio(provider="openai", config=cfg)
    d = agent.describe()
    assert d["name"] == "DesignStudio"
    assert "generate_image" in d["tools"]
