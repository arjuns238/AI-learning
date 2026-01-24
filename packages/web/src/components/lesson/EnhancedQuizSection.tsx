"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { EnhancedQuiz, QuizQuestion } from "@/types/pipeline";

type EnhancedQuizSectionProps = {
  quiz: EnhancedQuiz;
};

type QuestionState = {
  selectedOption: number | null;
  showFeedback: boolean;
  isCorrect: boolean | null;
};

export function EnhancedQuizSection({ quiz }: EnhancedQuizSectionProps) {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [questionStates, setQuestionStates] = useState<Record<string, QuestionState>>({});
  const [quizCompleted, setQuizCompleted] = useState(false);

  const currentQuestion = quiz.questions[currentQuestionIndex];
  const state = questionStates[currentQuestion?.id] || {
    selectedOption: null,
    showFeedback: false,
    isCorrect: null,
  };

  const handleSelectOption = (optionIndex: number) => {
    if (state.showFeedback) return; // Already answered

    const option = currentQuestion.options[optionIndex];
    const isCorrect = option.is_correct;

    setQuestionStates((prev) => ({
      ...prev,
      [currentQuestion.id]: {
        selectedOption: optionIndex,
        showFeedback: true,
        isCorrect,
      },
    }));
  };

  const handleNext = () => {
    if (currentQuestionIndex < quiz.questions.length - 1) {
      setCurrentQuestionIndex((prev) => prev + 1);
    } else {
      setQuizCompleted(true);
    }
  };

  const handleRestart = () => {
    setCurrentQuestionIndex(0);
    setQuestionStates({});
    setQuizCompleted(false);
  };

  // Calculate score
  const correctCount = Object.values(questionStates).filter((s) => s.isCorrect).length;
  const totalAnswered = Object.keys(questionStates).length;

  if (quizCompleted) {
    const passed = correctCount >= (quiz.passing_score || Math.ceil(quiz.questions.length / 2));

    return (
      <Card>
        <CardHeader>
          <CardTitle>Quiz Complete!</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="text-center py-8">
            <div className={cn(
              "inline-flex h-20 w-20 items-center justify-center rounded-full text-3xl font-bold",
              passed ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"
            )}>
              {correctCount}/{quiz.questions.length}
            </div>
            <p className="mt-4 text-lg font-medium text-slate-700">
              {passed
                ? "Great job! You've got a solid understanding."
                : "Keep learning! Review the sections above and try again."}
            </p>
          </div>

          <div className="space-y-2">
            {quiz.questions.map((q, i) => {
              const qState = questionStates[q.id];
              return (
                <div
                  key={q.id}
                  className={cn(
                    "flex items-center gap-3 rounded-lg border p-3",
                    qState?.isCorrect ? "border-emerald-200 bg-emerald-50" : "border-red-200 bg-red-50"
                  )}
                >
                  <span className={cn(
                    "flex h-6 w-6 items-center justify-center rounded-full text-sm font-medium",
                    qState?.isCorrect ? "bg-emerald-500 text-white" : "bg-red-500 text-white"
                  )}>
                    {qState?.isCorrect ? "✓" : "✗"}
                  </span>
                  <span className="text-sm text-slate-700 truncate flex-1">
                    Question {i + 1}: {q.question.slice(0, 60)}...
                  </span>
                </div>
              );
            })}
          </div>

          <Button onClick={handleRestart} variant="outline" className="w-full">
            Try Again
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Check Your Understanding</CardTitle>
          <Badge variant="outline">
            {currentQuestionIndex + 1} of {quiz.questions.length}
          </Badge>
        </div>
        {/* Progress bar */}
        <div className="mt-3 h-2 w-full rounded-full bg-slate-100">
          <div
            className="h-2 rounded-full bg-blue-500 transition-all duration-300"
            style={{ width: `${((currentQuestionIndex + 1) / quiz.questions.length) * 100}%` }}
          />
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Question */}
        <p className="text-lg font-medium text-slate-800">{currentQuestion.question}</p>

        {/* Options */}
        <div className="space-y-3">
          {currentQuestion.options.map((option, index) => {
            const isSelected = state.selectedOption === index;
            const showCorrect = state.showFeedback && option.is_correct;
            const showWrong = state.showFeedback && isSelected && !option.is_correct;

            return (
              <button
                key={index}
                onClick={() => handleSelectOption(index)}
                disabled={state.showFeedback}
                className={cn(
                  "w-full text-left p-4 rounded-lg border-2 transition-all",
                  !state.showFeedback && "hover:border-blue-300 hover:bg-blue-50 cursor-pointer",
                  !state.showFeedback && isSelected && "border-blue-500 bg-blue-50",
                  showCorrect && "border-emerald-500 bg-emerald-50",
                  showWrong && "border-red-500 bg-red-50",
                  state.showFeedback && !showCorrect && !showWrong && "border-slate-200 opacity-60"
                )}
              >
                <div className="flex items-start gap-3">
                  <span className={cn(
                    "flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-sm font-medium",
                    !state.showFeedback && "bg-slate-100 text-slate-600",
                    showCorrect && "bg-emerald-500 text-white",
                    showWrong && "bg-red-500 text-white"
                  )}>
                    {showCorrect ? "✓" : showWrong ? "✗" : String.fromCharCode(65 + index)}
                  </span>
                  <span className="text-slate-700">{option.text}</span>
                </div>
              </button>
            );
          })}
        </div>

        {/* Feedback */}
        {state.showFeedback && (
          <div
            className={cn(
              "rounded-lg p-4",
              "animate-in fade-in slide-in-from-top-2 duration-300",
              state.isCorrect ? "bg-emerald-50 border border-emerald-200" : "bg-amber-50 border border-amber-200"
            )}
          >
            {state.isCorrect ? (
              <>
                <p className="font-medium text-emerald-800">Correct!</p>
                <p className="mt-2 text-sm text-emerald-700">{currentQuestion.explanation}</p>
              </>
            ) : (
              <>
                <p className="font-medium text-amber-800">Not quite!</p>
                {state.selectedOption !== null && currentQuestion.options[state.selectedOption].misconception_hint && (
                  <p className="mt-2 text-sm text-amber-700">
                    {currentQuestion.options[state.selectedOption].misconception_hint}
                  </p>
                )}
                <p className="mt-2 text-sm text-slate-600">
                  The correct answer is:{" "}
                  <span className="font-medium">
                    {currentQuestion.options.find((o) => o.is_correct)?.text}
                  </span>
                </p>
              </>
            )}
          </div>
        )}

        {/* Navigation */}
        {state.showFeedback && (
          <Button onClick={handleNext} className="w-full">
            {currentQuestionIndex < quiz.questions.length - 1 ? "Next Question" : "See Results"}
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
