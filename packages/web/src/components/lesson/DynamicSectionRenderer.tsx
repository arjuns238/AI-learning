"use client";

import { MathExpression } from "@/components/math/MathExpression";
import type {
  PedagogicalSection,
  AnimationClipSummary,
  Comparison,
} from "@/types/pipeline";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

// ============================================
// Sub-components for structured content
// ============================================

function StepsList({ steps }: { steps: string[] }) {
  return (
    <ol className="list-decimal list-inside space-y-1 mt-3 text-gray-700">
      {steps.map((step, index) => (
        <li key={index} className="leading-relaxed">
          {step}
        </li>
      ))}
    </ol>
  );
}

function MathBlock({ expressions }: { expressions: string[] }) {
  return (
    <div className="mt-3 space-y-2">
      {expressions.map((expr, index) => (
        <div key={index} className="overflow-x-auto py-2">
          <MathExpression expression={expr} display={true} />
        </div>
      ))}
    </div>
  );
}

function ComparisonBlock({ comparison }: { comparison: Comparison }) {
  return (
    <div className="mt-3 text-gray-700">
      <p><strong>{comparison.item_a}</strong> vs <strong>{comparison.item_b}</strong></p>
      <p className="mt-1 text-gray-600">
        <em>Key difference:</em> {comparison.difference}
      </p>
    </div>
  );
}

function VideoPlayer({
  clip,
}: {
  clip: AnimationClipSummary;
}) {
  if (!clip.success || !clip.video_url) {
    return null;
  }

  const videoUrl = clip.video_url.startsWith("http")
    ? clip.video_url
    : `${API_BASE}${clip.video_url}`;

  return (
    <div className="mt-4 rounded-lg overflow-hidden bg-gray-900">
      <video
        className="w-full aspect-video"
        controls
        autoPlay
        loop
        muted
        playsInline
      >
        <source src={videoUrl} type="video/mp4" />
        Your browser does not support the video tag.
      </video>
    </div>
  );
}

// ============================================
// Single Section (Markdown-like)
// ============================================

type SectionProps = {
  section: PedagogicalSection;
  clip?: AnimationClipSummary;
};

function Section({ section, clip }: SectionProps) {
  return (
    <div className="space-y-2">
      {/* Section title */}
      <h3 className="text-lg font-semibold text-gray-900">
        {section.title}
      </h3>

      {/* Main content */}
      <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
        {section.content}
      </p>

      {/* Steps list */}
      {section.steps && section.steps.length > 0 && (
        <StepsList steps={section.steps} />
      )}

      {/* Math expressions */}
      {section.math_expressions && section.math_expressions.length > 0 && (
        <MathBlock expressions={section.math_expressions} />
      )}

      {/* Comparison */}
      {section.comparison && <ComparisonBlock comparison={section.comparison} />}

      {/* Embedded video for this section */}
      {clip && <VideoPlayer clip={clip} />}
    </div>
  );
}

// ============================================
// Main Dynamic Section Renderer
// ============================================

type DynamicSectionRendererProps = {
  sections: PedagogicalSection[];
  clips?: AnimationClipSummary[];
  jobId: string;
};

export function DynamicSectionRenderer({
  sections,
  clips,
}: DynamicSectionRendererProps) {
  // Sort sections by order
  const sortedSections = [...sections].sort((a, b) => a.order - b.order);

  // Create a map of section_order -> clip for easy lookup
  const clipMap = new Map<number, AnimationClipSummary>();
  if (clips) {
    for (const clip of clips) {
      if (clip.success) {
        clipMap.set(clip.section_order, clip);
      }
    }
  }

  return (
    <div className="space-y-6">
      {sortedSections.map((section) => {
        const clip = clipMap.get(section.order);

        return (
          <Section
            key={section.order}
            section={section}
            clip={clip}
          />
        );
      })}
    </div>
  );
}

export default DynamicSectionRenderer;
