"""
Visual Planner Schema

Defines the structure for visual opportunities - concepts that would
benefit from short animated explanations.
"""

from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class VisualOpportunity(BaseModel):
    """
    Represents a concept that would benefit from a short animation.

    The Visual Planner identifies 1-2 of these per lesson based on
    the pedagogical content from Layer 1.
    """

    id: str = Field(
        ...,
        description="Unique identifier for this visual opportunity (e.g., 'v1', 'v2')"
    )

    concept: str = Field(
        ...,
        description="The concept being visualized (e.g., 'Row-column dot product')",
        min_length=3
    )

    description: str = Field(
        ...,
        description="Detailed description of what the animation should show",
        min_length=20
    )

    placement: Literal["core_mechanism", "misconception", "example", "contrast"] = Field(
        ...,
        description="Where in the lesson UI this visual should appear"
    )

    pedagogical_purpose: str = Field(
        ...,
        description="Why this visual helps learning - what understanding it reinforces",
        min_length=10
    )

    duration_hint: int = Field(
        default=15,
        description="Suggested duration in seconds (10-20)",
        ge=10,
        le=30
    )


class VisualPlan(BaseModel):
    """
    The output of the Visual Planner - a curated list of visual opportunities.
    """

    topic: str = Field(
        ...,
        description="The topic being taught"
    )

    opportunities: List[VisualOpportunity] = Field(
        ...,
        description="1-2 visual opportunities identified for this lesson",
        min_length=0,
        max_length=3
    )

    reasoning: Optional[str] = Field(
        None,
        description="Brief explanation of why these visuals were chosen"
    )


class VisualPlannerMetadata(BaseModel):
    """Metadata about the visual planning process."""

    model_name: str = Field(
        ...,
        description="LLM model used for planning"
    )

    generation_timestamp: str = Field(
        ...,
        description="ISO timestamp of generation"
    )

    num_opportunities_requested: int = Field(
        default=2,
        description="How many opportunities were requested"
    )


class VisualPlanWithMetadata(BaseModel):
    """Visual plan bundled with generation metadata."""

    plan: VisualPlan
    metadata: VisualPlannerMetadata
