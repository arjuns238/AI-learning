"""
Layer 3 Generator: Pedagogical Section → Manim Prompt

Generates focused Manim prompts for pedagogical sections with visual hints.

The new architecture:
- Layer 1 outputs freeform sections with embedded visual hints
- Layer 3 generates Manim prompts for sections where should_animate=true
- No more storyboard/visual_planner - visuals are identified in Layer 1
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, List

from layer3.schema import (
    ManimPrompt,
    ManimPromptMetadata,
    ManimPromptWithMetadata
)
from layer1.schema import PedagogicalIntent, PedagogicalSection

# Resolve paths
_LAYER3_DIR = Path(__file__).parent
_PEDAGOGY_ENGINE_ROOT = _LAYER3_DIR.parent


class ManimPromptGenerator:
    """
    Generates Manim prompts for pedagogical sections with visual hints.

    The primary method is `generate_for_section()` which takes a section
    with `visual.should_animate=True` and produces a focused animation prompt.
    """

    def generate_for_section(
        self,
        section: PedagogicalSection,
        intent: PedagogicalIntent
    ) -> ManimPromptWithMetadata:
        """
        Generate a focused Manim prompt for a pedagogical section with a visual hint.

        Args:
            section: The section from Layer 1 with visual.should_animate=True
            intent: The pedagogical intent for context

        Returns:
            ManimPromptWithMetadata for this section's visual
        """
        if not section.visual or not section.visual.should_animate:
            raise ValueError(f"Section '{section.title}' does not have a visual hint")

        # Load prompt template
        template_path = _PEDAGOGY_ENGINE_ROOT / "prompts" / "visual_manim_prompt.txt"
        with open(template_path, 'r') as f:
            template = f.read()

        # Fill in template with section-based data
        user_prompt = template
        user_prompt = user_prompt.replace("{TOPIC}", intent.topic)
        user_prompt = user_prompt.replace("{SUMMARY}", intent.summary)
        user_prompt = user_prompt.replace("{SECTION_TITLE}", section.title)
        user_prompt = user_prompt.replace("{SECTION_CONTENT}", section.content)
        user_prompt = user_prompt.replace("{ANIMATION_DESCRIPTION}", section.visual.animation_description or "")
        user_prompt = user_prompt.replace("{DURATION_HINT}", str(section.visual.duration_hint or 15))

        title = f"Visual: {section.title} ({intent.topic})"

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
            "Focus ONLY on the specific visual described",
            "Ensure animations are smooth and pedagogically clear",
            "All elements must fit within screen boundaries (x: -7.5 to 7.5, y: -4 to 4)",
            "Use minimal on-screen text (labels, not paragraphs)",
        ]

        metadata = ManimPromptMetadata(
            source_storyboard_topic=intent.topic,
            pedagogical_pattern=None,
            generation_timestamp=datetime.now().isoformat(),
            source_layer2_id=f"section_{section.order}",
            source_visual_section=section.title
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

    def generate_for_intent(
        self,
        intent: PedagogicalIntent
    ) -> List[ManimPromptWithMetadata]:
        """
        Generate Manim prompts for all visual sections in a pedagogical intent.

        Args:
            intent: The pedagogical intent with sections

        Returns:
            List of ManimPromptWithMetadata for each visual section
        """
        prompts = []
        visual_sections = intent.get_visual_sections()

        for section in visual_sections:
            try:
                prompt = self.generate_for_section(section, intent)
                prompts.append(prompt)
            except Exception as e:
                print(f"Failed to generate prompt for section '{section.title}': {e}")

        return prompts

    def _save_prompt(self, prompt: ManimPromptWithMetadata, output_path: Path):
        """Save a prompt to a JSON file."""
        with open(output_path, "w") as f:
            json.dump(prompt.model_dump(), f, indent=2)


# ---------------- CLI ----------------

def main():
    """CLI for generating Manim prompts from Layer 1 output."""
    parser = argparse.ArgumentParser(
        description="Generate Manim prompts from Layer 1 pedagogical intent"
    )

    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to Layer 1 output JSON file (pedagogical intent)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output/manim_prompts",
        help="Directory to save Manim prompts"
    )

    args = parser.parse_args()

    # Load Layer 1 output
    with open(args.input, "r") as f:
        data = json.load(f)

    # Handle both wrapped and unwrapped formats
    if "intent" in data:
        intent = PedagogicalIntent(**data["intent"])
    else:
        intent = PedagogicalIntent(**data)

    # Generate prompts
    generator = ManimPromptGenerator()
    prompts = generator.generate_for_intent(intent)

    # Save prompts
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for prompt in prompts:
        section_id = prompt.metadata.source_layer2_id
        output_path = output_dir / f"{intent.topic.lower().replace(' ', '_')}_{section_id}.json"
        generator._save_prompt(prompt, output_path)
        print(f"✓ Saved: {output_path}")

    print(f"\nGenerated {len(prompts)} Manim prompts for visual sections")


if __name__ == "__main__":
    main()
