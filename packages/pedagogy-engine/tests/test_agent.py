"""
Test suite for the Educational Agent

Tests:
1. Agent initialization
2. Streaming text responses
3. Tool calling (generate_animation)
4. Supabase video upload
"""

import asyncio
import pytest
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env")

# Add parent to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestAgentInitialization:
    """Test agent can be initialized properly."""

    def test_import_agent(self):
        """Test that agent module can be imported."""
        from agent import EducationalAgent
        assert EducationalAgent is not None

    def test_import_schema(self):
        """Test that schema types can be imported."""
        from agent.schema import (
            TextChunk,
            ToolCall,
            ToolResult,
            StreamDone,
            Message,
            MessageRole,
            LearnerContext,
            Session,
        )
        assert TextChunk is not None
        assert ToolCall is not None

    def test_agent_init_anthropic(self):
        """Test agent initializes with Anthropic provider."""
        from agent import EducationalAgent

        # Skip if no API key
        if not os.getenv("ANTHROPIC_API_KEY"):
            pytest.skip("ANTHROPIC_API_KEY not set")

        agent = EducationalAgent(api_provider="anthropic")
        assert agent.api_provider == "anthropic"
        assert "claude" in agent.model.lower()

    def test_agent_init_openai(self):
        """Test agent initializes with OpenAI provider."""
        from agent import EducationalAgent

        # Skip if no API key
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")

        agent = EducationalAgent(api_provider="openai")
        assert agent.api_provider == "openai"
        assert "gpt" in agent.model.lower()


class TestAnimationTool:
    """Test the animation tool separately."""

    def test_tool_import(self):
        """Test animation tool can be imported."""
        from agent.tools.animation_tool import GenerateAnimationTool
        assert GenerateAnimationTool is not None

    def test_tool_init(self):
        """Test animation tool initializes."""
        from agent.tools.animation_tool import GenerateAnimationTool

        tool = GenerateAnimationTool(
            api_provider="anthropic",
            video_resolution="480p15",
            use_supabase=False  # Don't require Supabase for this test
        )
        assert tool.name == "generate_animation"
        assert "concept" in tool.parameters["properties"]

    def test_tool_definition(self):
        """Test tool definition format."""
        from agent.tools.animation_tool import GenerateAnimationTool

        tool = GenerateAnimationTool(use_supabase=False)
        definition = tool.get_tool_definition()

        assert definition["name"] == "generate_animation"
        assert "description" in definition
        assert "input_schema" in definition


class TestSupabaseIntegration:
    """Test Supabase video storage integration."""

    def test_supabase_import(self):
        """Test Supabase client can be imported."""
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / "api"))
            from supabase_client import VideoStore, get_client
            assert VideoStore is not None
        except ImportError:
            pytest.skip("Supabase client not available")

    def test_supabase_connection(self):
        """Test Supabase connection works."""
        if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_SECRET_KEY"):
            pytest.skip("Supabase credentials not set")

        try:
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / "api"))
            from supabase_client import get_client
            client = get_client()
            assert client is not None
        except Exception as e:
            pytest.fail(f"Supabase connection failed: {e}")


class TestAgentStreaming:
    """Test agent streaming functionality."""

    @pytest.mark.asyncio
    async def test_simple_chat_streaming(self):
        """Test streaming a simple response without tool use."""
        from agent import EducationalAgent, TextChunk, StreamDone, Message

        if not os.getenv("ANTHROPIC_API_KEY"):
            pytest.skip("ANTHROPIC_API_KEY not set")

        agent = EducationalAgent(api_provider="anthropic")

        # Simple question that shouldn't trigger animation
        message = "What is 2 + 2?"
        events = []

        async for event in agent.chat(
            message=message,
            conversation_history=[],
            learner_context=None,
            session=None
        ):
            events.append(event)
            print(f"Event: {type(event).__name__}", end=" ")
            if isinstance(event, TextChunk):
                print(f"- {event.content[:50]}..." if len(event.content) > 50 else f"- {event.content}")
            else:
                print()

        # Should have at least one text chunk and end with StreamDone
        text_chunks = [e for e in events if isinstance(e, TextChunk)]
        done_events = [e for e in events if isinstance(e, StreamDone)]

        assert len(text_chunks) > 0, "Should have received text chunks"
        assert len(done_events) == 1, "Should have exactly one StreamDone"

        # Combine text
        full_response = "".join(chunk.content for chunk in text_chunks)
        print(f"\nFull response: {full_response}")
        assert len(full_response) > 0


class TestAgentToolCalling:
    """Test agent tool calling functionality."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_animation_tool_calling(self):
        """Test that agent calls animation tool when appropriate."""
        from agent import (
            EducationalAgent,
            TextChunk,
            ToolCall,
            ToolResult,
            StreamDone,
        )

        if not os.getenv("ANTHROPIC_API_KEY"):
            pytest.skip("ANTHROPIC_API_KEY not set")

        agent = EducationalAgent(api_provider="anthropic")

        # Request that should trigger animation
        message = "Give me a brief explanation of how gradient descent works. I want to see an animation as well "
        events = []

        print(f"\n{'='*60}")
        print(f"Testing tool calling with: {message}")
        print(f"{'='*60}\n")

        async for event in agent.chat(
            message=message,
            conversation_history=[],
            learner_context=None,
            session=None
        ):
            events.append(event)

            if isinstance(event, TextChunk):
                print(event.content, end="", flush=True)
            elif isinstance(event, ToolCall):
                print(f"\n\n🔧 TOOL CALL: {event.name}")
                print(f"   Arguments: {event.arguments}\n")
            elif isinstance(event, ToolResult):
                print(f"\n📦 TOOL RESULT: {event.name}")
                print(f"   Success: {event.success}")
                if event.success:
                    print(f"   Video URL: {event.result.get('video_url', 'N/A')}")
                else:
                    print(f"   Error: {event.error}")
                print()
            elif isinstance(event, StreamDone):
                print("\n\n✓ Stream completed")

        # Check we got tool events
        tool_calls = [e for e in events if isinstance(e, ToolCall)]
        tool_results = [e for e in events if isinstance(e, ToolResult)]

        print(f"\nSummary:")
        print(f"  - Tool calls: {len(tool_calls)}")
        print(f"  - Tool results: {len(tool_results)}")

        # The agent should have called generate_animation
        assert len(tool_calls) > 0, "Agent should have called a tool"
        assert tool_calls[0].name == "generate_animation"

        # Should have a result
        print(f"Tool results: {tool_results}")
        assert len(tool_results) > 0, "Should have tool result"

        # If successful, should have video URL
        if tool_results[0].success:
            import json

        tool_message = tool_results[0].result['result']
        content_dict = json.loads(tool_message.content)
        video_url = content_dict.get("video_url")
        print(f"\n✓ Video URL: {video_url}")
        assert video_url is not None, "Should have video URL"
        


# Standalone test runner
async def run_manual_test():
    """Run a manual end-to-end test."""
    print("=" * 70)
    print("MANUAL END-TO-END TEST")
    print("=" * 70)

    # Check environment
    print("\n1. Checking environment...")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("   ✗ ANTHROPIC_API_KEY not set")
        return
    print("   ✓ ANTHROPIC_API_KEY found")

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SECRET_KEY")
    if supabase_url and supabase_key:
        print("   ✓ Supabase credentials found")
    else:
        print("   ⚠ Supabase credentials not set - videos will be local only")

    # Import and initialize
    print("\n2. Importing agent...")
    try:
        from agent import (
            EducationalAgent,
            TextChunk,
            ToolCall,
            ToolResult,
            StreamDone,
            Session,
            LearnerContext,
        )
        print("   ✓ Imports successful")
    except Exception as e:
        print(f"   ✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n3. Initializing agent...")
    try:
        agent = EducationalAgent(api_provider="anthropic")
        print("   ✓ Agent initialized")
    except Exception as e:
        print(f"   ✗ Agent init failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test simple chat
    print("\n4. Testing simple chat (no tool use)...")
    print("-" * 50)
    try:
        async for event in agent.chat(
            message="What is machine learning in one sentence?",
            conversation_history=[],
        ):
            if isinstance(event, TextChunk):
                print(event.content, end="", flush=True)
            elif isinstance(event, StreamDone):
                print("\n   ✓ Simple chat works")
    except Exception as e:
        print(f"\n   ✗ Simple chat failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test tool calling
    print("\n5. Testing tool calling (animation generation)...")
    print("-" * 50)
    print("   This may take 30-60 seconds for video rendering...\n")

    try:
        tool_called = False
        tool_succeeded = False
        video_url = None

        async for event in agent.chat(
            message="Create a visual animation showing how a simple neural network forward pass works.",
            conversation_history=[],
        ):
            if isinstance(event, TextChunk):
                print(event.content, end="", flush=True)
            elif isinstance(event, ToolCall):
                tool_called = True
                print(f"\n\n   🔧 Tool called: {event.name}")
                print(f"   Arguments: {event.arguments}")
            elif isinstance(event, ToolResult):
                tool_succeeded = event.success
                if event.success:
                    video_url = event.result.get("video_url")
                    print(f"\n   ✓ Tool succeeded")
                    print(f"   Video URL: {video_url}")
                else:
                    print(f"\n   ✗ Tool failed: {event.error}")
            elif isinstance(event, StreamDone):
                print()

        print("\n" + "-" * 50)
        if tool_called:
            print("   ✓ Tool was called")
        else:
            print("   ⚠ Tool was NOT called (agent may have decided not to)")

        if tool_succeeded:
            print("   ✓ Animation generated successfully")
            print(f"   Video URL: {video_url}")
        elif tool_called:
            print("   ✗ Animation generation failed")

    except Exception as e:
        print(f"\n   ✗ Tool calling test failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    # Run the manual test
    asyncio.run(run_manual_test())
