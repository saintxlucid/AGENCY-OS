"""AGENCY OS — Base agent (provider-agnostic, LLM-backed)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from aurora.llm.agents_sdk import AgentSpec, run_agent
from aurora.llm.config import LLMConfig, load_llm_config


@dataclass
class AgentResult:
    agent: str
    provider: str
    output: str
    context: Dict[str, Any] = field(default_factory=dict)


class BaseAgent:
    """Thin wrapper around an AgentSpec + shared LLM config."""

    def __init__(self, spec: AgentSpec, config: LLMConfig | None = None):
        self.spec = spec
        self.config = config or load_llm_config()

    @property
    def name(self) -> str:
        return self.spec.name

    async def run(self, task: str, session_context: Optional[Dict] = None) -> AgentResult:
        from aurora.llm.factory import pick_provider

        provider = self.spec.provider
        if provider == "auto":
            provider = pick_provider(self.config, "auto")
        output = await run_agent(self.spec, task, config=self.config, session_context=session_context)
        return AgentResult(agent=self.spec.name, provider=provider, output=output, context=session_context or {})

    def describe(self) -> Dict[str, Any]:
        return {"name": self.spec.name, "provider": self.spec.provider, "model": self.spec.model, "tools": self.spec.tools}
