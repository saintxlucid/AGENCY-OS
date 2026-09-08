"""
Design Intelligence Engine
Analyzes design systems, UI/UX, accessibility, component architecture.
"""
from __future__ import annotations

from typing import List, Optional
from aurora.core import IntelligenceEngine, IntelligenceDomain, CreativeInsight, MediaInterpretation, ProjectContext


class DesignIntelligence(IntelligenceEngine):
    """Analyzes design quality, systems, accessibility, and UX patterns."""
    
    def __init__(self):
        super().__init__(IntelligenceDomain.DESIGN)
        self._heuristics = self._load_heuristics()
    
    def _load_heuristics(self) -> Dict:
        return {
            "nielsen": [
                "visibility_of_system_status",
                "match_between_system_and_real_world",
                "user_control_and_freedom",
                "consistency_and_standards",
                "error_prevention",
                "recognition_rather_than_recall",
                "flexibility_and_efficiency",
                "aesthetic_and_minimalist",
                "help_users_recognize_diagnose_recover",
                "help_and_documentation"
            ],
            "wcag": {
                "perceivable": ["text_alternatives", "time_based_media", "adaptable", "distinguishable"],
                "operable": ["keyboard_accessible", "enough_time", "seizures", "navigable", "input_modalities"],
                "understandable": ["readable", "predictable", "input_assistance"],
                "robust": ["compatible"]
            },
            "design_system": [
                "token_structure", "component_library", "documentation",
                "versioning", "theming", "accessibility", "testing"
            ]
        }
    
    async def analyze(self, media: MediaInterpretation, context: Optional[ProjectContext] = None) -> List[CreativeInsight]:
        insights = []
        text = self._extract_text(media).lower()
        
        # Design system maturity
        ds = self._analyze_design_system(text)
        if ds:
            insights.append(ds)
        
        # Accessibility
        a11y = self._analyze_accessibility(text)
        if a11y:
            insights.append(a11y)
        
        # UI Patterns
        ui = self._analyze_ui_patterns(text)
        if ui:
            insights.append(ui)
        
        # Responsive/Adaptive
        resp = self._analyze_responsive(text)
        if resp:
            insights.append(resp)
        
        # Design tokens
        tokens = self._analyze_tokens(text)
        if tokens:
            insights.append(tokens)
        
        return insights
    
    def _extract_text(self, media: MediaInterpretation) -> str:
        parts = [media.summary]
        for insight in media.insights:
            parts.append(insight.finding)
            parts.extend(insight.evidence)
        return " ".join(parts)
    
    def _analyze_design_system(self, text: str) -> Optional[CreativeInsight]:
        indicators = ["design system", "component library", "style guide", "pattern library", "ui kit"]
        score = sum(text.count(ind) for ind in indicators)
        
        if score > 0:
            maturity = "nascent"
            if score > 3:
                maturity = "mature"
            elif score > 1:
                maturity = "developing"
            
            return CreativeInsight(
                domain=self.domain,
                category="design_system",
                finding=f"Design system maturity: {maturity} ({score} indicators)",
                confidence=0.7,
                suggestions=["Document component APIs", "Establish design token pipeline", "Automate visual regression testing"]
            )
        
        return CreativeInsight(
            domain=self.domain,
            category="design_system",
            finding="No formal design system detected",
            confidence=0.6,
            suggestions=["Create component inventory", "Define design tokens (color, spacing, typography)", "Build component library with Storybook"]
        )
    
    def _analyze_accessibility(self, text: str) -> Optional[CreativeInsight]:
        a11y_terms = ["accessibility", "a11y", "wcag", "contrast", "screen reader", "aria", "semantic", "keyboard", "focus", "alt text"]
        found = [t for t in a11y_terms if t in text]
        
        if found:
            return CreativeInsight(
                domain=self.domain,
                category="accessibility",
                finding=f"Accessibility considerations present: {', '.join(found)}",
                confidence=0.75,
                suggestions=["Run automated a11y audit (axe, lighthouse)", "Test with screen readers (NVDA, VoiceOver)", "Verify focus management", "Test color contrast ratios"]
            )
        
        return CreativeInsight(
            domain=self.domain,
            category="accessibility",
            finding="No explicit accessibility considerations detected",
            confidence=0.6,
            suggestions=["Audit against WCAG 2.1 AA", "Add semantic HTML", "Ensure keyboard navigation", "Provide alt text for all images", "Test with real users with disabilities"]
        )
    
    def _analyze_ui_patterns(self, text: str) -> Optional[CreativeInsight]:
        patterns = ["modal", "dropdown", "tabs", "accordion", "carousel", "breadcrumb", "pagination", "tooltip", "toast", "sidebar", "navigation", "form", "table", "card", "list"]
        found = [p for p in patterns if p in text]
        
        if found:
            return CreativeInsight(
                domain=self.domain,
                category="ui_patterns",
                finding=f"UI patterns detected: {', '.join(found)}",
                confidence=0.7,
                suggestions=["Verify patterns follow platform conventions", "Test pattern usability", "Document pattern variations", "Consider compound components for flexibility"]
            )
        
        return None
    
    def _analyze_responsive(self, text: str) -> Optional[CreativeInsight]:
        resp_terms = ["responsive", "mobile", "breakpoint", "fluid", "adaptive", "viewport", "media query", "container query"]
        found = [t for t in resp_terms if t in text]
        
        if found:
            return CreativeInsight(
                domain=self.domain,
                category="responsive_design",
                finding=f"Responsive design considerations: {', '.join(found)}",
                confidence=0.7,
                suggestions=["Test at all breakpoints", "Verify touch targets (min 44x44px)", "Check content reflow", "Test landscape/portrait"]
            )
        
        return CreativeInsight(
            domain=self.domain,
            category="responsive_design",
            finding="Responsive design not explicitly addressed",
            confidence=0.5,
            suggestions=["Define breakpoint strategy", "Design mobile-first", "Test on real devices", "Consider container queries"]
        )
    
    def _analyze_tokens(self, text: str) -> Optional[CreativeInsight]:
        token_terms = ["design token", "color token", "spacing token", "typography token", "semantic token", "alias token"]
        found = [t for t in token_terms if t in text]
        
        if found:
            return CreativeInsight(
                domain=self.domain,
                category="design_tokens",
                finding=f"Design token usage: {', '.join(found)}",
                confidence=0.75,
                suggestions=["Separate primitive vs semantic tokens", "Create token pipeline (Figma → Code)", "Version tokens independently", "Document token usage guidelines"]
            )
        
        return CreativeInsight(
            domain=self.domain,
            category="design_tokens",
            finding="Design tokens not explicitly structured",
            confidence=0.5,
            suggestions=["Extract primitive values (colors, spacing, type)", "Create semantic aliases (primary, surface, on-primary)", "Build token delivery pipeline"]
        )
    
    async def critique(self, media: MediaInterpretation, context: Optional[ProjectContext] = None) -> List[CreativeInsight]:
        return [
            CreativeInsight(
                domain=self.domain,
                category="consistency",
                finding="Verify visual and behavioral consistency across all components",
                confidence=0.85,
                suggestions=["Audit spacing scale adherence", "Check color usage against tokens", "Verify typography scale", "Test component states (hover, focus, disabled, error)"]
            ),
            CreativeInsight(
                domain=self.domain,
                category="scalability",
                finding="Design for scale: component variants, theming, localization",
                confidence=0.8,
                suggestions=["Plan for dark mode from start", "Design for RTL languages", "Create variant system (size, state, context)", "Document composition patterns"]
            ),
            CreativeInsight(
                domain=self.domain,
                category="handoff",
                finding="Ensure design-to-development handoff clarity",
                confidence=0.8,
                suggestions=["Annotate interactions and states", "Provide redlines/spacing specs", "Document responsive behavior", "Link to component library (Storybook)"]
            )
        ]
    
    async def improve(self, media: MediaInterpretation, context: Optional[ProjectContext] = None) -> List[CreativeInsight]:
        return [
            CreativeInsight(
                domain=self.domain,
                category="system_maturity",
                finding="Advance design system maturity level",
                confidence=0.85,
                suggestions=[
                    "Level 1: Component library + tokens",
                    "Level 2: Documentation + testing + versioning",
                    "Level 3: Automation (Figma sync, token pipeline)",
                    "Level 4: Governance + contribution model + metrics"
                ]
            ),
            CreativeInsight(
                domain=self.domain,
                category="accessibility_excellence",
                finding="Move beyond compliance to inclusive design",
                confidence=0.9,
                suggestions=[
                    "Co-design with disabled users",
                    "Test with diverse assistive tech",
                    "Create accessible component primitives",
                    "Build accessibility into CI/CD",
                    "Document accessibility patterns"
                ]
            )
        ]