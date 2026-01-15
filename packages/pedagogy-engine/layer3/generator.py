"""
Scene Spec Generator

Maps storyboard beats to structured scene specifications and exposes a CLI
for single-file and batch processing (storyboards -> scene specs).
"""

import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from layer2.schema import StoryboardWithMetadata, Beat
from layer3.schema import (
    SceneObject,
    SceneAction,
    SceneSpec,
    SceneSpecMetadata,
    SceneSpecWithMetadata
)


class SceneSpecGenerator:
    """
    Compiles a storyboard into a list of executable scene specifications.
    """

    def generate(self, storyboard_with_metadata: StoryboardWithMetadata) -> SceneSpecWithMetadata:
        storyboard = storyboard_with_metadata.storyboard

        scenes: List[SceneSpec] = []

        for idx, beat in enumerate(storyboard.beats):
            scene = self._compile_beat(beat, idx, storyboard.topic, storyboard.pedagogical_pattern)
            scenes.append(scene)

        metadata = SceneSpecMetadata(
            source_storyboard_topic=storyboard.topic,
            generation_timestamp=datetime.now().isoformat(),
            source_layer2_id=storyboard_with_metadata.metadata.source_pedagogical_intent_id
        )

        return SceneSpecWithMetadata(scenes=scenes, metadata=metadata)

    def _compile_beat(
        self,
        beat: Beat,
        idx: int,
        topic: str,
        pattern: str
    ) -> SceneSpec:
        purpose = beat.purpose.lower()

        if purpose == "set_context":
            return self._scene_set_context(beat, idx)

        if purpose == "place_initial_state":
            return self._scene_place_initial_state(beat, idx)

        if purpose in ["show_update_rule", "show_mechanism"]:
            return self._scene_show_update_rule(beat, idx)

        if purpose == "iterate_process":
            return self._scene_iterate_process(beat, idx)

        if purpose in ["contrast_failure_mode", "reveal_failure_mode"]:
            return self._scene_failure_mode(beat, idx)

        # Fallback
        return self._scene_generic(beat, idx)

    # -----------------------
    # Scene templates
    # -----------------------

    def _scene_set_context(self, beat: Beat, idx: int) -> SceneSpec:
        return SceneSpec(
            scene_id=f"set_context_{idx}",
            pedagogical_purpose=beat.purpose,
            conceptual_goal=beat.intent,
            objects=[
                SceneObject(id="loss_surface", type="surface", role="landscape"),
                SceneObject(id="axes", type="axes", role="reference_frame")
            ],
            actions=[
                SceneAction(action="create", target="axes"),
                SceneAction(action="create", target="loss_surface"),
                SceneAction(action="slow_rotate", target="loss_surface", parameters={"duration": 4})
            ],
            camera={"mode": "3d_orbit"}
        )

    def _scene_place_initial_state(self, beat: Beat, idx: int) -> SceneSpec:
        return SceneSpec(
            scene_id=f"initial_state_{idx}",
            pedagogical_purpose=beat.purpose,
            conceptual_goal=beat.intent,
            objects=[
                SceneObject(id="ball", type="point_mass", role="parameter_state")
            ],
            actions=[
                SceneAction(action="create", target="ball"),
                SceneAction(action="place_on_surface", target="ball", parameters={"region": "high_point"}),
                SceneAction(action="highlight", target="ball")
            ],
            camera={"mode": "focus", "target": "ball"}
        )

    def _scene_show_update_rule(self, beat: Beat, idx: int) -> SceneSpec:
        return SceneSpec(
            scene_id=f"update_rule_{idx}",
            pedagogical_purpose=beat.purpose,
            conceptual_goal=beat.intent,
            objects=[
                SceneObject(id="gradient_field", type="vector_field", role="mechanism")
            ],
            actions=[
                SceneAction(action="create", target="gradient_field"),
                SceneAction(action="pulse", target="gradient_field"),
                SceneAction(action="draw_arrow_from_gradient", target="ball")
            ]
        )

    def _scene_iterate_process(self, beat: Beat, idx: int) -> SceneSpec:
        return SceneSpec(
            scene_id=f"iterate_{idx}",
            pedagogical_purpose=beat.purpose,
            conceptual_goal=beat.intent,
            objects=[],
            actions=[
                SceneAction(
                    action="loop",
                    parameters={"count": 6},
                    steps=[
                        SceneAction(action="compute_gradient", target="ball"),
                        SceneAction(action="move_along_gradient", target="ball", parameters={"step_scale": 0.4}),
                        SceneAction(action="leave_trace", target="ball")
                    ]
                )
            ],
            camera={"mode": "follow", "target": "ball"}
        )

    def _scene_failure_mode(self, beat: Beat, idx: int) -> SceneSpec:
        return SceneSpec(
            scene_id=f"failure_{idx}",
            pedagogical_purpose=beat.purpose,
            conceptual_goal=beat.intent,
            objects=[],
            actions=[
                SceneAction(action="reset_ball", target="ball"),
                SceneAction(action="move_along_gradient", target="ball", parameters={"step_scale": 2.0}),
                SceneAction(action="shake_camera"),
                SceneAction(action="highlight_region", parameters={"region": "overshoot"})
            ]
        )

    def _scene_generic(self, beat: Beat, idx: int) -> SceneSpec:
        return SceneSpec(
            scene_id=f"generic_{idx}",
            pedagogical_purpose=beat.purpose,
            conceptual_goal=beat.intent,
            objects=[],
            actions=[
                SceneAction(action="display_text", parameters={"text": beat.intent})
            ]
        )


# -----------------------
# CLI / Batch utilities
# -----------------------

def _process_file(in_path: Path, out_path: Optional[Path] = None) -> Path:
    data = json.loads(in_path.read_text())
    swm = StoryboardWithMetadata(**data)
    spec = SceneSpecGenerator().generate(swm)

    if out_path is None:
        out_dir = in_path.parent.parent / "output" / "scenes"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / (in_path.stem + "_scenes.json")
    else:
        out_path.parent.mkdir(parents=True, exist_ok=True)

    out_path.write_text(json.dumps(spec.model_dump(), indent=2))
    return out_path


def generate_batch(input_dir: Path, output_dir: Path):
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    json_files = list(input_dir.glob("*.json"))
    if not json_files:
        print(f"No JSON files found in {input_dir}")
        return

    print(f"Generating scene specs for {len(json_files)} files...")
    for f in json_files:
        try:
            out_path = output_dir / (f.stem + "_scenes.json")
            saved = _process_file(f, out_path)
            print(f"✓ {f.name} -> {saved.name}")
        except Exception as e:
            print(f"✗ Error processing {f.name}: {e}")
            continue

    print(f"\nBatch complete. Output saved to: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Generate Layer 3 scene specs from Layer 2 storyboards")
    parser.add_argument("--input", help="single storyboard JSON file")
    parser.add_argument("--output", help="single output file (for --input)")
    parser.add_argument("--input-dir", help="directory with storyboard JSON files")
    parser.add_argument("--output-dir", help="directory to save scene JSON files (required with --input-dir)")

    args = parser.parse_args()

    if args.input:
        in_path = Path(args.input)
        out_path = Path(args.output) if args.output else None
        saved = _process_file(in_path, out_path)
        print("Saved:", saved)
    elif args.input_dir:
        if not args.output_dir:
            parser.error("--input-dir requires --output-dir")
        generate_batch(Path(args.input_dir), Path(args.output_dir))
    else:
        parser.error("Provide --input or --input-dir")


if __name__ == "__main__":
    main()