"""
Educational Agent: Conversational AI tutor with tool capabilities

Built on LangChain v1's create_agent for:
- Streaming responses
- Tool calling with automatic loops
- Middleware support (PII filtering, summarization, human-in-the-loop)
- Session/state management via checkpointing
"""

import json
from typing import AsyncIterator, Optional, List, Dict, Any
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

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


def _build_system_prompt(learner_context: Optional[LearnerContext] = None) -> str:
    """Build the system prompt with pedagogical instructions and learner context."""

    base_prompt = """You are an expert educational assistant that helps people learn complex technical concepts, especially in areas like machine learning, mathematics, algorithms, and computer science.

## Intent First Rule (Highest Priority)

Before explaining anything, determine the user's intent.

If the user is:
- greeting ("hi", "hey", "what's up")
- making small talk
- reacting briefly ("lol", "ok", "nice")
- asking for a quick or obvious response
- not explicitly asking a question

THEN:
- Respond briefly and naturally
- Do NOT explain concepts
- Do NOT define terms
- Do NOT switch into teaching mode
- Treat it like a normal human conversation

Only enter teaching/explaining mode when the user clearly asks to learn, understand, or explore something.

## Your Teaching Philosophy

1. **Meet learners where they are**: Adapt your explanations to the learner's current level of understanding.

2. **Build mental models**: Help learners develop intuitive understanding, not just memorize facts. Use analogies, metaphors, and concrete examples.

3. **Address misconceptions proactively**: Anticipate common misunderstandings and address them directly.

4. **Use visuals strategically**: When a concept is inherently spatial, involves transformations, or unfolds over time, use the generate_animation tool to create a visual explanation.

5. **Check for understanding**: Periodically ask if things make sense, invite questions.

6. **Connect concepts**: Help learners see how new concepts relate to what they already know.

## When to Use the Animation Tool

Use the `generate_animation` tool when:
- Explaining spatial or geometric concepts (vectors, transformations, graphs)
- Demonstrating processes that unfold over time (algorithms, optimization, training)
- The learner is struggling and a visual might unlock understanding
- The concept is abstract and hard to grasp from text alone
- The user explicitly asks for a visualization

Do NOT use it for:
- Simple questions with quick text answers
- Concepts that are already well understood
- When you just generated an animation for the same thing

## Response Style

- You dont always have to explain everything. Make sure you always maintain a conversation. If it seems like the user just wants a simple response or wants to have a conversation, give them that.
- Be conversational and encouraging, but not patronizing
- Use clear, precise language
- Break down complex ideas into digestible pieces
- Use markdown formatting for clarity (headers, lists, code blocks, math)
- When you use the animation tool, naturally incorporate it into your explanation (e.g., "Let me show you what this looks like...")
"""

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
                "openai": "gpt-4o"
            }
            self.model = default_models.get(api_provider, "claude-sonnet-4-5-20250929")

        # Initialize tools (lazy - animation tool created on first use)
        self._animation_tool_instance = None
        self._tools = None

        # Memory saver for session persistence
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

        animation_tool_instance = self._get_animation_tool()

        @tool
        async def generate_animation(
            concept: str,
            context: str,
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
                focus_area: Optional specific part to emphasize if the user had confusion
                duration_hint: Optional 'short' (5-10s) or 'detailed' (15-30s) animation
            """
            result = await animation_tool_instance.execute(
                concept=concept,
                context=context,
                focus_area=focus_area,
                duration_hint=duration_hint
            )
            return result.to_dict()

        self._tools = [generate_animation]
        return self._tools

    def _get_agent(self, system_prompt: str):
        """Create the agent with the given system prompt."""
        return create_agent(
            model=self.model,
            tools=self._get_tools(),
            system_prompt=system_prompt,
            checkpointer=self.checkpointer,
        )

    def _convert_messages_to_langchain(self, messages: List[Message]) -> List:
        """Convert our Message objects to LangChain message format."""
        lc_messages = []
        for msg in messages:
            if msg.role == MessageRole.USER:
                lc_messages.append(HumanMessage(content=msg.content))
            elif msg.role == MessageRole.ASSISTANT:
                lc_messages.append(AIMessage(content=msg.content))
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
        from langchain.messages import AIMessageChunk, ToolMessage

        system_prompt = _build_system_prompt(learner_context)
        agent = self._get_agent(system_prompt)

        # Convert conversation history and add new message
        lc_messages = self._convert_messages_to_langchain(conversation_history)
        lc_messages.append(HumanMessage(content=message))

        # Config for session persistence
        session_id = session.session_id if session else "default"
        config = {"configurable": {"thread_id": session_id}}

        # Track state for aggregating message chunks
        full_message = None
        tool_calls_yielded: set = set()

        try:
            # Use stream_mode="messages" for token streaming, and "updates" for completed messages
            async for stream_mode, data in agent.astream(
                {"messages": lc_messages},
                config=config,
                stream_mode=["messages", "updates"],
            ):
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
                                if isinstance(msg, ToolMessage):
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
