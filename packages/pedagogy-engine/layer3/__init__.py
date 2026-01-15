"""
Layer 3: Storyboard → Scene Specification DSL

Compiles pedagogical beats into structured scene programs
that define what exists and what happens visually.
"""

__version__ = "0.1.0"

from layer3.schema import (
    SceneObject,
    SceneAction,
    SceneSpec,
    SceneSpecMetadata,
    SceneSpecWithMetadata
)

from layer3.generator import SceneSpecGenerator

__all__ = [
    "SceneObject",
    "SceneAction",
    "SceneSpec",
    "SceneSpecMetadata",
    "SceneSpecWithMetadata",
    "SceneSpecGenerator"
]
