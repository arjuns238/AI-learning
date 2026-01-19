"""
Tests for Layer 2 Schema (Beat, Storyboard, Metadata)
"""

import pytest
from pydantic import ValidationError
from datetime import datetime

from layer2.schema import Beat, Storyboard, StoryboardMetadata, StoryboardWithMetadata


class TestBeat:
    """Tests for Beat model."""

    def test_valid_beat(self):
        """Test creating a valid beat."""
        beat = Beat(
            purpose="set_context",
            intent="Show the loss landscape being optimized."
        )
        assert beat.purpose == "set_context"
        assert beat.intent == "Show the loss landscape being optimized."

    def test_beat_purpose_too_short(self):
        """Test that purpose must be at least 3 characters."""
        with pytest.raises(ValidationError):
            Beat(purpose="ab", intent="Some intent here")

    def test_beat_intent_too_short(self):
        """Test that intent must be at least 10 characters."""
        with pytest.raises(ValidationError):
            Beat(purpose="set_context", intent="Short")

    def test_beat_intent_too_long(self):
        """Test that intent must be at most 500 characters."""
        long_intent = "a" * 501
        with pytest.raises(ValidationError):
            Beat(purpose="set_context", intent=long_intent)


class TestStoryboard:
    """Tests for Storyboard model."""

    def test_valid_storyboard(self):
        """Test creating a valid storyboard."""
        beats = [
            Beat(purpose="set_context", intent="Show the problem space."),
            Beat(purpose="show_mechanism", intent="Demonstrate the algorithm."),
            Beat(purpose="iterate_process", intent="Show repeated application."),
        ]
        storyboard = Storyboard(
            topic="Test Topic",
            beats=beats,
            pedagogical_pattern="iterative_process"
        )
        assert storyboard.topic == "Test Topic"
        assert len(storyboard.beats) == 3
        assert storyboard.pedagogical_pattern == "iterative_process"

    def test_storyboard_too_few_beats(self):
        """Test that storyboard must have at least 3 beats."""
        beats = [
            Beat(purpose="set_context", intent="Show the problem space."),
            Beat(purpose="show_mechanism", intent="Demonstrate the algorithm."),
        ]
        with pytest.raises(ValidationError):
            Storyboard(topic="Test Topic", beats=beats)

    def test_storyboard_too_many_beats(self):
        """Test that storyboard should have at most 12 beats."""
        beats = [
            Beat(purpose=f"beat_{i}", intent=f"Intent for beat {i}")
            for i in range(13)
        ]
        with pytest.raises(ValidationError):
            Storyboard(topic="Test Topic", beats=beats)

    def test_storyboard_without_pattern(self):
        """Test that pedagogical_pattern is optional."""
        beats = [
            Beat(purpose="set_context", intent="Show the problem space."),
            Beat(purpose="show_mechanism", intent="Demonstrate the algorithm."),
            Beat(purpose="iterate_process", intent="Show repeated application."),
        ]
        storyboard = Storyboard(topic="Test Topic", beats=beats)
        assert storyboard.pedagogical_pattern is None


class TestStoryboardMetadata:
    """Tests for StoryboardMetadata model."""

    def test_valid_metadata(self):
        """Test creating valid metadata."""
        metadata = StoryboardMetadata(
            generation_strategy="hybrid",
            pattern_used="iterative_process",
            generation_timestamp=datetime.now().isoformat()
        )
        assert metadata.generation_strategy == "hybrid"
        assert metadata.pattern_used == "iterative_process"
        assert metadata.generator_version == "0.1.0"  # default

    def test_metadata_with_source_id(self):
        """Test metadata with source pedagogical intent ID."""
        metadata = StoryboardMetadata(
            generation_strategy="rule_based",
            pattern_used="iterative_process",
            generation_timestamp=datetime.now().isoformat(),
            source_pedagogical_intent_id="gradient_descent"
        )
        assert metadata.source_pedagogical_intent_id == "gradient_descent"


class TestStoryboardWithMetadata:
    """Tests for StoryboardWithMetadata model."""

    def test_valid_storyboard_with_metadata(self):
        """Test creating valid storyboard with metadata."""
        beats = [
            Beat(purpose="set_context", intent="Show the problem space."),
            Beat(purpose="show_mechanism", intent="Demonstrate the algorithm."),
            Beat(purpose="iterate_process", intent="Show repeated application."),
        ]
        storyboard = Storyboard(
            topic="Test Topic",
            beats=beats,
            pedagogical_pattern="iterative_process"
        )
        metadata = StoryboardMetadata(
            generation_strategy="hybrid",
            pattern_used="iterative_process",
            generation_timestamp=datetime.now().isoformat()
        )
        result = StoryboardWithMetadata(
            storyboard=storyboard,
            metadata=metadata
        )
        assert result.storyboard.topic == "Test Topic"
        assert result.metadata.generation_strategy == "hybrid"

    def test_json_formatted_output(self):
        """Test that model_dump_json_formatted produces valid JSON."""
        beats = [
            Beat(purpose="set_context", intent="Show the problem space."),
            Beat(purpose="show_mechanism", intent="Demonstrate the algorithm."),
            Beat(purpose="iterate_process", intent="Show repeated application."),
        ]
        storyboard = Storyboard(
            topic="Test Topic",
            beats=beats,
            pedagogical_pattern="iterative_process"
        )
        metadata = StoryboardMetadata(
            generation_strategy="hybrid",
            pattern_used="iterative_process",
            generation_timestamp=datetime.now().isoformat()
        )
        result = StoryboardWithMetadata(
            storyboard=storyboard,
            metadata=metadata
        )

        json_output = result.model_dump_json_formatted()
        assert "Test Topic" in json_output
        assert "set_context" in json_output
        assert "hybrid" in json_output
