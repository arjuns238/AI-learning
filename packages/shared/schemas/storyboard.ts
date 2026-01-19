/**
 * Storyboard types - Layer 2 output schema
 *
 * Mirrors the Python Pydantic models in layer2/schema.py
 */

export interface Beat {
  purpose: string;
  intent: string;
}

export interface Storyboard {
  topic: string;
  beats: Beat[];
  pedagogical_pattern?: string;
}

export interface StoryboardMetadata {
  generator_version: string;
  generation_strategy: string;
  pattern_used?: string;
  generation_timestamp: string;
  source_pedagogical_intent_id?: string;
}

export interface StoryboardWithMetadata {
  storyboard: Storyboard;
  metadata: StoryboardMetadata;
}

// Type guards
export function isBeat(obj: any): obj is Beat {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    typeof obj.purpose === 'string' &&
    typeof obj.intent === 'string'
  );
}

export function isStoryboard(obj: any): obj is Storyboard {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    typeof obj.topic === 'string' &&
    Array.isArray(obj.beats) &&
    obj.beats.every(isBeat)
  );
}

export function isStoryboardWithMetadata(obj: any): obj is StoryboardWithMetadata {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    isStoryboard(obj.storyboard) &&
    typeof obj.metadata === 'object' &&
    typeof obj.metadata.generation_strategy === 'string'
  );
}
