"""
Pydantic models for Layer 3: Manim Prompt Schema
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ManimPrompt(BaseModel):
    """
    A single prompt intended to generate ManimCE Python code.
    """

    title: str = Field(
        ...,
        description="Short descriptive title of the animation request"
    )

    system_instruction: str = Field(
        ...,
        description="High-level instruction to the code-generation model"
    )

    user_prompt: str = Field(
        ...,
        description="Detailed prompt describing the desired animation"
    )

    constraints: Optional[List[str]] = Field(
        default=None,
        description="Hard constraints the generated code must follow"
    )


class ManimPromptMetadata(BaseModel):
    """
    Metadata for prompt generation and traceability.
    """

    generator_version: str = "0.1.0"
    source_storyboard_topic: str  # Topic name from Layer 1
    pedagogical_pattern: Optional[str] = None
    generation_timestamp: str
    source_layer2_id: Optional[str] = None  # Section ID (e.g., "section_1")
    source_visual_section: Optional[str] = None  # Section title that has the visual

    # Pedagogical context (optional)
    pedagogical_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Pedagogical reasoning and educational goals for this visualization"
    )


class ManimPromptWithMetadata(BaseModel):
    """
    Bundle of prompt and metadata.
    """

    prompt: ManimPrompt
    metadata: ManimPromptMetadata

    def model_dump_json_formatted(self) -> str:
        import json
        return json.dumps(self.model_dump(), indent=2)
