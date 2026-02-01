"""
Agent Tools Package

Tools that the educational agent can invoke during conversations.
"""

from .animation_tool import GenerateAnimationTool

# Registry of all available tools
AVAILABLE_TOOLS = {
    "generate_animation": GenerateAnimationTool,
}

__all__ = [
    "GenerateAnimationTool",
    "AVAILABLE_TOOLS",
]
