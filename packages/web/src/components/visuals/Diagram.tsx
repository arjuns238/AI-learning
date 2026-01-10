"use client";

import { useEffect, useId, useState } from "react";
import mermaid from "mermaid";

import type { LessonVisual } from "@/types/lesson";

export function Diagram({
  visual,
}: {
  visual: Extract<LessonVisual, { type: "diagram" }>;
}) {
  const id = useId();
  const safeId = id.replace(/:/g, "");
  const [svg, setSvg] = useState<string>("");

  useEffect(() => {
    mermaid.initialize({ startOnLoad: false, theme: "neutral" });
    mermaid
      .render(`mermaid-${safeId}`, visual.spec.mermaid)
      .then(({ svg }) => setSvg(svg))
      .catch(() => setSvg(""));
  }, [safeId, visual.spec.mermaid]);

  return (
    <div
      className="w-full overflow-x-auto rounded-lg border border-slate-200 bg-white p-4"
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}
