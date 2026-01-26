"""
Full Pipeline Orchestrator: Topic → Video + Pedagogical Metadata

New Architecture (section-based):
- Layer 1: Topic → Pedagogical Intent with freeform sections + embedded visual hints
- Layer 3: Visual sections → Manim prompts
- Layer 4: Manim prompts → Videos

No more Layer 2 (storyboard) or separate Visual Planner.
Visuals are now identified inline during Layer 1 generation.
"""

import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, List
from dataclasses import dataclass

from layer1.generator import PedagogicalIntentGenerator
from layer1.schema import PedagogicalIntentWithMetadata, PedagogicalSection
from layer3.generator import ManimPromptGenerator
from layer3.schema import ManimPromptWithMetadata
from layer4.generator import Layer4Generator
from layer4.schema import ManimExecutionWithMetadata, AnimationClip

from .schema import (
    PipelineStage,
    PipelineProgress,
    FullPipelineResponse,
    PedagogicalMetadata,
    PedagogicalSectionSummary,
    VisualHintSummary,
    ComparisonSummary,
    VideoMetadata,
    TimingBreakdown,
    AnimationClipSummary,
)


@dataclass
class LayerTimings:
    """Track execution time for each layer."""
    layer1: float = 0.0
    layer3: float = 0.0
    layer4: float = 0.0
    clip_generation: float = 0.0


class FullPipelineOrchestrator:
    """
    Orchestrates the complete pipeline from topic to video.

    New flow:
    - Layer 1: Topic → Pedagogical Intent (with sections + visual hints)
    - Layer 3: Visual sections → Manim prompts
    - Layer 4: Manim prompts → Videos

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
        self._intent_config = {
            "model_name": intent_model,
            "temperature": intent_temperature,
            "api_provider": intent_api_provider,
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
        self._layer3 = None
        self._layer4 = None

    @property
    def layer1(self) -> PedagogicalIntentGenerator:
        if self._layer1 is None:
            self._layer1 = PedagogicalIntentGenerator(**self._intent_config)
        return self._layer1

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
        progress_callback: Optional[Callable[[PipelineProgress], None]] = None,
        debug_callback: Optional[Callable[[int, dict, dict, float, Optional[str]], None]] = None,
        external_job_id: Optional[str] = None
    ) -> FullPipelineResponse:
        """
        Execute the full pipeline from topic to video.

        Args:
            topic: The learning topic to generate content for
            domain: Optional domain hint (e.g., 'machine_learning')
            difficulty_level: Optional difficulty (1-5)
            include_generated_code: Whether to include Manim code in response
            progress_callback: Optional callback for progress updates
            debug_callback: Optional callback for layer I/O debugging.
                            Called with (layer_num, input_data, output_data, duration, error)
            external_job_id: Optional job_id to use (for coordination with API routes)

        Returns:
            FullPipelineResponse with all outputs and metadata
        """
        job_id = external_job_id or str(uuid.uuid4())[:8]
        started_at = datetime.now()
        timings = LayerTimings()

        # Initialize results
        pedagogical_intent: Optional[PedagogicalIntentWithMetadata] = None
        generated_clips: List[AnimationClip] = []

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

        # Layer 1 input for debug
        layer1_input = {"topic": topic, "domain": domain, "difficulty_level": difficulty_level}

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

            update_progress(PipelineStage.LAYER1_INTENT, 30, "Pedagogical intent generated")
            print(f"✓ Layer 1 complete: {timings.layer1:.1f}s")

            # Debug callback
            if debug_callback:
                debug_callback(1, layer1_input, pedagogical_intent.model_dump(), timings.layer1, None)

            # === Extract visual sections from Layer 1 output ===
            intent = pedagogical_intent.intent
            visual_sections = intent.get_visual_sections()
            print(f"Found {len(visual_sections)} sections with visual hints")

            # === Generate clips for each visual section ===
            if visual_sections:
                clip_layer_data = []
                update_progress(
                    PipelineStage.GENERATING_CLIPS,
                    35,
                    f"Generating {len(visual_sections)} animation clips..."
                )

                clip_start = time.time()
                for i, section in enumerate(visual_sections):
                    try:
                        print(f"  Generating clip {i+1}/{len(visual_sections)}: {section.title}")

                        # Layer 3: Generate focused Manim prompt for this section
                        layer3_start = time.time()
                        clip_prompt = self.layer3.generate_for_section(
                            section=section,
                            intent=intent
                        )
                        layer3_time = time.time() - layer3_start
                        timings.layer3 += layer3_time

                        # Layer 4: Generate the video
                        layer4_start = time.time()
                        clip_execution = self.layer4.generate(clip_prompt)
                        layer4_time = time.time() - layer4_start
                        timings.layer4 += layer4_time

                        # Create AnimationClip from result
                        clip = AnimationClip(
                            clip_id=f"section_{section.order}",
                            opportunity_id=f"section_{section.order}",
                            concept=section.title,
                            placement=f"section_{section.order}",
                            video_path=clip_execution.execution_result.video_path if clip_execution.execution_result.success else None,
                            duration_seconds=clip_execution.execution_result.execution_time_seconds if clip_execution.execution_result.success else 0.0,
                            success=clip_execution.execution_result.success,
                            error_message=clip_execution.execution_result.error_message,
                            execution_time_seconds=clip_execution.execution_result.execution_time_seconds,
                            generated_code=clip_execution.code_response.code,
                        )
                        generated_clips.append(clip)

                        # Track Layer 3/4 data for this clip
                        clip_layer_data.append({
                            "clip_id": f"section_{section.order}",
                            "section_title": section.title,
                            "section_order": section.order,
                            "layer3_prompt": clip_prompt.model_dump(),
                            "layer4_execution": clip_execution.model_dump(),
                        })

                        if clip.success:
                            print(f"    ✓ Clip generated: {clip.video_path}")
                        else:
                            print(f"    ✗ Clip failed: {clip.error_message}")

                    except Exception as clip_error:
                        print(f"    ✗ Clip {i+1} failed: {clip_error}")
                        generated_clips.append(AnimationClip(
                            clip_id=f"section_{section.order}",
                            opportunity_id=f"section_{section.order}",
                            concept=section.title,
                            placement=f"section_{section.order}",
                            success=False,
                            error_message=str(clip_error),
                        ))

                timings.clip_generation = time.time() - clip_start
                successful_clips = sum(1 for c in generated_clips if c.success)
                print(f"✓ Clip generation complete: {successful_clips}/{len(visual_sections)} succeeded ({timings.clip_generation:.1f}s)")

                # Debug callbacks for Layer 3/4 aggregated data
                if debug_callback and clip_layer_data:
                    layer3_inputs = []
                    layer3_outputs = []
                    layer4_inputs = []
                    layer4_outputs = []

                    for clip_data in clip_layer_data:
                        layer3_prompt = clip_data.get("layer3_prompt", {})
                        layer4_exec = clip_data.get("layer4_execution", {})

                        layer3_inputs.append({
                            "clip_id": clip_data["clip_id"],
                            "section_title": clip_data["section_title"],
                            "section_order": clip_data["section_order"],
                        })
                        layer3_outputs.append({
                            "clip_id": clip_data["clip_id"],
                            "prompt": layer3_prompt.get("prompt"),
                            "metadata": layer3_prompt.get("metadata"),
                        })

                        layer4_inputs.append({
                            "clip_id": clip_data["clip_id"],
                            "prompt_title": layer3_prompt.get("prompt", {}).get("title"),
                            "prompt": layer3_prompt.get("prompt"),
                        })
                        layer4_outputs.append({
                            "clip_id": clip_data["clip_id"],
                            "code": layer4_exec.get("code_response", {}).get("code"),
                            "execution_result": layer4_exec.get("execution_result"),
                            "metadata": layer4_exec.get("metadata"),
                        })

                    debug_callback(
                        3,
                        {"clips": layer3_inputs, "clip_count": len(layer3_inputs)},
                        {"clips": layer3_outputs, "clip_count": len(layer3_outputs)},
                        timings.layer3,
                        None
                    )

                    debug_callback(
                        4,
                        {"clips": layer4_inputs, "clip_count": len(layer4_inputs)},
                        {"clips": layer4_outputs, "clip_count": len(layer4_outputs)},
                        timings.layer4,
                        None
                    )

                if successful_clips > 0:
                    update_progress(PipelineStage.COMPLETED, 100, "Clips generated successfully")
            else:
                # No visual sections - still success, just no clips
                update_progress(PipelineStage.COMPLETED, 100, "Content generated (no visual sections)")
                print("✓ No visual sections found - pipeline complete without clips")

        except Exception as e:
            error_stage = PipelineStage.LAYER1_INTENT.value
            error_message = f"Layer 1 failed: {str(e)}"
            update_progress(PipelineStage.FAILED, 10, error_message, str(e))
            print(f"✗ Layer 1 failed: {e}")
            if debug_callback:
                debug_callback(1, layer1_input, None, 0, str(e))

        # Build response
        completed_at = datetime.now()

        return self._build_response(
            job_id=job_id,
            topic=topic,
            pedagogical_intent=pedagogical_intent,
            generated_clips=generated_clips,
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
        generated_clips: List[AnimationClip],
        error_stage: Optional[str],
        error_message: Optional[str],
        started_at: datetime,
        completed_at: datetime,
        timings: LayerTimings,
        include_generated_code: bool,
    ) -> FullPipelineResponse:
        """Build the API response from pipeline outputs."""

        # Extract pedagogical metadata with sections
        pedagogy = None
        if pedagogical_intent:
            intent = pedagogical_intent.intent

            # Convert sections to summaries
            section_summaries = []
            for section in intent.sections:
                visual_summary = None
                if section.visual:
                    visual_summary = VisualHintSummary(
                        should_animate=section.visual.should_animate,
                        animation_description=section.visual.animation_description,
                        duration_hint=section.visual.duration_hint
                    )

                comparison_summary = None
                if section.comparison:
                    comparison_summary = ComparisonSummary(
                        item_a=section.comparison.item_a,
                        item_b=section.comparison.item_b,
                        difference=section.comparison.difference
                    )

                section_summaries.append(PedagogicalSectionSummary(
                    title=section.title,
                    content=section.content,
                    order=section.order,
                    visual=visual_summary,
                    steps=section.steps,
                    math_expressions=section.math_expressions,
                    comparison=comparison_summary,
                ))

            pedagogy = PedagogicalMetadata(
                topic=intent.topic,
                summary=intent.summary,
                sections=section_summaries,
                domain=intent.domain,
                difficulty_level=intent.difficulty_level,
            )

        # Build clip summaries
        clip_summaries = []
        for clip in generated_clips:
            # Extract section_order from clip_id (e.g., "section_1" -> 1)
            section_order = int(clip.clip_id.split("_")[1]) if "_" in clip.clip_id else 0

            clip_summaries.append(AnimationClipSummary(
                clip_id=clip.clip_id,
                section_order=section_order,
                section_title=clip.concept,
                video_url=f"{self.video_base_url}/clip/{job_id}/{clip.clip_id}" if clip.success else None,
                video_path=clip.video_path,
                duration_seconds=clip.duration_seconds,
                success=clip.success,
                error_message=clip.error_message,
            ))

        # Success if we have pedagogical intent (clips are optional)
        has_successful_clips = any(c.success for c in generated_clips)
        success = pedagogical_intent is not None

        # Build timing breakdown
        total_seconds = (completed_at - started_at).total_seconds()
        timing = TimingBreakdown(
            total_seconds=total_seconds,
            layer1_seconds=timings.layer1,
            layer3_seconds=timings.layer3,
            layer4_seconds=timings.layer4,
            clip_generation_seconds=timings.clip_generation,
        )

        return FullPipelineResponse(
            job_id=job_id,
            topic=topic,
            success=success,
            error_stage=error_stage,
            error_message=error_message,
            video=None,  # No single video in new architecture
            pedagogy=pedagogy,
            clips=clip_summaries,
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
    print(f"Sections: {len(result.pedagogy.sections) if result.pedagogy else 0}")
    print(f"Clips: {len(result.clips)} ({sum(1 for c in result.clips if c.success)} successful)")
    if result.error_message:
        print(f"Error: {result.error_message}")


if __name__ == "__main__":
    main()
