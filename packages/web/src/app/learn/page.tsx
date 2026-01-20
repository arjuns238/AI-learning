"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { usePipeline } from "@/hooks/usePipeline";
import {
  TopicForm,
  PipelineProgress,
  VideoPlayer,
  PedagogyPanel,
  StoryboardTimeline,
  QuizSection,
} from "@/components/pipeline";

type TabId = "video" | "pedagogy" | "storyboard" | "quiz";

export default function LearnPage() {
  const { isLoading, progress, result, error, generate, reset } = usePipeline();
  const [activeTab, setActiveTab] = useState<TabId>("video");

  const tabs: { id: TabId; label: string; available: boolean }[] = [
    { id: "video", label: "Video", available: !!result?.video },
    { id: "pedagogy", label: "Concepts", available: !!result?.pedagogy },
    { id: "storyboard", label: "Storyboard", available: !!result?.storyboard },
    { id: "quiz", label: "Quiz", available: !!result?.pedagogy },
  ];

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_#fff7e9,_#f7f2ea_55%,_#efe7db_100%)] text-slate-900">
      <main className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-6 py-12 lg:px-12">
        {/* Header */}
        <section className="space-y-4">
          <Badge variant="soft">Full Pipeline Demo</Badge>
          <h1 className="text-3xl font-semibold leading-tight text-slate-900 sm:text-4xl">
            Generate Educational Videos with AI
          </h1>
          <p className="text-lg text-slate-600">
            Enter a topic and watch as the system creates a complete learning
            experience: pedagogical analysis, storyboard, and animated video.
          </p>
        </section>

        <div className="grid gap-8 lg:grid-cols-[350px_1fr]">
          {/* Left sidebar: Form + Progress */}
          <div className="space-y-6">
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

          {/* Main content area */}
          <div className="space-y-6">
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
                        d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                      />
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={1.5}
                        d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                  </div>
                  <h3 className="text-lg font-medium text-slate-700">
                    No content yet
                  </h3>
                  <p className="mt-2 text-sm text-slate-500">
                    Enter a topic on the left to generate an educational video
                    with pedagogical analysis.
                  </p>
                </CardContent>
              </Card>
            )}

            {result && (
              <>
                {/* Topic title */}
                <div className="flex items-center justify-between">
                  <h2 className="text-2xl font-semibold text-slate-900">
                    {result.topic}
                  </h2>
                  {result.success && (
                    <Badge className="bg-emerald-100 text-emerald-700 border-emerald-200">
                      Success
                    </Badge>
                  )}
                </div>

                {/* Tab navigation */}
                <div className="flex gap-2 border-b border-slate-200">
                  {tabs.map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => tab.available && setActiveTab(tab.id)}
                      disabled={!tab.available}
                      className={cn(
                        "px-4 py-2 text-sm font-medium transition-colors",
                        "border-b-2 -mb-px",
                        activeTab === tab.id
                          ? "border-blue-500 text-blue-600"
                          : tab.available
                          ? "border-transparent text-slate-500 hover:text-slate-700"
                          : "border-transparent text-slate-300 cursor-not-allowed"
                      )}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>

                {/* Tab content */}
                <div className="min-h-[400px]">
                  {activeTab === "video" && result.video && (
                    <Card>
                      <CardHeader>
                        <CardTitle>Generated Animation</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <VideoPlayer video={result.video} jobId={result.job_id} />
                      </CardContent>
                    </Card>
                  )}

                  {activeTab === "video" && !result.video && (
                    <Card className="border-amber-200/70 bg-amber-50/50">
                      <CardContent className="py-8 text-center">
                        <p className="text-amber-800">
                          Video generation failed. Check the error message for details.
                        </p>
                        {result.error_message && (
                          <p className="mt-2 text-sm text-amber-600">
                            {result.error_message}
                          </p>
                        )}
                      </CardContent>
                    </Card>
                  )}

                  {activeTab === "pedagogy" && result.pedagogy && (
                    <PedagogyPanel pedagogy={result.pedagogy} />
                  )}

                  {activeTab === "storyboard" && result.storyboard && (
                    <Card>
                      <CardHeader>
                        <CardTitle>Animation Storyboard</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <StoryboardTimeline storyboard={result.storyboard} />
                      </CardContent>
                    </Card>
                  )}

                  {activeTab === "quiz" && result.pedagogy && (
                    <QuizSection question={result.pedagogy.check_for_understanding} />
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
