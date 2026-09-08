"""AGENCY OS — LLM provider integrations (Claude + OpenAI).

Follows the `aurora.integrations.connectors.Integration` contract so the
existing IntegrationManager / AuroraCore.register_integration paths work.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .connectors import Integration


class ClaudeIntegration(Integration):
    """Anthropic Claude as an AGENCY OS integration."""

    def __init__(self, config: Dict[str, Any] | None = None):
        super().__init__(config)
        from aurora.llm.config import load_llm_config

        self.llm_config = load_llm_config(config)
        self._client = None

    @property
    def name(self) -> str:
        return "claude"

    async def connect(self) -> bool:
        if not self.llm_config.claude_available:
            self._connected = False
            return False
        try:
            from aurora.llm.claude import ClaudeClient

            self._client = ClaudeClient(self.llm_config)
            self._connected = True
            return True
        except Exception:
            self._connected = False
            return False

    async def health(self) -> Dict:
        return {"name": "claude", "connected": self._connected, "model": self.llm_config.anthropic_model,
                "available": self.llm_config.claude_available}

    async def chat(self, prompt: str, system: Optional[str] = None, **kw) -> str:
        if self._client is None and not await self.connect():
            raise RuntimeError("Claude unavailable: ANTHROPIC_API_KEY missing.")
        return await self._client.ask(prompt, system=system, **kw)

    async def analyze_image(self, path_or_url: str, question: str = "Describe this image in detail.") -> str:
        if self._client is None and not await self.connect():
            raise RuntimeError("Claude unavailable: ANTHROPIC_API_KEY missing.")
        return await self._client.analyze_image(path_or_url, question)


class OpenAIIntegration(Integration):
    """OpenAI (SDK + Agents SDK) as an AGENCY OS integration."""

    def __init__(self, config: Dict[str, Any] | None = None):
        super().__init__(config)
        from aurora.llm.config import load_llm_config

        self.llm_config = load_llm_config(config)
        self._client = None

    @property
    def name(self) -> str:
        return "openai"

    async def connect(self) -> bool:
        if not self.llm_config.openai_available:
            self._connected = False
            return False
        try:
            from aurora.llm.openai_llm import OpenAIClient

            self._client = OpenAIClient(self.llm_config)
            self._connected = True
            return True
        except Exception:
            self._connected = False
            return False

    async def health(self) -> Dict:
        from aurora.llm.agents_sdk import adk_status

        return {"name": "openai", "connected": self._connected, "model": self.llm_config.openai_model,
                "available": self.llm_config.openai_available, "agents_sdk": True, "adk": adk_status()}

    async def chat(self, prompt: str, system: Optional[str] = None, **kw) -> str:
        if self._client is None and not await self.connect():
            raise RuntimeError("OpenAI unavailable: OPENAI_API_KEY missing.")
        return await self._client.ask(prompt, system=system, **kw)

    async def generate_image(self, prompt: str, **kw) -> Dict:
        if self._client is None and not await self.connect():
            raise RuntimeError("OpenAI unavailable: OPENAI_API_KEY missing.")
        return await self._client.generate_image(prompt, **kw)

    async def run_agent(self, task: str, agent: str = "design_studio", session_context: Optional[Dict] = None) -> str:
        from aurora.agents.studio import run_critique, run_research, run_studio

        runners = {"design_studio": run_studio, "researcher": run_research, "critic": run_critique}
        fn = runners.get(agent, run_studio)
        result = await fn(task, provider="openai", session_context=session_context, config=self.llm_config)
        return result.output


__all__ = ["ClaudeIntegration", "OpenAIIntegration"]
