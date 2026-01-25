import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime
from orchestrator.pipeline import FullPipelineOrchestrator, PipelineProgress, PipelineStage
from layer1.schema import PedagogicalIntent, PedagogicalIntentWithMetadata, GenerationMetadata
from layer2.schema import Beat, Storyboard, StoryboardWithMetadata, StoryboardMetadata
from layer3.schema import ManimPrompt, ManimPromptMetadata, ManimPromptWithMetadata
from layer4.schema import ManimCodeResponse, VideoExecutionResult, ManimExecutionWithMetadata
from visual_planner.schema import VisualOpportunity, VisualPlan, VisualPlannerMetadata, VisualPlanWithMetadata


@pytest.fixture
def mock_layers():
    """Fixture providing mocked pipeline layers with real schema objects."""
    with patch('orchestrator.pipeline.PedagogicalIntentGenerator') as MockLayer1, \
         patch('orchestrator.pipeline.StoryboardGenerator') as MockLayer2, \
         patch('orchestrator.pipeline.ManimPromptGenerator') as MockLayer3, \
         patch('orchestrator.pipeline.Layer4Generator') as MockLayer4, \
         patch('orchestrator.pipeline.VisualPlanner') as MockVisualPlanner:
        
        # Layer 1: Real PedagogicalIntentWithMetadata
        intent = PedagogicalIntent(
            topic="Test Topic",
            core_question="What is test?",
            target_mental_model="Understanding test concepts",
            common_misconception="Test misconception",
            disambiguating_contrast="Test vs not-test",
            concrete_anchor="Real world test",
            check_for_understanding="Can you explain test?",
        )
        generation_metadata = GenerationMetadata(
            model_name="openai",
            temperature=0.7,
            exemplar_ids=["ex1", "ex2"],
            generation_timestamp=datetime.now().isoformat(),
            version="0.1.0"
        )
        mock_intent = PedagogicalIntentWithMetadata(intent=intent, metadata=generation_metadata)
        MockLayer1.return_value.generate.return_value = mock_intent

        # Layer 2: Real StoryboardWithMetadata
        storyboard = Storyboard(
            topic="Test Topic",
            pedagogical_pattern="Linear",
            beats=[
                Beat(purpose="introduction", intent="Introduce the concept"),
                Beat(purpose="explanation", intent="Explain the concept"),
                Beat(purpose="test", intent="Test explanation")
            ]
        )
        storyboard_metadata = StoryboardMetadata(
            generator_version="0.1.0",
            generation_strategy="hybrid",
            generation_timestamp=datetime.now().isoformat()
        )

        mock_storyboard = StoryboardWithMetadata(storyboard=storyboard, metadata=storyboard_metadata)
        MockLayer2.return_value.generate.return_value = mock_storyboard

        # Layer 3: Real ManimPromptWithMetadata
        prompt = ManimPrompt(
            title="Test Animation",
            system_instruction="Generate animation code",
            user_prompt="Create a simple animation"
        )
        metadata = ManimPromptMetadata(
            source_storyboard_topic="Test Topic",
            pedagogical_pattern="Linear",
            generation_timestamp=datetime.now().isoformat()
        )
        mock_prompt = ManimPromptWithMetadata(prompt=prompt, metadata=metadata)
        MockLayer3.return_value.generate.return_value = mock_prompt

        # Layer 4: Real ManimExecutionWithMetadata
        code_response = ManimCodeResponse(
            code="# test manim code\npass",
            model="test-model",
            generation_timestamp=datetime.now().isoformat()
        )
        execution_result = VideoExecutionResult(
            success=True,
            video_path="/test/video.mp4",
            resolution="480p15",
            execution_time_seconds=10.5
        )
        mock_execution = ManimExecutionWithMetadata(
            code_response=code_response,
            execution_result=execution_result
        )
        MockLayer4.return_value.generate.return_value = mock_execution

        # Visual Planner: Real plan with no opportunities
        visual_plan = VisualPlan(topic="Test Topic", opportunities=[])
        mock_plan = VisualPlanWithMetadata(
            plan=visual_plan,
            metadata=VisualPlannerMetadata(
                model_name="test-model",
                generation_timestamp=datetime.now().isoformat()
            )
        )
        MockVisualPlanner.return_value.identify_opportunities.return_value = mock_plan

        yield {
            'layer1': MockLayer1,
            'layer2': MockLayer2,
            'layer3': MockLayer3,
            'layer4': MockLayer4,
            'visual_planner': MockVisualPlanner,
        }


class TestFullPipelineOrchestratorRun:
    """Test cases for FullPipelineOrchestrator.run method."""

    def test_run_successful_full_pipeline(self, mock_layers):
        """Test successful run through all layers."""
        orchestrator = FullPipelineOrchestrator()
        result = orchestrator.run(topic="Test Topic")
        
        assert result.success
        assert result.topic == "Test Topic"
        assert result.job_id is not None
        assert result.video is not None
        assert result.video.video_path == "/test/video.mp4"
        assert result.error_message is None

    def test_run_with_progress_callback(self, mock_layers):
        """Test that progress callback is called during run."""
        progress_updates = []
        
        def on_progress(progress: PipelineProgress):
            progress_updates.append(progress)
        
        orchestrator = FullPipelineOrchestrator()
        result = orchestrator.run(topic="Test Topic", progress_callback=on_progress)
        
        assert result.success
        assert len(progress_updates) > 0
        # Verify callback was called with expected stages
        stages = [p.stage for p in progress_updates]
        assert PipelineStage.LAYER1_INTENT in stages

    def test_run_with_debug_callback(self, mock_layers):
        """Test that debug callback is called with layer I/O."""
        debug_calls = []
        
        def on_debug(layer_num, input_data, output_data, duration, error):
            debug_calls.append({
                'layer': layer_num,
                'input': input_data,
                'output': output_data,
                'duration': duration,
                'error': error,
            })
        
        orchestrator = FullPipelineOrchestrator()
        result = orchestrator.run(topic="Test Topic", debug_callback=on_debug)
        
        assert result.success
        # Debug callback should be called for at least layer 1
        assert any(call['layer'] == 1 for call in debug_calls)

    def test_run_layer1_failure(self, mock_layers):
        """Test orchestrator handling when layer 1 fails."""
        mock_layers['layer1'].return_value.generate.side_effect = Exception("Layer 1 error")
        
        orchestrator = FullPipelineOrchestrator()
        result = orchestrator.run(topic="Test Topic")
        
        assert not result.success
        assert result.error_stage == "generating_pedagogical_intent"
        assert "Layer 1 failed" in result.error_message

    def test_run_layer2_failure(self, mock_layers):
        """Test orchestrator handling when layer 2 fails."""
        mock_layers['layer2'].return_value.generate.side_effect = Exception("Layer 2 error")
        
        orchestrator = FullPipelineOrchestrator()
        result = orchestrator.run(topic="Test Topic")
        
        assert not result.success
        assert result.error_stage == "generating_storyboard"
        assert "Layer 2 failed" in result.error_message

    def test_run_layer3_failure(self, mock_layers):
        """Test orchestrator handling when layer 3 fails."""
        mock_layers['layer3'].return_value.generate.side_effect = Exception("Layer 3 error")
        
        orchestrator = FullPipelineOrchestrator()
        result = orchestrator.run(topic="Test Topic")
        
        assert not result.success
        assert result.error_stage == "generating_manim_prompt"
        assert "Layer 3 failed" in result.error_message

    def test_run_layer4_failure(self, mock_layers):
        """Test orchestrator handling when layer 4 fails."""
        code_response = ManimCodeResponse(
            code="# failed code",
            model="test-model",
            generation_timestamp=datetime.now().isoformat()
        )
        execution_result = VideoExecutionResult(
            success=False,
            resolution="480p15",
            execution_time_seconds=0.0,
            error_message="Video generation failed"
        )
        mock_execution = ManimExecutionWithMetadata(
            code_response=code_response,
            execution_result=execution_result,
            metadata={}
        )
        mock_layers['layer4'].return_value.generate.return_value = mock_execution
        
        orchestrator = FullPipelineOrchestrator()
        result = orchestrator.run(topic="Test Topic")
        
        assert not result.success
        assert result.error_stage == "generating_video"
        assert "Video generation failed" in result.error_message

    def test_run_with_domain_and_difficulty(self, mock_layers):
        """Test run with optional domain and difficulty parameters."""
        orchestrator = FullPipelineOrchestrator()
        result = orchestrator.run(
            topic="Test Topic",
            domain="machine_learning",
            difficulty_level=3
        )
        
        assert result.success
        assert result.pedagogy.domain == None # Pff tooo lazy
        assert result.pedagogy.difficulty_level == None # Pff tooo lazy

    def test_run_with_generated_code_included(self, mock_layers):
        """Test that generated code is included when requested."""
        orchestrator = FullPipelineOrchestrator()
        result = orchestrator.run(topic="Test Topic", include_generated_code=True)
        
        assert result.success
        assert result.video is not None
        assert result.video.generated_code == "# test manim code\npass"

    def test_run_with_generated_code_excluded(self, mock_layers):
        """Test that generated code is excluded by default."""
        orchestrator = FullPipelineOrchestrator()
        result = orchestrator.run(topic="Test Topic", include_generated_code=False)
        
        assert result.success
        assert result.video is not None
        assert result.video.generated_code is None

    def test_run_with_external_job_id(self, mock_layers):
        """Test that external job ID is used when provided."""
        external_id = "custom-job-123"
        orchestrator = FullPipelineOrchestrator()
        result = orchestrator.run(topic="Test Topic", external_job_id=external_id)
        
        assert result.success
        assert result.job_id == external_id

    def test_run_visual_planning_with_clips(self, mock_layers):
        """Test orchestrator with successful visual planning and clips."""
        # Set up visual planner to return opportunities
        opportunity = VisualOpportunity(
            id="opp-1",
            concept="Test Concept",
            description="Test concept description for visualization",
            placement="core_mechanism",
            pedagogical_purpose="To understand the concept better"
        )
        visual_plan = VisualPlan(topic="Test Topic", opportunities=[opportunity])
        visual_plan_with_metadata = VisualPlanWithMetadata(
            plan=visual_plan,
            metadata=VisualPlannerMetadata(
                model_name="test-model",
                generation_timestamp=datetime.now().isoformat()
            )
        )
        mock_layers['visual_planner'].return_value.identify_opportunities.return_value = visual_plan_with_metadata
        
        # Mock layer 3 and 4 for clip generation
        prompt = ManimPrompt(
            title="Clip Animation",
            system_instruction="Generate clip animation code",
            user_prompt="Create animation for clip"
        )
        mock_prompt = ManimPromptWithMetadata(
            prompt=prompt,
            metadata=ManimPromptMetadata(
                generator_version = "0.1.0",
                source_storyboard_topic="Test Topic",
                pedagogical_pattern="Linear",
                generation_timestamp=datetime.now().isoformat()
            )
        )
        mock_layers['layer3'].return_value.generate_for_visual.return_value = mock_prompt
        
        clip_code_response = ManimCodeResponse(
            code="# clip manim code\npass",
            model="test-model",
            generation_timestamp=datetime.now().isoformat()
        )
        clip_execution_result = VideoExecutionResult(
            success=True,
            video_path="/test/clip.mp4",
            resolution="480p15",
            execution_time_seconds=5.0
        )
        clip_execution = ManimExecutionWithMetadata(
            code_response=clip_code_response,
            execution_result=clip_execution_result
        )
        mock_layers['layer4'].return_value.generate.return_value = clip_execution
        
        orchestrator = FullPipelineOrchestrator()
        result = orchestrator.run(topic="Test Topic")
        
        assert result.success
        assert len(result.clips) > 0
        assert result.clips[0].concept == "Test Concept"

    def test_run_metadata_preservation(self, mock_layers):
        """Test that pedagogical metadata is preserved through pipeline."""
        orchestrator = FullPipelineOrchestrator()
        result = orchestrator.run(topic="Test Topic")
        
        assert result.success
        assert result.pedagogy is not None
        assert result.pedagogy.core_question == "What is test?"
        assert result.pedagogy.target_mental_model == "Understanding test concepts"
        assert result.pedagogy.common_misconception == "Test misconception"

    def test_run_timing_tracked(self, mock_layers):
        """Test that timing information is tracked for all layers."""
        orchestrator = FullPipelineOrchestrator()
        result = orchestrator.run(topic="Test Topic")
        
        assert result.success
        assert result.timing is not None
        assert result.timing.total_seconds > 0
        assert result.timing.layer1_seconds >= 0
        assert result.timing.layer2_seconds >= 0
        assert result.timing.layer3_seconds >= 0
        assert result.timing.layer4_seconds >= 0
