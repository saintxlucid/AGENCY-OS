"""AGENCY OS — OpenAI SDK wrapper (chat / vision / images / embeddings).

Uses `openai[AsyncOpenAI]` if installed and key present.
Retries transient errors via tenacity. No network at import.
"""
from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, Dict, List, Optional

from tenacity import retry, stop_after_attempt, wait_exponential

from .config import LLMConfig, load_llm_config
from .types import ChatMessage, LLMResponse, ToolSpec


def _require_sdk():
    try:
        import openai  # type: ignore
    except ImportError as e:
        raise RuntimeError("openai package not installed. pip install openai>=2.53.0") from e
    return openai


class OpenAIClient:
    def __init__(self, config: LLMConfig | None = None):
        self.config = config or load_llm_config()
        self._client: Any = None

    def is_available(self) -> bool:
        return bool(self.config.openai_api_key)

    def _ensure(self):
        if not self.is_available():
            raise RuntimeError("OPENAI_API_KEY is not set — OpenAI is unavailable.")
        if self._client is None:
            openai = _require_sdk()
            self._client = openai.AsyncOpenAI(api_key=self.config.openai_api_key)
        return self._client

    @staticmethod
    def _to_openai_messages(messages: List[ChatMessage] | List[Dict]) -> List[Dict]:
        out = []
        for m in messages:
            if isinstance(m, ChatMessage):
                out.append({"role": m.role, "content": m.content})
            else:
                out.append({"role": m.get("role", "user"), "content": m.get("content", "")})
        return out

    async def chat(
        self,
        messages: List[ChatMessage] | List[Dict],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        tools: Optional[List[ToolSpec | Dict]] = None,
        tool_choice: Optional[str] = None,
    ) -> LLMResponse:
        self._ensure()  # fail fast (no retry) when key is missing
        return await self._chat_impl(messages, model=model, max_tokens=max_tokens, temperature=temperature, tools=tools, tool_choice=tool_choice)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def _chat_impl(
        self,
        messages: List[ChatMessage] | List[Dict],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        tools: Optional[List[ToolSpec | Dict]] = None,
        tool_choice: Optional[str] = None,
    ) -> LLMResponse:
        client = self._ensure()
        kwargs: Dict[str, Any] = {
            "model": model or self.config.openai_model,
            "messages": self._to_openai_messages(messages),
            "max_tokens": max_tokens or self.config.max_tokens,
            "temperature": self.config.temperature if temperature is None else temperature,
        }
        if tools:
            kwargs["tools"] = [t.to_openai() if isinstance(t, ToolSpec) else t for t in tools]
            if tool_choice:
                kwargs["tool_choice"] = tool_choice
        resp = await client.chat.completions.create(**kwargs)
        choice = resp.choices[0].message
        tool_calls: List[Dict] = []
        for tc in getattr(choice, "tool_calls", None) or []:
            try:
                import json as _json

                tool_calls.append({"id": tc.id, "name": tc.function.name, "arguments": _json.loads(tc.function.arguments or "{}")})
            except Exception:
                tool_calls.append({"id": getattr(tc, "id", ""), "name": "unknown", "arguments": {}})
        usage: Dict[str, Any] = {}
        try:
            u = resp.usage
            usage = {"prompt_tokens": getattr(u, "prompt_tokens", 0), "completion_tokens": getattr(u, "completion_tokens", 0), "total_tokens": getattr(u, "total_tokens", 0)}
        except Exception:
            pass
        return LLMResponse(provider="openai", model=kwargs["model"], text=getattr(choice, "content", "") or "", tool_calls=tool_calls, usage=usage, raw=resp)

    async def ask(self, prompt: str, system: Optional[str] = None, **kw) -> str:
        msgs: List[Dict] = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.append({"role": "user", "content": prompt})
        return (await self.chat(msgs, **kw)).text

    async def analyze_image(self, image_path_or_url: str, prompt: str = "Describe this image in detail.", model: Optional[str] = None) -> str:
        client = self._ensure()
        url = image_path_or_url
        if not image_path_or_url.startswith("http"):
            b64 = base64.b64encode(Path(image_path_or_url).read_bytes()).decode()
            url = f"data:image/jpeg;base64,{b64}"
        resp = await client.chat.completions.create(
            model=model or self.config.openai_model,
            messages=[{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": url, "detail": "high"}},
            ]}],
            max_tokens=self.config.max_tokens,
        )
        return resp.choices[0].message.content or ""

    async def generate_image(self, prompt: str, size: str = "1024x1024", quality: str = "standard", style: str = "vivid") -> Dict[str, Any]:
        client = self._ensure()
        resp = await client.images.generate(model=self.config.openai_image_model, prompt=prompt, size=size, quality=quality, style=style, n=1)
        d = resp.data[0]
        return {"url": getattr(d, "url", None), "revised_prompt": getattr(d, "revised_prompt", None), "model": self.config.openai_image_model}

    async def embed(self, texts: List[str], model: Optional[str] = None) -> List[List[float]]:
        client = self._ensure()
        resp = await client.embeddings.create(model=model or self.config.openai_embed_model, input=texts)
        return [list(d.embedding) for d in resp.data]

    async def close(self):
        try:
            if self._client is not None:
                await self._client.close()
        except Exception:
            pass
        finally:
            self._client = None
