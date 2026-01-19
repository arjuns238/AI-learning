"""
Layer 2: Pedagogical Intent → Storyboard

Maps pedagogical intent (Layer 1 output) to a sequence of pedagogical beats
that structure the learning experience.
"""

__version__ = "0.1.0"

from layer2.schema import (
    Beat,
    Storyboard,
    StoryboardMetadata,
    StoryboardWithMetadata
)

from layer2.generator import StoryboardGenerator

__all__ = [
    "Beat",
    "Storyboard",
    "StoryboardMetadata",
    "StoryboardWithMetadata",
    "StoryboardGenerator"
]
