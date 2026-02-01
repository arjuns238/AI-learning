"""
Educational Agent Package

An agentic framework for educational AI that learns from users
and generates personalized content including animations.
"""

from .schema import (
    TextChunk,
    ToolCall,
    ToolResult,
    StreamDone,
    StreamEvent,
    Message,
    MessageRole,
    LearnerContext,
    Session,
    AnimationResult,
)
from .educational_agent import EducationalAgent
from .tools import GenerateAnimationTool, AVAILABLE_TOOLS

__all__ = [
    # Agent
    "EducationalAgent",

    # Schema types
    "TextChunk",
    "ToolCall",
    "ToolResult",
    "StreamDone",
    "StreamEvent",
    "Message",
    "MessageRole",
    "LearnerContext",
    "Session",
    "AnimationResult",

    # Tools
    "GenerateAnimationTool",
    "AVAILABLE_TOOLS",
]
