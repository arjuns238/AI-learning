"""
Pydantic models for the Full Pipeline Orchestrator.

Defines request/response schemas for the end-to-end pipeline API.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class PipelineStage(str, Enum):
    """Pipeline execution stages for progress tracking."""
    PENDING = "pending"
    LAYER1_INTENT = "generating_pedagogical_intent"
    LAYER2_STORYBOARD = "generating_storyboard"
    VISUAL_PLANNING = "identifying_visual_opportunities"
    LAYER3_PROMPT = "generating_manim_prompt"
    LAYER4_VIDEO = "generating_video"
    GENERATING_CLIPS = "generating_animation_clips"
    COMPLETED = "completed"
    FAILED = "failed"


class PipelineProgress(BaseModel):
    """Progress update during pipeline execution."""
    job_id: str
    stage: PipelineStage
    progress_percent: int = Field(ge=0, le=100)
    message: str
    started_at: str
    updated_at: str
    error: Optional[str] = None


# --- Response Models ---

class PedagogicalMetadata(BaseModel):
    """Pedagogical metadata extracted for display."""
    topic: str
    core_question: str
    target_mental_model: str
    common_misconception: str
    disambiguating_contrast: str
    concrete_anchor: str
    check_for_understanding: str
    domain: Optional[str] = None
    difficulty_level: Optional[int] = None
    spatial_metaphor: Optional[str] = None


class StoryboardBeat(BaseModel):
    """Single beat from storyboard."""
    purpose: str
    intent: str


class StoryboardSummary(BaseModel):
    """Storyboard data for display."""
    topic: str
    pedagogical_pattern: Optional[str]
    beats: List[StoryboardBeat]


class VideoMetadata(BaseModel):
    """Video generation metadata."""
    video_url: Optional[str] = None
    video_path: Optional[str] = None
    resolution: str
    execution_time_seconds: float
    generated_code: Optional[str] = None


class AnimationClipSummary(BaseModel):
    """Summary of a generated animation clip for API response."""
    clip_id: str
    concept: str
    placement: str  # core_mechanism, misconception, example, contrast
    video_url: Optional[str] = None
    video_path: Optional[str] = None
    duration_seconds: float = 0.0
    success: bool = False
    error_message: Optional[str] = None


class TimingBreakdown(BaseModel):
    """Timing breakdown by layer."""
    total_seconds: float
    layer1_seconds: float = 0.0
    layer2_seconds: float = 0.0
    layer3_seconds: float = 0.0
    layer4_seconds: float = 0.0
    visual_planning_seconds: float = 0.0
    clip_generation_seconds: float = 0.0


class FullPipelineResponse(BaseModel):
    """Complete response from full pipeline endpoint."""

    # Job identification
    job_id: str
    topic: str

    # Success/failure status
    success: bool
    error_stage: Optional[str] = None
    error_message: Optional[str] = None

    # Primary outputs
    video: Optional[VideoMetadata] = None
    pedagogy: Optional[PedagogicalMetadata] = None
    storyboard: Optional[StoryboardSummary] = None

    # Animation clips (Phase 2 - multiple short clips)
    clips: List[AnimationClipSummary] = Field(
        default_factory=list,
        description="Short animation clips for specific concepts"
    )

    # Timing
    started_at: str
    completed_at: str
    timing: Optional[TimingBreakdown] = None


class FullPipelineRequest(BaseModel):
    """Request body for full pipeline endpoint."""
    topic: str = Field(..., min_length=3)
    domain: Optional[str] = None
    difficulty_level: Optional[int] = Field(None, ge=1, le=5)

    # Configuration overrides
    video_resolution: str = Field(
        default="480p15",
        description="Video resolution: 480p15 (fast), 720p30, 1080p60"
    )
    include_generated_code: bool = Field(
        default=False,
        description="Include generated Manim code in response"
    )

    # Layer configuration (optional overrides)
    api_provider: Optional[str] = Field(
        default=None,
        description="API provider for LLM calls (anthropic or openai)"
    )
    use_rag: bool = Field(
        default=True,
        description="Use RAG for code generation"
    )
