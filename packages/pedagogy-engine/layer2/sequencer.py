"""
Beat Sequencer

Handles ordering of pedagogical beats for optimal learning flow.
Supports both rule-based and LLM-enhanced sequencing.
"""

from typing import List, Optional
import os
from dotenv import load_dotenv
from layer2.schema import Beat

# Load environment variables
load_dotenv()


class BeatSequencer:
    """
    Sequences beats for pedagogical coherence.

    Supports two modes:
    1. Rule-based: Deterministic ordering based on pedagogical principles
    2. LLM-enhanced: Use language model to refine ordering
    """

    # Pedagogical ordering rules: earlier purposes should come before later ones
    PURPOSE_ORDERING = {
        'set_context': 0,
        'establish_baseline': 1,
        'place_initial_state': 2,
        'introduce_misconception': 3,
        'ground_in_example': 4,
        'show_mechanism': 5,
        'show_update_rule': 5,  # Alias for show_mechanism
        'iterate_process': 6,
        'demonstrate_convergence': 7,
        'manipulate_parameters': 8,
        'contrast_approaches': 9,
        'highlight_difference': 9,
        'contrast_failure_mode': 10,
        'reveal_failure_mode': 10,  # Alias
        'check_understanding': 11,
        'show_edge_case': 12,
    }

    def __init__(
        self,
        use_llm: bool = False,
        model: Optional[str] = None,
        api_provider: Optional[str] = None
    ):
        """
        Initialize the beat sequencer.

        Args:
            use_llm: Whether to use LLM for sequencing (experimental)
            model: Model name for LLM sequencing (defaults based on provider)
            api_provider: 'openai' or 'anthropic' (defaults to openai)
        """
        self.use_llm = use_llm
        self.api_provider = api_provider or os.getenv("API_PROVIDER", "openai")

        # Set default model based on provider
        if model is None:
            self.model = "gpt-4o-mini" if self.api_provider == "openai" else "claude-haiku-4"
        else:
            self.model = model

        # Get API key based on provider
        if self.use_llm:
            if self.api_provider == "openai":
                self.api_key = os.getenv("OPENAI_API_KEY")
                if not self.api_key:
                    raise ValueError("LLM sequencing with OpenAI requires OPENAI_API_KEY environment variable")
            elif self.api_provider == "anthropic":
                self.api_key = os.getenv("ANTHROPIC_API_KEY")
                if not self.api_key:
                    raise ValueError("LLM sequencing with Anthropic requires ANTHROPIC_API_KEY environment variable")
            else:
                raise ValueError(f"Unknown API provider: {self.api_provider}")

    def sequence_beats(self, beats: List[Beat], pattern: str) -> List[Beat]:
        """
        Order beats for pedagogical flow.

        Args:
            beats: List of unordered beats
            pattern: Pedagogical pattern name (for context)

        Returns:
            List of beats in pedagogical order
        """
        if self.use_llm:
            return self._llm_sequencing(beats, pattern)
        else:
            return self._rule_based_sequencing(beats)

    def _rule_based_sequencing(self, beats: List[Beat]) -> List[Beat]:
        """
        Apply rule-based ordering using pedagogical principles.

        Rules:
        1. Context-setting beats come first
        2. Mechanism explanation before iteration
        3. Failure modes and edge cases come last
        4. Understanding checks at the very end
        """
        def get_order_key(beat: Beat) -> int:
            """Get sorting key for a beat based on its purpose."""
            # Try exact match first
            if beat.purpose in self.PURPOSE_ORDERING:
                return self.PURPOSE_ORDERING[beat.purpose]

            # Try partial match (purpose contains a keyword)
            for known_purpose, order in self.PURPOSE_ORDERING.items():
                if known_purpose in beat.purpose.lower():
                    return order

            # Unknown purposes go in the middle (after mechanisms, before contrasts)
            return 7

        # Sort beats by pedagogical order
        sorted_beats = sorted(beats, key=get_order_key)

        return sorted_beats

    def _llm_sequencing(self, beats: List[Beat], pattern: str) -> List[Beat]:
        """
        Use LLM to determine optimal beat ordering.

        This is an experimental enhancement that uses a small LLM to refine
        the ordering based on pedagogical best practices.
        """
        if self.api_provider == "openai":
            return self._openai_sequencing(beats, pattern)
        elif self.api_provider == "anthropic":
            return self._anthropic_sequencing(beats, pattern)
        else:
            # Fallback to rule-based
            return self._rule_based_sequencing(beats)

    def _openai_sequencing(self, beats: List[Beat], pattern: str) -> List[Beat]:
        """Use OpenAI to sequence beats."""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "LLM sequencing with OpenAI requires openai library. "
                "Install with: pip install openai"
            )

        client = OpenAI(api_key=self.api_key)

        # Create a compact representation of beats for the prompt
        beats_summary = "\n".join([
            f"{i+1}. {beat.purpose}: {beat.intent}"
            for i, beat in enumerate(beats)
        ])

        prompt = f"""You are a pedagogical expert. Given these teaching beats for a {pattern} lesson, determine the optimal order for learning.

Current beats:
{beats_summary}

Pedagogical principles:
- Context before details
- Concrete before abstract
- Mechanism before iteration
- Success before failure modes
- Understanding checks last

Return ONLY a comma-separated list of beat numbers in optimal order (e.g., "1,3,2,4,5")."""

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.3  # Low temperature for consistent ordering
            )

            # Parse response
            response_text = response.choices[0].message.content.strip()

            # Extract numbers from response
            import re
            numbers = re.findall(r'\d+', response_text)
            order = [int(n) - 1 for n in numbers]  # Convert to 0-indexed

            # Validate ordering
            if len(order) != len(beats) or set(order) != set(range(len(beats))):
                # Fallback to rule-based if LLM output is invalid
                print("Warning: LLM sequencing produced invalid order, using rule-based fallback")
                return self._rule_based_sequencing(beats)

            # Reorder beats according to LLM suggestion
            reordered_beats = [beats[i] for i in order]
            return reordered_beats

        except Exception as e:
            # Fallback to rule-based on any error
            print(f"Warning: LLM sequencing failed ({e}), using rule-based fallback")
            return self._rule_based_sequencing(beats)

    def _anthropic_sequencing(self, beats: List[Beat], pattern: str) -> List[Beat]:
        """Use Anthropic to sequence beats."""
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "LLM sequencing with Anthropic requires anthropic library. "
                "Install with: pip install anthropic"
            )

        client = anthropic.Anthropic(api_key=self.api_key)

        # Create a compact representation of beats for the prompt
        beats_summary = "\n".join([
            f"{i+1}. {beat.purpose}: {beat.intent}"
            for i, beat in enumerate(beats)
        ])

        prompt = f"""You are a pedagogical expert. Given these teaching beats for a {pattern} lesson, determine the optimal order for learning.

Current beats:
{beats_summary}

Pedagogical principles:
- Context before details
- Concrete before abstract
- Mechanism before iteration
- Success before failure modes
- Understanding checks last

Return ONLY a comma-separated list of beat numbers in optimal order (e.g., "1,3,2,4,5")."""

        try:
            # Call Claude Haiku for fast, cheap sequencing
            message = client.messages.create(
                model=self.model,
                max_tokens=100,
                temperature=0.3,  # Low temperature for consistent ordering
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Parse response
            response_text = message.content[0].text.strip()

            # Extract numbers from response
            import re
            numbers = re.findall(r'\d+', response_text)
            order = [int(n) - 1 for n in numbers]  # Convert to 0-indexed

            # Validate ordering
            if len(order) != len(beats) or set(order) != set(range(len(beats))):
                # Fallback to rule-based if LLM output is invalid
                print("Warning: LLM sequencing produced invalid order, using rule-based fallback")
                return self._rule_based_sequencing(beats)

            # Reorder beats according to LLM suggestion
            reordered_beats = [beats[i] for i in order]
            return reordered_beats

        except Exception as e:
            # Fallback to rule-based on any error
            print(f"Warning: LLM sequencing failed ({e}), using rule-based fallback")
            return self._rule_based_sequencing(beats)

    def validate_sequence(self, beats: List[Beat]) -> bool:
        """
        Validate that beat sequence follows pedagogical principles.

        Checks:
        1. First beat is context-setting
        2. Understanding checks (if any) come last
        3. No major ordering violations

        Returns:
            True if sequence is valid, False otherwise
        """
        if not beats:
            return False

        # Check that first beat is context-setting
        first_purpose = beats[0].purpose.lower()
        if not any(kw in first_purpose for kw in ['context', 'baseline', 'introduce']):
            return False

        # Check that understanding checks come at the end
        check_purposes = ['check_understanding', 'understanding']
        for i, beat in enumerate(beats[:-1]):  # All except last
            if any(kw in beat.purpose.lower() for kw in check_purposes):
                # Understanding check found before the end
                return False

        # Sequence is valid
        return True
