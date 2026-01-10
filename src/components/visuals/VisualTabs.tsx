"use client";

import type { Visual } from "@/types/lesson";
import { Plot } from "@/components/visuals/Plot";
import { Diagram } from "@/components/visuals/Diagram";
import { DataTable } from "@/components/visuals/DataTable";
import { AttentionHeatmap } from "@/components/visuals/AttentionHeatmap";
import { ManimVideoPlayer } from "@/components/visuals/ManimVideoPlayer";

export type VisualTab = "interactive" | "animation";

type VisualTabsProps = {
  visuals: Visual[];
  activeTab: VisualTab;
  onTabChange: (tab: VisualTab) => void;
};

export function VisualTabs({ visuals, activeTab, onTabChange }: VisualTabsProps) {
  const interactiveVisual = visuals.find(
    (visual) => visual.kind === "interactive"
  ) as Extract<Visual, { kind: "interactive" }> | undefined;
  const videoVisual = visuals.find(
    (visual) => visual.kind === "video" && visual.type === "manim"
  ) as Extract<Visual, { kind: "video"; type: "manim" }> | undefined;

  const hasInteractive = Boolean(interactiveVisual);
  const hasAnimation = Boolean(videoVisual);

  const tabClass = (tab: VisualTab) =>
    `rounded-full px-3 py-1 text-sm font-medium transition ${
      activeTab === tab
        ? "bg-slate-900 text-white"
        : "border border-slate-200 text-slate-700 hover:bg-slate-50"
    }`;

  const renderInteractive = (
    visual: Extract<Visual, { kind: "interactive" }>
  ) => {
    const visualTitle =
      visual.type !== "attention_heatmap" ? visual.spec.title : undefined;

    return (
      <div className="space-y-3">
        {visualTitle ? (
          <p className="text-sm font-medium text-slate-600">{visualTitle}</p>
        ) : null}
        {visual.type === "plot" ? <Plot visual={visual} /> : null}
        {visual.type === "diagram" ? <Diagram visual={visual} /> : null}
        {visual.type === "table" ? <DataTable visual={visual} /> : null}
        {visual.type === "attention_heatmap" ? (
          Array.isArray(visual.spec?.tokens) &&
          Array.isArray(visual.spec?.weights) ? (
            <AttentionHeatmap
              tokens={visual.spec.tokens}
              weights={visual.spec.weights}
              explain_focus={visual.spec.explain_focus}
            />
          ) : (
            <p className="text-sm text-slate-600">
              Attention heatmap data is unavailable.
            </p>
          )
        ) : null}
      </div>
    );
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {hasInteractive ? (
          <button
            type="button"
            className={tabClass("interactive")}
            onClick={() => onTabChange("interactive")}
          >
            Interactive
          </button>
        ) : null}
        {hasAnimation ? (
          <button
            type="button"
            className={tabClass("animation")}
            onClick={() => onTabChange("animation")}
          >
            Animation
          </button>
        ) : null}
      </div>

      {activeTab === "interactive" && interactiveVisual
        ? renderInteractive(interactiveVisual)
        : null}
      {activeTab === "animation" && videoVisual ? (
        <ManimVideoPlayer spec={videoVisual.spec} />
      ) : null}

      {!interactiveVisual && !videoVisual ? (
        <p className="text-sm text-slate-600">No visuals available.</p>
      ) : null}
    </div>
  );
}
