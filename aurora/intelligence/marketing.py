"""
Marketing Intelligence Engine
Analyzes positioning, audience, conversion, funnels, brand strategy.
"""
from __future__ import annotations

from typing import List, Optional
from aurora.core import IntelligenceEngine, IntelligenceDomain, CreativeInsight, MediaInterpretation, ProjectContext


class MarketingIntelligence(IntelligenceEngine):
    """Analyzes marketing effectiveness, positioning, audience alignment."""
    
    def __init__(self):
        super().__init__(IntelligenceDomain.MARKETING)
        self._frameworks = self._load_frameworks()
    
    def _load_frameworks(self) -> Dict:
        return {
            "positioning": ["category", "target", "differentiator", "proof", "reason_to_believe"],
            "brand_pyramid": ["essence", "personality", "benefits", "attributes", "rtb"],
            "messaging": ["headline", "subhead", "body", "cta", "social_proof", "objection_handling"],
            "funnel": ["awareness", "interest", "consideration", "intent", "evaluation", "purchase"],
            "persuasion": ["reciprocity", "commitment", "social_proof", "authority", "liking", "scarcity", "unity"],
        }
    
    async def analyze(self, media: MediaInterpretation, context: Optional[ProjectContext] = None) -> List[CreativeInsight]:
        insights = []
        text = self._extract_text(media).lower()
        
        # Positioning clarity
        pos = self._analyze_positioning(text, context)
        if pos:
            insights.append(pos)
        
        # Audience alignment
        aud = self._analyze_audience(text, context)
        if aud:
            insights.append(aud)
        
        # Message effectiveness
        msg = self._analyze_messaging(text)
        if msg:
            insights.append(msg)
        
        # CTA analysis
        cta = self._analyze_cta(text)
        if cta:
            insights.append(cta)
        
        # Funnel stage
        funnel = self._analyze_funnel_stage(text)
        if funnel:
            insights.append(funnel)
        
        return insights
    
    def _extract_text(self, media: MediaInterpretation) -> str:
        parts = [media.summary]
        for insight in media.insights:
            parts.append(insight.finding)
            parts.extend(insight.evidence)
        return " ".join(parts)
    
    def _analyze_positioning(self, text: str, context: Optional[ProjectContext]) -> Optional[CreativeInsight]:
        elements = []
        for elem in self._frameworks["positioning"]:
            if elem.replace("_", " ") in text:
                elements.append(elem)
        
        if context and context.target_audience:
            elements.append("target_defined")
        
        if elements:
            return CreativeInsight(
                domain=self.domain,
                category="positioning",
                finding=f"Positioning elements present: {', '.join(elements)} ({len(elements)}/5 core)",
                confidence=0.75,
                suggestions=["Ensure all 5 positioning elements are explicit", "Test positioning with target audience", "Differentiate clearly from top 3 competitors"]
            )
        
        return CreativeInsight(
            domain=self.domain,
            category="positioning",
            finding="Positioning framework incomplete or implicit",
            confidence=0.5,
            suggestions=["Define: Category, Target, Differentiator, Proof, Reason to Believe", "Write positioning statement", "Validate with customer interviews"]
        )
    
    def _analyze_audience(self, text: str, context: Optional[ProjectContext]) -> Optional[CreativeInsight]:
        if context and context.target_audience:
            return CreativeInsight(
                domain=self.domain,
                category="audience_alignment",
                finding=f"Target audience defined: {context.target_audience}",
                confidence=0.8,
                suggestions=["Create detailed personas", "Map audience jobs-to-be-done", "Identify pain points and gains", "Test message resonance per segment"]
            )
        
        # Look for audience signals in text
        signals = ["persona", "demographic", "psychographic", "segment", "target", "audience", "customer", "user"]
        found = [s for s in signals if s in text]
        
        if found:
            return CreativeInsight(
                domain=self.domain,
                category="audience_alignment",
                finding=f"Audience references found: {', '.join(found)}",
                confidence=0.6,
                suggestions=["Formalize audience definition", "Create primary/secondary personas", "Define anti-personas"]
            )
        
        return CreativeInsight(
            domain=self.domain,
            category="audience_alignment",
            finding="No explicit audience definition detected",
            confidence=0.4,
            suggestions=["Define primary target audience", "Research audience needs/motivations", "Create empathy maps"]
        )
    
    def _analyze_messaging(self, text: str) -> Optional[CreativeInsight]:
        msg_elements = []
        for elem in self._frameworks["messaging"]:
            if elem.replace("_", " ") in text:
                msg_elements.append(elem)
        
        if msg_elements:
            return CreativeInsight(
                domain=self.domain,
                category="messaging",
                finding=f"Messaging structure: {', '.join(msg_elements)}",
                confidence=0.7,
                suggestions=["Ensure headline promises value", "Subhead supports headline", "Body builds desire", "CTA is clear and compelling", "Address top 3 objections"]
            )
        
        return CreativeInsight(
            domain=self.domain,
            category="messaging",
            finding="Messaging structure not clearly defined",
            confidence=0.4,
            suggestions=["Apply headline-subhead-body-CTA structure", "Lead with value proposition", "Use customer language", "Test multiple headline variants"]
        )
    
    def _analyze_cta(self, text: str) -> Optional[CreativeInsight]:
        cta_patterns = ["call to action", "cta", "buy now", "sign up", "learn more", "get started", "try free", "download", "subscribe", "contact"]
        found = [p for p in cta_patterns if p in text]
        
        if found:
            return CreativeInsight(
                domain=self.domain,
                category="cta",
                finding=f"CTA patterns detected: {', '.join(found)}",
                confidence=0.75,
                suggestions=["Use action-oriented verbs", "Create urgency/scarcity if genuine", "Reduce friction (fewer fields)", "Test button color/placement", "Match CTA to funnel stage"]
            )
        
        return CreativeInsight(
            domain=self.domain,
            category="cta",
            finding="No clear call-to-action detected",
            confidence=0.5,
            suggestions=["Add primary CTA above fold", "Make CTA visually distinct", "Align CTA with user intent", "Test CTA copy variants"]
        )
    
    def _analyze_funnel_stage(self, text: str) -> Optional[CreativeInsight]:
        stage_keywords = {
            "awareness": ["awareness", "discover", "introduce", "brand", "reach", "impression"],
            "interest": ["interest", "learn", "explore", "engage", "content", "educate"],
            "consideration": ["consider", "compare", "evaluate", "demo", "trial", "case study", "review"],
            "intent": ["intent", "pricing", "proposal", "quote", "cart", "checkout"],
            "purchase": ["buy", "purchase", "order", "subscribe", "convert", "customer"],
        }
        
        scores = {}
        for stage, keywords in stage_keywords.items():
            scores[stage] = sum(text.count(kw) for kw in keywords)
        
        if any(scores.values()):
            primary = max(scores, key=scores.get)
            return CreativeInsight(
                domain=self.domain,
                category="funnel_stage",
                finding=f"Content aligns with {primary.title()} stage (scores: {scores})",
                confidence=0.7,
                suggestions=[f"Ensure {primary} stage content matches user needs", "Create content for adjacent stages", "Map full funnel content strategy"]
            )
        
        return None
    
    async def critique(self, media: MediaInterpretation, context: Optional[ProjectContext] = None) -> List[CreativeInsight]:
        return [
            CreativeInsight(
                domain=self.domain,
                category="value_proposition",
                finding="Verify value prop is specific, measurable, and differentiated",
                confidence=0.9,
                suggestions=["Quantify benefits (save 40% time, not 'save time')", "Name the alternative you're better than", "Test with 5-second test: what does this do?"]
            ),
            CreativeInsight(
                domain=self.domain,
                category="trust_signals",
                finding="Audit trust signals: social proof, authority, guarantees, security",
                confidence=0.85,
                suggestions=["Add customer logos/testimonials", "Show usage numbers", "Display certifications/badges", "Offer risk reversal (guarantee/trial)"]
            ),
            CreativeInsight(
                domain=self.domain,
                category="objection_handling",
                finding="Pre-empt top 3 objections in content",
                confidence=0.8,
                suggestions=["Price → ROI calculator", "Complexity → demo video", "Risk → money-back guarantee", "Time → quick-start guide"]
            )
        ]
    
    async def improve(self, media: MediaInterpretation, context: Optional[ProjectContext] = None) -> List[CreativeInsight]:
        return [
            CreativeInsight(
                domain=self.domain,
                category="conversion_optimization",
                finding="Systematic conversion rate optimization",
                confidence=0.85,
                suggestions=[
                    "A/B test headlines (highest leverage)",
                    "Reduce form fields to minimum",
                    "Add progress indicators for multi-step",
                    "Use exit-intent offers",
                    "Personalize by segment/source"
                ]
            ),
            CreativeInsight(
                domain=self.domain,
                category="brand_building",
                finding="Balance brand and performance marketing",
                confidence=0.8,
                suggestions=[
                    "60/40 brand/performance split (Binet & Field)",
                    "Build mental availability (distinctive assets)",
                    "Measure brand lift alongside conversions",
                    "Invest in creative quality (drives 50%+ of ROI)"
                ]
            )
        ]