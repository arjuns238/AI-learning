export type PlotSpec = {
  title?: string;
  x_label?: string;
  y_label?: string;
  series: Array<{
    name: string;
    data: Array<{ x: number; y: number }>;
  }>;
};

export type DiagramSpec = {
  title?: string;
  mermaid: string;
};

export type TableSpec = {
  title?: string;
  columns: string[];
  rows: Array<Array<string | number>>;
};

export type AttentionHeatmapSpec = {
  tokens: string[];
  weights: number[][];
  explain_focus?: Array<{ query_index: number; note: string }>;
};

export type LessonVisual =
  | { type: "plot"; spec: PlotSpec }
  | { type: "diagram"; spec: DiagramSpec }
  | { type: "table"; spec: TableSpec }
  | { type: "attention_heatmap"; spec: AttentionHeatmapSpec };

export type ManimVideoSpec = {
  scene_id: "attention_intro_v1";
  src: string;
  poster?: string;
  chapters?: { t: number; label: string }[];
};

export type Visual =
  | { kind: "interactive"; type: "plot"; spec: PlotSpec }
  | { kind: "interactive"; type: "diagram"; spec: DiagramSpec }
  | { kind: "interactive"; type: "table"; spec: TableSpec }
  | { kind: "interactive"; type: "attention_heatmap"; spec: AttentionHeatmapSpec }
  | { kind: "video"; type: "manim"; spec: ManimVideoSpec };

export type Lesson = {
  title: string;
  intuition: string;
  concrete_example: string;
  common_confusion: string;
  visuals: Visual[];
  visual?: LessonVisual;
  quiz: {
    question: string;
    options: string[];
    correct_answer_index: number;
    explanation: string;
  };
};

export type LessonRequest = {
  topic: string;
  level: "Beginner" | "Practical" | "Mathy";
  style: "Visual-first" | "Text-first";
};
