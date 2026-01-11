"""
Pedagogical Pattern Templates

Defines pattern classes that map PedagogicalIntent to sequences of beats.
Each pattern represents a different pedagogical approach to structuring content.
"""

from abc import ABC, abstractmethod
from typing import List
import re

from layer1.schema import PedagogicalIntent
from layer2.schema import Beat


class PedagogicalPattern(ABC):
    """
    Abstract base class for pedagogical patterns.

    Each pattern defines how to generate beats from a pedagogical intent.
    """

    @abstractmethod
    def generate_beats(self, intent: PedagogicalIntent) -> List[Beat]:
        """
        Generate an ordered sequence of beats from pedagogical intent.

        Args:
            intent: The pedagogical intent from Layer 1

        Returns:
            List of Beat objects in pedagogical order
        """
        pass

    def _extract_keywords(self, text: str, keywords: List[str]) -> str:
        """
        Extract sentences containing specific keywords from text.

        Args:
            text: Source text to search
            keywords: List of keywords to look for

        Returns:
            First sentence containing any keyword, or original text if none found
        """
        sentences = text.split('.')
        for sentence in sentences:
            if any(keyword.lower() in sentence.lower() for keyword in keywords):
                return sentence.strip() + '.'
        return text[:100] + '...' if len(text) > 100 else text


class IterativeProcessPattern(PedagogicalPattern):
    """
    Pattern for algorithms with repeated updates and convergence.

    Examples: gradient descent, EM algorithm, Newton's method, iterative optimization

    Typical beat sequence:
    1. set_context - Show the landscape/problem space
    2. place_initial_state - Indicate starting point
    3. show_update_rule - Demonstrate the mechanism
    4. iterate_process - Show repeated application
    5. demonstrate_convergence - Show stable state (optional)
    6. contrast_failure_mode - Show what goes wrong
    """

    def generate_beats(self, intent: PedagogicalIntent) -> List[Beat]:
        """
        Generate beats for an iterative process visualization.

        Maps PedagogicalIntent fields to specific beats:
        - target_mental_model → context, mechanism
        - concrete_anchor → initial state
        - common_misconception → failure mode
        """
        beats = []

        # 1. Set context from mental model
        context_intent = self._extract_context(intent.target_mental_model, intent.topic)
        beats.append(Beat(
            purpose="set_context",
            intent=context_intent
        ))

        # 2. Place initial state from concrete anchor
        initial_state_intent = self._extract_initial_state(intent.concrete_anchor)
        beats.append(Beat(
            purpose="place_initial_state",
            intent=initial_state_intent
        ))

        # 3. Show update rule/mechanism
        mechanism_intent = self._extract_mechanism(intent.target_mental_model, intent.topic)
        beats.append(Beat(
            purpose="show_update_rule",
            intent=mechanism_intent
        ))

        # 4. Iterate the process
        iteration_intent = self._generate_iteration_intent(intent.topic)
        beats.append(Beat(
            purpose="iterate_process",
            intent=iteration_intent
        ))

        # 5. Demonstrate convergence (optional but recommended for iterative processes)
        convergence_intent = self._generate_convergence_intent(intent.target_mental_model)
        if convergence_intent:
            beats.append(Beat(
                purpose="demonstrate_convergence",
                intent=convergence_intent
            ))

        # 6. Contrast with failure mode (from misconception)
        if intent.common_misconception:
            failure_intent = self._extract_failure_mode(intent.common_misconception)
            beats.append(Beat(
                purpose="contrast_failure_mode",
                intent=failure_intent
            ))

        return beats

    def _extract_context(self, mental_model: str, topic: str) -> str:
        """
        Extract the problem landscape/space from mental model.

        For gradient descent: "the loss landscape being optimized"
        For EM algorithm: "the latent variable space being explored"
        """
        # Look for keywords related to spaces, landscapes, problems
        context_keywords = [
            'landscape', 'surface', 'space', 'terrain', 'problem',
            'error', 'loss', 'objective', 'function'
        ]

        # Try to find a sentence with these keywords
        context_text = self._extract_keywords(mental_model, context_keywords)

        # If we found a specific context, format it
        if any(kw in context_text.lower() for kw in context_keywords):
            # Extract the key noun phrase
            for keyword in ['landscape', 'surface', 'space', 'terrain']:
                if keyword in context_text.lower():
                    return f"Show the {keyword} being optimized."

        # Fallback: generic context
        return f"Show the problem space for {topic}."

    def _extract_initial_state(self, concrete_anchor: str) -> str:
        """
        Extract the starting point/initial state from concrete anchor.

        For gradient descent: "starting parameter value"
        For EM: "initial cluster assignments"
        """
        # Look for keywords about starting, initial, random
        initial_keywords = ['start', 'initial', 'random', 'begin']

        initial_text = self._extract_keywords(concrete_anchor, initial_keywords)

        # Try to extract what is being initialized
        if 'weight' in concrete_anchor.lower() or 'parameter' in concrete_anchor.lower():
            return "Indicate the starting parameter value."
        elif 'point' in concrete_anchor.lower():
            return "Indicate the starting point."
        else:
            return "Show the initial state of the system."

    def _extract_mechanism(self, mental_model: str, topic: str) -> str:
        """
        Extract the update rule/mechanism from mental model.

        For gradient descent: "how the gradient determines direction"
        For EM: "how expectations update beliefs"
        """
        # Look for action keywords that describe the mechanism
        mechanism_keywords = [
            'step', 'update', 'adjust', 'change', 'move',
            'gradient', 'direction', 'slope', 'compute'
        ]

        mechanism_text = self._extract_keywords(mental_model, mechanism_keywords)

        # Try to extract the key mechanism
        if 'gradient' in mental_model.lower():
            return "Demonstrate how the gradient determines direction."
        elif 'step' in mental_model.lower():
            return f"Show how {topic} takes steps toward the solution."
        else:
            return f"Demonstrate the update mechanism for {topic}."

    def _generate_iteration_intent(self, topic: str) -> str:
        """
        Generate intent for showing repeated application of the process.

        This is pattern-specific: iterative processes always repeat until convergence.
        """
        # Check topic for specific iteration language
        if 'descent' in topic.lower():
            return "Show repeated updates converging to a minimum."
        elif 'ascent' in topic.lower():
            return "Show repeated updates converging to a maximum."
        else:
            return "Show repeated application of the update rule."

    def _generate_convergence_intent(self, mental_model: str) -> str:
        """
        Generate intent for demonstrating convergence/stable state.

        Returns empty string if convergence is not mentioned in mental model.
        """
        # Look for convergence-related keywords
        convergence_keywords = ['converge', 'settle', 'valley', 'minimum', 'maximum', 'stable']

        if any(kw in mental_model.lower() for kw in convergence_keywords):
            if 'valley' in mental_model.lower() or 'minimum' in mental_model.lower():
                return "Show the process reaching a valley (local minimum)."
            elif 'stable' in mental_model.lower():
                return "Show the process reaching a stable state."
            else:
                return "Demonstrate convergence to a solution."

        # If no convergence mentioned, don't add this beat
        return ""

    def _extract_failure_mode(self, misconception: str) -> str:
        """
        Convert misconception to a failure mode description.

        For "always finds global minimum" → "what happens with wrong parameters"
        For "never gets stuck" → "what happens with poor initialization"
        """
        # Common failure modes for iterative processes
        if 'always' in misconception.lower() and 'global' in misconception.lower():
            return "Show what happens with too large a learning rate or poor initialization."
        elif 'never' in misconception.lower() and ('fail' in misconception.lower() or 'stuck' in misconception.lower()):
            return "Show when the algorithm gets stuck in a local minimum."
        elif 'fast' in misconception.lower() or 'quick' in misconception.lower():
            return "Show what happens with too large a step size."
        else:
            # Generic failure mode
            return "Contrast with a common failure mode."


class SpatialPartitioningPattern(PedagogicalPattern):
    """
    Pattern for spatial reasoning and boundaries (decision boundaries, regions).

    Future implementation for topics like:
    - Decision boundaries
    - Voronoi diagrams
    - Spatial clustering
    """

    def generate_beats(self, intent: PedagogicalIntent) -> List[Beat]:
        """Placeholder for future implementation."""
        raise NotImplementedError("SpatialPartitioningPattern not yet implemented")


class LocalOperationPattern(PedagogicalPattern):
    """
    Pattern for local operations and sliding windows (convolutions, filters).

    Future implementation for topics like:
    - Convolutions
    - Filters
    - Sliding window algorithms
    """

    def generate_beats(self, intent: PedagogicalIntent) -> List[Beat]:
        """Placeholder for future implementation."""
        raise NotImplementedError("LocalOperationPattern not yet implemented")


# Pattern registry for easy lookup
PATTERN_REGISTRY = {
    'iterative_process': IterativeProcessPattern(),
    'spatial_partitioning': SpatialPartitioningPattern(),
    'local_operation': LocalOperationPattern(),
}


def get_pattern(pattern_name: str) -> PedagogicalPattern:
    """
    Get a pattern instance by name.

    Args:
        pattern_name: Name of the pattern (e.g., 'iterative_process')

    Returns:
        PedagogicalPattern instance

    Raises:
        KeyError: If pattern name is not recognized
    """
    if pattern_name not in PATTERN_REGISTRY:
        raise KeyError(f"Unknown pattern: {pattern_name}. Available: {list(PATTERN_REGISTRY.keys())}")
    return PATTERN_REGISTRY[pattern_name]
