"""
Integration Tests: Layer 1 → Layer 2 Pipeline

Tests the full pipeline from pedagogical intent to storyboard.
"""

import pytest
import json
from pathlib import Path

from layer1.schema import PedagogicalIntent
from layer2.generator import StoryboardGenerator
from layer2.schema import StoryboardWithMetadata


class TestLayer1ToLayer2Integration:
    """Integration tests for the full L1→L2 pipeline."""

    @pytest.fixture
    def generator(self):
        """Create a StoryboardGenerator instance."""
        return StoryboardGenerator(strategy="hybrid", use_llm_sequencing=False)

    @pytest.fixture
    def gradient_descent_intent(self):
        """Load gradient descent exemplar as PedagogicalIntent."""
        # Load from Layer 2 test fixtures
        fixture_path = Path(__file__).parent.parent / "layer2" / "fixtures" / "gradient_descent_intent.json"
        with open(fixture_path) as f:
            data = json.load(f)
        return PedagogicalIntent(**data)

    def test_gradient_descent_pipeline(self, generator, gradient_descent_intent):
        """
        Test full pipeline for gradient descent example.

        This is the golden test case from the exemplars.
        """
        # Generate storyboard from intent
        result = generator.generate(gradient_descent_intent)

        # Validate result structure
        assert isinstance(result, StoryboardWithMetadata)
        assert result.storyboard.topic == "Gradient Descent"
        assert result.storyboard.pedagogical_pattern == "iterative_process"

        # Validate beats
        beats = result.storyboard.beats
        assert 3 <= len(beats) <= 12

        # Check that key purposes are present
        purposes = [beat.purpose for beat in beats]

        assert any('context' in purpose for purpose in purposes), "Should have context-setting beat"
        assert any('initial' in purpose or 'place' in purpose for purpose in purposes), "Should have initial state beat"
        assert any('update' in purpose or 'mechanism' in purpose for purpose in purposes), "Should have update rule beat"
        assert any('iterate' in purpose for purpose in purposes), "Should have iteration beat"

        # Validate beat intents are meaningful
        for beat in beats:
            assert len(beat.intent) >= 10, f"Beat intent too short: {beat.intent}"
            assert len(beat.intent) <= 500, f"Beat intent too long: {beat.intent}"

        # Validate metadata
        assert result.metadata.generation_strategy == "hybrid"
        assert result.metadata.pattern_used == "iterative_process"
        assert result.metadata.generation_timestamp is not None

    def test_existing_layer1_output(self, generator):
        """
        Test loading existing Layer 1 output and generating storyboard.

        Uses actual generated outputs from Layer 1 if they exist.
        """
        # Look for existing Layer 1 outputs
        output_dir = Path(__file__).parent.parent.parent / "output" / "generated"

        if not output_dir.exists():
            pytest.skip("No Layer 1 outputs found")

        json_files = list(output_dir.glob("*.json"))

        if not json_files:
            pytest.skip("No Layer 1 output files found")

        # Test with the first file found
        intent_file = json_files[0]

        # Load intent
        with open(intent_file) as f:
            data = json.load(f)

        # Handle both formats (with/without metadata wrapper)
        if 'intent' in data:
            intent = PedagogicalIntent(**data['intent'])
        else:
            intent = PedagogicalIntent(**data)

        # Generate storyboard
        result = generator.generate(intent)

        # Validate
        assert isinstance(result, StoryboardWithMetadata)
        assert len(result.storyboard.beats) >= 3
        assert result.storyboard.topic == intent.topic

    def test_pedagogical_flow_validation(self, generator, gradient_descent_intent):
        """
        Test that generated storyboards follow pedagogical principles.

        Principles:
        - Context before details
        - Mechanism before iteration
        - Failure modes toward the end
        """
        result = generator.generate(gradient_descent_intent)
        beats = result.storyboard.beats
        purposes = [beat.purpose.lower() for beat in beats]

        # Find indices of key beats
        context_idx = next((i for i, p in enumerate(purposes) if 'context' in p), None)
        mechanism_idx = next((i for i, p in enumerate(purposes) if 'update' in p or 'mechanism' in p), None)
        iterate_idx = next((i for i, p in enumerate(purposes) if 'iterate' in p), None)
        failure_idx = next((i for i, p in enumerate(purposes) if 'failure' in p), None)

        # Validate ordering
        if context_idx is not None and mechanism_idx is not None:
            assert context_idx < mechanism_idx, "Context should come before mechanism"

        if mechanism_idx is not None and iterate_idx is not None:
            assert mechanism_idx < iterate_idx, "Mechanism should come before iteration"

        if failure_idx is not None:
            # Failure modes should be in the latter half
            assert failure_idx >= len(beats) // 2, "Failure modes should come toward the end"

    def test_multiple_patterns(self, generator):
        """
        Test that different topics trigger appropriate patterns.

        This ensures pattern selection works correctly.
        """
        # Iterative process topic
        iterative_intent = PedagogicalIntent(
            topic="Gradient Descent",
            core_question="How does it optimize?",
            target_mental_model="Descend down the landscape by following gradients",
            common_misconception="Always finds global optimum",
            disambiguating_contrast="Local vs global",
            concrete_anchor="House price prediction",
            check_for_understanding="Why does it converge?"
        )

        result = generator.generate(iterative_intent)
        assert result.storyboard.pedagogical_pattern == "iterative_process"

    def test_storyboard_json_serialization(self, generator, gradient_descent_intent):
        """
        Test that generated storyboards can be serialized to JSON.

        This is important for saving outputs and API responses.
        """
        result = generator.generate(gradient_descent_intent)

        # Test model_dump
        data = result.model_dump()
        assert "storyboard" in data
        assert "metadata" in data

        # Test JSON serialization
        json_str = json.dumps(data)
        assert len(json_str) > 0

        # Test deserialization
        loaded_data = json.loads(json_str)
        assert loaded_data["storyboard"]["topic"] == "Gradient Descent"
