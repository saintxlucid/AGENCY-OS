"""
AGENCY OS — Industry Packs
Vertical solutions for specific creative industries.
"""
from __future__ import annotations
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class IndustryPack:
    """A vertical solution for a specific creative industry."""
    pack_id: str
    name: str
    industry: str
    description: str
    workflows: List[Dict] = field(default_factory=list)
    agents: List[Dict] = field(default_factory=list)
    templates: List[Dict] = field(default_factory=list)
    kpis: List[str] = field(default_factory=list)
    terminology: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True

    def to_dict(self) -> Dict:
        return {
            "pack_id": self.pack_id,
            "name": self.name,
            "industry": self.industry,
            "description": self.description,
            "workflows": self.workflows,
            "agents": self.agents,
            "templates_count": len(self.templates),
            "kpis": self.kpis
        }


class IndustryPackRegistry:
    """
    Registry of industry-specific packs.
    
    Each pack includes:
    - Tailored workflows
    - Specialized agents
    - Industry templates
    - Relevant KPIs
    - Industry terminology
    """

    def __init__(self):
        self.packs: Dict[str, IndustryPack] = {}
        self._create_default_packs()

    def _create_default_packs(self):
        """Create all 15 default industry packs."""

        # 1. Advertising Agency
        self.packs["advertising"] = IndustryPack(
            pack_id="advertising",
            name="Advertising Agency",
            industry="advertising",
            description="Full-service advertising agency operations",
            workflows=[
                {"name": "Campaign Production", "steps": ["Research", "Brief", "Creative", "Production", "Delivery"]},
                {"name": "Media Planning", "steps": ["Audience Analysis", "Channel Selection", "Budget Allocation", "Scheduling"]},
            ],
            agents=[
                {"name": "Media Planner", "domain": "marketing"},
                {"name": "Creative Director", "domain": "all"},
                {"name": "Copywriter", "domain": "narrative"},
            ],
            kpis=["ROAS", "CTR", "CPA", "Impressions", "Reach", "Frequency"],
            terminology={"brief": "creative brief", "deliverable": "ad creative", "client": "brand"}
        )

        # 2. Branding Studio
        self.packs["branding"] = IndustryPack(
            pack_id="branding",
            name="Branding Studio",
            industry="branding",
            description="Brand identity and strategy studio",
            workflows=[
                {"name": "Brand Identity", "steps": ["Discovery", "Strategy", "Visual Identity", "Guidelines", "Rollout"]},
                {"name": "Brand Refresh", "steps": ["Audit", "Research", "Evolution", "Implementation"]},
            ],
            agents=[
                {"name": "Brand Strategist", "domain": "marketing"},
                {"name": "Identity Designer", "domain": "visual"},
            ],
            kpis=["Brand Awareness", "Brand Recall", "Net Promoter Score", "Share of Voice"],
            terminology={"brief": "brand brief", "deliverable": "brand system", "client": "brand"}
        )

        # 3. Video Production House
        self.packs["video_production"] = IndustryPack(
            pack_id="video_production",
            name="Video Production House",
            industry="video_production",
            description="Video and film production studio",
            workflows=[
                {"name": "Video Production", "steps": ["Pre-production", "Production", "Post-production", "Delivery"]},
                {"name": "Commercial Production", "steps": ["Brief", "Storyboard", "Shoot", "Edit", "Delivery"]},
            ],
            agents=[
                {"name": "Video Editor", "domain": "narrative"},
                {"name": "Colorist", "domain": "visual"},
            ],
            kpis=["Production Days", "Budget Variance", "Revision Rounds", "Client Satisfaction"],
            terminology={"brief": "production brief", "deliverable": "final cut", "client": "production"}
        )

        # 4. Architecture Firm
        self.packs["architecture"] = IndustryPack(
            pack_id="architecture",
            name="Architecture Firm",
            industry="architecture",
            description="Architectural visualization and design",
            workflows=[
                {"name": "Design Development", "steps": ["Concept", "Schematic", "Design Development", "Construction Docs"]},
                {"name": "Visualization", "steps": ["Modeling", "Texturing", "Lighting", "Rendering"]},
            ],
            kpis=["Project Timeline", "Budget Accuracy", "Client Approvals", "Revision Rate"],
            terminology={"brief": "design brief", "deliverable": "visualization", "client": "developer"}
        )

        # 5. Game Studio
        self.packs["game_studio"] = IndustryPack(
            pack_id="game_studio",
            name="Game Studio",
            industry="gaming",
            description="Game development and art production",
            workflows=[
                {"name": "Game Art Pipeline", "steps": ["Concept Art", "3D Modeling", "Texturing", "Rigging", "Animation"]},
                {"name": "Level Design", "steps": ["Blockout", "Art Pass", "Lighting", "Polish"]},
            ],
            kpis=["Art Velocity", "Polygon Count", "Draw Calls", "Frame Rate"],
            terminology={"brief": "art brief", "deliverable": "game asset", "client": "publisher"}
        )

        # 6. Fashion Brand
        self.packs["fashion"] = IndustryPack(
            pack_id="fashion",
            name="Fashion Brand",
            industry="fashion",
            description="Fashion design and marketing",
            workflows=[
                {"name": "Collection Development", "steps": ["Trend Research", "Sketching", "Sampling", "Production"]},
                {"name": "Campaign Shoot", "steps": ["Creative Direction", "Photoshoot", "Retouching", "Publishing"]},
            ],
            kpis=["Sell-through Rate", "Return Rate", "Social Engagement", "E-commerce Conversion"],
            terminology={"brief": "season brief", "deliverable": "lookbook", "client": "retailer"}
        )

        # 7. Film Studio
        self.packs["film_studio"] = IndustryPack(
            pack_id="film_studio",
            name="Film Studio",
            industry="film",
            description="Film and television production",
            workflows=[
                {"name": "Film Production", "steps": ["Development", "Pre-production", "Production", "Post-production", "Distribution"]},
                {"name": "VFX Pipeline", "steps": ["Previz", "Tracking", "Animation", "Compositing", "Final"]},
            ],
            kpis=["Shooting Days", "Budget Variance", "VFX Shots", "On Schedule"],
            terminology={"brief": "script", "deliverable": "final cut", "client": "studio"}
        )

        # 8. Photography Studio
        self.packs["photography"] = IndustryPack(
            pack_id="photography",
            name="Photography Studio",
            industry="photography",
            description="Photography and retouching services",
            workflows=[
                {"name": "Photo Shoot", "steps": ["Brief", "Planning", "Shoot", "Culling", "Retouching", "Delivery"]},
                {"name": "Product Photography", "steps": ["Styling", "Shooting", "Editing", "Delivery"]},
            ],
            kpis=["Shoots per Month", "Turnaround Time", "Client Satisfaction", "Revenue per Shoot"],
            terminology={"brief": "shoot brief", "deliverable": "edited photos", "client": "brand"}
        )

        # 9. Marketing Consultancy
        self.packs["marketing"] = IndustryPack(
            pack_id="marketing",
            name="Marketing Consultancy",
            industry="marketing",
            description="Strategic marketing consulting",
            workflows=[
                {"name": "Strategy Development", "steps": ["Audit", "Research", "Strategy", "Roadmap"]},
                {"name": "Campaign Planning", "steps": ["Objectives", "Audience", "Channels", "Budget", "KPIs"]},
            ],
            kpis=["ROI", "Customer Acquisition Cost", "Lifetime Value", "Market Share"],
            terminology={"brief": "strategy brief", "deliverable": "marketing plan", "client": "brand"}
        )

        # 10. Podcast Network
        self.packs["podcast"] = IndustryPack(
            pack_id="podcast",
            name="Podcast Network",
            industry="podcast",
            description="Podcast production and distribution",
            workflows=[
                {"name": "Episode Production", "steps": ["Planning", "Recording", "Editing", "Publishing", "Promotion"]},
                {"name": "Show Launch", "steps": ["Concept", "Branding", "Trailer", "Launch"]},
            ],
            kpis=["Downloads", "Listeners", "Retention", "Sponsorship Revenue"],
            terminology={"brief": "episode brief", "deliverable": "final episode", "client": "sponsor"}
        )

        # 11. Music Label
        self.packs["music"] = IndustryPack(
            pack_id="music",
            name="Music Label",
            industry="music",
            description="Music production and artist management",
            workflows=[
                {"name": "Album Production", "steps": ["Songwriting", "Recording", "Mixing", "Mastering", "Release"]},
                {"name": "Music Video", "steps": ["Concept", "Storyboard", "Shoot", "Edit", "Release"]},
            ],
            kpis=["Streams", "Revenue", "Chart Position", "Social Growth"],
            terminology={"brief": "creative direction", "deliverable": "master", "client": "artist"}
        )

        # 12. Event Agency
        self.packs["events"] = IndustryPack(
            pack_id="events",
            name="Event Agency",
            industry="events",
            description="Event planning and production",
            workflows=[
                {"name": "Event Production", "steps": ["Concept", "Planning", "Design", "Setup", "Execution", "Wrap"]},
                {"name": "Virtual Event", "steps": ["Platform", "Content", "Rehearsal", "Live", "Post-event"]},
            ],
            kpis=["Attendee Satisfaction", "Budget Adherence", "Ticket Sales", "Sponsor Revenue"],
            terminology={"brief": "event brief", "deliverable": "event experience", "client": "organizer"}
        )

        # 13. Social Media Agency
        self.packs["social_media"] = IndustryPack(
            pack_id="social_media",
            name="Social Media Agency",
            industry="social_media",
            description="Social media content and strategy",
            workflows=[
                {"name": "Content Calendar", "steps": ["Strategy", "Content Plan", "Creation", "Scheduling", "Analytics"]},
                {"name": "Campaign Launch", "steps": ["Brief", "Creative", "Approvals", "Launch", "Optimize"]},
            ],
            kpis=["Engagement Rate", "Followers", "Reach", "Conversions"],
            terminology={"brief": "content brief", "deliverable": "content", "client": "brand"}
        )

        # 14. Software Agency
        self.packs["software"] = IndustryPack(
            pack_id="software",
            name="Software Agency",
            industry="software",
            description="Software development and design",
            workflows=[
                {"name": "Product Development", "steps": ["Discovery", "Design", "Development", "Testing", "Launch"]},
                {"name": "Design System", "steps": ["Audit", "Tokens", "Components", "Documentation"]},
            ],
            kpis=["Velocity", "Bug Rate", "Uptime", "Customer Satisfaction"],
            terminology={"brief": "product brief", "deliverable": "feature", "client": "product"}
        )

        # 15. Design Agency
        self.packs["design_agency"] = IndustryPack(
            pack_id="design_agency",
            name="Design Agency",
            industry="design",
            description="Digital product design agency",
            workflows=[
                {"name": "Product Design", "steps": ["Research", "Wireframes", "Visual Design", "Prototype", "Handoff"]},
                {"name": "Brand Website", "steps": ["Discovery", "Design", "Development", "Launch"]},
            ],
            kpis=["Project Margin", "Client Satisfaction", "Revision Rounds", "On-time Delivery"],
            terminology={"brief": "design brief", "deliverable": "design files", "client": "brand"}
        )

    def get_pack(self, pack_id: str) -> Optional[IndustryPack]:
        """Get an industry pack by ID."""
        return self.packs.get(pack_id)

    def list_packs(self) -> List[IndustryPack]:
        """List all available industry packs."""
        return list(self.packs.values())

    def get_packs_by_industry(self, industry: str) -> List[IndustryPack]:
        """Get packs for a specific industry."""
        return [p for p in self.packs.values() if p.industry == industry]

    def enable_pack(self, org_id: str, pack_id: str) -> Dict:
        """Enable an industry pack for an organization."""
        pack = self.packs.get(pack_id)
        if not pack:
            return {"error": "Pack not found"}

        return {
            "status": "enabled",
            "pack_id": pack_id,
            "org_id": org_id,
            "workflows": len(pack.workflows),
            "agents": len(pack.agents),
            "templates": len(pack.templates)
        }