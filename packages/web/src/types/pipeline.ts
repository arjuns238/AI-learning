/**
 * TypeScript types for the Full Pipeline API
 *
 * New Architecture (section-based):
 * - Layer 1: Topic -> Pedagogical Intent with freeform sections + embedded visual hints
 * - Layer 3: Visual sections -> Manim prompts
 * - Layer 4: Manim prompts -> Videos
 */

export type PipelineStage =
  | "pending"
  | "generating_pedagogical_intent"
  | "generating_manim_prompt"
  | "generating_video"
  | "generating_animation_clips"
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

// ============================================
// Section-based Pedagogical Schema
// ============================================

export type VisualHint = {
  should_animate: boolean;
  animation_description?: string;
  duration_hint?: number;
};

export type Comparison = {
  item_a: string;
  item_b: string;
  difference: string;
};

export type PedagogicalSection = {
  title: string;
  content: string;
  order: number;
  visual?: VisualHint;
  steps?: string[];
  math_expressions?: string[];
  comparison?: Comparison;
};

export type PedagogicalMetadata = {
  topic: string;
  summary: string;
  sections: PedagogicalSection[];
  domain?: string;
  difficulty_level?: number;
};

export type VideoMetadata = {
  video_url?: string;
  video_path?: string;
  resolution: string;
  execution_time_seconds: number;
  generated_code?: string;
};

// ============================================
// Animation Clips (linked to sections)
// ============================================

export type AnimationClipSummary = {
  clip_id: string;
  section_order: number;
  section_title: string;
  video_url?: string;
  video_path?: string;
  duration_seconds: number;
  success: boolean;
  error_message?: string;
};

export type TimingBreakdown = {
  total_seconds: number;
  layer1_seconds: number;
  layer3_seconds: number;
  layer4_seconds: number;
  clip_generation_seconds?: number;
};

export type FullPipelineResponse = {
  job_id: string;
  topic: string;
  success: boolean;
  error_stage?: string;
  error_message?: string;
  video?: VideoMetadata;
  pedagogy?: PedagogicalMetadata;
  clips?: AnimationClipSummary[];
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
// Enhanced Quiz Types
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
  related_section_order?: number; // Links to section
};

export type EnhancedQuiz = {
  questions: QuizQuestion[];
  passing_score?: number; // Min correct to "pass"
};

// ============================================
// Q&A Types
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
// Content Section Types (for rendering)
// ============================================

export type ContentSection = {
  section_id: string;
  order: number;
  title: string;
  content_markdown: string;
  steps?: string[];
  math_expressions?: string[];
  comparison?: Comparison;
  animation_clip?: AnimationClipSummary;
};

export type LessonContent = {
  topic: string;
  summary: string;
  sections: ContentSection[];
  quiz?: EnhancedQuiz;
  explore_deeper_prompts?: string[];
};
