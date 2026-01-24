"use client";

import { useState, useMemo } from "react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { usePipeline } from "@/hooks/usePipeline";
import {
  TopicForm,
  PipelineProgress,
  VideoPlayer,
} from "@/components/pipeline";
import {
  ContentSection,
  EnhancedQuizSection,
  ContextualQABox,
  ExploreDeeper,
} from "@/components/lesson";
import type { EnhancedQuiz, QuizQuestion, QuizOption } from "@/types/pipeline";

export default function Home() {
  const { isLoading, progress, result, error, generate, reset } = usePipeline();
  const [qaMinimized, setQaMinimized] = useState(true);

  // Generate mock quiz from pedagogy data (Phase 1: backend will do this later)
  const enhancedQuiz = useMemo<EnhancedQuiz | null>(() => {
    if (!result?.pedagogy) return null;

    const { pedagogy } = result;

    // Generate questions from the pedagogical context
    const questions: QuizQuestion[] = [
      {
        id: "q1",
        question: pedagogy.check_for_understanding,
        options: [
          {
            text: pedagogy.target_mental_model.split(".")[0] + ".",
            is_correct: true,
            misconception_hint: undefined,
          },
          {
            text: pedagogy.common_misconception,
            is_correct: false,
            misconception_hint: `This is actually a common misconception. ${pedagogy.disambiguating_contrast}`,
          },
          {
            text: "None of the above applies to this concept.",
            is_correct: false,
            misconception_hint: "Actually, the concept does have clear applications. Review the explanation above.",
          },
          {
            text: "All options are equally correct.",
            is_correct: false,
            misconception_hint: "One answer is more accurate than the others. Think about what distinguishes the correct mental model from common misconceptions.",
          },
        ] as QuizOption[],
        explanation: pedagogy.target_mental_model,
      },
      {
        id: "q2",
        question: `What distinguishes ${pedagogy.topic} from similar concepts?`,
        options: [
          {
            text: pedagogy.disambiguating_contrast,
            is_correct: true,
            misconception_hint: undefined,
          },
          {
            text: "There is no meaningful distinction.",
            is_correct: false,
            misconception_hint: "There are important distinctions! Review the key contrasts mentioned above.",
          },
          {
            text: pedagogy.common_misconception,
            is_correct: false,
            misconception_hint: "This represents a common misconception, not the key distinction.",
          },
          {
            text: "The distinction is purely theoretical with no practical implications.",
            is_correct: false,
            misconception_hint: "The distinction has real practical implications. Consider the concrete example discussed.",
          },
        ] as QuizOption[],
        explanation: `The key distinction is: ${pedagogy.disambiguating_contrast}`,
      },
      {
        id: "q3",
        question: `Which of the following best describes a concrete example of ${pedagogy.topic}?`,
        options: [
          {
            text: pedagogy.concrete_anchor,
            is_correct: true,
            misconception_hint: undefined,
          },
          {
            text: "An abstract theoretical framework without real-world applications.",
            is_correct: false,
            misconception_hint: "There are concrete, real-world applications of this concept.",
          },
          {
            text: "A purely mathematical construct with no intuitive meaning.",
            is_correct: false,
            misconception_hint: "This concept has intuitive, relatable applications.",
          },
          {
            text: "Something that only applies in very specialized circumstances.",
            is_correct: false,
            misconception_hint: "While there may be specialized applications, the concept has broader relevance.",
          },
        ] as QuizOption[],
        explanation: pedagogy.concrete_anchor,
      },
    ];

    return {
      questions,
      passing_score: 2,
    };
  }, [result?.pedagogy]);

  // Generate explore deeper prompts from pedagogy
  const explorePrompts = useMemo(() => {
    if (!result?.pedagogy) return [];
    const { pedagogy } = result;
    return [
      `Why is ${pedagogy.topic} important in practice?`,
      `What are common mistakes when applying ${pedagogy.topic}?`,
      `How does ${pedagogy.topic} relate to other concepts?`,
      `Can you explain the math behind ${pedagogy.topic}?`,
    ];
  }, [result?.pedagogy]);

  const handleExplore = (_prompt: string) => {
    // For now, open the Q&A box (in future, pre-fill the question)
    setQaMinimized(false);
  };

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_#fff7e9,_#f7f2ea_55%,_#efe7db_100%)] text-slate-900">
      <main className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-6 py-12 lg:px-12">
        {/* Header */}
        <section className="space-y-4">
          <Badge variant="soft">AI Learning Platform</Badge>
          <h1 className="text-3xl font-semibold leading-tight text-slate-900 sm:text-4xl">
            Learn Through AI-Generated Content
          </h1>
          <p className="text-lg text-slate-600">
            Enter a topic and explore a complete learning experience with
            explanations, animations, quizzes, and interactive Q&A.
          </p>
        </section>

        <div className="grid gap-8 lg:grid-cols-[350px_1fr]">
          {/* Left sidebar: Form + Progress */}
          <div className="space-y-6 lg:sticky lg:top-6 lg:self-start">
            <TopicForm onSubmit={generate} isLoading={isLoading} />

            {isLoading && progress && <PipelineProgress progress={progress} />}

            {error && !isLoading && (
              <Card className="border-red-200/70 bg-red-50/50">
                <CardHeader>
                  <CardTitle className="text-base text-red-800">
                    Error
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-red-700">{error}</p>
                  <Button
                    variant="outline"
                    size="sm"
                    className="mt-4"
                    onClick={reset}
                  >
                    Try Again
                  </Button>
                </CardContent>
              </Card>
            )}

            {result && result.timing && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm text-slate-500">
                    Generation Stats
                  </CardTitle>
                </CardHeader>
                <CardContent className="text-sm text-slate-600 space-y-1">
                  <p>Total time: {result.timing.total_seconds.toFixed(1)}s</p>
                  <div className="grid grid-cols-2 gap-2 pt-2">
                    <span>L1 (Intent): {result.timing.layer1_seconds.toFixed(1)}s</span>
                    <span>L2 (Story): {result.timing.layer2_seconds.toFixed(1)}s</span>
                    <span>L3 (Prompt): {result.timing.layer3_seconds.toFixed(1)}s</span>
                    <span>L4 (Video): {result.timing.layer4_seconds.toFixed(1)}s</span>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Main content area - SCROLLABLE */}
          <div className="space-y-8">
            {/* Empty state */}
            {!result && !isLoading && (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-16 text-center">
                  <div className="mb-4 rounded-full bg-slate-100 p-6">
                    <svg
                      className="h-12 w-12 text-slate-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={1.5}
                        d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                      />
                    </svg>
                  </div>
                  <h3 className="text-lg font-medium text-slate-700">
                    Ready to learn something new?
                  </h3>
                  <p className="mt-2 text-sm text-slate-500">
                    Enter a topic on the left to generate an interactive learning experience.
                  </p>
                </CardContent>
              </Card>
            )}

            {/* Content when result is available */}
            {result && (
              <>
                {/* Lesson Header */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h2 className="text-3xl font-semibold text-slate-900">
                      {result.topic}
                    </h2>
                    {result.success && (
                      <Badge className="bg-emerald-100 text-emerald-700 border-emerald-200">
                        Ready
                      </Badge>
                    )}
                  </div>
                </div>

                {/* Introduction - Core Question */}
                {result.pedagogy && (
                  <Card className="border-blue-200/50 bg-gradient-to-br from-blue-50 to-white">
                    <CardHeader>
                      <CardTitle className="text-lg text-blue-900">
                        The Core Question
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-lg text-blue-800 leading-relaxed">
                        {result.pedagogy.core_question}
                      </p>
                    </CardContent>
                  </Card>
                )}

                {/* Key Mental Model */}
                {result.pedagogy && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg">Understanding the Concept</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <p className="text-slate-700 leading-relaxed">
                        {result.pedagogy.target_mental_model}
                      </p>
                      {result.pedagogy.spatial_metaphor && (
                        <div className="rounded-lg border-l-4 border-indigo-500 bg-indigo-50 p-4">
                          <p className="font-medium text-indigo-800">
                            <span className="mr-2">🎯</span>
                            Visual Metaphor: {result.pedagogy.spatial_metaphor}
                          </p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )}

                {/* Video Section */}
                {result.video && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg">Watch It In Action</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <VideoPlayer video={result.video} jobId={result.job_id} />
                    </CardContent>
                  </Card>
                )}

                {/* Storyboard Beats as Content Sections */}
                {result.storyboard && result.storyboard.beats.length > 0 && (
                  <div className="space-y-6">
                    <h3 className="text-xl font-semibold text-slate-800">
                      Step-by-Step Breakdown
                    </h3>
                    {result.storyboard.beats.map((beat, index) => (
                      <ContentSection
                        key={`beat-${index}`}
                        beat={beat}
                        beatIndex={index}
                      />
                    ))}
                  </div>
                )}

                {/* Common Misconception Warning */}
                {result.pedagogy && (
                  <Card className="border-amber-200/50 bg-amber-50/50">
                    <CardHeader>
                      <CardTitle className="text-lg text-amber-800">
                        <span className="mr-2">⚠️</span>
                        Common Misconception
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <p className="text-amber-900">
                        {result.pedagogy.common_misconception}
                      </p>
                      <p className="text-sm text-amber-700">
                        <strong>The key distinction:</strong> {result.pedagogy.disambiguating_contrast}
                      </p>
                    </CardContent>
                  </Card>
                )}

                {/* Concrete Example */}
                {result.pedagogy && (
                  <Card className="border-emerald-200/50 bg-emerald-50/50">
                    <CardHeader>
                      <CardTitle className="text-lg text-emerald-800">
                        <span className="mr-2">📌</span>
                        Concrete Example
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-emerald-900">
                        {result.pedagogy.concrete_anchor}
                      </p>
                    </CardContent>
                  </Card>
                )}

                {/* Enhanced Quiz */}
                {enhancedQuiz && (
                  <div className="space-y-4">
                    <h3 className="text-xl font-semibold text-slate-800">
                      Test Your Understanding
                    </h3>
                    <EnhancedQuizSection quiz={enhancedQuiz} />
                  </div>
                )}

                {/* Explore Deeper */}
                {explorePrompts.length > 0 && (
                  <ExploreDeeper prompts={explorePrompts} onExplore={handleExplore} />
                )}
              </>
            )}
          </div>
        </div>
      </main>

      {/* Fixed Q&A Box */}
      {result && (
        <ContextualQABox
          lessonId={result.job_id}
          topic={result.topic}
          isMinimized={qaMinimized}
          onToggleMinimize={() => setQaMinimized(!qaMinimized)}
        />
      )}
    </div>
  );
}
