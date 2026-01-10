import { NextResponse } from "next/server";

import type { Lesson, LessonRequest, Visual } from "@/types/lesson";

const systemPrompt = `You are a teaching engine for machine learning concepts.
You output a single JSON object that strictly matches the required schema.
Rules:
- Prioritize intuition and a concrete toy example.
- Be descriptive and thorough while staying focused; each text field should be 5-9 sentences.
- Intuition must include: a plain definition, the core mechanism, and why it matters.
- Concrete example must walk through steps with small numbers and end with a takeaway.
- Common confusion must name the mistaken belief, correct it, and explain the fix.
- Include one or more visuals in the visuals field.
- Include exactly one quiz with 3-4 options.
- Do not reference being an AI or tutor.
- Do not wrap the JSON in markdown or code fences.
Schema:
{
  "title": string,
  "intuition": string,
  "concrete_example": string,
  "common_confusion": string,
  "visuals": [
    {
      "kind": "interactive" | "video",
      "type": "plot" | "diagram" | "table" | "attention_heatmap" | "manim",
      "spec": object
    }
  ],
  "quiz": {
    "question": string,
    "options": string[],
    "correct_answer_index": number,
    "explanation": string
  }
}
Visual spec rules:
- plot: { title?, x_label?, y_label?, series: [{ name, data: [{ x, y }] }] }
- diagram: { title?, mermaid } where mermaid is a flowchart string
- table: { title?, columns: string[], rows: (string|number)[][] }
- attention_heatmap: { tokens: string[] (N<=10), weights: number[][] (NxN, rows sum to ~1), explain_focus?: [{ query_index, note }] }
If the topic includes "attention" (case-insensitive), you must include an attention_heatmap interactive visual and also a manim video visual with scene_id \"attention_intro_v1\" and src \"/videos/attention_intro_v1.mp4\".
Tokens and weights must be nested inside the attention_heatmap spec, not on the visual directly.
For manim: { scene_id: \"attention_intro_v1\", src: string, poster?: string, chapters?: [{ t, label }] }
Example attention visual:
{
  "visuals": [
    {
      "kind": "interactive",
      "type": "attention_heatmap",
      "spec": {
        "tokens": ["The", "cat", "sat", "on", "mat"],
        "weights": [
          [0.1, 0.5, 0.2, 0.1, 0.1],
          [0.2, 0.4, 0.2, 0.1, 0.1],
          [0.1, 0.2, 0.5, 0.1, 0.1],
          [0.1, 0.15, 0.15, 0.5, 0.1],
          [0.1, 0.15, 0.2, 0.15, 0.4]
        ],
        "explain_focus": [
          { "query_index": 2, "note": "The token 'sat' focuses on 'cat' to identify the subject." }
        ]
      }
    },
    {
      "kind": "video",
      "type": "manim",
      "spec": {
        "scene_id": "attention_intro_v1",
        "src": "/videos/attention_intro_v1.mp4"
      }
    }
  ]
}`;

export async function POST(req: Request) {
  const apiKey = process.env.OPENAI_API_KEY;
  const model = process.env.OPENAI_MODEL ?? "gpt-4o-mini";

  if (!apiKey) {
    return NextResponse.json(
      { error: "Missing OPENAI_API_KEY" },
      { status: 500 }
    );
  }

  let payload: LessonRequest;
  try {
    payload = (await req.json()) as LessonRequest;
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }

  if (!payload?.topic?.trim()) {
    return NextResponse.json({ error: "Topic is required" }, { status: 400 });
  }

  const userPrompt = `Topic: ${payload.topic}
Explanation level: ${payload.level}
Style: ${payload.style}
If the topic includes "attention", you must include both an attention heatmap and a manim video in visuals.
Generate the lesson JSON now.`;

  const response = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model,
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: userPrompt },
      ],
      temperature: 0.4,
      response_format: { type: "json_object" },
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    return NextResponse.json(
      { error: "LLM request failed", detail: errorText },
      { status: 500 }
    );
  }

  const data = (await response.json()) as {
    choices: Array<{ message: { content: string } }>;
  };

  const content = data.choices?.[0]?.message?.content;
  if (!content) {
    return NextResponse.json({ error: "Empty LLM response" }, { status: 500 });
  }

  let lesson: Lesson;
  try {
    lesson = JSON.parse(content) as Lesson;
  } catch {
    return NextResponse.json(
      { error: "Failed to parse lesson JSON", raw: content },
      { status: 500 }
    );
  }

  console.log("LLM raw response:", content);

  if (
    lesson.visual?.type === "attention_heatmap" &&
    !("spec" in lesson.visual) &&
    (lesson.visual as unknown as { tokens?: unknown }).tokens
  ) {
    const visual = lesson.visual as unknown as {
      tokens?: string[];
      weights?: number[][];
      explain_focus?: Array<{ query_index: number; note: string }>;
    };
    lesson.visual = {
      type: "attention_heatmap",
      spec: {
        tokens: visual.tokens ?? [],
        weights: visual.weights ?? [],
        explain_focus: visual.explain_focus,
      },
    };
  }

  if (!Array.isArray(lesson.visuals) || lesson.visuals.length === 0) {
    if (lesson.visual) {
      lesson.visuals = [
        {
          kind: "interactive",
          type: lesson.visual.type,
          spec: lesson.visual.spec,
        },
      ];
    } else {
      lesson.visuals = [];
    }
  } else {
    lesson.visuals = lesson.visuals.map((visual) => {
      if (!("kind" in visual)) {
        return { ...(visual as Omit<Visual, "kind">), kind: "interactive" } as Visual;
      }
      return visual as Visual;
    });
  }

  const isAttentionTopic = /attention/i.test(payload.topic);
  const attentionIndex = lesson.visuals.findIndex(
    (visual) => visual.kind === "interactive" && visual.type === "attention_heatmap"
  );
  const attentionVisual =
    attentionIndex >= 0 ? lesson.visuals[attentionIndex] : undefined;
  const isAttentionSpecValid =
    attentionVisual?.kind === "interactive" &&
    attentionVisual.type === "attention_heatmap" &&
    Array.isArray(attentionVisual.spec?.tokens) &&
    Array.isArray(attentionVisual.spec?.weights);

  let isDefaultVisual = false;

  if (isAttentionTopic && !isAttentionSpecValid) {
    const fallbackVisual: Extract<
      Visual,
      { kind: "interactive"; type: "attention_heatmap" }
    > = {
      kind: "interactive",
      type: "attention_heatmap",
      spec: {
        tokens: ["The", "cat", "sat", "on", "mat"],
        weights: [
          [0.05, 0.5, 0.2, 0.15, 0.1],
          [0.2, 0.4, 0.2, 0.1, 0.1],
          [0.1, 0.2, 0.5, 0.1, 0.1],
          [0.1, 0.15, 0.15, 0.5, 0.1],
          [0.1, 0.15, 0.2, 0.15, 0.4],
        ],
        explain_focus: [
          {
            query_index: 1,
            note: "The token \"cat\" focuses on nearby context to decide its role.",
          },
          {
            query_index: 3,
            note: "\"on\" attends to the noun phrase to resolve its attachment.",
          },
        ],
      },
    };

    if (attentionIndex >= 0) {
      lesson.visuals[attentionIndex] = fallbackVisual;
    } else {
      lesson.visuals.push(fallbackVisual);
    }
    isDefaultVisual = true;
  }

  if (
    isAttentionTopic &&
    !lesson.visuals.some(
      (visual) => visual.kind === "video" && visual.type === "manim"
    )
  ) {
    lesson.visuals.push({
      kind: "video",
      type: "manim",
      spec: {
        scene_id: "attention_intro_v1",
        src: "/videos/attention_intro_v1.mp4",
      },
    });
  }

  return NextResponse.json({ lesson, raw: content, isDefaultVisual });
}
