"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { StoryboardBeat, VideoMetadata } from "@/types/pipeline";

type ContentSectionProps = {
  beat: StoryboardBeat;
  beatIndex: number;
  content?: string; // Additional markdown content for this section
  keyTakeaway?: string;
  video?: VideoMetadata; // In Phase 1, only one section gets the video
  jobId?: string;
  showVideo?: boolean;
};

// Map beat purposes to display-friendly titles and colors
const purposeConfig: Record<string, { label: string; color: string }> = {
  set_context: { label: "Setting the Stage", color: "bg-blue-100 text-blue-800 border-blue-200" },
  place_initial_state: { label: "Starting Point", color: "bg-purple-100 text-purple-800 border-purple-200" },
  show_update_rule: { label: "The Mechanism", color: "bg-indigo-100 text-indigo-800 border-indigo-200" },
  iterate_process: { label: "Iteration", color: "bg-cyan-100 text-cyan-800 border-cyan-200" },
  contrast_failure_mode: { label: "What Can Go Wrong", color: "bg-amber-100 text-amber-800 border-amber-200" },
  show_convergence: { label: "Convergence", color: "bg-green-100 text-green-800 border-green-200" },
  highlight_edge_case: { label: "Edge Case", color: "bg-red-100 text-red-800 border-red-200" },
  reinforce_takeaway: { label: "Key Takeaway", color: "bg-emerald-100 text-emerald-800 border-emerald-200" },
};

function getPurposeDisplay(purpose: string) {
  const normalized = purpose.toLowerCase().replace(/\s+/g, "_");
  return purposeConfig[normalized] || {
    label: purpose.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase()),
    color: "bg-slate-100 text-slate-800 border-slate-200"
  };
}

export function ContentSection({
  beat,
  beatIndex,
  content,
  keyTakeaway,
  video,
  jobId,
  showVideo = false,
}: ContentSectionProps) {
  const { label, color } = getPurposeDisplay(beat.purpose);
  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

  return (
    <section className="space-y-4">
      {/* Section header with beat number and purpose */}
      <div className="flex items-center gap-3">
        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-900 text-sm font-medium text-white">
          {beatIndex + 1}
        </span>
        <Badge className={cn("border", color)}>{label}</Badge>
      </div>

      {/* Main content */}
      <Card>
        <CardContent className="pt-6 space-y-4">
          {/* Beat intent - the core explanation */}
          <p className="text-lg text-slate-700 leading-relaxed">{beat.intent}</p>

          {/* Additional content if provided */}
          {content && (
            <div className="text-slate-600 leading-relaxed whitespace-pre-wrap">
              {content}
            </div>
          )}

          {/* Embedded video for this section (Phase 1: only one section gets the full video) */}
          {showVideo && video && jobId && (
            <div className="mt-6 rounded-lg overflow-hidden bg-slate-900">
              <video
                className="w-full"
                controls
                poster={`${API_BASE}/api/pipeline/video/${jobId}/thumbnail`}
              >
                <source
                  src={`${API_BASE}/api/pipeline/video/${jobId}`}
                  type="video/mp4"
                />
                Your browser does not support the video tag.
              </video>
              <div className="px-3 py-2 text-sm text-slate-400">
                Watch the animation to see this concept in action
              </div>
            </div>
          )}

          {/* Key takeaway callout */}
          {keyTakeaway && (
            <div className="mt-4 rounded-lg border-l-4 border-emerald-500 bg-emerald-50 p-4">
              <p className="font-medium text-emerald-800">
                <span className="mr-2">💡</span>
                {keyTakeaway}
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </section>
  );
}
