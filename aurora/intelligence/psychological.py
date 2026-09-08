"""
Psychological Intelligence Engine
Applies behavioral science, cognitive biases, neuromarketing, and decision science.
"""
from __future__ import annotations

from typing import List, Optional
from aurora.core import IntelligenceEngine, IntelligenceDomain, CreativeInsight, MediaInterpretation, ProjectContext


class PsychologicalIntelligence(IntelligenceEngine):
    """Applies behavioral psychology, cognitive biases, and decision science."""
    
    def __init__(self):
        super().__init__(IntelligenceDomain.PSYCHOLOGICAL)
        self._biases = self._load_biases()
        self._principles = self._load_principles()
    
    def _load_biases(self) -> Dict:
        return {
            "attention": [
                "salience_bias", "von_restorff_effect", "cocktail_party_effect",
                "attentional_blink", "change_blindness", "inattentional_blindness"
            ],
            "memory": [
                "primacy_effect", "recency_effect", "peak_end_rule", "serial_position",
                "spacing_effect", "testing_effect", "generation_effect", "von_restorff"
            ],
            "decision": [
                "anchoring", "availability_heuristic", "representativeness",
                "loss_aversion", "status_quo_bias", "choice_overload",
                "decoy_effect", "framing_effect", "sunk_cost", "endowment"
            ],
            "social": [
                "social_proof", "authority_bias", "liking", "reciprocity",
                "conformity", "halo_effect", "identifiable_victim", "in_group"
            ],
            "motivation": [
                "goal_gradient", "zeigarnik", "flow", "self_determination",
                "incentive_theory", "expectancy_value", "temporal_discounting"
            ],
        }
    
    def _load_principles(self) -> Dict:
        return {
            "cialdini": [
                "reciprocity", "commitment_consistency", "social_proof",
                "authority", "liking", "scarcity", "unity"
            ],
            "behavioral_design": [
                "nudge", "default", "feedback", "simplification",
                "commitment_device", "implementation_intention", "temptation_bundling"
            ],
            "neuromarketing": [
                "system1_system2", "emotional_tagging", "somatic_markers",
                "mirror_neurons", "dopamine_anticipation", "cortical_arousal"
            ],
        }
    
    async def analyze(self, media: MediaInterpretation, context: Optional[ProjectContext] = None) -> List[CreativeInsight]:
        insights = []
        text = self._extract_text(media).lower()
        
        # Cognitive biases leveraged
        biases = self._detect_biases(text)
        if biases:
            insights.append(biases)
        
        # Persuasion principles
        pers = self._detect_persuasion(text)
        if pers:
            insights.append(pers)
        
        # Attention design
        attn = self._analyze_attention(text, media)
        if attn:
            insights.append(attn)
        
        # Memory encoding
        mem = self._analyze_memory(text)
        if mem:
            insights.append(mem)
        
        # Motivation design
        mot = self._analyze_motivation(text)
        if mot:
            insights.append(mot)
        
        # Ethical check
        ethical = self._ethical_check(text)
        if ethical:
            insights.append(ethical)
        
        return insights
    
    def _extract_text(self, media: MediaInterpretation) -> str:
        parts = [media.summary]
        for insight in media.insights:
            parts.append(insight.finding)
            parts.extend(insight.evidence)
        return " ".join(parts)
    
    def _detect_biases(self, text: str) -> Optional[CreativeInsight]:
        all_biases = []
        for category, biases in self._biases.items():
            for bias in biases:
                if bias.replace("_", " ") in text:
                    all_biases.append((bias.replace("_", " "), category))
        
        if all_biases:
            return CreativeInsight(
                domain=self.domain,
                category="cognitive_biases",
                finding=f"Psychological biases leveraged: {len(all_biases)} detected",
                confidence=0.75,
                evidence=[f"{bias} ({cat})" for bias, cat in all_biases],
                suggestions=["Document intentional bias usage", "Avoid dark patterns", "Test ethical boundaries", "Measure long-term trust impact"]
            )
        
        return CreativeInsight(
            domain=self.domain,
            category="cognitive_biases",
            finding="No explicit cognitive bias strategies detected",
            confidence=0.4,
            suggestions=["Consider ethical bias application", "Use social proof for trust", "Apply loss aversion for urgency", "Leverage anchoring for pricing"]
        )
    
    def _detect_persuasion(self, text: str) -> Optional[CreativeInsight]:
        found = []
        for principle in self._principles["cialdini"]:
            if principle.replace("_", " ") in text:
                found.append(principle.replace("_", " "))
        
        if found:
            return CreativeInsight(
                domain=self.domain,
                category="persuasion_principles",
                finding=f"Cialdini principles applied: {', '.join(found)}",
                confidence=0.8,
                suggestions=["Stack principles ethically", "Match principle to context", "Test principle combinations", "Measure persuasion vs. manipulation line"]
            )
        
        return None
    
    def _analyze_attention(self, text: str, media: MediaInterpretation) -> Optional[CreativeInsight]:
        attn_terms = ["attention", "focus", "gaze", "eye tracking", "salience", "contrast", "motion", "novelty", "surprise"]
        found = [t for t in attn_terms if t in text]
        
        if found:
            return CreativeInsight(
                domain=self.domain,
                category="attention_design",
                finding=f"Attention mechanisms: {', '.join(found)}",
                confidence=0.7,
                suggestions=["Design for System 1 (fast) processing", "Use novelty for initial capture", "Sustain with relevance", "Avoid attention traps"]
            )
        
        return CreativeInsight(
            domain=self.domain,
            category="attention_design",
            finding="Attention design not explicitly addressed",
            confidence=0.5,
            suggestions=["Apply von Restorff effect (distinctiveness)", "Use motion/contrast for hierarchy", "Limit competing elements", "Design for peripheral vision"]
        )
    
    def _analyze_memory(self, text: str) -> Optional[CreativeInsight]:
        mem_terms = ["remember", "memorable", "recall", "recognition", "brand recall", "distinctive", "unique", "signature"]
        found = [t for t in mem_terms if t in text]
        
        if found:
            return CreativeInsight(
                domain=self.domain,
                category="memory_encoding",
                finding=f"Memory considerations: {', '.join(found)}",
                confidence=0.7,
                suggestions=["Apply peak-end rule for experiences", "Create distinctive brand assets", "Use spacing/repetition for retention", "Design for recognition over recall"]
            )
        
        return CreativeInsight(
            domain=self.domain,
            category="memory_encoding",
            finding="Memory encoding not explicitly designed",
            confidence=0.4,
            suggestions=["Create 'peak moments' in experience", "Design distinctive brand assets (sonic, visual, motion)", "Use spaced repetition in campaigns", "Leverage emotional tagging for memorability"]
        )
    
    def _analyze_motivation(self, text: str) -> Optional[CreativeInsight]:
        mot_terms = ["motivation", "incentive", "reward", "goal", "progress", "achievement", "autonomy", "mastery", "purpose", "gamification"]
        found = [t for t in mot_terms if t in text]
        
        if found:
            return CreativeInsight(
                domain=self.domain,
                category="motivation_design",
                finding=f"Motivation drivers: {', '.join(found)}",
                confidence=0.7,
                suggestions=["Support autonomy (choice/control)", "Enable mastery (progress/feedback)", "Connect to purpose (meaning)", "Use variable rewards carefully"]
            )
        
        return None
    
    def _ethical_check(self, text: str) -> Optional[CreativeInsight]:
        dark_patterns = ["dark pattern", "manipulation", "deception", "forced", "hidden", "trick", "mislead", "exploit"]
        found = [p for p in dark_patterns if p in text]
        
        if found:
            return CreativeInsight(
                domain=self.domain,
                category="ethics",
                finding=f"⚠️ Potential ethical concerns: {', '.join(found)}",
                confidence=0.9,
                suggestions=["Audit against ethical design principles", "Apply 'regret test': would user regret this?", "Ensure informed consent", "Provide easy opt-out", "Prioritize long-term trust over short-term metrics"]
            )
        
        return CreativeInsight(
            domain=self.domain,
            category="ethics",
            finding="No explicit dark patterns detected",
            confidence=0.7,
            suggestions=["Proactively document ethical guardrails", "Establish psychological safety review", "Measure trust metrics", "Create manipulation boundary checklist"]
        )
    
    async def critique(self, media: MediaInterpretation, context: Optional[ProjectContext] = None) -> List[CreativeInsight]:
        return [
            CreativeInsight(
                domain=self.domain,
                category="autonomy_respect",
                finding="Verify user autonomy is preserved at every decision point",
                confidence=0.95,
                suggestions=["No forced continuity", "Clear opt-outs", "Transparent defaults", "Respect user goals over business metrics"]
            ),
            CreativeInsight(
                domain=self.domain,
                category="cognitive_load",
                finding="Minimize cognitive load - reduce choices, chunk information, provide defaults",
                confidence=0.9,
                suggestions=["Apply Hick's Law (fewer choices = faster decisions)", "Use progressive disclosure", "Smart defaults with easy override", "Visual chunking (Miller's 7±2)"]
            ),
            CreativeInsight(
                domain=self.domain,
                category="emotional_design",
                finding="Design for positive emotion: delight, competence, connection",
                confidence=0.85,
                suggestions=["Micro-interactions for delight", "Progress visualization for competence", "Human touches for connection", "Avoid frustration/deception"]
            )
        ]
    
    async def improve(self, media: MediaInterpretation, context: Optional[ProjectContext] = None) -> List[CreativeInsight]:
        return [
            CreativeInsight(
                domain=self.domain,
                category="behavioral_optimization",
                finding="Apply behavioral design systematically",
                confidence=0.85,
                suggestions=[
                    "Map user journey to behavioral barriers",
                    "Design nudges for each barrier",
                    "A/B test nudge variations",
                    "Measure behavior change (not just clicks)",
                    "Iterate based on behavioral data"
                ]
            ),
            CreativeInsight(
                domain=self.domain,
                category="habit_formation",
                finding="Design for habit formation if retention is goal",
                confidence=0.8,
                suggestions=[
                    "Trigger → Action → Reward → Investment loop",
                    "Variable rewards for engagement",
                    "Streak/commitment mechanics",
                    "Social accountability",
                    "Identity-based habits (\"I am a...\")"
                ]
            )
        ]