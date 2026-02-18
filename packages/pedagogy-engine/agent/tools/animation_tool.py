"""
Animation Tool: Generate Manim animations

Wraps Layer 3 (prompt generation) and Layer 4 (code generation + execution)
to provide animation generation as a tool for the educational agent.

Videos are uploaded to Supabase Storage and served via signed URLs.

NOTE: Heavy imports (layer3, layer4) are deferred to avoid 7+ second import
cascade when the agent package is loaded. They are imported lazily in the
property getters where they're actually needed.
"""

import asyncio
import uuid
import os
from pathlib import Path
from typing import Optional, Dict, Any, TYPE_CHECKING
from concurrent.futures import ThreadPoolExecutor

from agent.schema import AnimationResult

# Type hints only - not imported at runtime
if TYPE_CHECKING:
    from layer1.schema import PedagogicalIntent, PedagogicalSection, VisualHint
    from layer3.generator import ManimPromptGenerator
    from layer4.generator import Layer4Generator

# Try to import Supabase VideoStore (may not be configured)
try:
    import sys
    # Add api package to path for supabase_client import
    api_path = Path(__file__).parent.parent.parent.parent / "api"
    sys.path.insert(0, str(api_path))
    from supabase_client import VideoStore
    SUPABASE_AVAILABLE = True
except Exception:
    SUPABASE_AVAILABLE = False
    VideoStore = None


class GenerateAnimationTool:
    """
    Tool that generates Manim animations for educational concepts.

    This tool wraps the existing Layer 3 and Layer 4 pipeline,
    allowing the educational agent to invoke animation generation
    when it determines a visual would help the learner.
    """

    # Tool metadata for LLM tool use
    name = "generate_animation"

    description = """Generate an educational animation to visually explain a concept.

Use this tool when:
- The concept is inherently spatial or visual (transformations, graphs, data flows, geometric concepts)
- The user is struggling to understand and a visual demonstration might help
- The user explicitly asks for a visualization or animation
- You're explaining a process that unfolds over time (algorithms, state changes)

Do NOT use this tool when:
- The concept is simple and better explained with text
- You've already generated an animation for the same concept recently
- The user is asking a quick clarifying question
- Text with maybe a simple diagram would suffice"""

    parameters = {
        "type": "object",
        "properties": {
            "concept": {
                "type": "string",
                "description": "The specific concept to visualize (e.g., 'gradient descent optimization', 'matrix multiplication')"
            },
            "context": {
                "type": "string",
                "description": "What the user is trying to understand - provides context for the animation"
            },
            "focus_area": {
                "type": "string",
                "description": "Optional: specific part to emphasize if the user had confusion about a particular aspect"
            },
            "duration_hint": {
                "type": "string",
                "enum": ["short", "detailed"],
                "description": "Optional: 'short' for 5-10 second focused animation, 'detailed' for 15-30 second comprehensive animation"
            }
        },
        "required": ["concept", "context"]
    }

    def __init__(
        self,
        api_provider: str = "anthropic",
        video_resolution: str = "480p15",
        output_dir: str = "/tmp/manim_agent_videos",  # Outside API folder to prevent uvicorn reload
        use_supabase: bool = True,
        url_expires_in: int = 3600  # 1 hour default
    ):
        self.api_provider = api_provider
        self.video_resolution = video_resolution
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Supabase configuration
        self.use_supabase = use_supabase and SUPABASE_AVAILABLE
        self.url_expires_in = url_expires_in

        if use_supabase and not SUPABASE_AVAILABLE:
            print("⚠ Supabase not configured - videos will only be saved locally")

        # Lazy initialization of generators
        self._layer3 = None
        self._layer4 = None
        self._executor = ThreadPoolExecutor(max_workers=1)

    @property
    def layer3(self) -> "ManimPromptGenerator":
        if self._layer3 is None:
            # Lazy import to avoid 7+ second import cascade at module load time
            from layer3.generator import ManimPromptGenerator
            self._layer3 = ManimPromptGenerator()
        return self._layer3

    @property
    def layer4(self) -> "Layer4Generator":
        if self._layer4 is None:
            # Lazy import to avoid 7+ second import cascade at module load time
            from layer4.generator import Layer4Generator
            self._layer4 = Layer4Generator(
                manim_resolution=self.video_resolution,
                output_dir=str(self.output_dir),
                use_rag=True,
                rag_examples=3,
                enable_caching=True
            )
        return self._layer4

    def _create_minimal_intent(
        self,
        concept: str,
        context: str,
        focus_area: Optional[str] = None
    ) -> tuple["PedagogicalIntent", "PedagogicalSection"]:
        """
        Create minimal PedagogicalIntent and Section for the animation tool.

        Since we're generating a single focused animation (not a full lesson),
        we create a simplified structure that Layer 3 can work with.
        """
        # Lazy import layer1 schema (lightweight but keeps imports consistent)
        from layer1.schema import PedagogicalIntent, PedagogicalSection, VisualHint

        # Build animation description
        animation_description = f"Visualize {concept}."
        if focus_area:
            animation_description += f" Focus specifically on: {focus_area}."
        animation_description += f" Context: {context}"

        # Create the visual hint
        visual_hint = VisualHint(
            should_animate=True,
            animation_description=animation_description,
            duration_hint=15  # Default duration
        )

        # Create a minimal section
        section = PedagogicalSection(
            title=concept,
            content=context,
            order=1,  # Must be >= 1
            visual=visual_hint
        )

        # Create a minimal intent
        intent = PedagogicalIntent(
            topic=concept,
            summary=context,
            sections=[section]
        )

        return intent, section

    def _execute_sync(
        self,
        concept: str,
        context: str,
        focus_area: Optional[str] = None,
        duration_hint: Optional[str] = None
    ) -> AnimationResult:
        """
        Synchronous execution of the animation pipeline.
        Called from async context via executor.
        """
        try:
            # Create minimal intent and section
            intent, section = self._create_minimal_intent(concept, context, focus_area)

            # Adjust duration based on hint
            if duration_hint == "short":
                section.visual.duration_hint = 8
            elif duration_hint == "detailed":
                section.visual.duration_hint = 25

            print(f"\n{'='*60}")
            print(f"ANIMATION TOOL: Generating animation for '{concept}'")
            print(f"{'='*60}")

            # Layer 3: Generate Manim prompt
            print("Step 1: Generating Manim prompt...")
            manim_prompt = self.layer3.generate_for_section(section, intent)

            # Layer 4: Generate code and render video
            print("Step 2: Generating code and rendering video...")
            execution_result_with_metadata = self.layer4.generate(manim_prompt)

            if execution_result_with_metadata.execution_result.success:
                # Generate a unique clip ID
                clip_id = str(uuid.uuid4())[:8]
                job_id = f"agent_{clip_id}"

                video_path = execution_result_with_metadata.execution_result.video_path
                video_url = None

                # Upload to Supabase Storage and get signed URL
                if self.use_supabase and VideoStore:
                    try:
                        print("Step 3: Uploading to Supabase Storage...")
                        storage_path = VideoStore.upload_clip(job_id, clip_id, video_path)

                        if storage_path:
                            video_url = VideoStore.get_signed_url(storage_path, self.url_expires_in)
                            if video_url:
                                print(f"✓ Video uploaded to Supabase: {storage_path}")
                            else:
                                print("⚠ Failed to get signed URL, using local path")
                        else:
                            print("⚠ Failed to upload to Supabase, using local path")
                    except Exception as e:
                        print(f"⚠ Supabase upload error: {e}, using local path")

                # Fallback to local file path if Supabase failed or not configured
                if not video_url:
                    # Return absolute path for local serving
                    video_url = f"file://{os.path.abspath(video_path)}"

                print(f"✓ Animation generated successfully: {video_path}")

                return AnimationResult(
                    success=True,
                    video_url=video_url,
                    video_path=video_path,
                    execution_time_seconds=execution_result_with_metadata.execution_result.execution_time_seconds
                )
            else:
                error_msg = execution_result_with_metadata.execution_result.error_message or "Unknown error"
                print(f"✗ Animation generation failed: {error_msg}")

                return AnimationResult(
                    success=False,
                    error=error_msg,
                    execution_time_seconds=execution_result_with_metadata.execution_result.execution_time_seconds
                )

        except Exception as e:
            print(f"✗ Animation tool error: {e}")
            import traceback
            traceback.print_exc()

            return AnimationResult(
                success=False,
                error=str(e)
            )

    async def execute(
        self,
        concept: str,
        context: str,
        focus_area: Optional[str] = None,
        duration_hint: Optional[str] = None
    ) -> AnimationResult:
        """
        Execute the animation generation asynchronously.

        This runs the CPU/GPU-intensive Manim rendering in a thread pool
        to avoid blocking the async event loop.
        """
        loop = asyncio.get_event_loop()

        # Run the sync execution in a thread pool
        result = await loop.run_in_executor(
            self._executor,
            self._execute_sync,
            concept,
            context,
            focus_area,
            duration_hint
        )

        return result

    def get_tool_definition(self) -> Dict[str, Any]:
        """
        Get the tool definition in the format expected by Claude/OpenAI.
        """
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters
        }
