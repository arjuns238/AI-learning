export type LessonVisual =
  | {
      type: "plot";
      spec: {
        title?: string;
        x_label?: string;
        y_label?: string;
        series: Array<{
          name: string;
          data: Array<{ x: number; y: number }>;
        }>;
      };
    }
  | {
      type: "diagram";
      spec: {
        title?: string;
        mermaid: string;
      };
    }
  | {
      type: "table";
      spec: {
        title?: string;
        columns: string[];
        rows: Array<Array<string | number>>;
      };
    }
  | {
      type: "attention_heatmap";
      spec: {
        tokens: string[];
        weights: number[][];
        explain_focus?: Array<{ query_index: number; note: string }>;
      };
    };

export type Lesson = {
  title: string;
  intuition: string;
  concrete_example: string;
  common_confusion: string;
  visual: LessonVisual;
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
