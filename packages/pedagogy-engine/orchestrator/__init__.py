"""
Orchestrator module for end-to-end pipeline execution.

New Architecture (section-based):
- Layer 1: Topic → Pedagogical Intent with freeform sections + embedded visual hints
- Layer 3: Visual sections → Manim prompts
- Layer 4: Manim prompts → Videos
"""

from .pipeline import FullPipelineOrchestrator
from .schema import (
    PipelineStage,
    PipelineProgress,
    FullPipelineRequest,
    FullPipelineResponse,
    PedagogicalMetadata,
    PedagogicalSectionSummary,
    VisualHintSummary,
    ComparisonSummary,
    VideoMetadata,
    AnimationClipSummary,
    TimingBreakdown,
)

__all__ = [
    "FullPipelineOrchestrator",
    "PipelineStage",
    "PipelineProgress",
    "FullPipelineRequest",
    "FullPipelineResponse",
    "PedagogicalMetadata",
    "PedagogicalSectionSummary",
    "VisualHintSummary",
    "ComparisonSummary",
    "VideoMetadata",
    "AnimationClipSummary",
    "TimingBreakdown",
]
