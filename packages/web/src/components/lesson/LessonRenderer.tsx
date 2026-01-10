"use client";

import { useEffect, useState } from "react";

import type { Lesson } from "@/types/lesson";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Plot } from "@/components/visuals/Plot";
import { Diagram } from "@/components/visuals/Diagram";
import { DataTable } from "@/components/visuals/DataTable";
import { AttentionHeatmap } from "@/components/visuals/AttentionHeatmap";

export function LessonRenderer({ lesson }: { lesson: Lesson }) {
  const [showAnswer, setShowAnswer] = useState(false);
  const isAttentionLesson =
    /attention/i.test(lesson.title) || lesson.visual.type === "attention_heatmap";
  const isAttentionSpecValid =
    lesson.visual.type === "attention_heatmap" &&
    Array.isArray(lesson.visual.spec?.tokens) &&
    Array.isArray(lesson.visual.spec?.weights);

  useEffect(() => {
    setShowAnswer(false);
  }, [lesson.title]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <Badge variant="soft">Lesson</Badge>
        <h1 className="text-3xl font-semibold text-slate-900">{lesson.title}</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Intuition</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-slate-700 leading-relaxed">{lesson.intuition}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Concrete example</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-slate-700 leading-relaxed">{lesson.concrete_example}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Visual</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {lesson.visual.spec?.title ? (
            <p className="text-sm font-medium text-slate-600">
              {lesson.visual.spec.title}
            </p>
          ) : null}
          {lesson.visual.type === "plot" ? <Plot visual={lesson.visual} /> : null}
          {lesson.visual.type === "diagram" ? <Diagram visual={lesson.visual} /> : null}
          {lesson.visual.type === "table" ? <DataTable visual={lesson.visual} /> : null}
          {lesson.visual.type === "attention_heatmap" ? (
            isAttentionLesson && isAttentionSpecValid ? (
              <AttentionHeatmap
                tokens={lesson.visual.spec.tokens}
                weights={lesson.visual.spec.weights}
                explain_focus={lesson.visual.spec.explain_focus}
              />
            ) : (
              <p className="text-sm text-slate-600">
                Attention heatmap data is unavailable.
              </p>
            )
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Common confusion</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-slate-700 leading-relaxed">{lesson.common_confusion}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Mini quiz</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-slate-800 font-medium">{lesson.quiz.question}</p>
          <div className="grid gap-2">
            {lesson.quiz.options.map((option, index) => (
              <div
                key={`option-${index}`}
                className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700"
              >
                {option}
              </div>
            ))}
          </div>
          <Button
            variant="outline"
            type="button"
            onClick={() => setShowAnswer((prev) => !prev)}
          >
            {showAnswer ? "Hide answer" : "Reveal answer"}
          </Button>
          {showAnswer ? (
            <div className="rounded-md border border-slate-200 bg-white p-3 text-sm text-slate-700">
              <p className="font-semibold text-slate-900">
                Correct:{" "}
                {lesson.quiz.options[lesson.quiz.correct_answer_index] ??
                  "Check the explanation below."}
              </p>
              <p className="mt-2">{lesson.quiz.explanation}</p>
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
