"""
Pydantic models for Layer 1: Pedagogical Intent Schema

Defines the structure of pedagogical intent outputs and validation rules.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
import re


class PedagogicalIntent(BaseModel):
    """
    Structured representation of pedagogical intent for a topic.

    This schema captures the key elements needed to teach a concept effectively,
    separating pedagogical reasoning from visualization concerns.
    """

    topic: str = Field(
        ...,
        description="The topic being taught",
        min_length=3,
        max_length=200
    )

    core_question: str = Field(
        ...,
        description="The fundamental question the learner is trying to answer. "
                    "Should capture actual learner confusion, not textbook definition.",
        min_length=10,
        max_length=800
    )

    target_mental_model: str = Field(
        ...,
        description="The conceptual framework the learner should build. "
                    "Should be a clear, specific mental model.",
        min_length=20,
        max_length=1000
    )

    common_misconception: str = Field(
        ...,
        description="A typical wrong understanding that learners hold. "
                    "Should be common (not obscure) and specific.",
        min_length=10,
        max_length=800
    )

    disambiguating_contrast: str = Field(
        ...,
        description="A comparison that clarifies the concept by highlighting "
                    "a key difference. Should compare two distinct concepts.",
        min_length=10,
        max_length=800
    )

    concrete_anchor: str = Field(
        ...,
        description="A specific, grounded example that makes the concept tangible. "
                    "Should be manipulable/visualizable and relatable.",
        min_length=10,
        max_length=800
    )

    check_for_understanding: str = Field(
        ...,
        description="A question to verify the learner has grasped the concept. "
                    "Should test understanding, not rote memorization.",
        min_length=10,
        max_length=800
    )

    # Optional metadata
    domain: Optional[str] = Field(
        None,
        description="Subject domain (e.g., 'mathematics', 'machine_learning', 'physics')"
    )

    difficulty_level: Optional[int] = Field(
        None,
        description="Difficulty level from 1 (basic) to 5 (advanced)",
        ge=1,
        le=5
    )

    spatial_metaphor: Optional[str] = Field(
        None,
        description="Optional hint for visualization (forward compatibility with Layer 2/3)"
    )

    @field_validator('core_question', 'check_for_understanding')
    @classmethod
    def must_be_question(cls, v: str, info) -> str:
        """Ensure question fields actually contain questions."""
        v = v.strip()
        if not (v.endswith('?') or 'how' in v.lower() or 'why' in v.lower() or 'what' in v.lower()):
            raise ValueError(f"{info.field_name} should be phrased as a question")
        return v

    @field_validator('common_misconception')
    @classmethod
    def check_specificity(cls, v: str) -> str:
        """Check that misconception is specific enough."""
        v = v.strip()
        generic_phrases = ['some people think', 'often confused', 'many believe']
        if any(phrase in v.lower() for phrase in generic_phrases) and len(v) < 50:
            raise ValueError("Misconception is too generic. Be more specific about the actual wrong belief.")
        return v

    def model_dump_json_formatted(self) -> str:
        """Return pretty-printed JSON representation."""
        import json
        return json.dumps(self.model_dump(), indent=2)


class GenerationMetadata(BaseModel):
    """Metadata about how the pedagogical intent was generated."""

    model_name: str = Field(..., description="Name of the model used for generation")
    temperature: float = Field(..., description="Temperature parameter used")
    exemplar_ids: list[str] = Field(default_factory=list, description="IDs of exemplars used")
    generation_timestamp: str = Field(..., description="ISO timestamp of generation")
    version: str = Field(default="0.1.0", description="Schema version")


class PedagogicalIntentWithMetadata(BaseModel):
    """Pedagogical intent bundled with generation metadata."""

    intent: PedagogicalIntent
    metadata: GenerationMetadata
    quality_scores: Optional[Dict[str, float]] = Field(
        None,
        description="Automated quality scores from evaluator"
    )
    needs_review: bool = Field(
        default=True,
        description="Whether this needs expert review"
    )


# Example instance for testing
EXAMPLE_PEDAGOGICAL_INTENT = PedagogicalIntent(
    topic="Bias-Variance Tradeoff",
    domain="machine_learning",
    difficulty_level=3,
    core_question="Why does my model perform well on training data but poorly on new data?",
    target_mental_model=(
        "Model complexity is a spectrum with two failure modes: oversimplification "
        "(high bias) misses patterns, while overfitting (high variance) memorizes noise. "
        "The goal is finding the sweet spot between them."
    ),
    common_misconception=(
        "More model complexity always leads to better predictions, since it captures "
        "more patterns in the data."
    ),
    disambiguating_contrast=(
        "A straight line (simple) vs a wiggly curve through every point (complex): "
        "the line misses some training points but generalizes better to new data, "
        "while the curve fits training perfectly but fails on new points."
    ),
    concrete_anchor=(
        "Imagine predicting house prices: a model that only uses 'number of bedrooms' "
        "(underfits) vs one that memorizes every house's unique scratches and stains "
        "(overfits). Neither works for new houses."
    ),
    check_for_understanding=(
        "You train two models on 100 data points. Model A gets 95% training accuracy, "
        "60% test accuracy. Model B gets 75% training accuracy, 72% test accuracy. "
        "Which likely has better bias-variance balance and why?"
    ),
    spatial_metaphor="U-shaped curve showing error vs model complexity"
)


if __name__ == "__main__":
    # Test the schema
    print("Testing PedagogicalIntent schema...")
    print(EXAMPLE_PEDAGOGICAL_INTENT.model_dump_json_formatted())
    print("\n✓ Schema validation passed!")
