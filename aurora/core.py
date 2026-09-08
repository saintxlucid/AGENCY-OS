"""
AURORA Core — Universal Creative Intelligence Platform
The cognitive layer connecting all creative tools, media, and workflows.
"""
from __future__ import annotations

import os
import json
import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from abc import ABC, abstractmethod

from dotenv import load_dotenv
load_dotenv()


class MediaType(Enum):
    """Supported media types for universal interpretation."""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    CODE = "code"
    DESIGN = "design"
    MODEL_3D = "3d_model"
    PROJECT = "project"
    SCREENSHOT = "screenshot"
    LIVE_FEED = "live_feed"


class IntelligenceDomain(Enum):
    """Six core intelligence domains."""
    NARRATIVE = "narrative"
    VISUAL = "visual"
    SYMBOLISM = "symbolism"
    DESIGN = "design"
    MARKETING = "marketing"
    PSYCHOLOGICAL = "psychological"


@dataclass
class CreativeInsight:
    """A single structured insight from interpretation."""
    domain: IntelligenceDomain
    category: str
    finding: str
    confidence: float  # 0.0 - 1.0
    evidence: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MediaInterpretation:
    """Complete interpretation of a media asset."""
    media_id: str
    media_type: MediaType
    source_path: str
    timestamp: str
    insights: List[CreativeInsight]
    summary: str
    quality_score: float  # 0.0 - 10.0
    metadata_graph: Dict[str, Any]
    connections: List[str] = field(default_factory=list)  # Related media IDs
    tags: List[str] = field(default_factory=list)


@dataclass
class ProjectContext:
    """Active project context for live observation."""
    project_id: str
    name: str
    description: str
    media_assets: List[str] = field(default_factory=list)
    brief: Optional[str] = None
    brand_guidelines: Optional[Dict] = None
    target_audience: Optional[str] = None
    goals: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class IntelligenceEngine(ABC):
    """Base class for all intelligence engines."""
    
    def __init__(self, domain: IntelligenceDomain):
        self.domain = domain
        self.model = None
    
    @abstractmethod
    async def analyze(self, media: MediaInterpretation, context: Optional[ProjectContext] = None) -> List[CreativeInsight]:
        """Analyze media and return insights for this domain."""
        pass
    
    @abstractmethod
    async def critique(self, media: MediaInterpretation, context: Optional[ProjectContext] = None) -> List[CreativeInsight]:
        """Provide constructive critique."""
        pass
    
    @abstractmethod
    async def improve(self, media: MediaInterpretation, context: Optional[ProjectContext] = None) -> List[CreativeInsight]:
        """Suggest specific improvements."""
        pass


class AuroraCore:
    """
    The central cognitive engine of Project AURORA.
    
    Orchestrates interpretation, memory, observation, and integration.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.session_id = str(uuid.uuid4())[:8]
        self.started_at = datetime.now().isoformat()
        
        # Core components (initialized lazily)
        self._interpreters: Dict[MediaType, Any] = {}
        self._intelligence_engines: Dict[IntelligenceDomain, IntelligenceEngine] = {}
        self._memory = None
        self._observation = None
        self._protocol_layer = None
        self._integrations: Dict[str, Any] = {}
        
        # Active state
        self.current_project: Optional[ProjectContext] = None
        self.observation_active = False
        self.knowledge_graph = {}
        
        print(f"""
╔═══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     🌅  A U R O R A   C O R E   v1.0                            ║
║     Universal Creative Intelligence Platform                     ║
║                                                                  ║
║     Session: {self.session_id}                                    ║
║     Started: {self.started_at}                           ║
║                                                                  ║
╚═══════════════════════════════════════════════════════════════════╝
        """)
    
    # ─── Initialization ───
    
    async def initialize(self):
        """Initialize all subsystems."""
        from aurora.memory.graph import CreativeMemoryGraph
        from aurora.observation.watcher import LiveObserver
        from aurora.protocols.mcp_layer import MCPLayer
        from aurora.intelligence.narrative import NarrativeIntelligence
        from aurora.intelligence.visual import VisualIntelligence
        from aurora.intelligence.symbolism import SymbolismIntelligence
        from aurora.intelligence.design import DesignIntelligence
        from aurora.intelligence.marketing import MarketingIntelligence
        from aurora.intelligence.psychological import PsychologicalIntelligence
        
        print("🔧 Initializing subsystems...")
        
        # Memory
        self._memory = CreativeMemoryGraph()
        await self._memory.initialize()
        print("  ✅ Creative Memory Graph")
        
        # Intelligence Engines
        self._intelligence_engines = {
            IntelligenceDomain.NARRATIVE: NarrativeIntelligence(),
            IntelligenceDomain.VISUAL: VisualIntelligence(),
            IntelligenceDomain.SYMBOLISM: SymbolismIntelligence(),
            IntelligenceDomain.DESIGN: DesignIntelligence(),
            IntelligenceDomain.MARKETING: MarketingIntelligence(),
            IntelligenceDomain.PSYCHOLOGICAL: PsychologicalIntelligence(),
        }
        print("  ✅ 6 Intelligence Engines")
        
        # Observation
        self._observation = LiveObserver(self)
        print("  ✅ Live Observer")
        
        # Protocol Layer
        self._protocol_layer = MCPLayer(self)
        await self._protocol_layer.initialize()
        print("  ✅ MCP/A2A Protocol Layer")
        
        print("\n🌅 AURORA fully initialized and ready.\n")
    
    # ─── Core Operations ───
    
    async def interpret(
        self,
        source: Union[str, Path],
        media_type: Optional[MediaType] = None,
        project_id: Optional[str] = None
    ) -> MediaInterpretation:
        """
        Universal interpretation entry point.
        Ingests any media, routes to appropriate interpreter,
        runs all intelligence engines, stores in memory.
        """
        from aurora.interpreters.universal import UniversalInterpreter
        
        source_path = Path(source)
        if not source_path.exists():
            raise FileNotFoundError(f"Source not found: {source_path}")
        
        # Auto-detect media type if not provided
        if media_type is None:
            media_type = self._detect_media_type(source_path)
        
        print(f"🔍 Interpreting: {source_path.name} ({media_type.value})")
        
        # Get or create interpreter
        if media_type not in self._interpreters:
            self._interpreters[media_type] = UniversalInterpreter(media_type)
        
        interpreter = self._interpreters[media_type]
        
        # Run interpretation pipeline
        media_interpretation = await interpreter.interpret(source_path)
        
        # Run all intelligence engines
        print("  🧠 Running intelligence engines...")
        all_insights = []
        
        for domain, engine in self._intelligence_engines.items():
            try:
                insights = await engine.analyze(media_interpretation, self.current_project)
                all_insights.extend(insights)
                print(f"    ✅ {domain.value}: {len(insights)} insights")
            except Exception as e:
                print(f"    ⚠️  {domain.value}: {e}")
        
        media_interpretation.insights = all_insights
        media_interpretation.summary = self._generate_summary(all_insights)
        media_interpretation.quality_score = self._calculate_quality_score(all_insights)
        
        # Store in memory
        await self._memory.store(media_interpretation)
        
        # Link to project if provided
        if project_id:
            await self._memory.link_to_project(media_interpretation.media_id, project_id)
        
        print(f"  ✨ Complete: {len(all_insights)} insights, quality: {media_interpretation.quality_score:.1f}/10")
        
        return media_interpretation
    
    async def critique(
        self,
        media: MediaInterpretation,
        context: Optional[ProjectContext] = None
    ) -> List[CreativeInsight]:
        """Run constructive critique across all intelligence domains."""
        print(f"📋 Critiquing: {media.media_id}")
        all_critiques = []
        
        for domain, engine in self._intelligence_engines.items():
            try:
                critiques = await engine.critique(media, context or self.current_project)
                all_critiques.extend(critiques)
            except Exception as e:
                print(f"  ⚠️  {domain.value}: {e}")
        
        return all_critiques
    
    async def improve(
        self,
        media: MediaInterpretation,
        context: Optional[ProjectContext] = None
    ) -> List[CreativeInsight]:
        """Generate specific improvement suggestions."""
        print(f"🚀 Improving: {media.media_id}")
        all_improvements = []
        
        for domain, engine in self._intelligence_engines.items():
            try:
                improvements = await engine.improve(media, context or self.current_project)
                all_improvements.extend(improvements)
            except Exception as e:
                print(f"  ⚠️  {domain.value}: {e}")
        
        return all_improvements
    
    # ─── Project Management ───
    
    async def create_project(
        self,
        name: str,
        description: str = "",
        brief: Optional[str] = None,
        brand_guidelines: Optional[Dict] = None,
        target_audience: Optional[str] = None,
        goals: Optional[List[str]] = None
    ) -> ProjectContext:
        """Create a new project context."""
        project = ProjectContext(
            project_id=str(uuid.uuid4())[:8],
            name=name,
            description=description,
            brief=brief,
            brand_guidelines=brand_guidelines,
            target_audience=target_audience,
            goals=goals or []
        )
        
        await self._memory.create_project(project)
        self.current_project = project
        
        print(f"📁 Project created: {project.name} ({project.project_id})")
        return project
    
    def set_active_project(self, project: ProjectContext):
        """Set the active project for context."""
        self.current_project = project
        print(f"📍 Active project: {project.name}")
    
    # ─── Live Observation ───
    
    async def start_observation(self, targets: List[str], interval: float = 5.0):
        """Start live creative observation on target files/applications."""
        if not self._observation:
            raise RuntimeError("Observation system not initialized")
        
        self.observation_active = True
        await self._observation.start(targets, interval)
        print(f"👁️  Live observation started on {len(targets)} targets")
    
    async def stop_observation(self):
        """Stop live observation."""
        if self._observation:
            await self._observation.stop()
        self.observation_active = False
        print("👁️  Live observation stopped")
    
    # ─── Query & Retrieval ───
    
    async def query(self, question: str, domain: Optional[IntelligenceDomain] = None) -> str:
        """Query the creative memory graph with natural language."""
        return await self._memory.query(question, domain)
    
    async def find_similar(self, media_id: str, limit: int = 10) -> List[MediaInterpretation]:
        """Find similar media in memory."""
        return await self._memory.find_similar(media_id, limit)
    
    async def get_project_timeline(self, project_id: str) -> List[Dict]:
        """Get chronological timeline of project assets and insights."""
        return await self._memory.get_project_timeline(project_id)
    
    # ─── Integration & Export ───
    
    async def export_to(self, media_id: str, target: str, format: str = "json") -> str:
        """Export interpretation to external format/tool."""
        if target not in self._integrations:
            raise ValueError(f"Integration not available: {target}")
        
        integration = self._integrations[target]
        media = await self._memory.get(media_id)
        return await integration.export(media, format)
    
    def register_integration(self, name: str, integration: Any):
        """Register an external tool integration."""
        self._integrations[name] = integration
        print(f"🔗 Integration registered: {name}")
    
    # ─── Helpers ───
    
    def _detect_media_type(self, path: Path) -> MediaType:
        """Auto-detect media type from file extension."""
        ext = path.suffix.lower()
        
        image_exts = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.tiff', '.svg', '.heic'}
        video_exts = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv', '.wmv', '.m4v'}
        audio_exts = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma'}
        doc_exts = {'.pdf', '.docx', '.doc', '.txt', '.md', '.rtf', '.odt'}
        code_exts = {'.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.json', '.yaml', '.yml', '.cpp', '.c', '.h', '.java', '.go', '.rs', '.cs', '.php', '.rb', '.swift', '.kt'}
        design_exts = {'.fig', '.sketch', '.xd', '.psd', '.ai', '.indd', '.afdesign', '.afphoto'}
        model3d_exts = {'.blend', '.fbx', '.obj', '.stl', '.gltf', '.glb', '.dae', '.3ds', '.c4d', '.ma', '.mb'}
        project_exts = {'.aep', '.prproj', '.drp', '.flp', '.als', '.logicx', '.reason', '.cpr', '.rpp', '.sesx'}
        
        if ext in image_exts:
            return MediaType.IMAGE
        elif ext in video_exts:
            return MediaType.VIDEO
        elif ext in audio_exts:
            return MediaType.AUDIO
        elif ext in doc_exts:
            return MediaType.DOCUMENT
        elif ext in code_exts:
            return MediaType.CODE
        elif ext in design_exts:
            return MediaType.DESIGN
        elif ext in model3d_exts:
            return MediaType.MODEL_3D
        elif ext in project_exts:
            return MediaType.PROJECT
        else:
            return MediaType.DOCUMENT  # Default
    
    def _generate_summary(self, insights: List[CreativeInsight]) -> str:
        """Generate human-readable summary from insights."""
        if not insights:
            return "No insights generated."
        
        by_domain = {}
        for insight in insights:
            by_domain.setdefault(insight.domain.value, []).append(insight)
        
        parts = []
        for domain, domain_insights in by_domain.items():
            top = sorted(domain_insights, key=lambda x: x.confidence, reverse=True)[:2]
            findings = "; ".join([i.finding for i in top])
            parts.append(f"{domain.title()}: {findings}")
        
        return " | ".join(parts)
    
    def _calculate_quality_score(self, insights: List[CreativeInsight]) -> float:
        """Calculate overall quality score from insights."""
        if not insights:
            return 5.0
        
        # Weight by confidence and domain importance
        weights = {
            IntelligenceDomain.NARRATIVE: 1.0,
            IntelligenceDomain.VISUAL: 1.2,
            IntelligenceDomain.SYMBOLISM: 0.8,
            IntelligenceDomain.DESIGN: 1.3,
            IntelligenceDomain.MARKETING: 0.9,
            IntelligenceDomain.PSYCHOLOGICAL: 1.0,
        }
        
        total = 0.0
        weight_sum = 0.0
        
        for insight in insights:
            w = weights.get(insight.domain, 1.0)
            total += insight.confidence * w
            weight_sum += w
        
        avg_confidence = total / weight_sum if weight_sum > 0 else 0.5
        return round(avg_confidence * 10, 1)
    
    # ─── Status ───
    
    def status(self) -> Dict:
        """Get system status."""
        return {
            "session_id": self.session_id,
            "started_at": self.started_at,
            "current_project": self.current_project.name if self.current_project else None,
            "observation_active": self.observation_active,
            "memory_stats": self._memory.stats() if self._memory else {},
            "integrations": list(self._integrations.keys()),
            "intelligence_engines": [d.value for d in self._intelligence_engines.keys()],
        }
    
    async def shutdown(self):
        """Graceful shutdown."""
        print("\n🌅 Shutting down AURORA...")
        if self.observation_active:
            await self.stop_observation()
        if self._memory:
            await self._memory.close()
        if self._protocol_layer:
            await self._protocol_layer.shutdown()
        print("✅ Shutdown complete")


# ─── Convenience Functions ───

async def create_aurora(config: Optional[Dict] = None) -> AuroraCore:
    """Factory function to create and initialize AURORA."""
    aurora = AuroraCore(config)
    await aurora.initialize()
    return aurora


# ─── Main Entry Point ───

async def main():
    """Demo entry point."""
    aurora = await create_aurora()
    
    # Example: Create project
    project = await aurora.create_project(
        name="Brand Campaign 2026",
        description="Q4 brand refresh campaign",
        target_audience="Urban professionals 25-40",
        goals=["Increase brand awareness", "Drive conversions", "Establish visual identity"]
    )
    
    # Example: Interpret media (if files exist)
    # media = await aurora.interpret("path/to/asset.png")
    # critiques = await aurora.critique(media)
    # improvements = await aurora.improve(media)
    
    print("\n📊 System Status:")
    print(json.dumps(aurora.status(), indent=2))
    
    await aurora.shutdown()


if __name__ == "__main__":
    asyncio.run(main())