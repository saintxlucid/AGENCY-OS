"""AGENCY OS — LLM environment config (Claude + OpenAI + ADK).

Single place that reads env, reports provider availability,
and supplies sane model defaults. Never raises on import.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List

from dotenv import load_dotenv

load_dotenv()


def _get(name: str, default: str = "") -> str:
    return os.getenv(name, default) or default


@dataclass
class LLMConfig:
    default_provider: str = "openai"  # openai | claude | auto
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_image_model: str = "dall-e-3"
    openai_embed_model: str = "text-embedding-3-small"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    google_api_key: str = ""
    max_tokens: int = 1500
    temperature: float = 0.7
    timeout_s: float = 60.0

    @property
    def openai_available(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def claude_available(self) -> bool:
        return bool(self.anthropic_api_key)

    def providers(self) -> List[str]:
        out = []
        if self.openai_available:
            out.append("openai")
        if self.claude_available:
            out.append("claude")
        return out

    def status(self) -> Dict:
        return {
            "default_provider": self.default_provider,
            "openai": {"available": self.openai_available, "model": self.openai_model},
            "claude": {"available": self.claude_available, "model": self.anthropic_model},
        }


def load_llm_config(overrides: Dict | None = None) -> LLMConfig:
    overrides = overrides or {}
    return LLMConfig(
        default_provider=overrides.get("default_provider", _get("LLM_DEFAULT_PROVIDER", "openai")),
        openai_api_key=overrides.get("openai_api_key", _get("OPENAI_API_KEY", "")),
        openai_model=overrides.get("openai_model", _get("OPENAI_MODEL", "gpt-4o")),
        openai_image_model=overrides.get("openai_image_model", _get("OPENAI_IMAGE_MODEL", "dall-e-3")),
        openai_embed_model=overrides.get("openai_embed_model", _get("OPENAI_EMBED_MODEL", "text-embedding-3-small")),
        anthropic_api_key=overrides.get("anthropic_api_key", _get("ANTHROPIC_API_KEY", "")),
        anthropic_model=overrides.get("anthropic_model", _get("ANTHROPIC_MODEL", "claude-sonnet-4-6")),
        google_api_key=overrides.get("google_api_key", _get("GOOGLE_API_KEY", "")),
        max_tokens=int(overrides.get("max_tokens", _get("LLM_MAX_TOKENS", "1500"))),
        temperature=float(overrides.get("temperature", _get("LLM_TEMPERATURE", "0.7"))),
    )


REQUIRED_ENV_DOC = """\
# LLM SDK — required / optional env
OPENAI_API_KEY=            # OpenAI SDK + Agents SDK
OPENAI_MODEL=gpt-4o        # chat default
OPENAI_IMAGE_MODEL=dall-e-3
OPENAI_EMBED_MODEL=text-embedding-3-small
ANTHROPIC_API_KEY=         # Claude SDK
ANTHROPIC_MODEL=claude-sonnet-4-6
LLM_DEFAULT_PROVIDER=openai  # openai | claude | auto
LLM_MAX_TOKENS=1500
LLM_TEMPERATURE=0.7
"""
