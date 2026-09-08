"""
AGENCY OS — Prompt Engineering System
Advanced prompt management, optimization, and evaluation.
"""
from __future__ import annotations
import json, uuid, re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum


class PromptType(Enum):
    ANALYSIS = "analysis"
    GENERATION = "generation"
    CRITIQUE = "critique"
    RESEARCH = "research"
    TRANSFORMATION = "transformation"
    CLASSIFICATION = "classification"
    EXTRACTION = "extraction"


class PromptStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    TESTING = "testing"


@dataclass
class PromptVariable:
    """A variable in a prompt template."""
    name: str
    description: str
    type: str = "string"  # string, number, boolean, array, enum
    default: Optional[str] = None
    options: List[str] = field(default_factory=list)
    required: bool = True


@dataclass
class Prompt:
    """A prompt template."""
    prompt_id: str
    org_id: str
    name: str
    content: str
    type: PromptType
    variables: List[PromptVariable] = field(default_factory=list)
    status: PromptStatus = PromptStatus.DRAFT
    version: str = "1.0"
    tags: List[str] = field(default_factory=list)
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000
    system_prompt: Optional[str] = None
    examples: List[Dict] = field(default_factory=list)
    test_results: List[Dict] = field(default_factory=list)
    parent_id: Optional[str] = None  # For versioning
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def render(self, variables: Dict[str, str] = None) -> str:
        """Render the prompt with variables."""
        result = self.content
        vars = variables or {}
        for var in self.variables:
            value = vars.get(var.name, var.default or f"{{{var.name}}}")
            result = result.replace(f"{{{var.name}}}", str(value))
        return result

    def to_dict(self) -> Dict:
        return {
            "prompt_id": self.prompt_id,
            "name": self.name,
            "content": self.content,
            "type": self.type.value,
            "status": self.status.value,
            "version": self.version,
            "model": self.model,
            "temperature": self.temperature,
            "variables": [{"name": v.name, "description": v.description, "type": v.type, "required": v.required} for v in self.variables],
            "tags": self.tags
        }


@dataclass
class PromptChain:
    """A chain of prompts executed sequentially."""
    chain_id: str
    org_id: str
    name: str
    description: Optional[str] = None
    steps: List[Dict] = field(default_factory=list)  # [{"prompt_id": "...", "input_mapping": {...}}]
    status: str = "draft"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        return {
            "chain_id": self.chain_id,
            "name": self.name,
            "steps": self.steps,
            "status": self.status
        }


@dataclass
class PromptEvaluation:
    """Results of prompt testing/evaluation."""
    evaluation_id: str
    prompt_id: str
    test_case: str
    output: str
    expected: Optional[str] = None
    score: float = 0.0
    metrics: Dict[str, float] = field(default_factory=dict)
    notes: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class PromptEngineeringSystem:
    """
    Advanced prompt engineering system.
    
    Features:
    - Prompt templates with variables
    - Version control
    - A/B testing
    - Automatic optimization
    - Chain composition
    - Evaluation suite
    - Model routing
    """

    def __init__(self, persist_dir: str = "./prompts_data"):
        self.prompts: Dict[str, Prompt] = {}
        self.chains: Dict[str, PromptChain] = {}
        self.evaluations: Dict[str, PromptEvaluation] = {}
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)

    # ─── Prompt Management ───

    def create_prompt(
        self,
        org_id: str,
        name: str,
        content: str,
        prompt_type: PromptType,
        variables: List[Dict] = None,
        tags: List[str] = None,
        model: Optional[str] = None
    ) -> Prompt:
        """Create a new prompt template."""
        prompt = Prompt(
            prompt_id=f"prompt_{uuid.uuid4().hex[:10]}",
            org_id=org_id,
            name=name,
            content=content,
            type=prompt_type,
            variables=[PromptVariable(**v) for v in (variables or [])],
            tags=tags or [],
            model=model
        )
        self.prompts[prompt.prompt_id] = prompt
        return prompt

    def get_prompt(self, prompt_id: str) -> Optional[Prompt]:
        """Get a prompt by ID."""
        return self.prompts.get(prompt_id)

    def update_prompt(self, prompt_id: str, **kwargs) -> Optional[Prompt]:
        """Update a prompt."""
        prompt = self.prompts.get(prompt_id)
        if not prompt:
            return None

        for key, value in kwargs.items():
            if hasattr(prompt, key):
                setattr(prompt, key, value)

        prompt.updated_at = datetime.now().isoformat()
        return prompt

    def delete_prompt(self, prompt_id: str) -> bool:
        """Delete a prompt."""
        if prompt_id in self.prompts:
            del self.prompts[prompt_id]
            return True
        return False

    def list_prompts(self, org_id: str, prompt_type: Optional[PromptType] = None,
                     status: Optional[PromptStatus] = None, tag: Optional[str] = None) -> List[Prompt]:
        """List prompts with filters."""
        results = [p for p in self.prompts.values() if p.org_id == org_id]
        if prompt_type:
            results = [p for p in results if p.type == prompt_type]
        if status:
            results = [p for p in results if p.status == status]
        if tag:
            results = [p for p in results if tag in p.tags]
        return results

    def render_prompt(self, prompt_id: str, variables: Dict[str, str] = None) -> Optional[str]:
        """Render a prompt with variables."""
        prompt = self.prompts.get(prompt_id)
        if not prompt:
            return None
        return prompt.render(variables)

    def duplicate_prompt(self, prompt_id: str, new_name: Optional[str] = None) -> Optional[Prompt]:
        """Duplicate a prompt for versioning."""
        original = self.prompts.get(prompt_id)
        if not original:
            return None

        dup = Prompt(
            prompt_id=f"prompt_{uuid.uuid4().hex[:10]}",
            org_id=original.org_id,
            name=new_name or f"{original.name} (copy)",
            content=original.content,
            type=original.type,
            variables=original.variables,
            tags=original.tags,
            model=original.model,
            parent_id=original.prompt_id,
            version=original.version
        )
        self.prompts[dup.prompt_id] = dup
        return dup

    # ─── Prompt Chains ───

    def create_chain(self, org_id: str, name: str, description: Optional[str] = None) -> PromptChain:
        """Create a new prompt chain."""
        chain = PromptChain(
            chain_id=f"chain_{uuid.uuid4().hex[:10]}",
            org_id=org_id,
            name=name,
            description=description
        )
        self.chains[chain.chain_id] = chain
        return chain

    def add_chain_step(self, chain_id: str, prompt_id: str, input_mapping: Dict[str, str] = None) -> bool:
        """Add a step to a chain."""
        chain = self.chains.get(chain_id)
        if not chain:
            return False

        chain.steps.append({
            "prompt_id": prompt_id,
            "input_mapping": input_mapping or {}
        })
        return True

    async def execute_chain(self, chain_id: str, initial_input: Dict = None) -> Dict:
        """Execute a prompt chain sequentially."""
        chain = self.chains.get(chain_id)
        if not chain:
            return {"error": "Chain not found"}

        results = []
        current_data = initial_input or {}

        for step in chain.steps:
            prompt = self.prompts.get(step["prompt_id"])
            if not prompt:
                continue

            # Map inputs
            mapped_input = {}
            for key, mapping in step.get("input_mapping", {}).items():
                if mapping.startswith("$"):
                    # Reference previous result
                    ref_idx = int(mapping[1:]) - 1
                    if ref_idx < len(results):
                        mapped_input[key] = results[ref_idx]
                else:
                    mapped_input[key] = current_data.get(mapping, mapping)

            rendered = prompt.render(mapped_input)
            results.append({"prompt": prompt.name, "rendered": rendered, "input": mapped_input})

        return {"chain_id": chain_id, "steps": results, "step_count": len(results)}

    # ─── Evaluation ───

    def evaluate_prompt(self, prompt_id: str, test_case: str, output: str,
                        expected: Optional[str] = None, metrics: Dict[str, float] = None) -> PromptEvaluation:
        """Evaluate a prompt against a test case."""
        eval_result = PromptEvaluation(
            evaluation_id=f"eval_{uuid.uuid4().hex[:10]}",
            prompt_id=prompt_id,
            test_case=test_case,
            output=output,
            expected=expected,
            metrics=metrics or {}
        )

        # Auto-score if expected output provided
        if expected:
            # Simple similarity scoring (would use embeddings in production)
            eval_result.score = self._calculate_similarity(output, expected)

        self.evaluations[eval_result.evaluation_id] = eval_result

        # Track in prompt
        prompt = self.prompts.get(prompt_id)
        if prompt:
            prompt.test_results.append({
                "evaluation_id": eval_result.evaluation_id,
                "score": eval_result.score,
                "timestamp": eval_result.created_at
            })

        return eval_result

    def _calculate_similarity(self, output: str, expected: str) -> float:
        """Calculate similarity between output and expected (simplified)."""
        # In production: use cosine similarity of embeddings
        output_words = set(output.lower().split())
        expected_words = set(expected.lower().split())
        if not expected_words:
            return 0.0
        overlap = output_words & expected_words
        return len(overlap) / len(expected_words)

    def compare_prompts(self, prompt_id_a: str, prompt_id_b: str, test_cases: List[str]) -> Dict:
        """A/B test two prompts."""
        a_evals = [e for e in self.evaluations.values() if e.prompt_id == prompt_id_a]
        b_evals = [e for e in self.evaluations.values() if e.prompt_id == prompt_id_b]

        a_avg = sum(e.score for e in a_evals) / len(a_evals) if a_evals else 0
        b_avg = sum(e.score for e in b_evals) / len(b_evals) if b_evals else 0

        return {
            "prompt_a": {"id": prompt_id_a, "avg_score": round(a_avg, 3), "tests": len(a_evals)},
            "prompt_b": {"id": prompt_id_b, "avg_score": round(b_avg, 3), "tests": len(b_evals)},
            "winner": prompt_id_a if a_avg > b_avg else prompt_id_b if b_avg > a_avg else "tie",
            "improvement": round(abs(a_avg - b_avg), 3)
        }

    # ─── Optimization ───

    def optimize_prompt(self, prompt_id: str, optimization_type: str = "clarity") -> Dict:
        """Suggest prompt optimizations."""
        prompt = self.prompts.get(prompt_id)
        if not prompt:
            return {"error": "Prompt not found"}

        suggestions = []

        # Check for clarity
        if optimization_type in ("clarity", "all"):
            if len(prompt.content) > 1000:
                suggestions.append("Consider shortening the prompt for better focus")
            if prompt.content.count("{") != prompt.content.count("}"):
                suggestions.append("Unmatched braces in variables")
            if "please" in prompt.content.lower():
                suggestions.append("Remove 'please' - be direct for better results")

        # Check for specificity
        if optimization_type in ("specificity", "all"):
            if "analyze" in prompt.content.lower() and "format" not in prompt.content.lower():
                suggestions.append("Specify the output format for more consistent results")
            if "detail" not in prompt.content.lower():
                suggestions.append("Specify the level of detail needed")

        # Check for examples
        if optimization_type in ("examples", "all"):
            if len(prompt.examples) == 0:
                suggestions.append("Add few-shot examples for more consistent outputs")

        return {
            "prompt_id": prompt_id,
            "optimization_type": optimization_type,
            "suggestions": suggestions,
            "current_length": len(prompt.content),
            "variable_count": len(prompt.variables)
        }

    # ─── Built-in Prompt Templates ───

    def create_builtin_prompts(self, org_id: str) -> List[Prompt]:
        """Create built-in prompt templates."""
        builtins = []

        # Image Analysis
        builtins.append(self.create_prompt(
            org_id, "Image Analysis", """Analyze this image in detail.

Focus on:
1. Composition and visual hierarchy
2. Color palette and harmony
3. Typography (if present)
4. Brand alignment
5. Emotional impact

Image: {image_description}

Provide structured analysis with scores.""",
            PromptType.ANALYSIS,
            variables=[{"name": "image_description", "description": "Description or URL of image", "required": True}],
            tags=["visual", "analysis", "built-in"]
        ))

        # Creative Brief Generator
        builtins.append(self.create_prompt(
            org_id, "Creative Brief Generator", """Create a creative brief based on the following:

Client: {client_name}
Industry: {industry}
Project: {project_name}
Goals: {goals}
Target Audience: {audience}
Budget: {budget}
Timeline: {timeline}

Generate a complete creative brief including:
1. Background & Context
2. Objectives
3. Target Audience
4. Key Message
5. Deliverables
6. Tone & Style
7. Success Metrics""",
            PromptType.GENERATION,
            variables=[
                {"name": "client_name", "description": "Client name"},
                {"name": "industry", "description": "Industry"},
                {"name": "project_name", "description": "Project name"},
                {"name": "goals", "description": "Project goals"},
                {"name": "audience", "description": "Target audience"},
                {"name": "budget", "description": "Budget range"},
                {"name": "timeline", "description": "Timeline"}
            ],
            tags=["brief", "planning", "built-in"]
        ))

        # Design Critique
        builtins.append(self.create_prompt(
            org_id, "Design Critique", """Provide a constructive design critique.

Design: {design_context}
Medium: {medium}
Target Audience: {audience}

Evaluate:
1. Visual Hierarchy (1-10)
2. Color Usage (1-10)
3. Typography (1-10)
4. Composition (1-10)
5. Accessibility (1-10)
6. Brand Alignment (1-10)

For each category:
- Score and reasoning
- Specific strengths
- Actionable improvements

Be specific, constructive, and reference design principles.""",
            PromptType.CRITIQUE,
            variables=[
                {"name": "design_context", "description": "Description or context of the design"},
                {"name": "medium", "description": "Medium (print, digital, video, etc.)"},
                {"name": "audience", "description": "Target audience"}
            ],
            tags=["design", "critique", "built-in"]
        ))

        return builtins

    # ─── Persistence ───

    def save(self):
        """Save all prompts to disk."""
        for prompt in self.prompts.values():
            with open(self.persist_dir / f"{prompt.prompt_id}.json", "w") as f:
                json.dump(prompt.to_dict(), f, indent=2)

    def load(self):
        """Load prompts from disk."""
        for file in self.persist_dir.glob("*.json"):
            with open(file) as f:
                data = json.load(f)
                # Would reconstruct Prompt objects
                self.prompts[data["prompt_id"]] = data