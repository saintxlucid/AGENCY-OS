"""AGENCY OS — Unified LLM types (provider-agnostic)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ChatMessage:
    role: str  # system | user | assistant | tool
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None


@dataclass
class ToolSpec:
    """Canonical tool definition shared by OpenAI / Claude / MCP."""

    name: str
    description: str
    parameters: Dict[str, Any]  # JSON-Schema object
    required: List[str] = field(default_factory=list)

    def to_openai(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters,
                    "required": self.required,
                },
            },
        }

    def to_claude(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": self.parameters,
                "required": self.required,
            },
        }

    def to_mcp(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": self.parameters,
                "required": self.required,
            },
        }


@dataclass
class LLMResponse:
    provider: str
    model: str
    text: str
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    usage: Dict[str, Any] = field(default_factory=dict)
    raw: Any = None
