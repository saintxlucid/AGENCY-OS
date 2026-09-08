"""
Symbolism Intelligence Engine
Recognizes cultural, religious, brand, and psychological symbols.
"""
from __future__ import annotations

from typing import List, Optional
from aurora.core import IntelligenceEngine, IntelligenceDomain, CreativeInsight, MediaInterpretation, ProjectContext


class SymbolismIntelligence(IntelligenceEngine):
    """Recognizes and interprets symbols, metaphors, and semiotic meaning."""
    
    def __init__(self):
        super().__init__(IntelligenceDomain.SYMBOLISM)
        self._symbol_database = self._load_symbol_database()
    
    def _load_symbol_database(self) -> Dict:
        return {
            "universal": {
                "circle": ["wholeness", "unity", "infinity", "protection", "cycles"],
                "triangle": ["stability", "aspiration", "trinity", "hierarchy", "fire"],
                "square": ["stability", "order", "earth", "foundation", "structure"],
                "spiral": ["growth", "evolution", "journey", "cosmic energy", "unfolding"],
                "cross": ["intersection", "choice", "sacrifice", "balance", "spiritual"],
                "star": ["guidance", "aspiration", "divinity", "excellence", "hope"],
                "heart": ["love", "compassion", "life", "emotion", "center"],
                "eye": ["vision", "awareness", "protection", "truth", "insight"],
                "hand": ["action", "creation", "blessing", "protection", "connection"],
                "tree": ["growth", "life", "connection", "wisdom", "roots"],
                "water": ["emotion", "purification", "flow", "unconscious", "adaptability"],
                "fire": ["transformation", "passion", "energy", "purification", "destruction"],
                "mountain": ["achievement", "stability", "perspective", "challenge", "permanence"],
                "bird": ["freedom", "spirit", "perspective", "messenger", "transcendence"],
                "snake": ["transformation", "healing", "wisdom", "danger", "rebirth"],
                "butterfly": ["transformation", "beauty", "ephemeral", "soul", "metamorphosis"],
            },
            "cultural": {
                "yin_yang": ["balance", "duality", "harmony", "interconnectedness"],
                "mandala": ["wholeness", "universe", "meditation", "cosmic order"],
                "lotus": ["purity", "enlightenment", "rebirth", "spiritual awakening"],
                "om": ["universal sound", "consciousness", "divine", "creation"],
                "hamsa": ["protection", "blessing", "good fortune", "divine protection"],
                "dreamcatcher": ["protection", "filtering", "dreams", "spiritual guidance"],
                "celtic_knot": ["eternity", "interconnection", "no beginning no end"],
                "ankh": ["life", "immortality", "divine life", "eternal life"],
                "torii": ["transition", "sacred space", "boundary", "purification"],
                "menorah": ["light", "wisdom", "divine presence", "miracle"],
                "crescent": ["faith", "guidance", "cycles", "divine feminine"],
                "ichthys": ["faith", "identity", "early christian symbol", "community"],
            },
            "brand_archetypes": {
                "hero": ["nike", "overcome", "achieve", "victory", "challenge"],
                "outlaw": ["harley", "rebel", "freedom", "break rules", "revolution"],
                "magician": ["apple", "disney", "transform", "vision", "make dreams real"],
                "innocent": ["dove", "coca-cola", "pure", "simple", "happy", "optimism"],
                "sage": ["google", "ibm", "wisdom", "truth", "knowledge", "expertise"],
                "explorer": ["jeep", "north face", "freedom", "adventure", "discover"],
                "creator": ["lego", "adobe", "create", "express", "innovation", "imagination"],
                "ruler": ["rolex", "mercedes", "control", "power", "excellence", "status"],
                "caregiver": ["johnson", "volvo", "protect", "nurture", "care", "safety"],
                "everyman": ["ikea", "target", "belonging", "practical", "accessible", "real"],
                "jester": ["m&ms", "old spice", "joy", "humor", "play", "lighthearted"],
                "lover": ["victoria's secret", "godiva", "intimacy", "passion", "beauty", "desire"],
            },
            "luxury_cues": [
                "gold", "platinum", "diamond", "pearl", "silk", "velvet",
                "marble", "crystal", "handcrafted", "bespoke", "limited",
                "heritage", "artisan", "exquisite", "rare", "exclusive"
            ],
            "tech_futurism": [
                "neon", "holographic", "geometric", "grid", "circuit",
                "data", "algorithm", "neural", "quantum", "cyber",
                "synthetic", "digital", "virtual", "augmented", "ai"
            ],
            "nature_sustainability": [
                "leaf", "green", "earth", "recycle", "organic", "sustainable",
                "renewable", "carbon", "eco", "bio", "natural", "pure"
            ],
        }
    
    async def analyze(self, media: MediaInterpretation, context: Optional[ProjectContext] = None) -> List[CreativeInsight]:
        insights = []
        text = self._extract_text(media).lower()
        
        # Universal symbols
        uni = self._detect_symbols(text, self._symbol_database["universal"], "universal")
        if uni:
            insights.append(uni)
        
        # Cultural symbols
        cult = self._detect_symbols(text, self._symbol_database["cultural"], "cultural")
        if cult:
            insights.append(cult)
        
        # Brand archetype
        arch = self._detect_archetype(text)
        if arch:
            insights.append(arch)
        
        # Luxury cues
        lux = self._detect_category(text, self._symbol_database["luxury_cues"], "luxury_signaling")
        if lux:
            insights.append(lux)
        
        # Tech futurism
        tech = self._detect_category(text, self._symbol_database["tech_futurism"], "tech_futurism")
        if tech:
            insights.append(tech)
        
        # Nature/sustainability
        nature = self._detect_category(text, self._symbol_database["nature_sustainability"], "nature_sustainability")
        if nature:
            insights.append(nature)
        
        # Hidden/Subtle symbolism
        hidden = self._analyze_hidden_symbolism(text, media)
        if hidden:
            insights.append(hidden)
        
        return insights
    
    def _extract_text(self, media: MediaInterpretation) -> str:
        parts = [media.summary]
        for insight in media.insights:
            parts.append(insight.finding)
            parts.extend(insight.evidence)
        return " ".join(parts)
    
    def _detect_symbols(self, text: str, database: Dict, category: str) -> Optional[CreativeInsight]:
        detected = {}
        for symbol, meanings in database.items():
            if symbol.replace("_", " ") in text:
                detected[symbol] = meanings
        
        if detected:
            details = []
            for sym, meanings in detected.items():
                details.append(f"{sym}: {', '.join(meanings[:3])}")
            
            return CreativeInsight(
                domain=self.domain,
                category=category,
                finding=f"{len(detected)} {category} symbols detected: {', '.join(detected.keys())}",
                confidence=0.75,
                evidence=details,
                suggestions=["Verify symbolic intent aligns with brand/message", "Consider cultural context of symbols", "Avoid unintended symbolic conflicts"]
            )
        return None
    
    def _detect_archetype(self, text: str) -> Optional[CreativeInsight]:
        scores = {}
        for archetype, keywords in self._symbol_database["brand_archetypes"].items():
            score = sum(text.count(kw) for kw in keywords)
            if score > 0:
                scores[archetype] = score
        
        if scores:
            top = max(scores, key=scores.get)
            return CreativeInsight(
                domain=self.domain,
                category="brand_archetype",
                finding=f"Brand archetype alignment: {top.title()} ({scores[top]} signals)",
                confidence=min(0.85, 0.5 + scores[top] * 0.1),
                evidence=[f"All archetype scores: {scores}"],
                suggestions=[f"Lean into {top} archetype consistently", "Avoid mixed archetype signals", "Audit all touchpoints for archetype coherence"]
            )
        return None
    
    def _detect_category(self, text: str, keywords: List, category: str) -> Optional[CreativeInsight]:
        found = [kw for kw in keywords if kw in text]
        if found:
            return CreativeInsight(
                domain=self.domain,
                category=category,
                finding=f"{category.replace('_', ' ').title()} signaling: {len(found)} cues ({', '.join(found[:5])})",
                confidence=0.7,
                evidence=[f"Detected cues: {found}"],
                suggestions=[f"Ensure {category} messaging is authentic, not performative"]
            )
        return None
    
    def _analyze_hidden_symbolism(self, text: str, media: MediaInterpretation) -> Optional[CreativeInsight]:
        # Look for compositional symbolism
        compositional = []
        if "ascending" in text or "stair" in text or "upward" in text:
            compositional.append("Ascending motifs → growth/aspiration")
        if "descending" in text or "downward" in text:
            compositional.append("Descending motifs → descent/introspection")
        if "mirror" in text or "reflection" in text:
            compositional.append("Mirrors/reflections → self-examination/duality")
        if "window" in text or "doorway" in text or "threshold" in text:
            compositional.append("Thresholds → transition/opportunity")
        if "path" in text or "road" in text or "journey" in text:
            compositional.append("Paths → life journey/choices")
        if "shadow" in text or "silhouette" in text:
            compositional.append("Shadows → hidden aspects/unconscious")
        if "light" in text and "dark" in text:
            compositional.append("Light/dark contrast → knowledge/ignorance, good/evil")
        
        if compositional:
            return CreativeInsight(
                domain=self.domain,
                category="hidden_symbolism",
                finding="Compositional symbolism detected",
                confidence=0.65,
                evidence=compositional,
                suggestions=["Verify intentional vs. emergent symbolism", "Strengthen intentional symbols", "Remove unintended contradictory symbols"]
            )
        return None
    
    async def critique(self, media: MediaInterpretation, context: Optional[ProjectContext] = None) -> List[CreativeInsight]:
        return [CreativeInsight(
            domain=self.domain,
            category="symbolic_coherence",
            finding="Audit all symbols for cultural sensitivity and brand alignment",
            confidence=0.9,
            suggestions=[
                "Research symbols in target markets",
                "Avoid appropriated sacred symbols",
                "Ensure symbols support (not contradict) message",
                "Test symbol recognition with target audience"
            ]
        )]
    
    async def improve(self, media: MediaInterpretation, context: Optional[ProjectContext] = None) -> List[CreativeInsight]:
        return [CreativeInsight(
            domain=self.domain,
            category="symbolic_depth",
            finding="Layer symbols for depth: surface + subtext + cultural resonance",
            confidence=0.8,
            suggestions=[
                "Primary: Immediately recognizable symbol",
                "Secondary: Cultural/archetypal resonance",
                "Tertiary: Personal/subjective interpretation",
                "Use visual metaphor over literal representation",
                "Create symbol system (not single symbols) for campaigns"
            ]
        )]