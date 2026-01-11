"""
Pydantic models for Layer 2: Storyboard Schema

Defines the structure of storyboard outputs and validation rules.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class Beat(BaseModel):
    """
    A single pedagogical beat in the storyboard.

    A beat represents one narrative moment or pedagogical transition
    in the explanation.
    """

    purpose: str = Field(
        ...,
        description="The pedagogical purpose of this beat (e.g., 'set_context', 'show_update_rule')",
        min_length=3,
        max_length=100
    )

    intent: str = Field(
        ...,
        description="What this beat should accomplish pedagogically",
        min_length=10,
        max_length=500
    )


class Storyboard(BaseModel):
    """
    A sequence of pedagogical beats that structure the learning experience.
    """

    topic: str = Field(
        ...,
        description="The topic being taught",
        min_length=3,
        max_length=200
    )

    beats: List[Beat] = Field(
        ...,
        description="Ordered sequence of pedagogical beats"
    )

    pedagogical_pattern: Optional[str] = Field(
        None,
        description="The pedagogical pattern used (e.g., 'iterative_process', 'spatial_partitioning')"
    )

    @field_validator('beats')
    @classmethod
    def validate_beat_count(cls, beats: List[Beat]) -> List[Beat]:
        """Validate that storyboard has appropriate number of beats."""
        if len(beats) < 3:
            raise ValueError("Storyboard must have at least 3 beats for pedagogical completeness")
        if len(beats) > 12:
            raise ValueError("Storyboard should have at most 12 beats to avoid overwhelming learners")
        return beats


class StoryboardMetadata(BaseModel):
    """Metadata about how the storyboard was generated."""

    generator_version: str = Field(
        default="0.1.0",
        description="Version of the storyboard generator"
    )

    generation_strategy: str = Field(
        ...,
        description="Strategy used: 'rule_based', 'hybrid', 'llm_sequenced'"
    )

    pattern_used: Optional[str] = Field(
        None,
        description="Pedagogical pattern template that was applied"
    )

    generation_timestamp: str = Field(
        ...,
        description="ISO timestamp of generation"
    )

    source_pedagogical_intent_id: Optional[str] = Field(
        None,
        description="ID or filename of source pedagogical intent (for traceability)"
    )


class StoryboardWithMetadata(BaseModel):
    """Storyboard bundled with generation metadata."""

    storyboard: Storyboard
    metadata: StoryboardMetadata

    def model_dump_json_formatted(self) -> str:
        """Return pretty-printed JSON representation."""
        import json
        return json.dumps(self.model_dump(), indent=2)


# Example instance for testing (matching user's gradient descent example)
EXAMPLE_STORYBOARD = Storyboard(
    topic="Gradient Descent",
    beats=[
        Beat(
            purpose="set_context",
            intent="Show the loss landscape being optimized."
        ),
        Beat(
            purpose="place_initial_state",
            intent="Indicate the starting parameter value."
        ),
        Beat(
            purpose="show_update_rule",
            intent="Demonstrate how the gradient determines direction."
        ),
        Beat(
            purpose="iterate_process",
            intent="Show repeated updates converging to a minimum."
        ),
        Beat(
            purpose="contrast_failure_mode",
            intent="Show what happens with too large a learning rate."
        )
    ],
    pedagogical_pattern="iterative_process"
)

EXAMPLE_METADATA = StoryboardMetadata(
    generation_strategy="hybrid",
    pattern_used="iterative_process",
    generation_timestamp=datetime.now().isoformat()
)

EXAMPLE_STORYBOARD_WITH_METADATA = StoryboardWithMetadata(
    storyboard=EXAMPLE_STORYBOARD,
    metadata=EXAMPLE_METADATA
)


if __name__ == "__main__":
    # Test the schema
    print("Testing Storyboard schema...")
    print(EXAMPLE_STORYBOARD_WITH_METADATA.model_dump_json_formatted())
    print("\n✓ Schema validation passed!")
