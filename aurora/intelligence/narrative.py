"""
Narrative Intelligence Engine
Understands story, structure, character, theme, and narrative patterns.
"""
from __future__ import annotations

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from aurora.core import IntelligenceEngine, IntelligenceDomain, CreativeInsight, MediaInterpretation, ProjectContext


NARRATIVE_PROMPT = """You are a master narrative analyst. Analyze the media for story structure, character arcs, themes, and narrative techniques.

Return JSON with this structure:
{
  "insights": [
    {
      "category": "story_structure",
      "finding": "Specific narrative finding",
      "confidence": 0.0-1.0,
      "evidence": ["evidence from media"],
      "suggestions": ["actionable improvement"]
    }
  ]
}

Categories: story_structure, character_development, theme, pacing, emotional_arc, narrative_voice, tension, resolution, symbolism_in_narrative, audience_engagement
"""


class NarrativeIntelligence(IntelligenceEngine):
    """Analyzes narrative structure, story, characters, themes."""
    
    def __init__(self):
        super().__init__(IntelligenceDomain.NARRATIVE)
        self._patterns = self._load_patterns()
    
    def _load_patterns(self) -> Dict:
        return {
            "hero_journey": ["call to adventure", "refusal", "mentor", "crossing threshold", "tests", "ordeal", "reward", "return"],
            "three_act": ["setup", "confrontation", "resolution"],
            "save_the_cat": ["opening image", "theme stated", "setup", "catalyst", "debate", "break into two", "b story", "fun and games", "midpoint", "bad guys close in", "all is lost", "dark night of the soul", "break into three", "finale", "final image"],
            "dan_harmon": ["comfort zone", "need", "go", "search", "find", "take", "return", "change"],
        }
    
    async def analyze(self, media: MediaInterpretation, context: Optional[ProjectContext] = None) -> List[CreativeInsight]:
        insights = []
        
        # Extract narrative elements from media summary and insights
        narrative_text = self._extract_narrative_context(media)
        
        if not narrative_text:
            return [CreativeInsight(
                domain=self.domain,
                category="story_structure",
                finding="No clear narrative structure detected in media",
                confidence=0.3,
                suggestions=["Consider adding narrative elements for engagement"]
            )]
        
        # Analyze story structure
        structure_insight = self._analyze_structure(narrative_text)
        if structure_insight:
            insights.append(structure_insight)
        
        # Analyze emotional arc
        arc_insight = self._analyze_emotional_arc(narrative_text, media)
        if arc_insight:
            insights.append(arc_insight)
        
        # Analyze themes
        theme_insight = self._analyze_themes(narrative_text)
        if theme_insight:
            insights.append(theme_insight)
        
        # Analyze pacing
        pace_insight = self._analyze_pacing(media)
        if pace_insight:
            insights.append(pace_insight)
        
        return insights
    
    def _extract_narrative_context(self, media: MediaInterpretation) -> str:
        """Extract narrative-relevant text from media interpretation."""
        parts = [media.summary]
        
        for insight in media.insights:
            if insight.domain == IntelligenceDomain.NARRATIVE:
                parts.append(insight.finding)
                parts.extend(insight.evidence)
        
        return " ".join(parts)
    
    def _analyze_structure(self, text: str) -> Optional[CreativeInsight]:
        """Detect narrative structure patterns."""
        text_lower = text.lower()
        
        detected_patterns = []
        for pattern_name, beats in self._patterns.items():
            matches = sum(1 for beat in beats if beat in text_lower)
            if matches >= len(beats) * 0.4:  # 40% of beats present
                detected_patterns.append((pattern_name, matches / len(beats)))
        
        if detected_patterns:
            best = max(detected_patterns, key=lambda x: x[1])
            return CreativeInsight(
                domain=self.domain,
                category="story_structure",
                finding=f"Follows {best[0].replace('_', ' ').title()} structure ({best[1]:.0%} beat match)",
                confidence=min(0.9, best[1] + 0.2),
                evidence=[f"Detected {len(detected_patterns)} structural patterns"],
                suggestions=["Consider reinforcing missing beats", "Verify act transitions are clear"]
            )
        
        return CreativeInsight(
            domain=self.domain,
            category="story_structure",
            finding="No classic narrative structure clearly detected",
            confidence=0.4,
            suggestions=["Consider applying Hero's Journey or Three-Act structure", "Define clear setup, confrontation, resolution"]
        )
    
    def _analyze_emotional_arc(self, text: str, media: MediaInterpretation) -> Optional[CreativeInsight]:
        """Analyze emotional trajectory."""
        # Look for emotion keywords
        emotions = {
            "tension": ["tension", "conflict", "struggle", "challenge", "obstacle"],
            "hope": ["hope", "optimism", "possibility", "discovery", "breakthrough"],
            "fear": ["fear", "anxiety", "danger", "threat", "uncertainty"],
            "joy": ["joy", "triumph", "success", "celebration", "victory"],
            "sadness": ["loss", "grief", "sadness", "melancholy", "sacrifice"],
            "anger": ["anger", "rage", "frustration", "outrage", "betrayal"],
        }
        
        text_lower = text.lower()
        emotion_scores = {}
        for emotion, keywords in emotions.items():
            score = sum(text_lower.count(kw) for kw in keywords)
            if score > 0:
                emotion_scores[emotion] = score
        
        if emotion_scores:
            dominant = max(emotion_scores, key=emotion_scores.get)
            return CreativeInsight(
                domain=self.domain,
                category="emotional_arc",
                finding=f"Dominant emotional tone: {dominant.title()}",
                confidence=0.7,
                evidence=[f"Emotion distribution: {emotion_scores}"],
                suggestions=[f"Consider balancing {dominant} with contrasting emotions for depth"]
            )
        
        return None
    
    def _analyze_themes(self, text: str) -> Optional[CreativeInsight]:
        """Identify thematic elements."""
        themes = {
            "identity": ["identity", "self", "who am i", "transformation", "becoming"],
            "freedom": ["freedom", "liberation", "escape", "independence", "autonomy"],
            "power": ["power", "control", "authority", "dominance", "corruption"],
            "love": ["love", "connection", "relationship", "intimacy", "belonging"],
            "sacrifice": ["sacrifice", "giving up", "cost", "price", "for others"],
            "redemption": ["redemption", "forgiveness", "second chance", "atonement", "healing"],
            "justice": ["justice", "fairness", "right", "wrong", "moral", "ethics"],
            "growth": ["growth", "learning", "maturation", "development", "evolution"],
        }
        
        text_lower = text.lower()
        detected = {}
        for theme, keywords in themes.items():
            score = sum(text_lower.count(kw) for kw in keywords)
            if score > 0:
                detected[theme] = score
        
        if detected:
            top_theme = max(detected, key=detected.get)
            return CreativeInsight(
                domain=self.domain,
                category="theme",
                finding=f"Primary theme: {top_theme.title()} (supported by {len(detected)} thematic threads)",
                confidence=0.75,
                evidence=[f"Themes detected: {', '.join(detected.keys())}"],
                suggestions=[f"Deepen {top_theme} through character choices", "Ensure thematic consistency across all elements"]
            )
        
        return None
    
    def _analyze_pacing(self, media: MediaInterpretation) -> Optional[CreativeInsight]:
        """Analyze narrative pacing from media metadata."""
        if media.media_type.value == "video":
            # Video pacing analysis would go here
            return CreativeInsight(
                domain=self.domain,
                category="pacing",
                finding="Video pacing analysis requires frame-level timing data",
                confidence=0.3,
                suggestions=["Provide shot duration data for detailed pacing analysis"]
            )
        
        return CreativeInsight(
            domain=self.domain,
            category="pacing",
            finding="Pacing analysis available for time-based media",
            confidence=0.2,
            suggestions=["For static media, consider visual rhythm and information density"]
        )
    
    async def critique(self, media: MediaInterpretation, context: Optional[ProjectContext] = None) -> List[CreativeInsight]:
        """Constructive narrative critique."""
        critiques = []
        
        # Check for clear protagonist
        has_protagonist = any("protagonist" in i.finding.lower() or "character" in i.finding.lower() 
                             for i in media.insights if i.domain == self.domain)
        
        if not has_protagonist:
            critiques.append(CreativeInsight(
                domain=self.domain,
                category="character_development",
                finding="No clear protagonist or character focus identified",
                confidence=0.8,
                suggestions=["Define a clear protagonist with specific wants/needs", "Show character through action, not description"]
            ))
        
        # Check for stakes
        has_stakes = any("stakes" in i.finding.lower() or "conflict" in i.finding.lower() 
                        for i in media.insights)
        
        if not has_stakes:
            critiques.append(CreativeInsight(
                domain=self.domain,
                category="tension",
                finding="Narrative stakes unclear - what happens if protagonist fails?",
                confidence=0.75,
                suggestions=["Establish clear consequences for failure", "Raise stakes progressively through acts"]
            ))
        
        return critiques
    
    async def improve(self, media: MediaInterpretation, context: Optional[ProjectContext] = None) -> List[CreativeInsight]:
        """Specific narrative improvements."""
        improvements = []
        
        # Structure improvements
        improvements.append(CreativeInsight(
            domain=self.domain,
            category="story_structure",
            finding="Strengthen act transitions with clear turning points",
            confidence=0.85,
            suggestions=[
                "Act 1→2: Protagonist makes active choice to pursue goal",
                "Midpoint: Major revelation or reversal",
                "Act 2→3: Lowest point / all is lost moment",
                "Climax: Protagonist uses transformed understanding to succeed"
            ]
        ))
        
        # Character depth
        improvements.append(CreativeInsight(
            domain=self.domain,
            category="character_development",
            finding="Add character contradiction for depth",
            confidence=0.8,
            suggestions=[
                "Give protagonist a flaw that contradicts their strength",
                "Show vulnerability in moments of strength",
                "Create internal conflict mirroring external conflict"
            ]
        ))
        
        # Theme integration
        improvements.append(CreativeInsight(
            domain=self.domain,
            category="theme",
            finding="Weave theme into every scene through subtext",
            confidence=0.8,
            suggestions=[
                "Each scene should reflect the central thematic question",
                "Use visual/verbal motifs to reinforce theme",
                "Character choices should embody thematic argument"
            ]
        ))
        
        return improvements