import { NextResponse } from "next/server";

import type { Lesson, LessonRequest } from "@/types/lesson";

const systemPrompt = `You are a teaching engine for machine learning concepts.
You output a single JSON object that strictly matches the required schema.
Rules:
- Prioritize intuition and a concrete toy example.
- Be descriptive and thorough while staying focused; each text field should be 5-9 sentences.
- Intuition must include: a plain definition, the core mechanism, and why it matters.
- Concrete example must walk through steps with small numbers and end with a takeaway.
- Common confusion must name the mistaken belief, correct it, and explain the fix.
- Include exactly one visual in the visual field.
- Include exactly one quiz with 3-4 options.
- Do not reference being an AI or tutor.
- Do not wrap the JSON in markdown or code fences.
Schema:
{
  "title": string,
  "intuition": string,
  "concrete_example": string,
  "common_confusion": string,
  "visual": {
    "type": "plot" | "diagram" | "table" | "attention_heatmap",
    "spec": object
  },
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
If the topic includes "attention" (case-insensitive), you must return visual.type = "attention_heatmap" and include 1-2 explain_focus notes tied to real tokens.
Tokens and weights must be nested inside visual.spec, not on visual directly.
Example attention visual:
{
  "visual": {
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
  }
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
If the topic includes "attention", you must set visual.type to "attention_heatmap" and return a valid attention heatmap spec.
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

  const isAttentionTopic = /attention/i.test(payload.topic);
  const isAttentionSpecValid =
    lesson.visual?.type === "attention_heatmap" &&
    "tokens" in lesson.visual.spec &&
    "weights" in lesson.visual.spec &&
    Array.isArray(lesson.visual.spec.tokens) &&
    Array.isArray(lesson.visual.spec.weights);

  let isDefaultVisual = false;

  if (isAttentionTopic && !isAttentionSpecValid) {
    lesson.visual = {
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
    isDefaultVisual = true;
  }

  return NextResponse.json({ lesson, raw: content, isDefaultVisual });
}
