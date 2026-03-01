"""
Pydantic models for Layer 4: Manim Code Execution and Video Generation
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ManimCodeResponse(BaseModel):
    """
    Response from ChatGPT containing ManimCE Python code.
    """

    code: str = Field(
        ...,
        description="Complete Python code for a Manim scene"
    )

    model: str = Field(
        ...,
        description="The model used to generate the code (e.g., 'gpt-4o-mini')"
    )

    generation_timestamp: str = Field(
        ...,
        description="ISO timestamp when the code was generated"
    )

    raw_response: Optional[str] = Field(
        default=None,
        description="Full raw response from the API for debugging"
    )


class VideoExecutionResult(BaseModel):
    """
    Result of executing Manim code and generating video.
    """

    success: bool = Field(
        ...,
        description="Whether the Manim execution succeeded"
    )

    video_path: Optional[str] = Field(
        default=None,
        description="Path to the generated video file"
    )

    resolution: str = Field(
        default="1080p60",
        description="Video resolution and frame rate"
    )

    execution_time_seconds: float = Field(
        ...,
        description="Time taken to render the animation"
    )

    error_message: Optional[str] = Field(
        default=None,
        description="Error message if execution failed"
    )

    output_log: Optional[str] = Field(
        default=None,
        description="Stdout/stderr from Manim execution"
    )

    cancelled: bool = Field(
        default=False,
        description="Whether the execution was cancelled by the user"
    )


class ManimExecutionWithMetadata(BaseModel):
    """
    Complete record of code generation and video execution.
    """

    code_response: ManimCodeResponse
    execution_result: VideoExecutionResult
    metadata: dict = Field(
        default_factory=dict,
        description="Traceability metadata linking back to layer3 prompt"
    )


class Layer4ExecutionMetadata(BaseModel):
    """
    Metadata for layer4 execution tracking.
    """

    generator_version: str = "0.1.0"
    source_manim_prompt_id: Optional[str] = None
    source_storyboard_topic: str
    execution_timestamp: str
    api_provider: str = "openai"
    model_used: str


# ============================================
# Animation Clip Types (Phase 2)
# ============================================

class AnimationClip(BaseModel):
    """
    A short, focused animation clip for a specific concept.

    Generated from a VisualOpportunity identified by the Visual Planner.
    """

    clip_id: str = Field(
        ...,
        description="Unique identifier for this clip (matches opportunity.id)"
    )

    opportunity_id: str = Field(
        ...,
        description="ID of the VisualOpportunity this clip was generated from"
    )

    concept: str = Field(
        ...,
        description="The concept being visualized"
    )

    placement: str = Field(
        ...,
        description="Where in the UI this clip should appear: core_mechanism, misconception, example, contrast"
    )

    video_path: Optional[str] = Field(
        default=None,
        description="Local path to the generated video file"
    )

    video_url: Optional[str] = Field(
        default=None,
        description="URL to access the video (if uploaded)"
    )

    duration_seconds: float = Field(
        default=0.0,
        description="Actual duration of the generated clip"
    )

    success: bool = Field(
        default=False,
        description="Whether the clip was successfully generated"
    )

    error_message: Optional[str] = Field(
        default=None,
        description="Error message if generation failed"
    )

    execution_time_seconds: float = Field(
        default=0.0,
        description="Time taken to generate this clip"
    )

    generated_code: Optional[str] = Field(
        default=None,
        description="The Manim code that was generated (for debugging)"
    )


class ClipGenerationResult(BaseModel):
    """
    Result of generating multiple clips for a lesson.
    """

    topic: str = Field(
        ...,
        description="The topic these clips are for"
    )

    clips: list[AnimationClip] = Field(
        default_factory=list,
        description="List of generated clips (0-2 typically)"
    )

    total_generation_time_seconds: float = Field(
        default=0.0,
        description="Total time to generate all clips"
    )

    clips_requested: int = Field(
        default=0,
        description="Number of clips that were requested"
    )

    clips_succeeded: int = Field(
        default=0,
        description="Number of clips that generated successfully"
    )