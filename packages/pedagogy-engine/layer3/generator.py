"""
Layer 3 Generator: Storyboard → Manim Prompt

Compiles a storyboard into a single high-quality ManimCE
code generation prompt.

Also supports generating focused prompts for individual visual opportunities.
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional

from layer2.schema import StoryboardWithMetadata
from layer3.schema import (
    ManimPrompt,
    ManimPromptMetadata,
    ManimPromptWithMetadata
)
from layer1.schema import PedagogicalIntent
from visual_planner.schema import VisualOpportunity

# Resolve paths
_LAYER3_DIR = Path(__file__).parent
_PEDAGOGY_ENGINE_ROOT = _LAYER3_DIR.parent


class ManimPromptGenerator:
    """
    Converts pedagogical storyboards into Manim code-generation prompts.
    """

    def generate(self, storyboard_with_metadata: StoryboardWithMetadata) -> ManimPromptWithMetadata:
        storyboard = storyboard_with_metadata.storyboard

        title = f"Educational animation: {storyboard.topic}"

        system_instruction = (
            "Generate accurate and correct Manim Community Edition (ManimCE) "
            "Python code that produces the requested animation. "
            "The output should be a complete, runnable Manim scene.\n\n"
            "TECHNICAL CONSTRAINTS:\n"
            "- All elements must stay within screen aspect ratio: x-axis [-7.5, 7.5], y-axis [-4, 4]\n"
            "- Plan proper spacing between elements to avoid overlap\n"
            "- Use proper mathematical notation (both symbolic and descriptive forms)\n"
            "- Ensure text and objects are clearly positioned and never overlapping"
        )

        user_prompt = self._build_user_prompt(storyboard)

        constraints = [
            "Use Manim Community Edition (ManimCE)",
            "Produce a single Scene class",
            "Ensure animations are smooth and pedagogically clear",
            "Do not include explanations outside of code comments",
            "All elements must fit within screen boundaries (x: -7.5 to 7.5, y: -4 to 4)",
            "Maintain proper spacing to prevent overlapping objects or text",
            "Format mathematical expressions with proper notation"
        ]

        metadata = ManimPromptMetadata(
            source_storyboard_topic=storyboard.topic,
            pedagogical_pattern=storyboard.pedagogical_pattern,
            generation_timestamp=datetime.now().isoformat(),
            source_layer2_id=storyboard_with_metadata.metadata.source_pedagogical_intent_id
        )

        return ManimPromptWithMetadata(
            prompt=ManimPrompt(
                title=title,
                system_instruction=system_instruction,
                user_prompt=user_prompt,
                constraints=constraints
            ),
            metadata=metadata
        )

    def _build_user_prompt(self, storyboard) -> str:
        lines = []

        lines.append(
            f"I would like an educational animation that explains the concept of {storyboard.topic}."
        )

        lines.append("The animation should proceed step-by-step as follows:")

        for i, beat in enumerate(storyboard.beats, start=1):
            lines.append(f"{i}. {beat.intent}")

        lines.append("The animation should be clear, visually intuitive, and paced to support learning.")
        lines.append("Include on-screen text where appropriate to guide the viewer.")
        lines.append("Conclude the animation by reinforcing the main takeaway of the concept.")

        return "\n".join(lines)

    # ---------- Visual Opportunity Methods ----------

    def generate_for_visual(
        self,
        opportunity: VisualOpportunity,
        intent: PedagogicalIntent
    ) -> ManimPromptWithMetadata:
        """
        Generate a focused Manim prompt for a specific visual opportunity.

        Args:
            opportunity: The visual opportunity from the Visual Planner
            intent: The pedagogical intent for context

        Returns:
            ManimPromptWithMetadata for this specific visual
        """
        # Load prompt template
        template_path = _PEDAGOGY_ENGINE_ROOT / "prompts" / "visual_manim_prompt.txt"
        with open(template_path, 'r') as f:
            template = f.read()

        # Fill in template
        user_prompt = template
        user_prompt = user_prompt.replace("{TOPIC}", intent.topic)
        user_prompt = user_prompt.replace("{TARGET_MENTAL_MODEL}", intent.target_mental_model)
        user_prompt = user_prompt.replace("{CONCEPT}", opportunity.concept)
        user_prompt = user_prompt.replace("{DESCRIPTION}", opportunity.description)
        user_prompt = user_prompt.replace("{PEDAGOGICAL_PURPOSE}", opportunity.pedagogical_purpose)
        user_prompt = user_prompt.replace("{DURATION_HINT}", str(opportunity.duration_hint))

        title = f"Visual: {opportunity.concept} ({intent.topic})"

        system_instruction = (
            "Generate accurate and correct Manim Community Edition (ManimCE) "
            "Python code that produces the requested animation. "
            "The output should be a complete, runnable Manim scene.\n\n"
            "IMPORTANT: This is a SHORT, FOCUSED animation (15-20 seconds) for a single concept.\n"
            "Keep it simple and clear. Do not try to explain the entire topic.\n\n"
            "TECHNICAL CONSTRAINTS:\n"
            "- All elements must stay within screen aspect ratio: x-axis [-7.5, 7.5], y-axis [-4, 4]\n"
            "- Plan proper spacing between elements to avoid overlap\n"
            "- Use proper mathematical notation where applicable\n"
            "- Ensure text and objects are clearly positioned and never overlapping"
        )

        constraints = [
            "Use Manim Community Edition (ManimCE)",
            "Produce a single Scene class",
            "Keep animation to approximately 15-20 seconds",
            "Focus ONLY on the specific concept described",
            "Ensure animations are smooth and pedagogically clear",
            "All elements must fit within screen boundaries (x: -7.5 to 7.5, y: -4 to 4)",
            "Use minimal on-screen text (labels, not paragraphs)",
        ]

        metadata = ManimPromptMetadata(
            source_storyboard_topic=intent.topic,
            pedagogical_pattern=None,
            generation_timestamp=datetime.now().isoformat(),
            source_layer2_id=opportunity.id
        )

        return ManimPromptWithMetadata(
            prompt=ManimPrompt(
                title=title,
                system_instruction=system_instruction,
                user_prompt=user_prompt,
                constraints=constraints
            ),
            metadata=metadata
        )

    # ---------- Layer 2 style helpers ----------

    def generate_from_file(
        self,
        storyboard_file: Path,
        output_file: Optional[Path] = None
    ) -> ManimPromptWithMetadata:

        with open(storyboard_file, "r") as f:
            data = json.load(f)

        # Accept both wrapped and unwrapped formats
        if "storyboard" in data:
            storyboard = StoryboardWithMetadata(**data)
        else:
            storyboard = StoryboardWithMetadata(storyboard=data)

        result = self.generate(storyboard)

        if output_file:
            self._save_prompt(result, output_file)
        else:
            output_dir = storyboard_file.parent.parent / "output" / "manim_prompts"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / (storyboard_file.stem + "_manim_prompt.json")
            self._save_prompt(result, output_path)
            print(f"Saved Manim prompt to: {output_path}")

        return result

    def generate_batch(self, input_dir: Path, output_dir: Path):
        input_dir = Path(input_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        json_files = list(input_dir.glob("*.json"))

        if not json_files:
            print(f"No JSON files found in {input_dir}")
            return

        print(f"Generating Manim prompts for {len(json_files)} files...")

        for file in json_files:
            try:
                print(f"\nProcessing: {file.name}")
                result = self.generate_from_file(file, output_dir / (file.stem + "_manim_prompt.json"))
                print("✓ Generated Manim prompt")
            except Exception as e:
                print(f"✗ Error processing {file.name}: {e}")

        print("\nBatch generation complete.")

    def _save_prompt(self, prompt: ManimPromptWithMetadata, output_path: Path):
        with open(output_path, "w") as f:
            json.dump(prompt.model_dump(), f, indent=2)


# ---------------- CLI ----------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate Manim prompts from Layer 2 storyboards"
    )

    parser.add_argument("--input", type=str, help="Path to storyboard JSON file")
    parser.add_argument("--output", type=str, help="Path to save Manim prompt JSON")
    parser.add_argument("--input-dir", type=str, help="Directory of storyboard JSON files")
    parser.add_argument("--output-dir", type=str, help="Directory to save Manim prompts")

    args = parser.parse_args()

    if not args.input and not args.input_dir:
        parser.error("Must provide either --input or --input-dir")

    if args.input_dir and not args.output_dir:
        parser.error("--input-dir requires --output-dir")

    generator = ManimPromptGenerator()

    if args.input:
        generator.generate_from_file(
            Path(args.input),
            Path(args.output) if args.output else None
        )
    else:
        generator.generate_batch(
            input_dir=Path(args.input_dir),
            output_dir=Path(args.output_dir)
        )


if __name__ == "__main__":
    main()
