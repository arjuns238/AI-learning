"""
Orchestrator module for end-to-end pipeline execution.

Chains all 4 layers: Topic → Pedagogical Intent → Storyboard → Manim Prompt → Video
"""

from .pipeline import FullPipelineOrchestrator
from .schema import (
    PipelineStage,
    PipelineProgress,
    FullPipelineRequest,
    FullPipelineResponse,
    PedagogicalMetadata,
    StoryboardSummary,
    StoryboardBeat,
    VideoMetadata,
    TimingBreakdown,
)

__all__ = [
    "FullPipelineOrchestrator",
    "PipelineStage",
    "PipelineProgress",
    "FullPipelineRequest",
    "FullPipelineResponse",
    "PedagogicalMetadata",
    "StoryboardSummary",
    "StoryboardBeat",
    "VideoMetadata",
    "TimingBreakdown",
]
