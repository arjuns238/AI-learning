"use client";

import { useMemo, useState } from "react";

const clampOpacity = (value: number) => Math.min(1, Math.max(0.05, value));

type ExplainFocus = { query_index: number; note: string };

type AttentionHeatmapProps = {
  tokens: string[];
  weights: number[][];
  explain_focus?: ExplainFocus[];
};

export function AttentionHeatmap({
  tokens,
  weights,
  explain_focus = [],
}: AttentionHeatmapProps) {
  const [hoveredQueryIndex, setHoveredQueryIndex] = useState<number | null>(
    null
  );
  const [selectedQueryIndex, setSelectedQueryIndex] = useState<number | null>(
    null
  );

  const size = tokens.length;
  const isValid =
    size > 0 &&
    size <= 10 &&
    weights.length === size &&
    weights.every((row) => row.length === size);

  const activeQueryIndex =
    selectedQueryIndex ?? hoveredQueryIndex ?? (isValid ? 0 : null);

  const topTokens = useMemo(() => {
    if (!isValid || activeQueryIndex === null) return [];
    const row = weights[activeQueryIndex] ?? [];
    const ranked = row
      .map((value, index) => ({ index, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 2)
      .map((entry) => tokens[entry.index])
      .filter(Boolean);
    return ranked;
  }, [activeQueryIndex, isValid, tokens, weights]);

  const activeNote = useMemo(() => {
    if (activeQueryIndex === null) return null;
    return explain_focus.find((item) => item.query_index === activeQueryIndex);
  }, [activeQueryIndex, explain_focus]);

  if (!isValid) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-4 text-sm text-slate-600">
        Attention heatmap data is unavailable.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div
        className="grid gap-2"
        style={{
          gridTemplateColumns: `minmax(80px, 140px) repeat(${size}, minmax(2.5rem, 1fr))`,
        }}
      >
        <div className="text-xs uppercase tracking-wide text-slate-500">
          Query →
        </div>
        {tokens.map((token, index) => (
          <button
            key={`query-${token}-${index}`}
            type="button"
            onClick={() =>
              setSelectedQueryIndex((prev) => (prev === index ? null : index))
            }
            onMouseEnter={() => setHoveredQueryIndex(index)}
            onMouseLeave={() => setHoveredQueryIndex(null)}
            className={`rounded-md border px-2 py-1 text-xs font-semibold transition ${
              activeQueryIndex === index
                ? "border-orange-400 bg-orange-100 text-orange-700"
                : "border-slate-200 bg-white text-slate-600 hover:border-slate-300"
            }`}
          >
            {token}
          </button>
        ))}
        {weights.map((row, rowIndex) => (
          <div key={`row-${rowIndex}`} className="contents">
            <div
              className={`flex items-center text-xs font-semibold ${
                activeQueryIndex === rowIndex
                  ? "text-slate-900"
                  : "text-slate-500"
              }`}
              onMouseEnter={() => setHoveredQueryIndex(rowIndex)}
              onMouseLeave={() => setHoveredQueryIndex(null)}
            >
              {tokens[rowIndex]}
            </div>
            {row.map((value, colIndex) => {
              const opacity = clampOpacity(value);
              const isActive = activeQueryIndex === rowIndex;
              return (
                <div
                  key={`cell-${rowIndex}-${colIndex}`}
                  title={`Weight: ${value.toFixed(2)}`}
                  className={`h-10 rounded-md border transition ${
                    isActive ? "border-orange-300" : "border-slate-200"
                  }`}
                  style={{
                    backgroundColor: `rgba(249, 115, 22, ${opacity})`,
                    opacity: isActive ? 1 : 0.5,
                  }}
                  onMouseEnter={() => setHoveredQueryIndex(rowIndex)}
                  onMouseLeave={() => setHoveredQueryIndex(null)}
                />
              );
            })}
          </div>
        ))}
      </div>

      {activeQueryIndex !== null ? (
        <div className="space-y-1 text-sm text-slate-700">
          <p>
            Token "{tokens[activeQueryIndex]}" attends most to:{" "}
            {topTokens.length ? topTokens.join(", ") : "n/a"}
          </p>
          {activeNote ? (
            <p className="text-xs text-slate-500">{activeNote.note}</p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
