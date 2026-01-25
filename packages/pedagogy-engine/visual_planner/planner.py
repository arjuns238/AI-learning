"""
Visual Planner: Identifies concepts that benefit from animation

Takes pedagogical intent from Layer 1 and identifies 1-2 visual opportunities
that would enhance understanding. These opportunities are then passed to
Layer 3 for prompt generation and Layer 4 for video creation.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from layer1.schema import PedagogicalIntent, PedagogicalIntentWithMetadata
from visual_planner.schema import (
    VisualOpportunity,
    VisualPlan,
    VisualPlannerMetadata,
    VisualPlanWithMetadata
)

load_dotenv()

# Resolve paths relative to package root
_VISUAL_PLANNER_DIR = Path(__file__).parent
_PEDAGOGY_ENGINE_ROOT = _VISUAL_PLANNER_DIR.parent


class VisualPlanner:
    """
    Identifies visual opportunities from pedagogical content.

    Analyzes Layer 1 output to find 1-2 concepts that would most benefit
    from short animated explanations.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        api_provider: Optional[str] = None,
        max_opportunities: int = 2,
        prompt_template_path: Optional[str] = None
    ):
        self.api_provider = api_provider or os.getenv("API_PROVIDER", "openai")

        if model_name is None:
            model_name = os.getenv("DEFAULT_MODEL")
            if model_name is None:
                model_name = "gpt-4o-mini" if self.api_provider == "openai" else "claude-sonnet-4-20250514"

        self.model_name = model_name
        self.temperature = temperature
        self.max_opportunities = max_opportunities

        # Load prompt template
        if prompt_template_path is None:
            self.prompt_template_path = _PEDAGOGY_ENGINE_ROOT / "prompts" / "visual_planner.txt"
        else:
            self.prompt_template_path = Path(prompt_template_path)

        self.prompt_template = self._load_prompt_template()

        # Initialize API client
        if self.api_provider == "openai":
            self._init_openai()
        elif self.api_provider == "anthropic":
            self._init_anthropic()
        else:
            raise ValueError(f"Unknown API provider: {self.api_provider}")

    def _init_openai(self):
        """Initialize OpenAI client."""
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found")
        self.client = OpenAI(api_key=api_key)

    def _init_anthropic(self):
        """Initialize Anthropic client."""
        import anthropic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found")
        self.client = anthropic.Anthropic(api_key=api_key)

    def _load_prompt_template(self) -> str:
        """Load prompt template from file."""
        if not self.prompt_template_path.exists():
            raise FileNotFoundError(f"Prompt template not found: {self.prompt_template_path}")

        with open(self.prompt_template_path, 'r') as f:
            return f.read()

    def _build_prompt(self, intent: PedagogicalIntent) -> str:
        """Build the prompt by filling in the template."""
        prompt = self.prompt_template
        prompt = prompt.replace("{TOPIC}", intent.topic)
        prompt = prompt.replace("{CORE_QUESTION}", intent.core_question)
        prompt = prompt.replace("{TARGET_MENTAL_MODEL}", intent.target_mental_model)
        prompt = prompt.replace("{COMMON_MISCONCEPTION}", intent.common_misconception)
        prompt = prompt.replace("{DISAMBIGUATING_CONTRAST}", intent.disambiguating_contrast)
        prompt = prompt.replace("{CONCRETE_ANCHOR}", intent.concrete_anchor)
        prompt = prompt.replace("{SPATIAL_METAPHOR}", intent.spatial_metaphor or "Not specified")
        return prompt

    def _call_api(self, prompt: str) -> str:
        """Call the LLM API."""
        if self.api_provider == "openai":
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=2048
            )
            return response.choices[0].message.content
        else:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=2048,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text

    def identify_opportunities(
        self,
        pedagogy: PedagogicalIntentWithMetadata
    ) -> VisualPlanWithMetadata:
        """
        Identify visual opportunities from pedagogical intent.

        Args:
            pedagogy: The pedagogical intent from Layer 1

        Returns:
            VisualPlanWithMetadata with 0-2 visual opportunities
        """
        intent = pedagogy.intent

        print(f"\nVisual Planner: Analyzing '{intent.topic}' for visual opportunities...")

        # Build and send prompt
        prompt = self._build_prompt(intent)
        response_text = self._call_api(prompt)

        # Parse JSON from response
        json_text = response_text
        if "```json" in response_text:
            json_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_text = response_text.split("```")[1].split("```")[0].strip()

        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as e:
            print(f"Failed to parse Visual Planner response: {e}")
            print(f"Response: {response_text[:500]}...")
            # Return empty plan on failure
            data = {"opportunities": [], "reasoning": "Failed to parse LLM response"}

        # Convert to VisualOpportunity objects
        opportunities = []
        for opp_data in data.get("opportunities", [])[:self.max_opportunities]:
            try:
                opp = VisualOpportunity(
                    id=opp_data.get("id", f"v{len(opportunities)+1}"),
                    concept=opp_data["concept"],
                    description=opp_data["description"],
                    placement=opp_data.get("placement", "core_mechanism"),
                    pedagogical_purpose=opp_data.get("pedagogical_purpose", "Enhances understanding"),
                    duration_hint=opp_data.get("duration_hint", 15)
                )
                opportunities.append(opp)
            except Exception as e:
                print(f"Failed to parse opportunity: {e}")
                continue

        # Build result
        plan = VisualPlan(
            topic=intent.topic,
            opportunities=opportunities,
            reasoning=data.get("reasoning")
        )

        metadata = VisualPlannerMetadata(
            model_name=self.model_name,
            generation_timestamp=datetime.now().isoformat(),
            num_opportunities_requested=self.max_opportunities
        )

        result = VisualPlanWithMetadata(plan=plan, metadata=metadata)

        print(f"✓ Identified {len(opportunities)} visual opportunity(ies)")
        for opp in opportunities:
            print(f"  - {opp.concept} ({opp.placement})")

        return result


def main():
    """CLI for testing the Visual Planner."""
    import argparse
    from layer1.generator import PedagogicalIntentGenerator

    parser = argparse.ArgumentParser(description="Test Visual Planner")
    parser.add_argument("--topic", type=str, required=True, help="Topic to analyze")
    parser.add_argument("--provider", type=str, choices=["openai", "anthropic"], help="API provider")

    args = parser.parse_args()

    # Generate pedagogical intent first
    print("Step 1: Generating pedagogical intent...")
    layer1 = PedagogicalIntentGenerator(api_provider=args.provider)
    pedagogy = layer1.generate(args.topic)

    # Run Visual Planner
    print("\nStep 2: Identifying visual opportunities...")
    planner = VisualPlanner(api_provider=args.provider)
    result = planner.identify(pedagogy)

    # Print results
    print(f"\n{'='*60}")
    print("Visual Plan")
    print(f"{'='*60}\n")
    print(json.dumps(result.plan.model_dump(), indent=2))


if __name__ == "__main__":
    main()
