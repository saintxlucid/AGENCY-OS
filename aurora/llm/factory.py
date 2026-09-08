"""AGENCY OS — LLM factory (provider selection + unified chat)."""
from __future__ import annotations

from typing import Dict, List, Optional

from .claude import ClaudeClient
from .config import LLMConfig, load_llm_config
from .openai_llm import OpenAIClient
from .types import ChatMessage, LLMResponse


def create_clients(config: LLMConfig | None = None) -> Dict[str, object]:
    config = config or load_llm_config()
    return {"openai": OpenAIClient(config), "claude": ClaudeClient(config)}


def pick_provider(config: LLMConfig | None = None, preferred: str = "auto") -> str:
    config = config or load_llm_config()
    if preferred in ("openai", "claude"):
        client = OpenAIClient(config) if preferred == "openai" else ClaudeClient(config)
        if client.is_available():
            return preferred
        raise RuntimeError(f"LLM provider '{preferred}' requested but its API key is missing.")
    # auto: default first, then fallback
    if config.default_provider == "claude" and config.claude_available:
        return "claude"
    if config.openai_available:
        return "openai"
    if config.claude_available:
        return "claude"
    raise RuntimeError("No LLM provider available. Set OPENAI_API_KEY and/or ANTHROPIC_API_KEY.")


async def chat_auto(prompt: str, system: Optional[str] = None, provider: str = "auto", config: LLMConfig | None = None, **kw) -> str:
    config = config or load_llm_config()
    chosen = pick_provider(config, provider)
    msgs: List[ChatMessage] = []
    if system:
        msgs.append(ChatMessage(role="system", content=system))
    msgs.append(ChatMessage(role="user", content=prompt))
    if chosen == "claude":
        return (await ClaudeClient(config).chat(msgs, **kw)).text
    return (await OpenAIClient(config).chat(msgs, **kw)).text


async def chat_with_provider(provider: str, messages: List[ChatMessage] | List[Dict], config: LLMConfig | None = None, **kw) -> LLMResponse:
    config = config or load_llm_config()
    if provider == "claude":
        return await ClaudeClient(config).chat(messages, **kw)  # type: ignore[arg-type]
    return await OpenAIClient(config).chat(messages, **kw)  # type: ignore[arg-type]
