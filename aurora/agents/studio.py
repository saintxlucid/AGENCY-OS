"""AGENCY OS — Built-in studio agents (unified LLM backends)."""
from __future__ import annotations

from typing import Dict, Optional

from aurora.llm.agents_sdk import PREBUILT_SPECS
from aurora.llm.config import LLMConfig, load_llm_config

from .base import AgentResult, BaseAgent


def _agent(key: str, provider: str = "auto", config: LLMConfig | None = None) -> BaseAgent:
    base = PREBUILT_SPECS[key]
    from dataclasses import replace

    return BaseAgent(replace(base, provider=provider), config or load_llm_config())


def design_studio(provider: str = "auto", config: LLMConfig | None = None) -> BaseAgent:
    return _agent("design_studio", provider, config)


def researcher(provider: str = "auto", config: LLMConfig | None = None) -> BaseAgent:
    return _agent("researcher", provider, config)


def critic(provider: str = "auto", config: LLMConfig | None = None) -> BaseAgent:
    return _agent("critic", provider, config)


async def run_studio(task: str, provider: str = "auto", session_context: Optional[Dict] = None, config: LLMConfig | None = None) -> AgentResult:
    """Run the DesignStudio agent (OpenAI Agents SDK or Claude loop)."""
    return await design_studio(provider, config).run(task, session_context)


async def run_research(task: str, provider: str = "auto", session_context: Optional[Dict] = None, config: LLMConfig | None = None) -> AgentResult:
    return await researcher(provider, config).run(task, session_context)


async def run_critique(task: str, provider: str = "auto", session_context: Optional[Dict] = None, config: LLMConfig | None = None) -> AgentResult:
    return await critic(provider, config).run(task, session_context)
