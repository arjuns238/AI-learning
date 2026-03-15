"use client";

import { useState, useRef, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import type { QAMessage } from "@/types/pipeline";

type ContextualQABoxProps = {
  lessonId: string;
  topic: string;
  isMinimized?: boolean;
  onToggleMinimize?: () => void;
};

export function ContextualQABox({
  lessonId,
  topic,
  isMinimized: initialMinimized = true,
  onToggleMinimize,
}: ContextualQABoxProps) {
  const [isMinimized, setIsMinimized] = useState(initialMinimized);
  const [question, setQuestion] = useState("");
  const [conversation, setConversation] = useState<QAMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [conversation]);

  useEffect(() => {
    if (!isMinimized && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isMinimized]);

  const handleToggle = () => {
    const newState = !isMinimized;
    setIsMinimized(newState);
    onToggleMinimize?.();
  };

  const askQuestion = async () => {
    if (!question.trim() || isLoading) return;

    const userQuestion = question.trim();
    setQuestion("");
    setError(null);

    // Add user message immediately
    setConversation((prev) => [...prev, { role: "user", content: userQuestion }]);
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE}/api/lessons/qa/${lessonId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lesson_id: lessonId, question: userQuestion }),
      });

      if (!response.ok) {
        throw new Error("Failed to get answer");
      }

      const data = await response.json();

      setConversation((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.answer,
          followups: data.suggested_followups,
        },
      ]);
    } catch (err) {
      setError("Unable to get an answer. The Q&A service may not be available yet.");
      // Remove the user's message if the request failed
      setConversation((prev) => prev.slice(0, -1));
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      askQuestion();
    }
  };

  const handleFollowup = (followupQuestion: string) => {
    setQuestion(followupQuestion);
    inputRef.current?.focus();
  };

  if (isMinimized) {
    return (
      <button
        onClick={handleToggle}
        className={cn(
          "fixed bottom-6 right-6 z-50",
          "flex items-center gap-2 rounded-full bg-blue-600 px-4 py-3 text-white shadow-lg",
          "hover:bg-blue-700 transition-colors",
          "animate-in slide-in-from-bottom-4 duration-300"
        )}
      >
        <svg
          className="h-5 w-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
          />
        </svg>
        <span className="text-sm font-medium">Ask a question</span>
      </button>
    );
  }

  return (
    <div
      className={cn(
        "fixed bottom-6 right-6 z-50 w-96",
        "animate-in slide-in-from-bottom-4 duration-300"
      )}
    >
      <Card className="shadow-xl border-slate-200">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm">
              Questions about {topic}?
            </CardTitle>
            <button
              onClick={handleToggle}
              className="rounded-full p-1 hover:bg-slate-100 transition-colors"
            >
              <svg
                className="h-5 w-5 text-slate-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {/* Conversation history */}
          <div className="max-h-64 overflow-y-auto space-y-3 pr-1">
            {conversation.length === 0 && (
              <p className="text-sm text-slate-500 text-center py-4">
                Ask any clarifying question about this lesson
              </p>
            )}

            {conversation.map((msg, i) => (
              <div
                key={i}
                className={cn(
                  "rounded-lg p-3 text-sm",
                  msg.role === "user"
                    ? "bg-blue-50 text-blue-900 ml-8"
                    : "bg-slate-50 text-slate-700 mr-4"
                )}
              >
                <p className="whitespace-pre-wrap">{msg.content}</p>

                {/* Followup suggestions */}
                {msg.role === "assistant" && msg.followups && msg.followups.length > 0 && (
                  <div className="mt-3 space-y-1">
                    <p className="text-xs font-medium text-slate-500">Related questions:</p>
                    {msg.followups.map((f, j) => (
                      <button
                        key={j}
                        onClick={() => handleFollowup(f)}
                        className="block w-full text-left text-xs text-blue-600 hover:text-blue-800 hover:underline"
                      >
                        → {f}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}

            {isLoading && (
              <div className="bg-slate-50 rounded-lg p-3 mr-4">
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-slate-400 animate-pulse" />
                  <div className="h-2 w-2 rounded-full bg-slate-400 animate-pulse delay-75" />
                  <div className="h-2 w-2 rounded-full bg-slate-400 animate-pulse delay-150" />
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Error message */}
          {error && (
            <p className="text-xs text-amber-600 bg-amber-50 rounded p-2">{error}</p>
          )}

          {/* Input */}
          <div className="flex gap-2">
            <Input
              ref={inputRef}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your question..."
              className="text-sm"
              disabled={isLoading}
            />
            <Button
              onClick={askQuestion}
              disabled={isLoading || !question.trim()}
              size="sm"
              className="shrink-0"
            >
              {isLoading ? (
                <svg
                  className="h-4 w-4 animate-spin"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                  />
                </svg>
              ) : (
                "Ask"
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
