"""AGENCY OS — Canonical studio tools (OpenAI + Claude + MCP shapes).

Single source of truth for function schemas. Provider-specific
adapters (`agents_sdk`, MCP layer) consume TOOL_SPECS + HANDLERS.
No provider import at module load — handlers import lazily.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List

from .types import ToolSpec

STUDIO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = STUDIO_ROOT / "output"
PROJECTS_DIR = STUDIO_ROOT / "projects"
OUTPUT_DIR.mkdir(exist_ok=True)


def _ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


TOOL_SPECS: List[ToolSpec] = [
    ToolSpec(
        name="generate_image",
        description="Generate an image with DALL-E 3.",
        parameters={
            "prompt": {"type": "string", "description": "Detailed image description"},
            "size": {"type": "string", "enum": ["1024x1024", "1792x1024", "1024x1792"], "default": "1024x1024"},
            "quality": {"type": "string", "enum": ["standard", "hd"], "default": "standard"},
            "style": {"type": "string", "enum": ["vivid", "natural"], "default": "vivid"},
        },
        required=["prompt"],
    ),
    ToolSpec(
        name="analyze_image_openai",
        description="Analyze an image with GPT-4o vision.",
        parameters={
            "image_path_or_url": {"type": "string"},
            "analysis_type": {"type": "string", "enum": ["general", "design", "color_palette", "accessibility", "composition"], "default": "general"},
        },
        required=["image_path_or_url"],
    ),
    ToolSpec(
        name="analyze_image_claude",
        description="Analyze an image with Claude vision.",
        parameters={
            "image_path_or_url": {"type": "string"},
            "question": {"type": "string", "default": "Describe this image in detail."},
        },
        required=["image_path_or_url"],
    ),
    ToolSpec(
        name="research_topic",
        description="Research a topic with an LLM (trends, tools, competitors).",
        parameters={
            "query": {"type": "string"},
            "focus": {"type": "string", "enum": ["general", "design_trends", "ai_tools", "color_trends", "competitor_analysis"], "default": "general"},
            "provider": {"type": "string", "enum": ["auto", "openai", "claude"], "default": "auto"},
        },
        required=["query"],
    ),
    ToolSpec(
        name="save_project_brief",
        description="Save a project brief (JSON + markdown).",
        parameters={
            "project_name": {"type": "string"},
            "brief": {"type": "string"},
            "tags": {"type": "string", "default": ""},
        },
        required=["project_name", "brief"],
    ),
    ToolSpec(
        name="process_image",
        description="Local image ops: info, resize, thumbnail, convert, compress.",
        parameters={
            "image_path": {"type": "string"},
            "operation": {"type": "string", "enum": ["info", "resize", "thumbnail", "convert_png", "convert_jpeg", "compress"], "default": "info"},
            "width": {"type": "integer", "default": 512},
            "height": {"type": "integer", "default": 512},
            "size": {"type": "integer", "default": 256},
            "quality": {"type": "integer", "default": 85},
        },
        required=["image_path"],
    ),
]


async def handle_generate_image(prompt: str, size: str = "1024x1024", quality: str = "standard", style: str = "vivid") -> str:
    from .openai_llm import OpenAIClient

    result = await OpenAIClient().generate_image(prompt, size=size, quality=quality, style=style)
    payload = {"original_prompt": prompt, "size": size, "quality": quality, "style": style, "timestamp": _ts(), **result}
    (OUTPUT_DIR / f"image_{_ts()}.json").write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return json.dumps(payload, indent=2)


async def handle_analyze_image_openai(image_path_or_url: str, analysis_type: str = "general") -> str:
    from .openai_llm import OpenAIClient

    prompts = {
        "general": "Describe this image in detail including subject, style, mood, colors, and composition.",
        "design": "Analyze from a design perspective: typography, layout, color, hierarchy, balance. Give actionable feedback.",
        "color_palette": "Extract the color palette with hex codes and relationships. Suggest design-system usage.",
        "accessibility": "Evaluate accessibility: contrast, legibility, WCAG issues and fixes.",
        "composition": "Analyze composition: rule of thirds, focal points, negative space, flow. Rate quality.",
    }
    text = await OpenAIClient().analyze_image(image_path_or_url, prompts.get(analysis_type, prompts["general"]))
    return json.dumps({"analysis_type": analysis_type, "result": text, "timestamp": _ts()}, indent=2)


async def handle_analyze_image_claude(image_path_or_url: str, question: str = "Describe this image in detail.") -> str:
    from .claude import ClaudeClient

    text = await ClaudeClient().analyze_image(image_path_or_url, question)
    return json.dumps({"provider": "claude", "result": text, "timestamp": _ts()}, indent=2)


async def handle_research_topic(query: str, focus: str = "general", provider: str = "auto") -> str:
    from .factory import chat_auto

    prompts = {
        "general": f"Research: {query}. Provide comprehensive, up-to-date information.",
        "design_trends": f"Research 2025-2026 design trends for: {query}. Tools, techniques, examples.",
        "ai_tools": f"Best AI tools for: {query}. Compare features, pricing, use cases.",
        "color_trends": f"Current color trends/palettes for: {query}. Hex codes + usage.",
        "competitor_analysis": f"Competitor analysis for: {query}. Strengths, weaknesses, positioning.",
    }
    text = await chat_auto(prompts.get(focus, prompts["general"]), provider=provider)
    payload = {"query": query, "focus": focus, "provider": provider, "result": text, "timestamp": _ts()}
    (OUTPUT_DIR / f"research_{_ts()}.json").write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return json.dumps(payload, indent=2)


async def handle_save_project_brief(project_name: str, brief: str, tags: str = "") -> str:
    project_dir = PROJECTS_DIR / project_name.replace(" ", "_").lower()
    project_dir.mkdir(parents=True, exist_ok=True)
    data = {"project_name": project_name, "brief": brief, "tags": [t.strip() for t in tags.split(",") if t.strip()], "created_at": _ts(), "status": "active"}
    (project_dir / "brief.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    (project_dir / "brief.md").write_text(f"# {project_name}\n\n**Tags:** {tags}\n\n**Created:** {data['created_at']}\n\n{brief}", encoding="utf-8")
    return f"Project brief saved to {project_dir / 'brief.json'}"


async def handle_process_image(image_path: str, operation: str = "info", width: int = 512, height: int = 512, size: int = 256, quality: int = 85) -> str:
    from PIL import Image as _Image

    img = _Image.open(image_path)
    if operation == "info":
        result: Dict[str, Any] = {"format": img.format, "mode": img.mode, "size": list(img.size), "path": image_path}
    elif operation == "resize":
        out = OUTPUT_DIR / f"resized_{_ts()}.png"
        img.resize((width, height), _Image.LANCZOS).save(out)
        result = {"operation": "resize", "saved_to": str(out)}
    elif operation == "thumbnail":
        out = OUTPUT_DIR / f"thumb_{_ts()}.png"
        img.thumbnail((size, size), _Image.LANCZOS)
        img.save(out)
        result = {"operation": "thumbnail", "saved_to": str(out)}
    elif operation == "convert_png":
        out = OUTPUT_DIR / f"converted_{_ts()}.png"
        img.save(out, "PNG")
        result = {"operation": "convert_png", "saved_to": str(out)}
    elif operation == "convert_jpeg":
        out = OUTPUT_DIR / f"converted_{_ts()}.jpg"
        img.convert("RGB").save(out, "JPEG", quality=quality)
        result = {"operation": "convert_jpeg", "saved_to": str(out)}
    elif operation == "compress":
        out = OUTPUT_DIR / f"compressed_{_ts()}.jpg"
        img.convert("RGB").save(out, "JPEG", quality=quality, optimize=True)
        result = {"operation": "compress", "saved_to": str(out)}
    else:
        result = {"error": f"Unknown operation: {operation}"}
    return json.dumps(result, indent=2)


HANDLERS: Dict[str, Callable] = {
    "generate_image": handle_generate_image,
    "analyze_image_openai": handle_analyze_image_openai,
    "analyze_image_claude": handle_analyze_image_claude,
    "research_topic": handle_research_topic,
    "save_project_brief": handle_save_project_brief,
    "process_image": handle_process_image,
}


def openai_tools() -> List[Dict]:
    return [t.to_openai() for t in TOOL_SPECS]


def claude_tools() -> List[Dict]:
    return [t.to_claude() for t in TOOL_SPECS]


def mcp_tools() -> List[Dict]:
    return [t.to_mcp() for t in TOOL_SPECS]
