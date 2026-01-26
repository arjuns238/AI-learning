"use client";

import { Card, CardContent } from "@/components/ui/card";
import { MathExpression } from "@/components/math/MathExpression";
import type { PedagogicalSection, AnimationClipSummary } from "@/types/pipeline";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

type ContentSectionProps = {
  section: PedagogicalSection;
  clip?: AnimationClipSummary;
};

export function ContentSection({ section, clip }: ContentSectionProps) {
  return (
    <section className="space-y-4">
      {/* Section header with order number */}
      <div className="flex items-center gap-3">
        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-900 text-sm font-medium text-white">
          {section.order}
        </span>
        <h2 className="text-xl font-semibold text-slate-900">{section.title}</h2>
      </div>

      {/* Main content */}
      <Card>
        <CardContent className="pt-6 space-y-4">
          {/* Section content */}
          <p className="text-lg text-slate-700 leading-relaxed whitespace-pre-wrap">
            {section.content}
          </p>

          {/* Steps list */}
          {section.steps && section.steps.length > 0 && (
            <ol className="list-decimal list-inside space-y-2 mt-4 pl-2">
              {section.steps.map((step, index) => (
                <li key={index} className="text-slate-700 leading-relaxed">
                  {step}
                </li>
              ))}
            </ol>
          )}

          {/* Math expressions */}
          {section.math_expressions && section.math_expressions.length > 0 && (
            <div className="mt-4 space-y-4 bg-slate-50 rounded-lg p-4">
              {section.math_expressions.map((expr, index) => (
                <MathExpression key={index} expression={expr} display={true} />
              ))}
            </div>
          )}

          {/* Comparison */}
          {section.comparison && (
            <div className="mt-4 grid grid-cols-2 gap-4">
              <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
                <h4 className="font-semibold text-blue-800 mb-2">
                  {section.comparison.item_a}
                </h4>
              </div>
              <div className="rounded-lg border border-purple-200 bg-purple-50 p-4">
                <h4 className="font-semibold text-purple-800 mb-2">
                  {section.comparison.item_b}
                </h4>
              </div>
              <div className="col-span-2 rounded-lg border border-slate-200 bg-slate-50 p-4">
                <p className="text-slate-700">
                  <span className="font-medium">Key difference:</span>{" "}
                  {section.comparison.difference}
                </p>
              </div>
            </div>
          )}

          {/* Embedded video for this section */}
          {clip && clip.success && clip.video_url && (
            <div className="mt-6 rounded-lg overflow-hidden bg-slate-900">
              <video
                className="w-full aspect-video"
                controls
                autoPlay
                loop
                muted
                playsInline
              >
                <source
                  src={
                    clip.video_url.startsWith("http")
                      ? clip.video_url
                      : `${API_BASE}${clip.video_url}`
                  }
                  type="video/mp4"
                />
                Your browser does not support the video tag.
              </video>
              <div className="px-3 py-2 text-sm text-slate-400">
                Watch the animation to see this concept in action
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </section>
  );
}
