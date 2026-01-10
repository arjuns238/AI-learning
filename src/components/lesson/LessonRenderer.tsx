"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import type { Lesson, Visual } from "@/types/lesson";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  VisualTabs,
  type VisualTab,
} from "@/components/visuals/VisualTabs";

export function LessonRenderer({ lesson }: { lesson: Lesson }) {
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [quizStatus, setQuizStatus] = useState<
    "unanswered" | "correct" | "incorrect"
  >("unanswered");
  const [activeVisualTab, setActiveVisualTab] = useState<VisualTab>(
    "interactive"
  );
  const visualPanelRef = useRef<HTMLDivElement | null>(null);

  const visuals = useMemo<Visual[]>(() => {
    if (lesson.visuals?.length) {
      return lesson.visuals;
    }

    if (lesson.visual) {
      return [
        {
          kind: "interactive",
          type: lesson.visual.type,
          spec: lesson.visual.spec,
        },
      ];
    }

    return [];
  }, [lesson.visuals, lesson.visual]);

  const hasInteractive = visuals.some((visual) => visual.kind === "interactive");
  const hasAnimation = visuals.some((visual) => visual.kind === "video");

  useEffect(() => {
    setSelectedOption(null);
    setQuizStatus("unanswered");
    setActiveVisualTab(
      hasInteractive ? "interactive" : hasAnimation ? "animation" : "interactive"
    );
  }, [lesson.title, hasInteractive, hasAnimation]);

  const handleSubmitAnswer = () => {
    if (selectedOption === null) {
      return;
    }

    if (selectedOption === lesson.quiz.correct_answer_index) {
      setQuizStatus("correct");
    } else {
      setQuizStatus("incorrect");
    }
  };

  const handleRetry = () => {
    setSelectedOption(null);
    setQuizStatus("unanswered");
  };

  const handleWatchAnimation = () => {
    if (!hasAnimation) {
      return;
    }

    setActiveVisualTab("animation");
    visualPanelRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

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
          <p className="text-slate-700 leading-relaxed">
            {lesson.concrete_example}
          </p>
        </CardContent>
      </Card>

      <Card ref={visualPanelRef}>
        <CardHeader>
          <CardTitle>Visuals</CardTitle>
        </CardHeader>
        <CardContent>
          <VisualTabs
            visuals={visuals}
            activeTab={activeVisualTab}
            onTabChange={setActiveVisualTab}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Common confusion</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-slate-700 leading-relaxed">
            {lesson.common_confusion}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Mini quiz</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-slate-800 font-medium">{lesson.quiz.question}</p>
          <div className="grid gap-2">
            {lesson.quiz.options.map((option, index) => {
              const isSelected = selectedOption === index;
              return (
                <button
                  key={`option-${index}`}
                  type="button"
                  onClick={() =>
                    quizStatus === "unanswered" && setSelectedOption(index)
                  }
                  className={`rounded-md border px-3 py-2 text-left text-sm transition ${
                    quizStatus === "unanswered"
                      ? "border-slate-200 bg-slate-50 text-slate-700 hover:border-slate-300"
                      : "border-slate-200 bg-slate-50 text-slate-500"
                  } ${
                    isSelected
                      ? "border-slate-900 bg-white text-slate-900"
                      : ""
                  }`}
                >
                  {option}
                </button>
              );
            })}
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              type="button"
              onClick={handleSubmitAnswer}
              disabled={selectedOption === null || quizStatus !== "unanswered"}
            >
              Check answer
            </Button>
            {quizStatus === "correct" ? (
              <Button variant="ghost" type="button" onClick={handleRetry}>
                Retry
              </Button>
            ) : null}
          </div>

          {quizStatus !== "unanswered" ? (
            <div className="rounded-md border border-slate-200 bg-white p-3 text-sm text-slate-700">
              <p className="font-semibold text-slate-900">
                {quizStatus === "correct" ? "Correct" : "Not quite"}: {" "}
                {lesson.quiz.options[lesson.quiz.correct_answer_index] ??
                  "Check the explanation below."}
              </p>
              <p className="mt-2">{lesson.quiz.explanation}</p>
            </div>
          ) : null}

          {quizStatus === "incorrect" ? (
            <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
              <p className="font-medium">
                Watch the animation for a different perspective, then retry.
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                <Button
                  type="button"
                  onClick={handleWatchAnimation}
                  disabled={!hasAnimation}
                >
                  Watch animation
                </Button>
                <Button variant="outline" type="button" onClick={handleRetry}>
                  Retry now
                </Button>
              </div>
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
