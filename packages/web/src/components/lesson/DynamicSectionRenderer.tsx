"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
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
    <ol className="list-decimal list-inside space-y-2 mt-4 pl-2">
      {steps.map((step, index) => (
        <li key={index} className="text-slate-700 leading-relaxed">
          {step}
        </li>
      ))}
    </ol>
  );
}

function MathBlock({ expressions }: { expressions: string[] }) {
  return (
    <div className="mt-4 space-y-3 bg-slate-50 rounded-lg p-4">
      {expressions.map((expr, index) => (
        <div key={index} className="overflow-x-auto">
          <MathExpression expression={expr} display={true} />
        </div>
      ))}
    </div>
  );
}

function ComparisonTable({ comparison }: { comparison: Comparison }) {
  return (
    <div className="mt-4 grid grid-cols-2 gap-4">
      <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
        <h4 className="font-semibold text-blue-800 mb-2">{comparison.item_a}</h4>
      </div>
      <div className="rounded-lg border border-purple-200 bg-purple-50 p-4">
        <h4 className="font-semibold text-purple-800 mb-2">{comparison.item_b}</h4>
      </div>
      <div className="col-span-2 rounded-lg border border-slate-200 bg-slate-50 p-4">
        <p className="text-slate-700">
          <span className="font-medium">Key difference:</span> {comparison.difference}
        </p>
      </div>
    </div>
  );
}

function VideoPlayer({
  clip,
  jobId,
}: {
  clip: AnimationClipSummary;
  jobId: string;
}) {
  if (!clip.success || !clip.video_url) {
    return (
      <div className="mt-4 rounded-lg bg-slate-100 p-4 text-center text-slate-500">
        Video unavailable{clip.error_message && `: ${clip.error_message}`}
      </div>
    );
  }

  const videoUrl = clip.video_url.startsWith("http")
    ? clip.video_url
    : `${API_BASE}${clip.video_url}`;

  return (
    <div className="mt-4 rounded-lg overflow-hidden bg-slate-900">
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
      {clip.duration_seconds > 0 && (
        <div className="px-3 py-2 text-sm text-slate-400">
          Duration: {clip.duration_seconds.toFixed(1)}s
        </div>
      )}
    </div>
  );
}

// ============================================
// Single Section Card
// ============================================

type SectionCardProps = {
  section: PedagogicalSection;
  clip?: AnimationClipSummary;
  jobId: string;
};

function SectionCard({ section, clip, jobId }: SectionCardProps) {
  return (
    <Card className="overflow-hidden">
      <CardContent className="pt-6 space-y-4">
        {/* Section header */}
        <div className="flex items-center gap-3">
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-900 text-sm font-medium text-white">
            {section.order}
          </span>
          <h2 className="text-xl font-semibold text-slate-900">{section.title}</h2>
        </div>

        {/* Main content */}
        <p className="text-slate-700 leading-relaxed whitespace-pre-wrap">
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

        {/* Comparison table */}
        {section.comparison && <ComparisonTable comparison={section.comparison} />}

        {/* Embedded video for this section */}
        {clip && <VideoPlayer clip={clip} jobId={jobId} />}
      </CardContent>
    </Card>
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
  jobId,
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
    <div className="space-y-8">
      {sortedSections.map((section) => {
        const clip = clipMap.get(section.order);

        return (
          <SectionCard
            key={section.order}
            section={section}
            clip={clip}
            jobId={jobId}
          />
        );
      })}
    </div>
  );
}

export default DynamicSectionRenderer;
