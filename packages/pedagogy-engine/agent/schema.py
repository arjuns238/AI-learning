"""
Agent Schema: Types for the Educational Assistant Agent

Defines events, messages, and context types used by the agent.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from datetime import datetime


# ============ Event Types ============
# These are yielded by the agent during streaming

@dataclass
class TextChunk:
    """A chunk of streamed text from the agent."""
    content: str


@dataclass
class ToolCall:
    """Agent is calling a tool."""
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class ToolResult:
    """Result from a tool execution."""
    id: str
    name: str
    result: Dict[str, Any]
    success: bool = True
    error: Optional[str] = None


@dataclass
class StreamDone:
    """Stream has completed."""
    pass


# Union type for all stream events
StreamEvent = Union[TextChunk, ToolCall, ToolResult, StreamDone]


# ============ Message Types ============

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


@dataclass
class Message:
    """A message in the conversation history."""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)

    # For assistant messages that include tool calls
    tool_calls: Optional[List[ToolCall]] = None

    # For tool result messages
    tool_call_id: Optional[str] = None

    # For assistant messages that include animations
    animations: List[str] = field(default_factory=list)

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to format expected by LLM APIs."""
        result = {
            "role": self.role.value,
            "content": self.content
        }

        # Include tool calls for assistant messages
        if self.tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "name": tc.name,
                    "arguments": tc.arguments
                }
                for tc in self.tool_calls
            ]

        # Include tool_call_id for tool result messages
        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id

        return result


# ============ Learner Context ============

@dataclass
class LearnerContext:
    """
    Context about the learner that builds over time.
    Used to personalize the agent's responses.
    """
    # Topics the learner has explored
    topics_explored: List[str] = field(default_factory=list)

    # Concepts the learner struggled with (inferred from questions/confusion)
    concepts_struggled_with: List[str] = field(default_factory=list)

    # Learning preferences (e.g., prefers visuals, likes examples, etc.)
    learning_preferences: Dict[str, Any] = field(default_factory=dict)

    # Current topic being discussed
    current_topic: Optional[str] = None

    # Difficulty level preference (1-5)
    preferred_difficulty: int = 3

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/serialization."""
        return {
            "topics_explored": self.topics_explored,
            "concepts_struggled_with": self.concepts_struggled_with,
            "learning_preferences": self.learning_preferences,
            "current_topic": self.current_topic,
            "preferred_difficulty": self.preferred_difficulty
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LearnerContext":
        """Create from dictionary."""
        return cls(
            topics_explored=data.get("topics_explored", []),
            concepts_struggled_with=data.get("concepts_struggled_with", []),
            learning_preferences=data.get("learning_preferences", {}),
            current_topic=data.get("current_topic"),
            preferred_difficulty=data.get("preferred_difficulty", 3)
        )


# ============ Animation Result ============

@dataclass
class AnimationResult:
    """Result from generating an animation."""
    success: bool
    video_url: Optional[str] = None
    video_path: Optional[str] = None
    error: Optional[str] = None
    execution_time_seconds: float = 0.0
    cancelled: bool = False  # True if cancelled by user

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "video_url": self.video_url,
            "video_path": self.video_path,
            "error": self.error,
            "execution_time_seconds": self.execution_time_seconds,
            "cancelled": self.cancelled
        }


# ============ Session ============

@dataclass
class Session:
    """
    A learning session containing conversation history and learner context.
    """
    session_id: str
    messages: List[Message] = field(default_factory=list)
    learner_context: LearnerContext = field(default_factory=LearnerContext)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def add_message(self, role: MessageRole, content: str, **kwargs) -> Message:
        """Add a message to the session."""
        message = Message(role=role, content=content, **kwargs)
        self.messages.append(message)
        self.updated_at = datetime.now()
        return message

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get messages in API format for LLM calls."""
        return [msg.to_api_format() for msg in self.messages]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        messages_data = []
        for msg in self.messages:
            msg_dict = {
                "role": msg.role.value,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "animations": msg.animations
            }
            # Include tool calls for assistant messages
            if msg.tool_calls:
                msg_dict["tool_calls"] = [
                    {"id": tc.id, "name": tc.name, "arguments": tc.arguments}
                    for tc in msg.tool_calls
                ]
            # Include tool_call_id for tool result messages
            if msg.tool_call_id:
                msg_dict["tool_call_id"] = msg.tool_call_id
            messages_data.append(msg_dict)

        return {
            "session_id": self.session_id,
            "messages": messages_data,
            "learner_context": self.learner_context.to_dict(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
