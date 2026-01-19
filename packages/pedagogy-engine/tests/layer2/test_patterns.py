"""
Tests for Layer 2 Patterns (IterativeProcessPattern, etc.)
"""

import pytest
import json
from pathlib import Path

from layer1.schema import PedagogicalIntent
from layer2.patterns import (
    IterativeProcessPattern,
    get_pattern,
    PATTERN_REGISTRY
)
from layer2.schema import Beat


class TestIterativeProcessPattern:
    """Tests for IterativeProcessPattern."""

    @pytest.fixture
    def gradient_descent_intent(self):
        """Load gradient descent intent fixture."""
        fixture_path = Path(__file__).parent / "fixtures" / "gradient_descent_intent.json"
        with open(fixture_path) as f:
            data = json.load(f)
        return PedagogicalIntent(**data)

    def test_generate_beats(self, gradient_descent_intent):
        """Test that IterativeProcessPattern generates valid beats."""
        pattern = IterativeProcessPattern()
        beats = pattern.generate_beats(gradient_descent_intent)

        # Should generate between 3-12 beats
        assert 3 <= len(beats) <= 12

        # All beats should be Beat instances
        for beat in beats:
            assert isinstance(beat, Beat)
            assert len(beat.purpose) >= 3
            assert len(beat.intent) >= 10

    def test_beat_purposes(self, gradient_descent_intent):
        """Test that generated beats have expected purposes."""
        pattern = IterativeProcessPattern()
        beats = pattern.generate_beats(gradient_descent_intent)

        purposes = [beat.purpose for beat in beats]

        # Should have context-setting beat
        assert any('context' in purpose for purpose in purposes)

        # Should have initial state beat
        assert any('initial' in purpose or 'place' in purpose for purpose in purposes)

        # Should have mechanism/update rule beat
        assert any('update' in purpose or 'mechanism' in purpose for purpose in purposes)

        # Should have iteration beat
        assert any('iterate' in purpose for purpose in purposes)

    def test_beat_sequence_order(self, gradient_descent_intent):
        """Test that beats follow logical pedagogical order."""
        pattern = IterativeProcessPattern()
        beats = pattern.generate_beats(gradient_descent_intent)

        purposes = [beat.purpose for beat in beats]

        # Context should come before mechanism
        context_idx = next((i for i, p in enumerate(purposes) if 'context' in p), -1)
        mechanism_idx = next((i for i, p in enumerate(purposes) if 'update' in p or 'mechanism' in p), -1)

        if context_idx >= 0 and mechanism_idx >= 0:
            assert context_idx < mechanism_idx

        # Mechanism should come before iteration
        iterate_idx = next((i for i, p in enumerate(purposes) if 'iterate' in p), -1)

        if mechanism_idx >= 0 and iterate_idx >= 0:
            assert mechanism_idx < iterate_idx

    def test_handles_minimal_misconception(self):
        """Test that pattern handles minimal but valid misconception field."""
        intent = PedagogicalIntent(
            topic="Test Topic",
            core_question="How does this work exactly?",
            target_mental_model="Like a ball rolling down a hill with friction and gravity.",
            common_misconception="Misconceptions are uncommon in this case.",  # Minimal but valid
            disambiguating_contrast="This approach vs that alternative",
            concrete_anchor="Example with specific numbers and calculations",
            check_for_understanding="Can you explain why this happens?"
        )

        pattern = IterativeProcessPattern()
        beats = pattern.generate_beats(intent)

        # Should still generate beats
        assert len(beats) >= 3

        # With a minimal misconception, should still include failure mode
        purposes = [beat.purpose for beat in beats]
        assert any('failure' in purpose or 'contrast' in purpose for purpose in purposes)


class TestPatternRegistry:
    """Tests for pattern registry and lookup."""

    def test_get_pattern_iterative(self):
        """Test getting iterative_process pattern."""
        pattern = get_pattern("iterative_process")
        assert isinstance(pattern, IterativeProcessPattern)

    def test_get_pattern_invalid(self):
        """Test that invalid pattern name raises error."""
        with pytest.raises(KeyError):
            get_pattern("invalid_pattern_name")

    def test_pattern_registry_contents(self):
        """Test that pattern registry has expected entries."""
        assert "iterative_process" in PATTERN_REGISTRY
        assert "spatial_partitioning" in PATTERN_REGISTRY
        assert "local_operation" in PATTERN_REGISTRY


class TestPatternExtraction:
    """Tests for text extraction methods."""

    def test_extract_context(self):
        """Test context extraction from mental model."""
        pattern = IterativeProcessPattern()

        mental_model = "Gradient descent is like navigating down a mountainside in fog: you can't see the whole landscape, but you can feel which direction slopes downward."
        topic = "Gradient Descent"

        context = pattern._extract_context(mental_model, topic)

        # Should mention landscape or surface
        assert len(context) > 10
        assert any(keyword in context.lower() for keyword in ['landscape', 'surface', 'space', 'problem'])

    def test_extract_initial_state(self):
        """Test initial state extraction from concrete anchor."""
        pattern = IterativeProcessPattern()

        concrete_anchor = "Start with random weights. The error surface is a bowl-shaped landscape."

        initial_state = pattern._extract_initial_state(concrete_anchor)

        # Should mention starting or initial
        assert len(initial_state) > 10
        assert any(keyword in initial_state.lower() for keyword in ['start', 'initial', 'parameter', 'point'])

    def test_extract_failure_mode(self):
        """Test failure mode extraction from misconception."""
        pattern = IterativeProcessPattern()

        misconception = "Gradient descent always finds the single best solution (global minimum)"

        failure_mode = pattern._extract_failure_mode(misconception)

        # Should describe what goes wrong
        assert len(failure_mode) > 10
