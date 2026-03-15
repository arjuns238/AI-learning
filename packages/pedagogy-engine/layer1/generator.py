"""
Layer 1 Generator: Topic → Pedagogical Intent

Generates structured pedagogical content with dynamic sections and embedded visual hints.
Supports both OpenAI and Anthropic APIs.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

from layer1.schema import (
    PedagogicalIntent,
    PedagogicalIntentWithMetadata,
    GenerationMetadata,
    PedagogicalSection,
    VisualHint,
    Comparison
)

# Load environment variables
load_dotenv()

# Get the pedagogy-engine root directory for resolving default paths
_LAYER1_DIR = Path(__file__).parent
_PEDAGOGY_ENGINE_ROOT = _LAYER1_DIR.parent


class PedagogicalIntentGenerator:
    """Generates pedagogical intent from topics using LLM."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        api_provider: Optional[str] = None,
        prompt_template_path: Optional[str] = None
    ):
        # Determine API provider and model
        self.api_provider = api_provider or os.getenv("API_PROVIDER", "openai")

        # Set default model based on provider if not specified
        if model_name is None:
            model_name = os.getenv("DEFAULT_MODEL")
            if model_name is None:
                # Default models by provider
                model_name = "gpt-4o-mini" if self.api_provider == "openai" else "claude-sonnet-4-20250514"

        self.model_name = model_name
        self.temperature = temperature

        # Resolve prompt template path
        if prompt_template_path is None:
            self.prompt_template_path = str(_PEDAGOGY_ENGINE_ROOT / "prompts" / "pedagogical_intent.txt")
        elif not Path(prompt_template_path).is_absolute():
            self.prompt_template_path = str(_PEDAGOGY_ENGINE_ROOT / prompt_template_path)
        else:
            self.prompt_template_path = prompt_template_path

        # Initialize API client based on provider
        if self.api_provider == "openai":
            self._init_openai()
        elif self.api_provider == "anthropic":
            self._init_anthropic()
        else:
            raise ValueError(
                f"Unknown API provider: {self.api_provider}. "
                "Must be 'openai' or 'anthropic'"
            )

        # Load prompt template
        self.prompt_template = self._load_prompt_template()

    def _init_openai(self):
        """Initialize OpenAI client."""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "OpenAI package not installed. Run: pip install openai"
            )

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY not found in environment. "
                "Add it to your .env file."
            )

        self.client = OpenAI(api_key=api_key)
        print(f"Initialized OpenAI client with model: {self.model_name}")

    def _init_anthropic(self):
        """Initialize Anthropic client."""
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "Anthropic package not installed. Run: pip install anthropic"
            )

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found in environment. "
                "Add it to your .env file."
            )

        self.client = anthropic.Anthropic(api_key=api_key)
        print(f"Initialized Anthropic client with model: {self.model_name}")

    def _load_prompt_template(self) -> str:
        """Load prompt template from file."""
        template_file = Path(self.prompt_template_path)

        if not template_file.exists():
            raise FileNotFoundError(f"Prompt template not found: {template_file}")

        with open(template_file, 'r') as f:
            template = f.read()

        return template

    def _build_prompt(self, topic: str) -> str:
        """Build the full prompt."""
        return self.prompt_template.replace("{TOPIC}", topic)

    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API."""
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{
                "role": "user",
                "content": prompt
            }],
            temperature=self.temperature,
            max_tokens=4096,
            response_format={"type": "json_object"} if "gpt-" in self.model_name else None
        )

        return response.choices[0].message.content

    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic API."""
        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=4096,
            temperature=self.temperature,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        return response.content[0].text

    def _call_api(self, prompt: str) -> str:
        """Call the appropriate API based on provider."""
        if self.api_provider == "openai":
            return self._call_openai(prompt)
        elif self.api_provider == "anthropic":
            return self._call_anthropic(prompt)
        else:
            raise ValueError(f"Unknown API provider: {self.api_provider}")

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling markdown code blocks."""
        json_text = response_text

        # Handle markdown code blocks
        if "```json" in response_text:
            json_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_text = response_text.split("```")[1].split("```")[0].strip()

        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON from response: {e}")
            print(f"Response: {response_text[:500]}...")
            raise

    def generate(
        self,
        topic: str,
        domain: Optional[str] = None,
        difficulty_level: Optional[int] = None
    ) -> PedagogicalIntentWithMetadata:
        """
        Generate pedagogical intent for a topic.

        Args:
            topic: The topic to generate pedagogy for
            domain: Optional domain hint (e.g., 'machine_learning')
            difficulty_level: Optional difficulty hint (1-5)

        Returns:
            PedagogicalIntentWithMetadata with dynamic sections
        """
        print(f"\nGenerating pedagogical intent for: {topic}")
        print(f"Provider: {self.api_provider}, Model: {self.model_name}, Temperature: {self.temperature}")

        # Build and call
        prompt = self._build_prompt(topic)
        response_text = self._call_api(prompt)

        # Parse response
        intent_data = self._parse_response(response_text)

        # Create PedagogicalIntent (validates schema)
        intent = PedagogicalIntent(**intent_data)

        # Create metadata
        metadata = GenerationMetadata(
            model_name=self.model_name,
            temperature=self.temperature,
            generation_timestamp=datetime.now().isoformat()
        )

        # Bundle together
        result = PedagogicalIntentWithMetadata(
            intent=intent,
            metadata=metadata,
            quality_scores=None,
            needs_review=True
        )

        # Summary
        visual_count = len(intent.get_visual_sections())
        print(f"✓ Generated pedagogical intent for: {intent.topic}")
        print(f"  - {len(intent.sections)} sections")
        print(f"  - {visual_count} sections with visual opportunities")

        return result

    def generate_batch(
        self,
        topics: List[str],
        output_dir: str = "output/generated"
    ) -> List[PedagogicalIntentWithMetadata]:
        """Generate pedagogical intent for multiple topics."""
        results = []
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for i, topic in enumerate(topics, 1):
            print(f"\n{'='*60}")
            print(f"Generating {i}/{len(topics)}")
            print(f"{'='*60}")

            try:
                result = self.generate(topic)
                results.append(result)

                # Save individual result
                filename = f"{topic.lower().replace(' ', '_')}.json"
                filepath = output_path / filename

                with open(filepath, 'w') as f:
                    json.dump(result.model_dump(), f, indent=2, default=str)

                print(f"✓ Saved to: {filepath}")

            except Exception as e:
                print(f"✗ Failed to generate for '{topic}': {e}")
                continue

        return results


def main():
    """CLI for generating pedagogical intent."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate pedagogical intent for topics"
    )
    parser.add_argument(
        '--topic',
        type=str,
        help="Single topic to generate pedagogy for"
    )
    parser.add_argument(
        '--topics',
        type=str,
        nargs='+',
        help="Multiple topics to generate pedagogy for"
    )
    parser.add_argument(
        '--topics-file',
        type=str,
        help="File containing topics (one per line)"
    )
    parser.add_argument(
        '--output',
        type=str,
        default="output/generated",
        help="Output directory for generated files"
    )
    parser.add_argument(
        '--provider',
        type=str,
        choices=['openai', 'anthropic'],
        help="API provider to use (overrides .env)"
    )
    parser.add_argument(
        '--model',
        type=str,
        help="Model to use for generation (overrides .env)"
    )
    parser.add_argument(
        '--temperature',
        type=float,
        default=0.7,
        help="Temperature for generation"
    )

    args = parser.parse_args()

    # Collect topics
    topics = []
    if args.topic:
        topics = [args.topic]
    elif args.topics:
        topics = args.topics
    elif args.topics_file:
        with open(args.topics_file, 'r') as f:
            topics = [line.strip() for line in f if line.strip()]
    else:
        print("Error: Must provide --topic, --topics, or --topics-file")
        return

    # Create generator
    generator = PedagogicalIntentGenerator(
        model_name=args.model,
        api_provider=args.provider,
        temperature=args.temperature
    )

    # Generate
    if len(topics) == 1:
        result = generator.generate(topics[0])

        # Print result
        print(f"\n{'='*60}")
        print("Generated Pedagogical Intent")
        print(f"{'='*60}\n")
        print(json.dumps(result.intent.model_dump(), indent=2))

        # Save
        output_path = Path(args.output)
        output_path.mkdir(parents=True, exist_ok=True)
        filename = f"{topics[0].lower().replace(' ', '_')}.json"
        filepath = output_path / filename

        with open(filepath, 'w') as f:
            json.dump(result.model_dump(), f, indent=2, default=str)

        print(f"\n✓ Saved to: {filepath}")

    else:
        results = generator.generate_batch(topics, args.output)
        print(f"\n{'='*60}")
        print(f"Batch Generation Complete")
        print(f"{'='*60}")
        print(f"Successfully generated: {len(results)}/{len(topics)}")


if __name__ == "__main__":
    main()
