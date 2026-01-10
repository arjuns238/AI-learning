/**
 * Pedagogical Intent Schema (TypeScript)
 *
 * Mirrors the Python Pydantic schema in packages/pedagogy-engine/layer1/schema.py
 */

export interface PedagogicalIntent {
  topic: string;
  core_question: string;
  target_mental_model: string;
  common_misconception: string;
  disambiguating_contrast: string;
  concrete_anchor: string;
  check_for_understanding: string;
  domain?: string;
  difficulty_level?: 1 | 2 | 3 | 4 | 5;
  spatial_metaphor?: string;
}

export interface GenerationMetadata {
  model_name: string;
  temperature: number;
  exemplar_ids: string[];
  generation_timestamp: string;
  version: string;
}

export interface PedagogicalIntentWithMetadata {
  intent: PedagogicalIntent;
  metadata: GenerationMetadata;
  quality_scores?: Record<string, number> | null;
  needs_review: boolean;
}

export interface GenerateRequest {
  topic: string;
  domain?: string;
  difficulty_level?: number;
  num_exemplars?: number;
}

export interface BatchGenerateRequest {
  topics: string[];
  domain?: string;
  difficulty_level?: number;
  num_exemplars?: number;
}
