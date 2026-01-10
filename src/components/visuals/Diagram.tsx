"use client";

import { useEffect, useId, useState } from "react";
import mermaid from "mermaid";

import type { Visual } from "@/types/lesson";

export function Diagram({
  visual,
}: {
  visual: Extract<Visual, { kind: "interactive"; type: "diagram" }>;
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
