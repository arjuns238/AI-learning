"""
Layer 2 Generator: Pedagogical Intent → Storyboard

Generates structured storyboards from pedagogical intent using pattern templates.
"""

import json
import os
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from layer1.schema import PedagogicalIntent, PedagogicalIntentWithMetadata
from layer2.schema import Storyboard, StoryboardMetadata, StoryboardWithMetadata
from layer2.patterns import get_pattern, PATTERN_REGISTRY
from layer2.sequencer import BeatSequencer


class StoryboardGenerator:
    """Generates storyboards from pedagogical intent using pattern templates."""

    def __init__(
        self,
        strategy: str = "hybrid",
        use_llm_sequencing: bool = False,
        model_name: Optional[str] = None,
        api_provider: Optional[str] = None,
        default_pattern: str = "iterative_process"
    ):
        """
        Initialize the storyboard generator.

        Args:
            strategy: Generation strategy ('rule_based' or 'hybrid')
            use_llm_sequencing: Whether to use LLM for beat sequencing (experimental)
            model_name: Model name for LLM sequencing (if enabled)
            api_provider: API provider for LLM ('openai' or 'anthropic')
            default_pattern: Default pattern to use if auto-detection fails
        """
        self.strategy = strategy
        self.use_llm_sequencing = use_llm_sequencing
        self.default_pattern = default_pattern

        # Initialize beat sequencer
        self.sequencer = BeatSequencer(
            use_llm=use_llm_sequencing,
            model=model_name,
            api_provider=api_provider
        )

    def generate(
        self,
        pedagogical_intent: PedagogicalIntent,
        pattern_override: Optional[str] = None
    ) -> StoryboardWithMetadata:
        """
        Generate storyboard from pedagogical intent.

        Args:
            pedagogical_intent: The Layer 1 output
            pattern_override: Optionally force a specific pattern

        Returns:
            StoryboardWithMetadata with beats and generation info
        """
        # 1. Determine which pattern to use
        pattern_name = pattern_override or self._select_pattern(pedagogical_intent)

        # 2. Get pattern instance and generate beats
        try:
            pattern = get_pattern(pattern_name)
        except KeyError:
            print(f"Warning: Pattern '{pattern_name}' not found, using default: {self.default_pattern}")
            pattern_name = self.default_pattern
            pattern = get_pattern(pattern_name)

        beats = pattern.generate_beats(pedagogical_intent)

        # 3. Sequence beats (rule-based or LLM-enhanced)
        ordered_beats = self.sequencer.sequence_beats(beats, pattern_name)

        # 4. Create storyboard
        storyboard = Storyboard(
            topic=pedagogical_intent.topic,
            beats=ordered_beats,
            pedagogical_pattern=pattern_name
        )

        # 5. Validate storyboard
        if not self.sequencer.validate_sequence(ordered_beats):
            print("Warning: Generated storyboard may not follow optimal pedagogical flow")

        # 6. Create metadata
        metadata = StoryboardMetadata(
            generation_strategy=self.strategy,
            pattern_used=pattern_name,
            generation_timestamp=datetime.now().isoformat(),
            source_pedagogical_intent_id=getattr(pedagogical_intent, 'topic', None)
        )

        return StoryboardWithMetadata(
            storyboard=storyboard,
            metadata=metadata
        )

    def _select_pattern(self, intent: PedagogicalIntent) -> str:
        """
        Select appropriate pedagogical pattern based on intent content.

        Currently uses simple keyword matching. Future versions could use
        a learned classifier.

        Args:
            intent: The pedagogical intent

        Returns:
            Pattern name (e.g., 'iterative_process')
        """
        # Combine all text fields for analysis
        text = ' '.join([
            intent.topic.lower(),
            intent.target_mental_model.lower(),
            intent.concrete_anchor.lower() if intent.concrete_anchor else '',
            intent.spatial_metaphor.lower() if intent.spatial_metaphor else ''
        ])

        # Keyword-based pattern detection
        pattern_keywords = {
            'iterative_process': [
                'descent', 'ascent', 'optimize', 'converge', 'iterate',
                'update', 'step', 'algorithm', 'minimize', 'maximize'
            ],
            'spatial_partitioning': [
                'boundary', 'region', 'partition', 'classify', 'separate',
                'divide', 'space', 'decision', 'cluster'
            ],
            'local_operation': [
                'filter', 'convolve', 'slide', 'window', 'local',
                'kernel', 'convolution', 'patch'
            ]
        }

        # Score each pattern
        scores = {}
        for pattern_name, keywords in pattern_keywords.items():
            score = sum(1 for kw in keywords if kw in text)
            scores[pattern_name] = score

        # Return pattern with highest score, or default
        best_pattern = max(scores.items(), key=lambda x: x[1])
        if best_pattern[1] > 0:
            return best_pattern[0]
        else:
            return self.default_pattern

    def generate_from_file(
        self,
        intent_file: Path,
        output_file: Optional[Path] = None
    ) -> StoryboardWithMetadata:
        """
        Load pedagogical intent from file and generate storyboard.

        Args:
            intent_file: Path to JSON file with PedagogicalIntent
            output_file: Optional path to save storyboard (auto-generated if None)

        Returns:
            StoryboardWithMetadata
        """
        # Load intent from file
        with open(intent_file, 'r') as f:
            data = json.load(f)

        # Handle both PedagogicalIntent and PedagogicalIntentWithMetadata
        if 'intent' in data:
            intent = PedagogicalIntent(**data['intent'])
        else:
            intent = PedagogicalIntent(**data)

        # Generate storyboard
        result = self.generate(intent)

        # Save to file if output path provided
        if output_file:
            self._save_storyboard(result, output_file)
        else:
            # Auto-generate output filename
            output_dir = intent_file.parent.parent / 'output' / 'storyboards'
            output_dir.mkdir(parents=True, exist_ok=True)
            output_filename = intent_file.stem + '_storyboard.json'
            output_path = output_dir / output_filename
            self._save_storyboard(result, output_path)
            print(f"Saved storyboard to: {output_path}")

        return result

    def generate_batch(
        self,
        input_dir: Path,
        output_dir: Path,
        pattern: Optional[str] = None
    ):
        """
        Generate storyboards for all pedagogical intents in a directory.

        Args:
            input_dir: Directory containing PedagogicalIntent JSON files
            output_dir: Directory to save generated storyboards
            pattern: Optional pattern to force for all generations
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Find all JSON files
        json_files = list(input_path.glob('*.json'))

        if not json_files:
            print(f"No JSON files found in {input_dir}")
            return

        print(f"Generating storyboards for {len(json_files)} files...")

        for intent_file in json_files:
            try:
                print(f"\nProcessing: {intent_file.name}")

                # Load intent
                with open(intent_file, 'r') as f:
                    data = json.load(f)

                if 'intent' in data:
                    intent = PedagogicalIntent(**data['intent'])
                else:
                    intent = PedagogicalIntent(**data)

                # Generate storyboard
                result = self.generate(intent, pattern_override=pattern)

                # Save to output directory
                output_filename = intent_file.stem + '_storyboard.json'
                output_file = output_path / output_filename
                self._save_storyboard(result, output_file)

                print(f"✓ Generated {len(result.storyboard.beats)} beats")

            except Exception as e:
                print(f"✗ Error processing {intent_file.name}: {e}")
                continue

        print(f"\nBatch generation complete. Output saved to: {output_dir}")

    def _save_storyboard(self, storyboard: StoryboardWithMetadata, output_path: Path):
        """Save storyboard to JSON file."""
        with open(output_path, 'w') as f:
            json.dump(storyboard.model_dump(), f, indent=2)


def main():
    """CLI interface for storyboard generation."""
    parser = argparse.ArgumentParser(
        description="Generate pedagogical storyboards from Layer 1 intent"
    )

    # Input/output arguments
    parser.add_argument(
        '--input',
        type=str,
        help='Path to pedagogical intent JSON file'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Path to save storyboard JSON (optional, auto-generated if not provided)'
    )
    parser.add_argument(
        '--input-dir',
        type=str,
        help='Directory containing pedagogical intent files (for batch processing)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        help='Directory to save storyboards (for batch processing)'
    )

    # Generation options
    parser.add_argument(
        '--pattern',
        type=str,
        choices=list(PATTERN_REGISTRY.keys()),
        help='Force specific pedagogical pattern'
    )
    parser.add_argument(
        '--strategy',
        type=str,
        default='hybrid',
        choices=['rule_based', 'hybrid'],
        help='Generation strategy (default: hybrid)'
    )
    parser.add_argument(
        '--use-llm-sequencing',
        action='store_true',
        help='Use LLM to refine beat ordering (experimental)'
    )
    parser.add_argument(
        '--model',
        type=str,
        help='Model name for LLM sequencing (e.g., gpt-4o-mini, claude-haiku-4)'
    )
    parser.add_argument(
        '--api-provider',
        type=str,
        choices=['openai', 'anthropic'],
        help='API provider for LLM sequencing'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.input and not args.input_dir:
        parser.error("Must provide either --input or --input-dir")

    if args.input_dir and not args.output_dir:
        parser.error("--input-dir requires --output-dir")

    # Initialize generator
    generator = StoryboardGenerator(
        strategy=args.strategy,
        use_llm_sequencing=args.use_llm_sequencing,
        model_name=args.model,
        api_provider=args.api_provider
    )

    # Single file or batch processing
    if args.input:
        # Single file mode
        input_path = Path(args.input)
        output_path = Path(args.output) if args.output else None

        result = generator.generate_from_file(input_path, output_path)

        # Print summary
        print(f"\nGenerated storyboard for: {result.storyboard.topic}")
        print(f"Pattern: {result.storyboard.pedagogical_pattern}")
        print(f"Beats ({len(result.storyboard.beats)}):")
        for i, beat in enumerate(result.storyboard.beats, 1):
            print(f"  {i}. {beat.purpose}: {beat.intent}")

    else:
        # Batch mode
        generator.generate_batch(
            input_dir=Path(args.input_dir),
            output_dir=Path(args.output_dir),
            pattern=args.pattern
        )


if __name__ == "__main__":
    main()
