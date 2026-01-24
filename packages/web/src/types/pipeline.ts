/**
 * TypeScript types for the Full Pipeline API
 */

export type PipelineStage =
  | "pending"
  | "generating_pedagogical_intent"
  | "generating_storyboard"
  | "generating_manim_prompt"
  | "generating_video"
  | "completed"
  | "failed";

export type PipelineProgress = {
  job_id: string;
  stage: PipelineStage;
  progress_percent: number;
  message: string;
  started_at: string;
  updated_at: string;
  error?: string;
};

export type PedagogicalMetadata = {
  topic: string;
  core_question: string;
  target_mental_model: string;
  common_misconception: string;
  disambiguating_contrast: string;
  concrete_anchor: string;
  check_for_understanding: string;
  domain?: string;
  difficulty_level?: number;
  spatial_metaphor?: string;
};

export type StoryboardBeat = {
  purpose: string;
  intent: string;
};

export type StoryboardSummary = {
  topic: string;
  pedagogical_pattern?: string;
  beats: StoryboardBeat[];
};

export type VideoMetadata = {
  video_url?: string;
  video_path?: string;
  resolution: string;
  execution_time_seconds: number;
  generated_code?: string;
};

export type TimingBreakdown = {
  total_seconds: number;
  layer1_seconds: number;
  layer2_seconds: number;
  layer3_seconds: number;
  layer4_seconds: number;
};

export type FullPipelineResponse = {
  job_id: string;
  topic: string;
  success: boolean;
  error_stage?: string;
  error_message?: string;
  video?: VideoMetadata;
  pedagogy?: PedagogicalMetadata;
  storyboard?: StoryboardSummary;
  started_at: string;
  completed_at: string;
  timing?: TimingBreakdown;
};

export type FullPipelineRequest = {
  topic: string;
  domain?: string;
  difficulty_level?: number;
  video_resolution?: "480p15" | "720p30" | "1080p60";
  include_generated_code?: boolean;
  api_provider?: "anthropic" | "openai";
  use_rag?: boolean;
};

export type AsyncJobResponse = {
  job_id: string;
  status: "started";
  poll_url: string;
};

export type JobStatusResponse =
  | {
      status: "completed";
      result: FullPipelineResponse;
    }
  | {
      status: "in_progress";
      progress: PipelineProgress;
    }
  | {
      status: "failed";
      progress: PipelineProgress;
      error: string;
    };

// ============================================
// Enhanced Quiz Types (Phase 1)
// ============================================

export type QuizOption = {
  text: string;
  is_correct: boolean;
  misconception_hint?: string; // Shown when this wrong answer is selected
};

export type QuizQuestion = {
  id: string;
  question: string;
  options: QuizOption[];
  explanation: string; // Shown after correct answer
  related_beat_index?: number; // Links to storyboard beat
};

export type EnhancedQuiz = {
  questions: QuizQuestion[];
  passing_score?: number; // Min correct to "pass"
};

// ============================================
// Q&A Types (Phase 1)
// ============================================

export type QAMessage = {
  role: "user" | "assistant";
  content: string;
  followups?: string[];
};

export type QARequest = {
  lesson_id: string;
  question: string;
};

export type QAResponse = {
  answer: string;
  suggested_followups: string[];
  related_section?: string;
};

// ============================================
// Content Section Types (Phase 1)
// ============================================

export type ContentSection = {
  section_id: string;
  beat_index: number;
  title: string;
  content_markdown: string;
  key_takeaway?: string;
  // In Phase 2, this will have animation_clip
};

export type LessonContent = {
  topic: string;
  introduction: string;
  sections: ContentSection[];
  summary: string;
  quiz: EnhancedQuiz;
  explore_deeper_prompts: string[];
};
