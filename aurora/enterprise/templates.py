"""
AGENCY OS — Sample Project Templates
Pre-built templates for common agency project types.
"""
from __future__ import annotations
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class ProjectTemplate:
    """A reusable project template."""
    template_id: str
    name: str
    description: str
    category: str
    default_brief: str
    default_goals: List[str]
    default_tasks: List[Dict[str, str]]
    default_tags: List[str]
    estimated_duration_days: int
    suggested_budget_range: tuple  # (min, max)


# ─── Template Library ───

TEMPLATES: Dict[str, ProjectTemplate] = {
    "brand_identity": ProjectTemplate(
        template_id="brand_identity",
        name="Brand Identity",
        description="Complete brand identity development including logo, colors, typography, and guidelines",
        category="branding",
        default_brief="Develop a comprehensive brand identity that communicates the client's values, mission, and market position. Deliverables include logo, color palette, typography system, and brand guidelines.",
        default_goals=["Establish visual identity", "Create brand guidelines", "Ensure brand consistency"],
        default_tasks=[
            {"title": "Discovery & Research", "estimated_hours": "16"},
            {"title": "Moodboard & Direction", "estimated_hours": "8"},
            {"title": "Logo Concepts", "estimated_hours": "24"},
            {"title": "Color & Typography", "estimated_hours": "12"},
            {"title": "Brand Guidelines", "estimated_hours": "20"},
            {"title": "Final Delivery", "estimated_hours": "8"},
        ],
        default_tags=["branding", "identity", "logo", "guidelines"],
        estimated_duration_days=30,
        suggested_budget_range=(15000, 50000)
    ),
    "website_design": ProjectTemplate(
        template_id="website_design",
        name="Website Design",
        description="Full website design from wireframes to final assets",
        category="digital",
        default_brief="Design a modern, responsive website that converts visitors into customers. Includes wireframes, visual design, and developer-ready assets.",
        default_goals=["Increase conversions", "Improve user experience", "Mobile-first design"],
        default_tasks=[
            {"title": "Discovery & Strategy", "estimated_hours": "12"},
            {"title": "Sitemap & Wireframes", "estimated_hours": "16"},
            {"title": "Visual Design", "estimated_hours": "32"},
            {"title": "Responsive Layouts", "estimated_hours": "16"},
            {"title": "Design System", "estimated_hours": "12"},
            {"title": "Handoff & Documentation", "estimated_hours": "8"},
        ],
        default_tags=["web", "design", "responsive", "ux"],
        estimated_duration_days=21,
        suggested_budget_range=(10000, 35000)
    ),
    "campaign_production": ProjectTemplate(
        template_id="campaign_production",
        name="Campaign Production",
        description="End-to-end campaign production from concept to delivery",
        category="marketing",
        default_brief="Create a multi-channel marketing campaign including creative concept, ad copy, visual assets, and production-ready files.",
        default_goals=["Increase brand awareness", "Drive conversions", "Multi-channel consistency"],
        default_tasks=[
            {"title": "Campaign Strategy", "estimated_hours": "12"},
            {"title": "Creative Concept", "estimated_hours": "16"},
            {"title": "Copywriting", "estimated_hours": "12"},
            {"title": "Visual Design", "estimated_hours": "32"},
            {"title": "Production", "estimated_hours": "24"},
            {"title": "Review & Delivery", "estimated_hours": "8"},
        ],
        default_tags=["campaign", "marketing", "multi-channel"],
        estimated_duration_days=25,
        suggested_budget_range=(20000, 75000)
    ),
    "social_media_kit": ProjectTemplate(
        template_id="social_media_kit",
        name="Social Media Kit",
        description="Social media templates and content strategy",
        category="social",
        default_brief="Design a comprehensive social media kit with templates, content guidelines, and a posting strategy for all major platforms.",
        default_goals=["Consistent social presence", "Increase engagement", "Streamline content creation"],
        default_tasks=[
            {"title": "Platform Audit", "estimated_hours": "8"},
            {"title": "Content Strategy", "estimated_hours": "12"},
            {"title": "Template Design", "estimated_hours": "24"},
            {"title": "Content Guidelines", "estimated_hours": "8"},
            {"title": "Delivery", "estimated_hours": "4"},
        ],
        default_tags=["social", "templates", "content"],
        estimated_duration_days=14,
        suggested_budget_range=(5000, 15000)
    ),
    "video_production": ProjectTemplate(
        template_id="video_production",
        name="Video Production",
        description="Professional video production from script to final cut",
        category="video",
        default_brief="Produce a professional marketing video including scripting, storyboarding, filming, editing, and final delivery in multiple formats.",
        default_goals=["Engaging video content", "Multi-platform delivery", "Brand consistency"],
        default_tasks=[
            {"title": "Script Writing", "estimated_hours": "16"},
            {"title": "Storyboard", "estimated_hours": "12"},
            {"title": "Pre-production", "estimated_hours": "12"},
            {"title": "Filming", "estimated_hours": "24"},
            {"title": "Editing", "estimated_hours": "32"},
            {"title": "Sound & Color", "estimated_hours": "16"},
            {"title": "Delivery", "estimated_hours": "8"},
        ],
        default_tags=["video", "production", "editing"],
        estimated_duration_days=35,
        suggested_budget_range=(25000, 100000)
    ),
    "photo_shoot": ProjectTemplate(
        template_id="photo_shoot",
        name="Photo Shoot",
        description="Professional photography shoot and post-production",
        category="photography",
        default_brief="Plan and execute a professional photography shoot including concept development, styling, shooting, and post-production.",
        default_goals=["High-quality imagery", "Brand consistency", "Multi-use assets"],
        default_tasks=[
            {"title": "Concept Development", "estimated_hours": "8"},
            {"title": "Location Scouting", "estimated_hours": "4"},
            {"title": "Styling & Prep", "estimated_hours": "8"},
            {"title": "Photoshoot", "estimated_hours": "16"},
            {"title": "Post-production", "estimated_hours": "24"},
            {"title": "Delivery", "estimated_hours": "4"},
        ],
        default_tags=["photography", "shoot", "post-production"],
        estimated_duration_days=14,
        suggested_budget_range=(8000, 30000)
    ),
    "print_design": ProjectTemplate(
        template_id="print_design",
        name="Print Design",
        description="Print-ready design for brochures, posters, and collateral",
        category="print",
        default_brief="Design print-ready materials including brochures, posters, business cards, and marketing collateral.",
        default_goals=["Print-ready files", "Brand consistency", "Cost-effective production"],
        default_tasks=[
            {"title": "Requirements Gathering", "estimated_hours": "4"},
            {"title": "Concept Design", "estimated_hours": "12"},
            {"title": "Layout & Design", "estimated_hours": "24"},
            {"title": "Revisions", "estimated_hours": "8"},
            {"title": "Print Preparation", "estimated_hours": "8"},
        ],
        default_tags=["print", "brochure", "poster", "collateral"],
        estimated_duration_days=14,
        suggested_budget_range=(5000, 20000)
    ),
    "ui_ux_design": ProjectTemplate(
        template_id="ui_ux_design",
        name="UI/UX Design",
        description="User interface and experience design for digital products",
        category="digital",
        default_brief="Design a user-centered digital product including research, wireframes, prototypes, and high-fidelity designs.",
        default_goals=["Improve user experience", "Increase engagement", "Accessible design"],
        default_tasks=[
            {"title": "User Research", "estimated_hours": "16"},
            {"title": "Information Architecture", "estimated_hours": "12"},
            {"title": "Wireframes", "estimated_hours": "16"},
            {"title": "Visual Design", "estimated_hours": "32"},
            {"title": "Prototype", "estimated_hours": "16"},
            {"title": "Usability Testing", "estimated_hours": "12"},
        ],
        default_tags=["ui", "ux", "prototype", "research"],
        estimated_duration_days=28,
        suggested_budget_range=(20000, 60000)
    ),
    "motion_graphics": ProjectTemplate(
        template_id="motion_graphics",
        name="Motion Graphics",
        description="Animated motion graphics and video effects",
        category="motion",
        default_brief="Create engaging motion graphics including logo animations, explainer videos, and social media animations.",
        default_goals=["Engaging motion content", "Brand animation", "Multi-platform delivery"],
        default_tasks=[
            {"title": "Creative Direction", "estimated_hours": "8"},
            {"title": "Storyboard", "estimated_hours": "12"},
            {"title": "Animation", "estimated_hours": "32"},
            {"title": "Sound Design", "estimated_hours": "8"},
            {"title": "Delivery", "estimated_hours": "4"},
        ],
        default_tags=["motion", "animation", "video"],
        estimated_duration_days=21,
        suggested_budget_range=(10000, 40000)
    ),
}


def get_template(template_id: str) -> Optional[ProjectTemplate]:
    """Get a template by ID."""
    return TEMPLATES.get(template_id)


def list_templates(category: Optional[str] = None) -> List[ProjectTemplate]:
    """List all templates, optionally filtered by category."""
    templates = list(TEMPLATES.values())
    if category:
        templates = [t for t in templates if t.category == category]
    return templates


def get_categories() -> List[str]:
    """Get all unique template categories."""
    return sorted(set(t.category for t in TEMPLATES.values()))


def apply_template(template_id: str, org_id: str, client_id: Optional[str] = None,
                   custom_name: Optional[str] = None) -> Dict[str, Any]:
    """Apply a template to create a project plan."""
    template = TEMPLATES.get(template_id)
    if not template:
        raise ValueError(f"Template not found: {template_id}")

    return {
        "name": custom_name or template.name,
        "description": template.description,
        "brief": template.default_brief,
        "goals": template.default_goals,
        "tasks": template.default_tasks,
        "tags": template.default_tags,
        "estimated_duration_days": template.estimated_duration_days,
        "suggested_budget_range": template.suggested_budget_range,
    }