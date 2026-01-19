"""
Layer 3: Storyboard → Manim Code Generation Prompt

Transforms pedagogical storyboards into structured prompts
designed to elicit accurate ManimCE Python code from an LLM.
"""

__version__ = "0.1.0"

from layer3.schema import (
    ManimPrompt,
    ManimPromptMetadata,
    ManimPromptWithMetadata
)

from layer3.generator import ManimPromptGenerator

__all__ = [
    "ManimPrompt",
    "ManimPromptMetadata",
    "ManimPromptWithMetadata",
    "ManimPromptGenerator"
]
