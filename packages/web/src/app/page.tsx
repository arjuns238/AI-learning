"use client";

import { useState, useMemo, useRef, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { usePipeline } from "@/hooks/usePipeline";
import { Navbar, ChatInput, MessageArea, EmptyState } from "@/components/sections";
import { VideoPlayer } from "@/components/pipeline";
import {
  EnhancedQuizSection,
  ExploreDeeper,
} from "@/components/lesson";
import { DynamicSectionRenderer } from "@/components/lesson/DynamicSectionRenderer";
import type { EnhancedQuiz, QuizQuestion, QuizOption } from "@/types/pipeline";
import { Loader2, AlertCircle } from "lucide-react";

// Message types for chat display
interface ChatMessage {
  id: string;
  type: "user" | "assistant" | "loading";
  content: string;
}

export default function Home() {
  const { isLoading, progress, result, error, generate, reset } = usePipeline();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, result, isLoading]);

  // Handle topic submission
  const handleSend = (topic: string) => {
    // Add user message
    setMessages(prev => [
      ...prev,
      { id: `user-${Date.now()}`, type: "user", content: topic }
    ]);
    // Trigger generation with FullPipelineRequest
    generate({ topic });
  };

  // Handle try again
  const handleTryAgain = () => {
    reset();
    setMessages([]);
  };

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

  const handleExplore = (prompt: string) => {
    // Add as new user message and generate
    handleSend(prompt);
  };

  return (
    <div className="min-h-screen bg-white">
      <Navbar />

      <main className="pb-40 pt-20">
        <MessageArea>
          {/* Empty state when no messages */}
          {messages.length === 0 && !isLoading && !result && !error && (
            <EmptyState />
          )}

          {/* Message history */}
          <div className="space-y-6">
            {messages.map((message) => (
              <div key={message.id} className={`flex ${message.type === "user" ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                    message.type === "user"
                      ? "bg-blue-500 text-white"
                      : "bg-gray-100 text-gray-900"
                  }`}
                >
                  <p>{message.content}</p>
                </div>
              </div>
            ))}

            {/* Loading indicator */}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-2xl px-4 py-3">
                  <div className="flex items-center gap-3">
                    <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
                    <div className="text-gray-600">
                      {progress ? (
                        <span>
                          {progress.stage === "generating_pedagogical_intent" && "Understanding your topic..."}
                          {progress.stage === "generating_manim_prompt" && "Creating visual explanations..."}
                          {progress.stage === "generating_video" && "Generating animations..."}
                          {progress.stage === "generating_animation_clips" && "Creating animation clips..."}
                          {progress.stage === "pending" && "Starting..."}
                          {!["generating_pedagogical_intent", "generating_manim_prompt", "generating_video", "generating_animation_clips", "pending"].includes(progress.stage) && progress.message}
                        </span>
                      ) : (
                        <span>Generating your lesson...</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Error state */}
            {error && !isLoading && (
              <div className="flex justify-start">
                <Card className="max-w-[85%] border-red-200 bg-red-50">
                  <CardContent className="py-4">
                    <div className="flex items-start gap-3">
                      <AlertCircle className="w-5 h-5 text-red-500 mt-0.5" />
                      <div>
                        <p className="text-red-700 font-medium">Something went wrong</p>
                        <p className="text-red-600 text-sm mt-1">{error}</p>
                        <Button
                          variant="outline"
                          size="sm"
                          className="mt-3"
                          onClick={handleTryAgain}
                        >
                          Try Again
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Lesson content as assistant response */}
            {result && !isLoading && (
              <div className="space-y-6">
                {/* Assistant response bubble with lesson content */}
                <div className="flex justify-start">
                  <div className="bg-gray-100 rounded-2xl px-5 py-4 max-w-full">
                    {/* Summary */}
                    {result.pedagogy && (
                      <div className="space-y-4">
                        <p className="text-gray-800 leading-relaxed">
                          {result.pedagogy.summary}
                        </p>

                        {/* Video */}
                        {result.video && (
                          <div className="rounded-lg overflow-hidden bg-gray-900">
                            <VideoPlayer video={result.video} jobId={result.job_id} />
                          </div>
                        )}

                        {/* Sections */}
                        {result.pedagogy.sections && result.pedagogy.sections.length > 0 && (
                          <DynamicSectionRenderer
                            sections={result.pedagogy.sections}
                            clips={result.clips}
                            jobId={result.job_id}
                          />
                        )}
                      </div>
                    )}
                  </div>
                </div>

                {/* Quiz section */}
                {enhancedQuiz && (
                  <div className="space-y-3">
                    <h3 className="text-base font-medium text-gray-700">
                      Quick Quiz
                    </h3>
                    <EnhancedQuizSection quiz={enhancedQuiz} />
                  </div>
                )}

                {/* Explore Deeper */}
                {explorePrompts.length > 0 && (
                  <ExploreDeeper prompts={explorePrompts} onExplore={handleExplore} />
                )}
              </div>
            )}

            {/* Scroll anchor */}
            <div ref={messagesEndRef} />
          </div>
        </MessageArea>
      </main>

      <ChatInput
        onSend={handleSend}
        isLoading={isLoading}
        placeholder="What would you like to learn?"
      />
    </div>
  );
}
