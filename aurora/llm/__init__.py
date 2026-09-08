"""AGENCY OS — aurora.llm package (Claude SDK + OpenAI SDK/ADK)."""
from .agents_sdk import PREBUILT_SPECS, AgentSpec, adk_status, create_openai_agent, run_agent, run_claude_tool_loop, run_openai_agent
from .claude import ClaudeClient
from .config import LLMConfig, load_llm_config
from .factory import chat_auto, chat_with_provider, create_clients, pick_provider
from .openai_llm import OpenAIClient
from .tools import HANDLERS, TOOL_SPECS, claude_tools, mcp_tools, openai_tools
from .types import ChatMessage, LLMResponse, ToolSpec

__all__ = [
    "AgentSpec", "PREBUILT_SPECS", "adk_status", "create_openai_agent",
    "run_agent", "run_claude_tool_loop", "run_openai_agent",
    "ClaudeClient", "LLMConfig", "load_llm_config",
    "chat_auto", "chat_with_provider", "create_clients", "pick_provider",
    "OpenAIClient", "HANDLERS", "TOOL_SPECS", "claude_tools", "mcp_tools", "openai_tools",
    "ChatMessage", "LLMResponse", "ToolSpec",
]
