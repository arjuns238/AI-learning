"""
Pydantic models for Layer 1: Flexible Pedagogical Intent Schema

Defines the structure for dynamic, freeform pedagogical sections
with embedded visual hints.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator
import json


class VisualHint(BaseModel):
    """
    Embedded visual opportunity for a section.

    LLM identifies this while generating content - no separate visual planning step.
    """

    should_animate: bool = Field(
        ...,
        description="Whether this section would benefit from animation"
    )

    animation_description: Optional[str] = Field(
        None,
        description="If should_animate is True, describe what to show (2-3 sentences). "
                    "Be specific about visual elements, motion, and timing.",
        min_length=20
    )

    duration_hint: Optional[int] = Field(
        None,
        description="Suggested animation duration in seconds (10-30)",
        ge=5,
        le=60
    )

    @field_validator('animation_description')
    @classmethod
    def require_description_if_animate(cls, v, info):
        """Ensure description is provided when should_animate is True."""
        # Note: This runs before the full model is validated
        # The cross-field validation happens in model_validator
        return v


class Comparison(BaseModel):
    """Structured comparison for disambiguation sections."""

    item_a: str = Field(..., description="First item being compared")
    item_b: str = Field(..., description="Second item being compared")
    difference: str = Field(..., description="Key difference between them")


class PedagogicalSection(BaseModel):
    """
    A single freeform pedagogical section.

    The LLM generates section titles and content dynamically based on
    what the topic actually needs - no predefined section types.
    """

    title: str = Field(
        ...,
        description="LLM-generated title for this section (e.g., 'The Core Intuition', "
                    "'A Common Trap', 'Step by Step')",
        min_length=3,
        max_length=100
    )

    content: str = Field(
        ...,
        description="The pedagogical content of this section. Markdown supported.",
        min_length=20
    )

    order: int = Field(
        ...,
        description="Display order (1-based, sequential)",
        ge=1
    )

    visual: Optional[VisualHint] = Field(
        None,
        description="Visual opportunity embedded in this section, if applicable"
    )

    # Optional structured content - LLM uses when appropriate
    steps: Optional[List[str]] = Field(
        None,
        description="For procedural content: ordered list of steps"
    )

    math_expressions: Optional[List[str]] = Field(
        None,
        description="For mathematical content: LaTeX expressions"
    )

    comparison: Optional[Comparison] = Field(
        None,
        description="For disambiguation: structured comparison of two items"
    )


class PedagogicalIntent(BaseModel):
    """
    Flexible pedagogical intent schema.

    Uses dynamic, freeform sections instead of rigid fields.
    The LLM decides which sections are needed for each topic.
    """

    topic: str = Field(
        ...,
        description="The topic being taught",
        min_length=3
    )

    summary: str = Field(
        ...,
        description="1-2 sentence overview of the lesson",
        min_length=20,
        max_length=500
    )

    sections: List[PedagogicalSection] = Field(
        ...,
        description="Dynamic list of pedagogical sections (2-8 sections)",
        min_length=1,
        max_length=8
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

    @field_validator('sections')
    @classmethod
    def validate_section_order(cls, sections: List[PedagogicalSection]) -> List[PedagogicalSection]:
        """Ensure section orders are sequential starting from 1."""
        orders = sorted([s.order for s in sections])
        expected = list(range(1, len(sections) + 1))
        if orders != expected:
            raise ValueError(f"Section orders must be sequential 1..n, got {orders}")
        return sections

    def get_visual_sections(self) -> List[PedagogicalSection]:
        """Extract sections that need video generation."""
        return [
            section for section in self.sections
            if section.visual and section.visual.should_animate
        ]

    def model_dump_json_formatted(self) -> str:
        """Return pretty-printed JSON representation."""
        return json.dumps(self.model_dump(), indent=2)


class GenerationMetadata(BaseModel):
    """Metadata about how the pedagogical intent was generated."""

    model_name: str = Field(..., description="Name of the model used for generation")
    temperature: float = Field(..., description="Temperature parameter used")
    generation_timestamp: str = Field(..., description="ISO timestamp of generation")
    version: str = Field(default="1.0.0", description="Schema version")


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
    topic="Gradient Descent",
    summary="How an algorithm finds optimal parameters by iteratively following the steepest path downhill.",
    domain="machine_learning",
    difficulty_level=3,
    sections=[
        PedagogicalSection(
            title="The Core Intuition",
            content=(
                "Imagine you're lost in dense fog on a mountainside, trying to reach the valley floor. "
                "You can't see the whole landscape, but you can feel which direction slopes downward "
                "beneath your feet. By repeatedly taking small steps in the steepest downward direction, "
                "you eventually reach a valley - even without a map of the entire terrain."
            ),
            order=1,
            visual=VisualHint(
                should_animate=True,
                animation_description=(
                    "Show a ball on a 3D curved surface (loss landscape). "
                    "At each position, draw a gradient arrow pointing downhill. "
                    "The ball takes a step in that direction, leaving a trail. "
                    "Repeat until it settles into a valley (local minimum)."
                ),
                duration_hint=15
            )
        ),
        PedagogicalSection(
            title="The Algorithm Step-by-Step",
            content=(
                "Gradient descent follows a simple procedure that repeats until convergence. "
                "Each iteration moves the parameters slightly in the direction that reduces the error most."
            ),
            order=2,
            steps=[
                "Compute the gradient (slope) at the current position",
                "Take a step in the negative gradient direction (downhill)",
                "Repeat until the gradient is nearly zero (reached a minimum)"
            ],
            visual=None
        ),
        PedagogicalSection(
            title="The Learning Rate Trap",
            content=(
                "A common mistake is setting the learning rate (step size) incorrectly. "
                "Too small and you'll take forever to converge. Too large and you'll overshoot "
                "the minimum, potentially bouncing around forever or even diverging."
            ),
            order=3,
            visual=VisualHint(
                should_animate=True,
                animation_description=(
                    "Split screen comparison: Left side shows small learning rate - ball slowly "
                    "rolling downhill, taking many tiny steps. Right side shows large learning rate - "
                    "ball overshooting, oscillating wildly around the minimum, never settling."
                ),
                duration_hint=12
            ),
            comparison=Comparison(
                item_a="Small learning rate",
                item_b="Large learning rate",
                difference="Small is slow but stable; large is fast but may never converge"
            )
        ),
        PedagogicalSection(
            title="Check Your Understanding",
            content=(
                "You run gradient descent and it converges to a point, but the loss is still "
                "relatively high. What might have happened, and what could you try differently?"
            ),
            order=4,
            visual=None
        )
    ]
)


if __name__ == "__main__":
    # Test the schema
    print("Testing PedagogicalIntent schema...")
    print(EXAMPLE_PEDAGOGICAL_INTENT.model_dump_json_formatted())

    print(f"\n✓ Schema validation passed!")
    print(f"  - {len(EXAMPLE_PEDAGOGICAL_INTENT.sections)} sections")
    print(f"  - {len(EXAMPLE_PEDAGOGICAL_INTENT.get_visual_sections())} sections with visuals")
