"""
Universal Media Interpreter
Ingests any media format and extracts structured understanding.
"""
from __future__ import annotations

import os
import json
import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass

from aurora.core import MediaType, MediaInterpretation, IntelligenceDomain, CreativeInsight


class UniversalInterpreter:
    """
    Routes media to appropriate specialized interpreter based on type.
    Uses multiple models/providers for best-in-class extraction.
    """
    
    def __init__(self, media_type: MediaType, ocr: bool = False):
        self.media_type = media_type
        self.ocr = ocr
        self.models = self._load_model_config()
    
    def _load_model_config(self) -> Dict:
        return {
            MediaType.IMAGE: {
                "primary": "gpt-4o",
                "fallback": "claude-3-5-sonnet",
                "specialized": ["clip", "blip", "detr"]
            },
            MediaType.VIDEO: {
                "primary": "gpt-4o",  # frame sampling
                "fallback": "gemini-1.5-pro",
                "specialized": ["videollama", "video_chatgpt"]
            },
            MediaType.AUDIO: {
                "primary": "whisper",
                "fallback": "gemini-1.5-pro",
                "specialized": ["wav2vec", "ast"]
            },
            MediaType.DOCUMENT: {
                "primary": "gpt-4o",
                "fallback": "claude-3-5-sonnet",
                "specialized": ["layoutlm", "donut"]
            },
            MediaType.CODE: {
                "primary": "gpt-4o",
                "fallback": "claude-3-5-sonnet",
                "specialized": ["codebert", "graphcodebert"]
            },
            MediaType.DESIGN: {
                "primary": "gpt-4o",
                "fallback": "claude-3-5-sonnet",
                "specialized": ["figma_api", "design_token_extractor"]
            },
            MediaType.MODEL_3D: {
                "primary": "gpt-4o",
                "fallback": "claude-3-5-sonnet",
                "specialized": ["pointnet", "mesh_r_cnn"]
            },
            MediaType.PROJECT: {
                "primary": "gpt-4o",
                "fallback": "claude-3-5-sonnet",
                "specialized": ["project_parser"]
            },
        }
    
    async def interpret(self, source_path: Path) -> MediaInterpretation:
        """Main interpretation pipeline."""
        media_id = str(uuid.uuid4())[:12]
        
        # Extract raw content based on media type
        raw_content = await self._extract_content(source_path)
        
        # Generate base insights using LLM
        base_insights = await self._generate_base_insights(raw_content)
        
        # Create metadata graph
        metadata_graph = await self._build_metadata_graph(raw_content, source_path)
        
        # Generate tags
        tags = self._generate_tags(raw_content, base_insights)
        
        interpretation = MediaInterpretation(
            media_id=media_id,
            media_type=self.media_type,
            source_path=str(source_path),
            timestamp=datetime.now().isoformat(),
            insights=base_insights,
            summary=self._generate_summary(base_insights),
            quality_score=5.0,  # Will be recalculated by core
            metadata_graph=metadata_graph,
            tags=tags
        )
        
        return interpretation
    
    async def _extract_content(self, source_path: Path) -> Dict[str, Any]:
        """Extract raw content from media file."""
        if self.media_type == MediaType.IMAGE:
            return await self._extract_image(source_path)
        elif self.media_type == MediaType.VIDEO:
            return await self._extract_video(source_path)
        elif self.media_type == MediaType.AUDIO:
            return await self._extract_audio(source_path)
        elif self.media_type == MediaType.DOCUMENT:
            return await self._extract_document(source_path)
        elif self.media_type == MediaType.CODE:
            return await self._extract_code(source_path)
        elif self.media_type == MediaType.DESIGN:
            return await self._extract_design(source_path)
        elif self.media_type == MediaType.MODEL_3D:
            return await self._extract_3d(source_path)
        elif self.media_type == MediaType.PROJECT:
            return await self._extract_project(source_path)
        else:
            return await self._extract_generic(source_path)
    
    async def _extract_image(self, path: Path) -> Dict:
        """Extract image content using vision model."""
        # In production: use GPT-4o vision, Claude vision, or local models
        return {
            "type": "image",
            "path": str(path),
            "size": path.stat().st_size,
            "format": path.suffix,
            "vision_analysis": "Would use GPT-4o vision API here",
            "extracted_text": "OCR text would go here",
            "objects": [],
            "colors": [],
            "composition": {},
        }
    
    async def _extract_video(self, path: Path) -> Dict:
        """Extract video content via frame sampling + audio."""
        return {
            "type": "video",
            "path": str(path),
            "size": path.stat().st_size,
            "format": path.suffix,
            "duration": "Would extract via ffprobe",
            "frame_analyses": [],
            "audio_transcript": "Would extract via Whisper",
            "scene_changes": [],
        }
    
    async def _extract_audio(self, path: Path) -> Dict:
        """Extract audio content via transcription."""
        return {
            "type": "audio",
            "path": str(path),
            "size": path.stat().st_size,
            "format": path.suffix,
            "duration": "Would extract via ffprobe",
            "transcript": "Would transcribe via Whisper",
            "speakers": [],
            "music_segments": [],
            "silence_segments": [],
        }
    
    async def _extract_document(self, path: Path) -> Dict:
        """
        Extract document content.

        PDFs route through aurora.documents.pdftool, which inspects before
        extracting and refuses active content (JavaScript, launch actions)
        unless forced. That refusal is surfaced rather than swallowed: a
        blocked document must not look like an empty one.

        The import is local and optional because pdftool depends on PyMuPDF
        (AGPL-3.0). If it is absent, this degrades to a metadata-only result
        instead of breaking the interpreter.
        """
        base = {
            "type": "document",
            "path": str(path),
            "size": path.stat().st_size,
            "format": path.suffix,
            "text": "",
            "structure": {},
            "images": [],
            "tables": [],
        }

        if path.suffix.lower() != ".pdf":
            base["text"] = f"No extractor wired for {path.suffix or 'unknown'}"
            return base

        try:
            from aurora.documents.pdftool import PDFExtractor
        except ImportError as e:
            base["extractor_error"] = f"pdftool unavailable: {e}"
            return base

        try:
            res = PDFExtractor().extract(path, want_tables=True, ocr=self.ocr)
        except Exception as e:
            base["extractor_error"] = f"{type(e).__name__}: {e}"
            return base

        insp = res.inspection or {}
        base.update({
            "text": res.text,
            "page_count": res.page_count,
            "char_count": res.char_count,
            "metadata": res.metadata,
            "tables": res.tables,
            "images": res.images,
            "structure": {
                "outline": res.outline,
                "pages": [
                    {"number": p.number, "chars": p.char_count,
                     "words": p.word_count, "images": p.image_count}
                    for p in res.pages
                ],
            },
            "risk": insp.get("risk"),
            "encrypted": insp.get("encrypted"),
            "likely_scanned": insp.get("likely_scanned"),
            "ocr_pages": res.ocr_pages,
            "ocr_available": res.ocr_available,
            "findings": [
                {"code": f["code"], "risk": f["risk"], "title": f["title"]}
                for f in insp.get("findings", [])
            ],
            "truncated": res.truncated,
            "warnings": res.warnings,
        })
        if res.errors:
            # Most commonly the safety interlock or a missing password.
            base["extractor_error"] = "; ".join(res.errors)
        return base
    
    async def _extract_code(self, path: Path) -> Dict:
        """Extract code content."""
        content = path.read_text(encoding="utf-8", errors="ignore")
        return {
            "type": "code",
            "path": str(path),
            "size": path.stat().st_size,
            "language": path.suffix[1:],
            "content": content,
            "lines": len(content.splitlines()),
            "functions": "Would parse AST",
            "classes": "Would parse AST",
            "imports": "Would parse AST",
            "complexity": "Would calculate",
        }
    
    async def _extract_design(self, path: Path) -> Dict:
        """Extract design file content (Figma, Sketch, etc.)."""
        return {
            "type": "design",
            "path": str(path),
            "size": path.stat().st_size,
            "format": path.suffix,
            "frames": "Would parse via Figma API or file format",
            "components": [],
            "styles": {},
            "tokens": {},
        }
    
    async def _extract_3d(self, path: Path) -> Dict:
        """Extract 3D model content."""
        return {
            "type": "3d_model",
            "path": str(path),
            "size": path.stat().st_size,
            "format": path.suffix,
            "vertices": "Would parse",
            "faces": "Would parse",
            "materials": [],
            "animations": [],
        }
    
    async def _extract_project(self, path: Path) -> Dict:
        """Extract project file (Premiere, After Effects, etc.)."""
        return {
            "type": "project",
            "path": str(path),
            "size": path.stat().st_size,
            "format": path.suffix,
            "timeline": "Would parse",
            "assets": [],
            "effects": [],
        }
    
    async def _extract_generic(self, path: Path) -> Dict:
        """Generic fallback extraction."""
        return {
            "type": "unknown",
            "path": str(path),
            "size": path.stat().st_size,
            "format": path.suffix,
        }
    
    async def _generate_base_insights(self, content: Dict) -> List[CreativeInsight]:
        """Generate initial insights from raw content using LLM."""
        # In production: call LLM with structured prompt
        # For now, return placeholder insights
        return [
            CreativeInsight(
                domain=IntelligenceDomain.VISUAL,
                category="extraction",
                finding=f"Extracted {self.media_type.value} content from {content.get('path', 'unknown')}",
                confidence=0.9,
                evidence=[f"File size: {content.get('size', 0)} bytes", f"Format: {content.get('format', 'unknown')}"]
            )
        ]
    
    async def _build_metadata_graph(self, content: Dict, path: Path) -> Dict:
        """Build rich metadata graph."""
        return {
            "file": {
                "name": path.name,
                "path": str(path),
                "size": content.get("size", 0),
                "format": content.get("format", ""),
                "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
            },
            "content": {k: v for k, v in content.items() if k != "content"},  # Exclude large content
            "extracted_at": datetime.now().isoformat(),
        }
    
    def _generate_tags(self, content: Dict, insights: List[CreativeInsight]) -> List[str]:
        """Generate searchable tags."""
        tags = [self.media_type.value, content.get("format", "").lstrip(".")]
        
        for insight in insights:
            tags.append(insight.category)
            tags.append(insight.domain.value)
        
        return list(set(tags))
    
    def _generate_summary(self, insights: List[CreativeInsight]) -> str:
        if not insights:
            return f"{self.media_type.value.title()} media interpreted"
        return f"{self.media_type.value.title()} with {len(insights)} initial insights"