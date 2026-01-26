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
  EnhancedQuizSection,
  ContextualQABox,
  ExploreDeeper,
} from "@/components/lesson";
import { DynamicSectionRenderer } from "@/components/lesson/DynamicSectionRenderer";
import type { EnhancedQuiz, QuizQuestion, QuizOption, AnimationClipSummary } from "@/types/pipeline";

const API_BASE = "http://localhost:8000";

// Inline clip player component - displays as looping GIF-like video
function ClipPlayer({ clip, jobId, className = "" }: { clip: AnimationClipSummary; jobId: string; className?: string }) {
  const baseUrl = clip.video_url || `/api/pipeline/video/clip/${jobId}/${clip.clip_id}`;
  const videoUrl = baseUrl.startsWith("http") ? baseUrl : `${API_BASE}${baseUrl}`;

  return (
    <div className={`rounded-lg overflow-hidden border border-slate-200 ${className}`}>
      <video
        src={videoUrl}
        autoPlay
        loop
        muted
        playsInline
        className="w-full max-h-[300px] bg-slate-900"
        preload="metadata"
      >
        Your browser does not support video playback.
      </video>
      <div className="px-3 py-2 bg-slate-50 text-xs text-slate-500 flex justify-between">
        <span>{clip.section_title}</span>
        <span>{clip.duration_seconds.toFixed(1)}s</span>
      </div>
    </div>
  );
}

export default function Home() {
  const { isLoading, progress, result, error, generate, reset } = usePipeline();
  const [qaMinimized, setQaMinimized] = useState(true);

  // Generate quiz from pedagogy sections (dynamic based on content)
  const enhancedQuiz = useMemo<EnhancedQuiz | null>(() => {
    if (!result?.pedagogy) return null;

    const { pedagogy } = result;
    const sections = pedagogy.sections || [];

    if (sections.length === 0) return null;

    // Generate questions based on sections
    const questions: QuizQuestion[] = [];

    // Question about the main topic
    questions.push({
      id: "q1",
      question: `What is the main concept behind ${pedagogy.topic}?`,
      options: [
        {
          text: pedagogy.summary,
          is_correct: true,
          misconception_hint: undefined,
        },
        {
          text: "It's a purely theoretical concept with no practical applications.",
          is_correct: false,
          misconception_hint: "This concept has practical applications as discussed in the lesson.",
        },
        {
          text: "None of the above applies to this concept.",
          is_correct: false,
          misconception_hint: "Review the lesson summary above.",
        },
        {
          text: "All options are equally correct.",
          is_correct: false,
          misconception_hint: "One answer is more accurate than the others.",
        },
      ] as QuizOption[],
      explanation: pedagogy.summary,
    });

    // Add questions based on sections (first 2 sections)
    sections.slice(0, 2).forEach((section, idx) => {
      questions.push({
        id: `q${idx + 2}`,
        question: `Regarding "${section.title}", which statement is most accurate?`,
        options: [
          {
            text: section.content.split(".")[0] + ".",
            is_correct: true,
            misconception_hint: undefined,
          },
          {
            text: "This section is not relevant to the main topic.",
            is_correct: false,
            misconception_hint: "This section is directly relevant to understanding the topic.",
          },
          {
            text: "The opposite is actually true.",
            is_correct: false,
            misconception_hint: "Review the section content above.",
          },
          {
            text: "This only applies in specialized circumstances.",
            is_correct: false,
            misconception_hint: "The concept has broader applicability.",
          },
        ] as QuizOption[],
        explanation: section.content,
        related_section_order: section.order,
      });
    });

    return {
      questions,
      passing_score: Math.ceil(questions.length * 0.66),
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
      `Can you explain more about ${pedagogy.topic}?`,
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
                    <span>L3 (Prompt): {result.timing.layer3_seconds.toFixed(1)}s</span>
                    <span>L4 (Video): {result.timing.layer4_seconds.toFixed(1)}s</span>
                    {result.timing.clip_generation_seconds !== undefined && result.timing.clip_generation_seconds > 0 && (
                      <span>Clips: {result.timing.clip_generation_seconds.toFixed(1)}s</span>
                    )}
                  </div>
                  {result.clips && result.clips.length > 0 && (
                    <p className="pt-2 text-xs text-slate-500">
                      {result.clips.filter(c => c.success).length}/{result.clips.length} clips generated
                    </p>
                  )}
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

                {/* Summary */}
                {result.pedagogy && (
                  <Card className="border-blue-200/50 bg-gradient-to-br from-blue-50 to-white">
                    <CardHeader>
                      <CardTitle className="text-lg text-blue-900">
                        Overview
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-lg text-blue-800 leading-relaxed">
                        {result.pedagogy.summary}
                      </p>
                    </CardContent>
                  </Card>
                )}

                {/* Video Section (if single video exists) */}
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

                {/* Dynamic Sections with embedded clips */}
                {result.pedagogy && result.pedagogy.sections && result.pedagogy.sections.length > 0 && (
                  <div className="space-y-6">
                    <h3 className="text-xl font-semibold text-slate-800">
                      Lesson Content
                    </h3>
                    <DynamicSectionRenderer
                      sections={result.pedagogy.sections}
                      clips={result.clips}
                      jobId={result.job_id}
                    />
                  </div>
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
