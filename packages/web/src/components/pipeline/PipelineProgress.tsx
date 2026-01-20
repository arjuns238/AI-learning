"use client";

import { cn } from "@/lib/utils";
import type { PipelineProgress as PipelineProgressType } from "@/types/pipeline";

const STAGE_CONFIG: Record<
  string,
  { label: string; description: string; color: string }
> = {
  pending: {
    label: "Queued",
    description: "Waiting to start...",
    color: "bg-slate-400",
  },
  generating_pedagogical_intent: {
    label: "Analyzing Topic",
    description: "Understanding the core concepts and learning goals...",
    color: "bg-blue-500",
  },
  generating_storyboard: {
    label: "Creating Storyboard",
    description: "Planning the visual narrative and learning beats...",
    color: "bg-purple-500",
  },
  generating_manim_prompt: {
    label: "Preparing Animation",
    description: "Translating pedagogy into animation instructions...",
    color: "bg-indigo-500",
  },
  generating_video: {
    label: "Rendering Video",
    description: "Generating and rendering the educational animation...",
    color: "bg-green-500",
  },
  completed: {
    label: "Complete",
    description: "Video ready!",
    color: "bg-emerald-500",
  },
  failed: {
    label: "Failed",
    description: "Something went wrong",
    color: "bg-red-500",
  },
};

type PipelineProgressProps = {
  progress: PipelineProgressType;
};

export function PipelineProgress({ progress }: PipelineProgressProps) {
  const config = STAGE_CONFIG[progress.stage] || STAGE_CONFIG.pending;
  const isFailed = progress.stage === "failed";

  return (
    <div className="space-y-4 rounded-lg border border-slate-200/70 bg-white/80 p-6 shadow-sm">
      {/* Stage label and percentage */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span
            className={cn(
              "inline-flex h-3 w-3 rounded-full",
              config.color,
              progress.stage !== "completed" &&
                progress.stage !== "failed" &&
                "animate-pulse"
            )}
          />
          <span
            className={cn(
              "font-medium",
              isFailed ? "text-red-700" : "text-slate-900"
            )}
          >
            {config.label}
          </span>
        </div>
        <span className="text-sm text-slate-500">
          {progress.progress_percent}%
        </span>
      </div>

      {/* Progress bar */}
      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
        <div
          className={cn(
            "h-full transition-all duration-500 ease-out",
            isFailed ? "bg-red-500" : "bg-gradient-to-r from-blue-500 to-emerald-500"
          )}
          style={{ width: `${progress.progress_percent}%` }}
        />
      </div>

      {/* Description */}
      <p
        className={cn(
          "text-sm",
          isFailed ? "text-red-600" : "text-slate-600"
        )}
      >
        {progress.error || progress.message || config.description}
      </p>

      {/* Stage steps indicator */}
      <div className="flex justify-between pt-2">
        {["L1", "L2", "L3", "L4"].map((step, index) => {
          const stepStages = [
            "generating_pedagogical_intent",
            "generating_storyboard",
            "generating_manim_prompt",
            "generating_video",
          ];
          const currentIndex = stepStages.indexOf(progress.stage);
          const isComplete =
            progress.stage === "completed" || currentIndex > index;
          const isCurrent = currentIndex === index;

          return (
            <div key={step} className="flex flex-col items-center gap-1">
              <div
                className={cn(
                  "flex h-8 w-8 items-center justify-center rounded-full text-xs font-medium",
                  isComplete
                    ? "bg-emerald-500 text-white"
                    : isCurrent
                    ? "bg-blue-500 text-white"
                    : "bg-slate-100 text-slate-400"
                )}
              >
                {step}
              </div>
              <span className="text-xs text-slate-500">
                {["Intent", "Storyboard", "Prompt", "Video"][index]}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
