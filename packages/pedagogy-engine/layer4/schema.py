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