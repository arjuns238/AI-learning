"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

import type { LessonVisual } from "@/types/lesson";

export function Plot({ visual }: { visual: Extract<LessonVisual, { type: "plot" }> }) {
  const { series, x_label, y_label } = visual.spec;

  const data =
    series[0]?.data.map((point, index) => {
      const entry: Record<string, number> = { x: point.x };
      series.forEach((s) => {
        entry[s.name] = s.data[index]?.y ?? 0;
      });
      return entry;
    }) ?? [];

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey="x"
            label={x_label ? { value: x_label, position: "insideBottom" } : undefined}
            tick={{ fill: "#475569" }}
          />
          <YAxis
            label={
              y_label
                ? { value: y_label, angle: -90, position: "insideLeft" }
                : undefined
            }
            tick={{ fill: "#475569" }}
          />
          <Tooltip />
          <Legend />
          {series.map((s, index) => (
            <Line
              key={s.name}
              type="monotone"
              dataKey={s.name}
              stroke={index % 2 === 0 ? "#0f172a" : "#f97316"}
              strokeWidth={2}
              dot={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
