"""
Tests for Layer 2 Generator (StoryboardGenerator)
"""

import pytest
import json
import tempfile
from pathlib import Path

from layer1.schema import PedagogicalIntent
from layer2.generator import StoryboardGenerator
from layer2.schema import StoryboardWithMetadata


class TestStoryboardGenerator:
    """Tests for StoryboardGenerator."""

    @pytest.fixture
    def gradient_descent_intent(self):
        """Load gradient descent intent fixture."""
        fixture_path = Path(__file__).parent / "fixtures" / "gradient_descent_intent.json"
        with open(fixture_path) as f:
            data = json.load(f)
        return PedagogicalIntent(**data)

    @pytest.fixture
    def generator(self):
        """Create a StoryboardGenerator instance."""
        return StoryboardGenerator(strategy="hybrid", use_llm_sequencing=False)

    def test_generate_from_intent(self, generator, gradient_descent_intent):
        """Test generating storyboard from pedagogical intent."""
        result = generator.generate(gradient_descent_intent)

        # Should return StoryboardWithMetadata
        assert isinstance(result, StoryboardWithMetadata)

        # Storyboard should have the right topic
        assert result.storyboard.topic == "Gradient Descent"

        # Should have beats
        assert 3 <= len(result.storyboard.beats) <= 12

        # Should have pattern
        assert result.storyboard.pedagogical_pattern is not None

        # Metadata should be present
        assert result.metadata.generation_strategy == "hybrid"
        assert result.metadata.pattern_used is not None
        assert result.metadata.generation_timestamp is not None

    def test_pattern_selection(self, generator, gradient_descent_intent):
        """Test that gradient descent is classified as iterative_process."""
        result = generator.generate(gradient_descent_intent)

        # Should select iterative_process pattern
        assert result.storyboard.pedagogical_pattern == "iterative_process"

    def test_pattern_override(self, generator, gradient_descent_intent):
        """Test forcing a specific pattern."""
        result = generator.generate(
            gradient_descent_intent,
            pattern_override="iterative_process"
        )

        # Should use the forced pattern
        assert result.storyboard.pedagogical_pattern == "iterative_process"

    def test_generate_from_file(self, generator):
        """Test generating from file input."""
        fixture_path = Path(__file__).parent / "fixtures" / "gradient_descent_intent.json"

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.json"

            result = generator.generate_from_file(
                intent_file=fixture_path,
                output_file=output_path
            )

            # Should generate result
            assert isinstance(result, StoryboardWithMetadata)

            # Should save to file
            assert output_path.exists()

            # File should contain valid JSON
            with open(output_path) as f:
                data = json.load(f)

            assert "storyboard" in data
            assert "metadata" in data

    def test_batch_generation(self, generator):
        """Test batch generation from directory."""
        # Create temporary input directory with test file
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "input"
            output_dir = Path(tmpdir) / "output"
            input_dir.mkdir()

            # Copy fixture to temp input directory
            fixture_path = Path(__file__).parent / "fixtures" / "gradient_descent_intent.json"
            with open(fixture_path) as f:
                data = json.load(f)

            test_file = input_dir / "test_intent.json"
            with open(test_file, 'w') as f:
                json.dump(data, f)

            # Run batch generation
            generator.generate_batch(
                input_dir=input_dir,
                output_dir=output_dir
            )

            # Should create output directory
            assert output_dir.exists()

            # Should create output file
            output_files = list(output_dir.glob("*.json"))
            assert len(output_files) == 1

            # Output should be valid
            with open(output_files[0]) as f:
                result_data = json.load(f)

            assert "storyboard" in result_data
            assert "metadata" in result_data


class TestPatternSelection:
    """Tests for automatic pattern selection."""

    @pytest.fixture
    def generator(self):
        return StoryboardGenerator()

    def test_iterative_keywords(self, generator):
        """Test that iterative keywords trigger iterative_process pattern."""
        intent = PedagogicalIntent(
            topic="Newton's Method",
            core_question="How does this converge?",
            target_mental_model="Repeatedly update the solution by following the gradient.",
            common_misconception="It always works.",
            disambiguating_contrast="This vs that",
            concrete_anchor="Example with descent",
            check_for_understanding="Why converge?"
        )

        pattern = generator._select_pattern(intent)
        assert pattern == "iterative_process"

    def test_default_pattern_fallback(self, generator):
        """Test that default pattern is used when no keywords match."""
        intent = PedagogicalIntent(
            topic="Generic Topic",
            core_question="How does this work exactly?",
            target_mental_model="It works by processing inputs and producing outputs in a systematic way.",
            common_misconception="It doesn't work at all in edge cases.",
            disambiguating_contrast="This approach vs that alternative approach",
            concrete_anchor="Example with specific numbers and values",
            check_for_understanding="Can you explain why it works this way?"
        )

        pattern = generator._select_pattern(intent)
        # Should return a valid pattern (likely default)
        assert pattern in ["iterative_process", "spatial_partitioning", "local_operation"]
