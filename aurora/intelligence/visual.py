"""
Visual Intelligence Engine
Analyzes composition, color, lighting, typography, and visual hierarchy.
"""
from __future__ import annotations

from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from aurora.core import IntelligenceEngine, IntelligenceDomain, CreativeInsight, MediaInterpretation, ProjectContext


class VisualIntelligence(IntelligenceEngine):
    """Analyzes visual composition, color theory, lighting, hierarchy."""
    
    def __init__(self):
        super().__init__(IntelligenceDomain.VISUAL)
        self._principles = self._load_principles()
    
    def _load_principles(self) -> Dict:
        return {
            "composition_rules": [
                "rule_of_thirds", "golden_ratio", "leading_lines", "symmetry",
                "asymmetry", "framing", "negative_space", "depth_layers"
            ],
            "color_harmonies": [
                "monochromatic", "analogous", "complementary", "split_complementary",
                "triadic", "tetradic", "warm_cool", "high_contrast"
            ],
            "lighting_patterns": [
                "rembrandt", "butterfly", "split", "loop", "broad", "short",
                "high_key", "low_key", "natural", "dramatic", "three_point"
            ],
            "gestalt_principles": [
                "proximity", "similarity", "closure", "continuity",
                "figure_ground", "symmetry", "common_fate"
            ],
        }
    
    async def analyze(self, media: MediaInterpretation, context: Optional[ProjectContext] = None) -> List[CreativeInsight]:
        insights = []
        
        # Extract visual context
        visual_text = self._extract_visual_context(media)
        
        if not visual_text:
            return [CreativeInsight(
                domain=self.domain,
                category="composition",
                finding="Visual analysis requires image/video media",
                confidence=0.2,
                suggestions=["Provide visual media for composition analysis"]
            )]
        
        # Composition analysis
        comp = self._analyze_composition(visual_text, media)
        if comp:
            insights.append(comp)
        
        # Color analysis
        color = self._analyze_color(visual_text, media)
        if color:
            insights.append(color)
        
        # Lighting analysis
        light = self._analyze_lighting(visual_text, media)
        if light:
            insights.append(light)
        
        # Hierarchy
        hier = self._analyze_hierarchy(visual_text, media)
        if hier:
            insights.append(hier)
        
        # Typography (if applicable)
        typo = self._analyze_typography(visual_text, media)
        if typo:
            insights.append(typo)
        
        return insights
    
    def _extract_visual_context(self, media: MediaInterpretation) -> str:
        parts = [media.summary]
        for insight in media.insights:
            if insight.domain in (IntelligenceDomain.VISUAL, IntelligenceDomain.DESIGN):
                parts.append(insight.finding)
                parts.extend(insight.evidence)
        return " ".join(parts)
    
    def _analyze_composition(self, text: str, media: MediaInterpretation) -> Optional[CreativeInsight]:
        text_lower = text.lower()
        
        detected = []
        for rule in self._principles["composition_rules"]:
            if rule.replace("_", " ") in text_lower or rule in text_lower:
                detected.append(rule.replace("_", " "))
        
        if detected:
            return CreativeInsight(
                domain=self.domain,
                category="composition",
                finding=f"Composition techniques detected: {', '.join(detected)}",
                confidence=0.75,
                evidence=[f"Found {len(detected)} compositional principles"],
                suggestions=["Verify focal point aligns with primary composition rule", "Consider secondary composition for supporting elements"]
            )
        
        return CreativeInsight(
            domain=self.domain,
            category="composition",
            finding="No clear compositional framework detected",
            confidence=0.4,
            suggestions=["Apply Rule of Thirds or Golden Ratio for stronger composition", "Establish clear visual hierarchy", "Use leading lines to guide eye"]
        )
    
    def _analyze_color(self, text: str, media: MediaInterpretation) -> Optional[CreativeInsight]:
        text_lower = text.lower()
        
        detected = []
        for harmony in self._principles["color_harmonies"]:
            if harmony.replace("_", " ") in text_lower or harmony in text_lower:
                detected.append(harmony.replace("_", " "))
        
        # Look for color psychology
        psych = {
            "trust": ["blue", "navy", "teal"],
            "energy": ["red", "orange", "yellow"],
            "calm": ["green", "blue", "pastel"],
            "luxury": ["gold", "black", "purple", "deep"],
            "nature": ["green", "brown", "earth"],
            "innovation": ["purple", "cyan", "electric"],
            "urgency": ["red", "orange"],
            "optimism": ["yellow", "gold", "bright"],
        }
        
        psych_detected = []
        for mood, colors in psych.items():
            if any(c in text_lower for c in colors):
                psych_detected.append(mood)
        
        findings = []
        if detected:
            findings.append(f"Color harmony: {', '.join(detected)}")
        if psych_detected:
            findings.append(f"Psychological tone: {', '.join(psych_detected)}")
        
        if findings:
            return CreativeInsight(
                domain=self.domain,
                category="color_theory",
                finding=" | ".join(findings),
                confidence=0.7,
                evidence=[f"Color analysis from visual metadata"],
                suggestions=["Verify color accessibility (WCAG contrast)", "Test color blindness safety", "Ensure brand color consistency"]
            )
        
        return CreativeInsight(
            domain=self.domain,
            category="color_theory",
            finding="Color palette analysis requires visual data",
            confidence=0.3,
            suggestions=["Provide image for color extraction and harmony analysis"]
        )
    
    def _analyze_lighting(self, text: str, media: MediaInterpretation) -> Optional[CreativeInsight]:
        text_lower = text.lower()
        
        detected = []
        for pattern in self._principles["lighting_patterns"]:
            if pattern.replace("_", " ") in text_lower:
                detected.append(pattern.replace("_", " "))
        
        if detected:
            return CreativeInsight(
                domain=self.domain,
                category="lighting",
                finding=f"Lighting style: {', '.join(detected)}",
                confidence=0.7,
                evidence=[f"Detected {len(detected)} lighting patterns"],
                suggestions=["Ensure lighting supports narrative mood", "Check for consistent light direction", "Verify subject separation from background"]
            )
        
        return None
    
    def _analyze_hierarchy(self, text: str, media: MediaInterpretation) -> Optional[CreativeInsight]:
        keywords = ["hierarchy", "focal", "emphasis", "dominance", "priority", "visual weight", "eye flow"]
        text_lower = text.lower()
        
        if any(kw in text_lower for kw in keywords):
            return CreativeInsight(
                domain=self.domain,
                category="visual_hierarchy",
                finding="Visual hierarchy considerations present",
                confidence=0.65,
                suggestions=["Verify single primary focal point", "Ensure 3-level hierarchy (primary/secondary/tertiary)", "Check reading order matches intent"]
            )
        
        return CreativeInsight(
            domain=self.domain,
            category="visual_hierarchy",
            finding="Visual hierarchy not explicitly structured",
            confidence=0.5,
            suggestions=["Establish clear primary focal point", "Create secondary/tertiary information levels", "Use size, contrast, color for hierarchy"]
        )
    
    def _analyze_typography(self, text: str, media: MediaInterpretation) -> Optional[CreativeInsight]:
        typo_keywords = ["font", "typeface", "typography", "kerning", "leading", "tracking", "serif", "sans", "weight", "size"]
        text_lower = text.lower()
        
        if any(kw in text_lower for kw in typo_keywords):
            return CreativeInsight(
                domain=self.domain,
                category="typography",
                finding="Typography elements detected in visual analysis",
                confidence=0.6,
                suggestions=["Limit to 2 font families max", "Ensure readable line length (45-75 chars)", "Verify hierarchy through weight/size", "Check accessibility: min 16px body text"]
            )
        
        return None
    
    async def critique(self, media: MediaInterpretation, context: Optional[ProjectContext] = None) -> List[CreativeInsight]:
        critiques = []
        
        # Check for common visual issues
        critiques.append(CreativeInsight(
            domain=self.domain,
            category="composition",
            finding="Verify single clear focal point - avoid competing elements",
            confidence=0.8,
            suggestions=["Squint test: blur image, one element should dominate", "Remove or reduce secondary elements near focal point"]
        ))
        
        critiques.append(CreativeInsight(
            domain=self.domain,
            category="color_theory",
            finding="Check color contrast ratios meet WCAG AA (4.5:1) or AAA (7:1)",
            confidence=0.85,
            suggestions=["Test all text/background combinations", "Don't rely on color alone for meaning", "Provide patterns/textures as alternatives"]
        ))
        
        critiques.append(CreativeInsight(
            domain=self.domain,
            category="visual_hierarchy",
            finding="Ensure information hierarchy matches user/task priority",
            confidence=0.75,
            suggestions=["Map user goals to visual priority", "Test with 5-second glance test", "Verify mobile/desktop hierarchy consistency"]
        ))
        
        return critiques
    
    async def improve(self, media: MediaInterpretation, context: Optional[ProjectContext] = None) -> List[CreativeInsight]:
        improvements = []
        
        improvements.append(CreativeInsight(
            domain=self.domain,
            category="composition",
            finding="Strengthen composition with intentional negative space",
            confidence=0.8,
            suggestions=[
                "Add breathing room around focal point",
                "Use negative space to create tension or calm",
                "Align key elements to grid intersections"
            ]
        ))
        
        improvements.append(CreativeInsight(
            domain=self.domain,
            category="color_theory",
            finding="Refine palette for emotional impact and accessibility",
            confidence=0.85,
            suggestions=[
                "Select one dominant, one supporting, one accent color",
                "Test palette in grayscale for value structure",
                "Create dark/light mode variants",
                "Document hex codes for consistency"
            ]
        ))
        
        improvements.append(CreativeInsight(
            domain=self.domain,
            category="lighting",
            finding="Use lighting to direct attention and create depth",
            confidence=0.75,
            suggestions=[
                "Brightest area = primary focal point",
                "Rim light for subject separation",
                "Shadows to create dimension",
                "Consistent light direction throughout"
            ]
        ))
        
        return improvements