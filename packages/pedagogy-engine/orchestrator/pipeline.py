"""
Full Pipeline Orchestrator: Topic → Video + Pedagogical Metadata

Chains all 4 layers to produce complete educational content from a topic.
"""

import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable
from dataclasses import dataclass, field

from layer1.generator import PedagogicalIntentGenerator
from layer1.schema import PedagogicalIntentWithMetadata
from layer2.generator import StoryboardGenerator
from layer2.schema import StoryboardWithMetadata
from layer3.generator import ManimPromptGenerator
from layer3.schema import ManimPromptWithMetadata
from layer4.generator import Layer4Generator
from layer4.schema import ManimExecutionWithMetadata

from .schema import (
    PipelineStage,
    PipelineProgress,
    FullPipelineResponse,
    PedagogicalMetadata,
    StoryboardSummary,
    StoryboardBeat,
    VideoMetadata,
    TimingBreakdown,
)


@dataclass
class LayerTimings:
    """Track execution time for each layer."""
    layer1: float = 0.0
    layer2: float = 0.0
    layer3: float = 0.0
    layer4: float = 0.0


class FullPipelineOrchestrator:
    """
    Orchestrates the complete pipeline from topic to video.

    Chains:
    - Layer 1: Topic → Pedagogical Intent
    - Layer 2: Pedagogical Intent → Storyboard
    - Layer 3: Storyboard → Manim Prompt
    - Layer 4: Manim Prompt → Video

    Supports:
    - Progress callbacks for real-time updates
    - Graceful error handling with partial results
    - Configurable layer parameters
    """

    def __init__(
        self,
        # Layer 1 config
        intent_model: Optional[str] = None,
        intent_temperature: float = 0.7,
        intent_api_provider: str = "anthropic",

        # Layer 2 config
        storyboard_strategy: str = "hybrid",

        # Layer 4 config
        code_api_provider: str = "anthropic",
        code_model: Optional[str] = None,
        code_temperature: float = 0.0,
        video_resolution: str = "480p15",
        use_rag: bool = True,
        rag_examples: int = 3,

        # Output config
        output_dir: str = "output/pipeline",
        video_base_url: str = "/api/pipeline/video"
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.video_base_url = video_base_url

        # Store config for lazy initialization
        # Layer 1 now handles path resolution internally
        self._intent_config = {
            "model_name": intent_model,
            "temperature": intent_temperature,
            "api_provider": intent_api_provider,
        }
        self._storyboard_config = {
            "strategy": storyboard_strategy,
        }
        self._layer4_config = {
            "api_provider": code_api_provider,
            "code_model": code_model,
            "code_temperature": code_temperature,
            "manim_resolution": video_resolution,
            "output_dir": str(self.output_dir / "videos"),
            "use_rag": use_rag,
            "rag_examples": rag_examples,
        }

        # Lazy-initialized generators
        self._layer1 = None
        self._layer2 = None
        self._layer3 = None
        self._layer4 = None

    @property
    def layer1(self) -> PedagogicalIntentGenerator:
        if self._layer1 is None:
            self._layer1 = PedagogicalIntentGenerator(**self._intent_config)
        return self._layer1

    @property
    def layer2(self) -> StoryboardGenerator:
        if self._layer2 is None:
            self._layer2 = StoryboardGenerator(**self._storyboard_config)
        return self._layer2

    @property
    def layer3(self) -> ManimPromptGenerator:
        if self._layer3 is None:
            self._layer3 = ManimPromptGenerator()
        return self._layer3

    @property
    def layer4(self) -> Layer4Generator:
        if self._layer4 is None:
            self._layer4 = Layer4Generator(**self._layer4_config)
        return self._layer4

    def run(
        self,
        topic: str,
        domain: Optional[str] = None,
        difficulty_level: Optional[int] = None,
        include_generated_code: bool = False,
        progress_callback: Optional[Callable[[PipelineProgress], None]] = None
    ) -> FullPipelineResponse:
        """
        Execute the full pipeline from topic to video.

        Args:
            topic: The learning topic to generate content for
            domain: Optional domain hint (e.g., 'machine_learning')
            difficulty_level: Optional difficulty (1-5)
            include_generated_code: Whether to include Manim code in response
            progress_callback: Optional callback for progress updates

        Returns:
            FullPipelineResponse with all outputs and metadata
        """
        job_id = str(uuid.uuid4())[:8]
        started_at = datetime.now()
        timings = LayerTimings()

        # Initialize partial results
        pedagogical_intent: Optional[PedagogicalIntentWithMetadata] = None
        storyboard: Optional[StoryboardWithMetadata] = None
        manim_prompt: Optional[ManimPromptWithMetadata] = None
        execution: Optional[ManimExecutionWithMetadata] = None

        error_stage: Optional[str] = None
        error_message: Optional[str] = None

        def update_progress(stage: PipelineStage, percent: int, message: str, error: Optional[str] = None):
            if progress_callback:
                progress = PipelineProgress(
                    job_id=job_id,
                    stage=stage,
                    progress_percent=percent,
                    message=message,
                    started_at=started_at.isoformat(),
                    updated_at=datetime.now().isoformat(),
                    error=error
                )
                progress_callback(progress)

        try:
            # === Layer 1: Topic → Pedagogical Intent ===
            update_progress(PipelineStage.LAYER1_INTENT, 10, "Generating pedagogical intent...")

            layer1_start = time.time()
            pedagogical_intent = self.layer1.generate(
                topic=topic,
                domain=domain,
                difficulty_level=difficulty_level
            )
            timings.layer1 = time.time() - layer1_start

            update_progress(PipelineStage.LAYER1_INTENT, 25, "Pedagogical intent generated")
            print(f"✓ Layer 1 complete: {timings.layer1:.1f}s")

        except Exception as e:
            error_stage = PipelineStage.LAYER1_INTENT.value
            error_message = f"Layer 1 failed: {str(e)}"
            update_progress(PipelineStage.FAILED, 10, error_message, str(e))
            print(f"✗ Layer 1 failed: {e}")

        # Continue to Layer 2 if Layer 1 succeeded
        if pedagogical_intent:
            try:
                # === Layer 2: Pedagogical Intent → Storyboard ===
                update_progress(PipelineStage.LAYER2_STORYBOARD, 30, "Generating storyboard...")

                layer2_start = time.time()
                storyboard = self.layer2.generate(
                    pedagogical_intent=pedagogical_intent.intent
                )
                timings.layer2 = time.time() - layer2_start

                update_progress(PipelineStage.LAYER2_STORYBOARD, 45, "Storyboard generated")
                print(f"✓ Layer 2 complete: {timings.layer2:.1f}s")

            except Exception as e:
                error_stage = PipelineStage.LAYER2_STORYBOARD.value
                error_message = f"Layer 2 failed: {str(e)}"
                update_progress(PipelineStage.FAILED, 30, error_message, str(e))
                print(f"✗ Layer 2 failed: {e}")

        # Continue to Layer 3 if Layer 2 succeeded
        if storyboard:
            try:
                # === Layer 3: Storyboard → Manim Prompt ===
                update_progress(PipelineStage.LAYER3_PROMPT, 50, "Generating Manim prompt...")

                layer3_start = time.time()
                manim_prompt = self.layer3.generate(storyboard)

                # Enrich with pedagogical context for Layer 4
                manim_prompt.metadata.pedagogical_context = {
                    "core_question": pedagogical_intent.intent.core_question,
                    "target_mental_model": pedagogical_intent.intent.target_mental_model,
                    "common_misconception": pedagogical_intent.intent.common_misconception,
                    "visual_metaphor": pedagogical_intent.intent.spatial_metaphor,
                    "key_insight": pedagogical_intent.intent.disambiguating_contrast,
                }
                timings.layer3 = time.time() - layer3_start

                update_progress(PipelineStage.LAYER3_PROMPT, 55, "Manim prompt generated")
                print(f"✓ Layer 3 complete: {timings.layer3:.1f}s")

            except Exception as e:
                error_stage = PipelineStage.LAYER3_PROMPT.value
                error_message = f"Layer 3 failed: {str(e)}"
                update_progress(PipelineStage.FAILED, 50, error_message, str(e))
                print(f"✗ Layer 3 failed: {e}")

        # Continue to Layer 4 if Layer 3 succeeded
        if manim_prompt:
            try:
                # === Layer 4: Manim Prompt → Video ===
                update_progress(PipelineStage.LAYER4_VIDEO, 60, "Generating and rendering video...")

                layer4_start = time.time()
                execution = self.layer4.generate(manim_prompt)
                timings.layer4 = time.time() - layer4_start

                if execution.execution_result.success:
                    update_progress(PipelineStage.COMPLETED, 100, "Video generated successfully")
                    print(f"✓ Layer 4 complete: {timings.layer4:.1f}s")
                else:
                    error_stage = PipelineStage.LAYER4_VIDEO.value
                    error_message = f"Video generation failed: {execution.execution_result.error_message}"
                    update_progress(PipelineStage.FAILED, 90, error_message)
                    print(f"✗ Layer 4 failed: {execution.execution_result.error_message}")

            except Exception as e:
                error_stage = PipelineStage.LAYER4_VIDEO.value
                error_message = f"Layer 4 failed: {str(e)}"
                update_progress(PipelineStage.FAILED, 60, error_message, str(e))
                print(f"✗ Layer 4 failed: {e}")

        # Build response
        completed_at = datetime.now()
        total_seconds = (completed_at - started_at).total_seconds()

        return self._build_response(
            job_id=job_id,
            topic=topic,
            pedagogical_intent=pedagogical_intent,
            storyboard=storyboard,
            execution=execution,
            error_stage=error_stage,
            error_message=error_message,
            started_at=started_at,
            completed_at=completed_at,
            timings=timings,
            include_generated_code=include_generated_code,
        )

    def _build_response(
        self,
        job_id: str,
        topic: str,
        pedagogical_intent: Optional[PedagogicalIntentWithMetadata],
        storyboard: Optional[StoryboardWithMetadata],
        execution: Optional[ManimExecutionWithMetadata],
        error_stage: Optional[str],
        error_message: Optional[str],
        started_at: datetime,
        completed_at: datetime,
        timings: LayerTimings,
        include_generated_code: bool,
    ) -> FullPipelineResponse:
        """Build the API response from pipeline outputs."""

        # Extract pedagogical metadata
        pedagogy = None
        if pedagogical_intent:
            intent = pedagogical_intent.intent
            pedagogy = PedagogicalMetadata(
                topic=intent.topic,
                core_question=intent.core_question,
                target_mental_model=intent.target_mental_model,
                common_misconception=intent.common_misconception,
                disambiguating_contrast=intent.disambiguating_contrast,
                concrete_anchor=intent.concrete_anchor,
                check_for_understanding=intent.check_for_understanding,
                domain=intent.domain,
                difficulty_level=intent.difficulty_level,
                spatial_metaphor=intent.spatial_metaphor,
            )

        # Extract storyboard summary
        storyboard_summary = None
        if storyboard:
            sb = storyboard.storyboard
            storyboard_summary = StoryboardSummary(
                topic=sb.topic,
                pedagogical_pattern=sb.pedagogical_pattern,
                beats=[
                    StoryboardBeat(purpose=b.purpose, intent=b.intent)
                    for b in sb.beats
                ],
            )

        # Extract video metadata
        video = None
        success = False
        if execution and execution.execution_result.success:
            success = True
            video = VideoMetadata(
                video_url=f"{self.video_base_url}/{job_id}",
                video_path=execution.execution_result.video_path,
                resolution=execution.execution_result.resolution,
                execution_time_seconds=execution.execution_result.execution_time_seconds,
                generated_code=execution.code_response.code if include_generated_code else None,
            )

        # Build timing breakdown
        total_seconds = (completed_at - started_at).total_seconds()
        timing = TimingBreakdown(
            total_seconds=total_seconds,
            layer1_seconds=timings.layer1,
            layer2_seconds=timings.layer2,
            layer3_seconds=timings.layer3,
            layer4_seconds=timings.layer4,
        )

        return FullPipelineResponse(
            job_id=job_id,
            topic=topic,
            success=success,
            error_stage=error_stage,
            error_message=error_message,
            video=video,
            pedagogy=pedagogy,
            storyboard=storyboard_summary,
            started_at=started_at.isoformat(),
            completed_at=completed_at.isoformat(),
            timing=timing,
        )


# --- CLI for testing ---

def main():
    """CLI for testing the full pipeline."""
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Run the full pipeline from topic to video"
    )
    parser.add_argument(
        "--topic",
        type=str,
        required=True,
        help="Topic to generate content for"
    )
    parser.add_argument(
        "--domain",
        type=str,
        help="Optional domain hint (e.g., 'machine_learning')"
    )
    parser.add_argument(
        "--difficulty",
        type=int,
        choices=[1, 2, 3, 4, 5],
        help="Difficulty level (1-5)"
    )
    parser.add_argument(
        "--resolution",
        type=str,
        default="480p15",
        choices=["480p15", "720p30", "1080p60"],
        help="Video resolution"
    )
    parser.add_argument(
        "--api-provider",
        type=str,
        default="anthropic",
        choices=["anthropic", "openai"],
        help="API provider for LLM calls"
    )
    parser.add_argument(
        "--include-code",
        action="store_true",
        help="Include generated Manim code in output"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Path to save output JSON"
    )

    args = parser.parse_args()

    # Create orchestrator
    orchestrator = FullPipelineOrchestrator(
        intent_api_provider=args.api_provider,
        code_api_provider=args.api_provider,
        video_resolution=args.resolution,
    )

    # Progress callback
    def on_progress(progress: PipelineProgress):
        print(f"[{progress.progress_percent:3d}%] {progress.stage.value}: {progress.message}")

    # Run pipeline
    print(f"\n{'='*60}")
    print(f"Full Pipeline: {args.topic}")
    print(f"{'='*60}\n")

    result = orchestrator.run(
        topic=args.topic,
        domain=args.domain,
        difficulty_level=args.difficulty,
        include_generated_code=args.include_code,
        progress_callback=on_progress,
    )

    # Print result
    print(f"\n{'='*60}")
    print("Pipeline Result")
    print(f"{'='*60}\n")

    result_dict = result.model_dump()
    print(json.dumps(result_dict, indent=2, default=str))

    # Save to file if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result_dict, f, indent=2, default=str)
        print(f"\n✓ Saved to: {output_path}")

    # Print summary
    print(f"\n{'='*60}")
    print("Summary")
    print(f"{'='*60}")
    print(f"Success: {result.success}")
    print(f"Total time: {result.timing.total_seconds:.1f}s")
    if result.video:
        print(f"Video: {result.video.video_path}")
    if result.error_message:
        print(f"Error: {result.error_message}")


if __name__ == "__main__":
    main()
