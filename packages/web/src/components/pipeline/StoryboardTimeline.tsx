"use client";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { StoryboardSummary } from "@/types/pipeline";

const PURPOSE_COLORS: Record<string, string> = {
  set_context: "bg-blue-100 text-blue-700 border-blue-200",
  establish_baseline: "bg-slate-100 text-slate-700 border-slate-200",
  place_initial_state: "bg-purple-100 text-purple-700 border-purple-200",
  introduce_misconception: "bg-amber-100 text-amber-700 border-amber-200",
  ground_in_example: "bg-emerald-100 text-emerald-700 border-emerald-200",
  show_mechanism: "bg-indigo-100 text-indigo-700 border-indigo-200",
  show_update_rule: "bg-indigo-100 text-indigo-700 border-indigo-200",
  iterate_process: "bg-cyan-100 text-cyan-700 border-cyan-200",
  demonstrate_convergence: "bg-green-100 text-green-700 border-green-200",
  contrast_failure_mode: "bg-red-100 text-red-700 border-red-200",
  check_understanding: "bg-orange-100 text-orange-700 border-orange-200",
};

const PURPOSE_LABELS: Record<string, string> = {
  set_context: "Context",
  establish_baseline: "Baseline",
  place_initial_state: "Initial State",
  introduce_misconception: "Misconception",
  ground_in_example: "Example",
  show_mechanism: "Mechanism",
  show_update_rule: "Update Rule",
  iterate_process: "Iteration",
  demonstrate_convergence: "Convergence",
  contrast_failure_mode: "Edge Case",
  check_understanding: "Check",
};

type StoryboardTimelineProps = {
  storyboard: StoryboardSummary;
};

export function StoryboardTimeline({ storyboard }: StoryboardTimelineProps) {
  return (
    <div className="space-y-4">
      {/* Pattern badge */}
      {storyboard.pedagogical_pattern && (
        <div className="flex items-center gap-2">
          <span className="text-sm text-slate-500">Pattern:</span>
          <Badge variant="outline">
            {storyboard.pedagogical_pattern.replace(/_/g, " ")}
          </Badge>
        </div>
      )}

      {/* Timeline */}
      <div className="relative">
        {/* Connecting line */}
        <div className="absolute left-4 top-0 h-full w-0.5 bg-slate-200" />

        {/* Beats */}
        <div className="space-y-4">
          {storyboard.beats.map((beat, index) => {
            const colorClass =
              PURPOSE_COLORS[beat.purpose] ||
              "bg-slate-100 text-slate-700 border-slate-200";
            const label =
              PURPOSE_LABELS[beat.purpose] ||
              beat.purpose.replace(/_/g, " ");

            return (
              <div key={index} className="relative flex items-start gap-4 pl-8">
                {/* Timeline dot */}
                <div
                  className={cn(
                    "absolute left-2 mt-1.5 h-4 w-4 rounded-full border-2 bg-white",
                    colorClass.includes("blue")
                      ? "border-blue-400"
                      : colorClass.includes("purple")
                      ? "border-purple-400"
                      : colorClass.includes("emerald")
                      ? "border-emerald-400"
                      : colorClass.includes("indigo")
                      ? "border-indigo-400"
                      : colorClass.includes("amber")
                      ? "border-amber-400"
                      : colorClass.includes("red")
                      ? "border-red-400"
                      : colorClass.includes("green")
                      ? "border-green-400"
                      : colorClass.includes("cyan")
                      ? "border-cyan-400"
                      : colorClass.includes("orange")
                      ? "border-orange-400"
                      : "border-slate-400"
                  )}
                />

                {/* Beat content */}
                <div className="flex-1 rounded-lg border bg-white p-3 shadow-sm">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-medium text-slate-400">
                      {index + 1}
                    </span>
                    <Badge
                      variant="outline"
                      className={cn("text-xs", colorClass)}
                    >
                      {label}
                    </Badge>
                  </div>
                  <p className="text-sm text-slate-700">{beat.intent}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
