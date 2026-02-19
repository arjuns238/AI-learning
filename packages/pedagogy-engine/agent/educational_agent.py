"""
Educational Agent: Conversational AI tutor with tool capabilities

Built on LangChain v1's create_agent for:
- Streaming responses
- Tool calling with automatic loops
- Middleware support (PII filtering, summarization, human-in-the-loop)
- Session/state management via checkpointing

NOTE: Heavy LangChain imports are deferred to avoid slow import times.
They are loaded lazily when EducationalAgent is first instantiated.
"""

import json
from typing import AsyncIterator, Optional, List, Dict, Any
from dotenv import load_dotenv
from pathlib import Path

# NOTE: Heavy LangChain imports are deferred to avoid 3+ second import time.
# They are imported lazily inside methods where needed:
# - InMemorySaver: in __init__
# - tool decorator: in _get_tools
# - create_agent: in _get_agent
# - HumanMessage, AIMessage, etc.: in _convert_messages_to_langchain and chat

from agent.schema import (
    TextChunk,
    ToolCall,
    ToolResult,
    StreamDone,
    StreamEvent,
    Message,
    MessageRole,
    LearnerContext,
    Session,
)

load_dotenv()
# Resolve paths
_AGENT_LAYER_DIR = Path(__file__).parent
_PEDAGOGY_ENGINE_ROOT = _AGENT_LAYER_DIR.parent

# Cache the system prompt template (read once, reused across all requests)
_cached_system_prompt: Optional[str] = None


def _get_base_system_prompt() -> str:
    """Get the cached base system prompt template (loaded once from disk)."""
    global _cached_system_prompt
    if _cached_system_prompt is None:
        template_path = _PEDAGOGY_ENGINE_ROOT / "prompts" / "agent_system_prompt.txt"
        with open(template_path, 'r') as f:
            _cached_system_prompt = f.read()
    return _cached_system_prompt


def _build_system_prompt(learner_context: Optional[LearnerContext] = None) -> str:
    """Build the system prompt with pedagogical instructions and learner context."""
    # Use cached template instead of reading from disk each time
    base_prompt = _get_base_system_prompt()

    # Add learner context if available
    if learner_context and (learner_context.topics_explored or learner_context.concepts_struggled_with):
        context_section = "\n\n## About This Learner\n\n"

        if learner_context.current_topic:
            context_section += f"Currently learning about: {learner_context.current_topic}\n\n"

        if learner_context.topics_explored:
            recent_topics = learner_context.topics_explored[-5:]
            context_section += f"Recently explored: {', '.join(recent_topics)}\n\n"

        if learner_context.concepts_struggled_with:
            context_section += f"Has struggled with: {', '.join(learner_context.concepts_struggled_with)}\n"
            context_section += "Be extra clear when explaining related concepts.\n\n"

        if learner_context.learning_preferences:
            prefs = learner_context.learning_preferences
            if prefs.get("prefers_visuals"):
                context_section += "This learner responds well to visual explanations.\n"
            if prefs.get("prefers_examples"):
                context_section += "This learner learns best through examples.\n"

        base_prompt += context_section

    return base_prompt


class EducationalAgent:
    """
    Conversational educational assistant built on LangChain v1's create_agent.

    Uses the new create_agent API for automatic tool calling loops,
    with streaming support and session management.
    """

    def __init__(
        self,
        api_provider: str = "anthropic",
        model: Optional[str] = None,
        video_resolution: str = "480p15"
    ):
        self.api_provider = api_provider
        self.video_resolution = video_resolution

        # Set default model (using model string format for create_agent)
        if model:
            self.model = model
        else:
            default_models = {
                "anthropic": "claude-sonnet-4-5-20250929",
                "openai": "gpt-5"
            }
            self.model = default_models.get(api_provider, "claude-sonnet-4-5-20250929")

        # Initialize tools (lazy - animation tool created on first use)
        self._animation_tool_instance = None
        self._tools = None

        # Memory saver for session persistence (lazy import)
        from langgraph.checkpoint.memory import InMemorySaver
        self.checkpointer = InMemorySaver()

        print(f"✓ Educational Agent initialized with LangChain v1 create_agent ({self.api_provider}: {self.model})")

    def _get_animation_tool(self):
        """Get or create the animation tool instance."""
        if self._animation_tool_instance is None:
            from agent.tools.animation_tool import GenerateAnimationTool
            self._animation_tool_instance = GenerateAnimationTool(
                api_provider=self.api_provider,
                video_resolution=self.video_resolution
            )
        return self._animation_tool_instance

    def _get_tools(self) -> List:
        """Get the list of tools for the agent."""
        if self._tools is not None:
            return self._tools

        # Lazy import of LangChain tool decorator
        from langchain_core.tools import tool

        animation_tool_instance = self._get_animation_tool()

        @tool
        async def generate_animation(
            concept: str,
            context: str,
            animation_description: str,
            focus_area: Optional[str] = None,
            duration_hint: Optional[str] = None
        ) -> Dict[str, Any]:
            """Generate an educational animation to visually explain a concept.

            Use this tool when:
            - The concept is inherently spatial or visual (transformations, graphs, geometric concepts)
            - The user is struggling to understand and a visual demonstration might help
            - The user explicitly asks for a visualization or animation
            - You're explaining a process that unfolds over time (algorithms, state changes)

            Do NOT use this tool when:
            - The concept is simple and better explained with text
            - You've already generated an animation for the same concept recently
            - The user is asking a quick clarifying question

            Args:
                concept: The specific concept to visualize (e.g., 'gradient descent optimization')
                context: What the user is trying to understand - provides context for the animation
                animation_description: A detailed 2-3 sentence description of what to animate.
                    Be SPECIFIC about visual elements, motion, and spatial relationships.
                    Good: 'Show a 3D bowl-shaped loss surface. Place a ball at a high point.
                    Animate the ball rolling downhill following gradient arrows. Leave a trail.'
                    Bad: 'Visualize gradient descent.' - too vague, produces poor animation.
                focus_area: Optional specific part to emphasize if the user had confusion
                duration_hint: Optional 'short' (5-10s) or 'detailed' (15-30s) animation
            """
            # Debug: Print what the LLM passed to the tool
            print(f"\n{'='*60}", flush=True)
            print(f"TOOL CALLED: generate_animation", flush=True)
            print(f"  concept: {concept}", flush=True)
            print(f"  context: {context}", flush=True)
            print(f"  animation_description: {animation_description}", flush=True)
            print(f"  focus_area: {focus_area}", flush=True)
            print(f"  duration_hint: {duration_hint}", flush=True)
            print(f"{'='*60}\n", flush=True)

            result = await animation_tool_instance.execute(
                concept=concept,
                context=context,
                animation_description=animation_description,
                focus_area=focus_area,
                duration_hint=duration_hint
            )
            return result.to_dict()

        self._tools = [generate_animation]
        return self._tools

    def _get_agent(self, system_prompt: str):
        """Create the agent with the given system prompt."""
        # Lazy import of LangChain agent factory
        from langchain.agents import create_agent
        return create_agent(
            model=self.model,
            tools=self._get_tools(),
            system_prompt=system_prompt,
            checkpointer=self.checkpointer,
        )

    def _convert_messages_to_langchain(self, messages: List[Message]) -> List:
        """Convert our Message objects to LangChain message format.

        Properly handles tool calls and tool results to maintain context.
        """
        # Lazy import of LangChain message types
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

        lc_messages = []
        for msg in messages:
            if msg.role == MessageRole.USER:
                lc_messages.append(HumanMessage(content=msg.content))

            elif msg.role == MessageRole.ASSISTANT:
                # Convert tool calls to LangChain format if present
                lc_tool_calls = None
                if msg.tool_calls:
                    lc_tool_calls = [
                        {
                            "id": tc.id,
                            "name": tc.name,
                            "args": tc.arguments
                        }
                        for tc in msg.tool_calls
                    ]
                lc_messages.append(AIMessage(
                    content=msg.content,
                    tool_calls=lc_tool_calls or []
                ))

            elif msg.role == MessageRole.TOOL:
                # Tool result message - requires tool_call_id
                lc_messages.append(ToolMessage(
                    content=msg.content,
                    tool_call_id=msg.tool_call_id or ""
                ))

            elif msg.role == MessageRole.SYSTEM:
                lc_messages.append(SystemMessage(content=msg.content))

        return lc_messages

    async def chat(
        self,
        message: str,
        conversation_history: List[Message],
        learner_context: Optional[LearnerContext] = None,
        session: Optional[Session] = None
    ) -> AsyncIterator[StreamEvent]:
        """
        Stream a response to the user's message.

        Yields StreamEvent objects:
        - TextChunk: Streamed text content
        - ToolCall: When the agent decides to use a tool
        - ToolResult: When a tool completes
        - StreamDone: When streaming is complete
        """
        # Lazy imports for LangChain message types
        from langchain.messages import AIMessageChunk
        from langchain_core.messages import HumanMessage, ToolMessage as LCToolMessage

        # DEBUG: Timing for performance analysis
        import sys
        import time
        timings = {}

        t0 = time.time()
        print(f"\n{'='*60}", flush=True)
        print(f"DEBUG: chat() called with {len(conversation_history)} messages in history", flush=True)
        print(f"DEBUG: New message: {message[:80]}...", flush=True)
        print(f"{'='*60}\n", flush=True)
        sys.stdout.flush()

        t1 = time.time()
        system_prompt = _build_system_prompt(learner_context)
        timings['build_system_prompt'] = time.time() - t1

        t1 = time.time()
        agent = self._get_agent(system_prompt)
        timings['get_agent'] = time.time() - t1

        t1 = time.time()
        # Convert conversation history and add new message
        lc_messages = self._convert_messages_to_langchain(conversation_history)
        timings['convert_messages'] = time.time() - t1

        print(f"⏱️  TIMING: build_prompt={timings['build_system_prompt']:.3f}s, get_agent={timings['get_agent']:.3f}s, convert_msgs={timings['convert_messages']:.3f}s")
        print(f"⏱️  TIMING: Total setup before LLM call: {time.time() - t0:.3f}s")
        sys.stdout.flush()

        lc_messages.append(HumanMessage(content=message))

        # Config for session persistence
        session_id = session.session_id if session else "default"
        config = {"configurable": {"thread_id": session_id}}

        # Track state for aggregating message chunks
        full_message = None
        tool_calls_yielded: set = set()
        first_token_time = None
        stream_start_time = time.time()

        try:
            print(f"⏱️  TIMING: Starting LLM stream...", flush=True)
            # Use stream_mode="messages" for token streaming, and "updates" for completed messages
            async for stream_mode, data in agent.astream(
                {"messages": lc_messages},
                config=config,
                stream_mode=["messages", "updates"],
            ):
                if first_token_time is None:
                    first_token_time = time.time()
                    print(f"⏱️  TIMING: Time to first token: {first_token_time - stream_start_time:.3f}s", flush=True)

                if stream_mode == "messages":
                    token, metadata = data

                    # Stream text chunks from AI responses
                    if isinstance(token, AIMessageChunk):
                        # Yield text content as it streams
                        if token.text:
                            yield TextChunk(content=token.text)

                        # Track tool call chunks for later processing
                        if token.tool_call_chunks:
                            for tool_chunk in token.tool_call_chunks:
                                tool_id = tool_chunk.get("id", "")
                                if tool_id and tool_id not in tool_calls_yielded:
                                    tool_calls_yielded.add(tool_id)
                                    yield ToolCall(
                                        id=tool_id,
                                        name=tool_chunk.get("name", "unknown"),
                                        arguments=tool_chunk.get("args", {}) if isinstance(tool_chunk.get("args"), dict) else {}
                                    )

                        # Aggregate chunks
                        full_message = token if full_message is None else full_message + token

                        # When message is complete, process any tool calls
                        if token.chunk_position == "last":
                            full_message = None

                elif stream_mode == "updates":
                    # Handle completed messages from tools node
                    for source, update in data.items():
                        if source == "tools":
                            messages = update.get("messages", [])
                            for msg in messages:
                                if isinstance(msg, LCToolMessage):
                                    # Parse the tool result
                                    content = msg.content
                                    if isinstance(content, str):
                                        try:
                                            result = json.loads(content)
                                        except json.JSONDecodeError:
                                            result = {"result": content}
                                    else:
                                        result = content if isinstance(content, dict) else {"result": str(content)}

                                    success = result.get("success", True) if isinstance(result, dict) else True
                                    error = result.get("error") if isinstance(result, dict) else None

                                    yield ToolResult(
                                        id=msg.tool_call_id or "",
                                        name=msg.name or "unknown",
                                        result=result if isinstance(result, dict) else {"result": result},
                                        success=success,
                                        error=error
                                    )

        except Exception as e:
            print(f"Error in agent streaming: {e}")
            import traceback
            traceback.print_exc()
            raise

        yield StreamDone()

    async def chat_simple(
        self,
        message: str,
        session: Session
    ) -> AsyncIterator[StreamEvent]:
        """Simplified chat interface that uses session for context."""
        async for event in self.chat(
            message=message,
            conversation_history=session.messages,
            learner_context=session.learner_context,
            session=session
        ):
            yield event
