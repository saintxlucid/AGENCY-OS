"""AGENCY OS — Claude SDK wrapper (async-first, tool-aware).

Uses `anthropic[AsyncAnthropic]` if installed and key present.
All methods raise RuntimeError with a clear message when unavailable,
so callers can fall back to OpenAI instead of crashing at import.
"""
from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import LLMConfig, load_llm_config
from .types import ChatMessage, LLMResponse, ToolSpec


def _require_sdk():
    try:
        import anthropic  # type: ignore
    except ImportError as e:
        raise RuntimeError("anthropic package not installed. pip install anthropic>=0.120.2") from e
    return anthropic


class ClaudeClient:
    """Thin async wrapper around Anthropic Messages API."""

    def __init__(self, config: LLMConfig | None = None):
        self.config = config or load_llm_config()
        self._client: Any = None

    def is_available(self) -> bool:
        return bool(self.config.claude_available)

    def _ensure(self):
        if not self.is_available():
            raise RuntimeError("ANTHROPIC_API_KEY is not set — Claude is unavailable.")
        if self._client is None:
            anthropic = _require_sdk()
            self._client = anthropic.AsyncAnthropic(api_key=self.config.anthropic_api_key)
        return self._client

    @staticmethod
    def _to_anthropic_messages(messages: List[ChatMessage]) -> tuple[Optional[str], List[Dict]]:
        system: Optional[str] = None
        out: List[Dict] = []
        for m in messages:
            if m.role == "system":
                system = (system + "\n" + m.content) if system else m.content
                continue
            out.append({"role": m.role if m.role in ("user", "assistant") else "user", "content": m.content})
        return system, out

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def chat(
        self,
        messages: List[ChatMessage] | List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        tools: Optional[List[ToolSpec | Dict]] = None,
    ) -> LLMResponse:
        client = self._ensure()
        norm = [m if isinstance(m, ChatMessage) else ChatMessage(role=m.get("role", "user"), content=m.get("content", "")) for m in messages]
        system, msgs = self._to_anthropic_messages(norm)
        kwargs: Dict[str, Any] = {
            "model": model or self.config.anthropic_model,
            "max_tokens": max_tokens or self.config.max_tokens,
            "temperature": self.config.temperature if temperature is None else temperature,
            "messages": msgs,
        }
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = [t.to_claude() if isinstance(t, ToolSpec) else t for t in tools]
        msg = await client.messages.create(**kwargs)
        text_parts, tool_calls = [], []
        for block in getattr(msg, "content", []) or []:
            btype = getattr(block, "type", "")
            if btype == "text":
                text_parts.append(getattr(block, "text", ""))
            elif btype == "tool_use":
                tool_calls.append({"id": getattr(block, "id", ""), "name": getattr(block, "name", ""), "input": getattr(block, "input", {})})
        usage = {}
        try:
            u = msg.usage
            usage = {"input_tokens": getattr(u, "input_tokens", 0), "output_tokens": getattr(u, "output_tokens", 0)}
        except Exception:
            pass
        return LLMResponse(provider="claude", model=kwargs["model"], text="".join(text_parts), tool_calls=tool_calls, usage=usage, raw=msg)

    async def ask(self, prompt: str, system: Optional[str] = None, **kw) -> str:
        msgs: List[ChatMessage] = []
        if system:
            msgs.append(ChatMessage(role="system", content=system))
        msgs.append(ChatMessage(role="user", content=prompt))
        resp = await self.chat(msgs, **kw)
        return resp.text

    async def analyze_image(self, image_path_or_url: str, question: str = "Describe this image in detail.", model: Optional[str] = None) -> str:
        """Async Claude vision (replaces the old sync blocking helper)."""
        client = self._ensure()
        if image_path_or_url.startswith("http"):
            async with httpx.AsyncClient(timeout=30.0) as hc:
                r = await hc.get(image_path_or_url)
                r.raise_for_status()
                data = r.content
            media_type = "image/png"
        else:
            data = Path(image_path_or_url).read_bytes()
            ext = Path(image_path_or_url).suffix.lower().lstrip(".")
            media_type = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp", "gif": "image/gif"}.get(ext, "image/png")
        b64 = base64.b64encode(data).decode()
        msg = await client.messages.create(
            model=model or self.config.anthropic_model,
            max_tokens=self.config.max_tokens,
            messages=[{"role": "user", "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}},
                {"type": "text", "text": question},
            ]}],
        )
        parts = [getattr(b, "text", "") for b in (msg.content or []) if getattr(b, "type", "") == "text"]
        return "".join(parts)

    async def close(self):
        try:
            if self._client is not None:
                await self._client.close()
        except Exception:
            pass
        finally:
            self._client = None
