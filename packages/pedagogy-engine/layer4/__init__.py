"""
Layer 4: Manim Prompt → Code Generation → Video Execution

Converts Manim prompts into executable Python code via ChatGPT,
then executes the code using Manim Community Edition to produce video.
"""

__version__ = "0.1.0"

from layer4.schema import (
    ManimCodeResponse,
    VideoExecutionResult,
    ManimExecutionWithMetadata,
    Layer4ExecutionMetadata
)

from layer4.generator import (
    ManimCodeGenerator,
    ManimExecutor,
    Layer4Generator
)

__all__ = [
    "ManimCodeResponse",
    "VideoExecutionResult",
    "ManimExecutionWithMetadata",
    "Layer4ExecutionMetadata",
    "ManimCodeGenerator",
    "ManimExecutor",
    "Layer4Generator"
]