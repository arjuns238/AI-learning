"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useChat, ChatMessage, PendingAnimation } from "@/hooks/useChat";
import { useSmartScroll } from "@/hooks/useSmartScroll";
import {
  ArrowUp,
  BookOpen,
  Loader2,
  RotateCcw,
  Video,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";

// Custom sparkle icon matching the reference image
function SparkleIcon({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      {/* Main 4-point star */}
      <path d="M12 3v18M3 12h18M5.6 5.6l12.8 12.8M18.4 5.6L5.6 18.4" />
    </svg>
  );
}

// Animated sparkle with small accent star
function AnimatedSparkle({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className={className}
    >
      {/* Main star */}
      <path
        d="M12 2L13.5 8.5L20 10L13.5 11.5L12 18L10.5 11.5L4 10L10.5 8.5L12 2Z"
        fill="currentColor"
      />
      {/* Small accent star */}
      <path
        d="M19 2L19.5 4L21.5 4.5L19.5 5L19 7L18.5 5L16.5 4.5L18.5 4L19 2Z"
        fill="currentColor"
        opacity="0.6"
      />
    </svg>
  );
}

export default function ChatPage() {
  const {
    messages,
    isStreaming,
    pendingAnimations,
    sessionId,
    error,
    sendMessage,
    reset,
  } = useChat();

  const [input, setInput] = useState("");

  const { containerRef } = useSmartScroll({
    threshold: 100,
    dependencies: [messages, pendingAnimations],
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;

    sendMessage(input.trim());
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Minimal Header */}
      <header className="flex-shrink-0 border-b border-border/60 bg-background/80 backdrop-blur-sm">
        <div className="max-w-3xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="relative">
                <div className="w-9 h-9 rounded-xl bg-secondary flex items-center justify-center">
                  <BookOpen className="w-4 h-4 text-foreground/70" />
                </div>
                {sessionId && (
                  <div className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-primary border-2 border-background" />
                )}
              </div>
              <div>
                <h1 className="font-semibold text-foreground tracking-tight">
                  Lesson Loom
                </h1>
                <p className="text-xs text-muted-foreground">
                  {sessionId ? "Session active" : "Ready to learn"}
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={reset}
              className="text-muted-foreground hover:text-foreground gap-1.5"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">New chat</span>
            </Button>
          </div>
        </div>
      </header>

      {/* Messages Area - scrollable */}
      <main className="flex-1 overflow-hidden relative">
        <div
          ref={containerRef}
          className="h-full overflow-y-auto"
        >
          <div className="max-w-3xl mx-auto px-6 py-8 pb-36">
            {/* Empty state */}
            {messages.length === 0 && (
              <div className="animate-fade-in-up">
                <div className="text-center py-16">
                  {/* Icon */}
                  <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-secondary mb-6">
                    <AnimatedSparkle className="w-6 h-6 text-foreground/70" />
                  </div>

                  {/* Title */}
                  <h2 className="text-2xl font-semibold text-foreground mb-3 tracking-tight">
                    What would you like to learn?
                  </h2>

                  {/* Description */}
                  <p className="text-muted-foreground max-w-md mx-auto leading-relaxed">
                    Ask about any technical concept. I&apos;ll explain it clearly and
                    generate visual animations when they help illustrate the idea.
                  </p>

                  {/* Suggested prompts */}
                  <div className="mt-10 flex flex-wrap justify-center gap-2">
                    {[
                      "Explain gradient descent",
                      "How does backpropagation work?",
                      "What is a neural network?",
                      "Explain matrix multiplication",
                    ].map((prompt, index) => (
                      <button
                        key={prompt}
                        onClick={() => {
                          setInput(prompt);
                          sendMessage(prompt);
                        }}
                        className="group px-4 py-2.5 rounded-full border border-border hover:border-primary/30 bg-card hover:bg-secondary/50 transition-all duration-200 text-sm text-muted-foreground hover:text-foreground"
                        style={{ animationDelay: `${index * 75}ms` }}
                      >
                        {prompt}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Messages */}
            <div className="space-y-8">
              {messages.map((message, index) => (
                <MessageRow
                  key={message.id}
                  message={message}
                  pendingAnimations={
                    message.role === "assistant" && message.isStreaming
                      ? pendingAnimations
                      : []
                  }
                  isLatest={index === messages.length - 1}
                />
              ))}
            </div>
          </div>
        </div>

      </main>

      {/* Error display */}
      {error && (
        <div className="fixed bottom-32 left-1/2 -translate-x-1/2 z-20 max-w-md w-full px-6">
          <Card className="border-destructive/30 bg-destructive/5 shadow-lg">
            <CardContent className="py-3 px-4">
              <p className="text-destructive text-sm">{error}</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Fixed Input Area */}
      <div className="fixed bottom-0 left-0 right-0 z-10">
        {/* Gradient fade */}
        <div className="h-12 bg-gradient-to-t from-background via-background/80 to-transparent pointer-events-none" />

        {/* Input container */}
        <div className="bg-background pb-6 pt-0">
          <div className="max-w-3xl mx-auto px-6">
            <form onSubmit={handleSubmit} className="relative">
              {/* Pill-shaped input container */}
              <div className="relative flex items-center gap-2 p-1.5 pl-2 rounded-full bg-card border border-border shadow-sm focus-within:border-primary/30 focus-within:shadow-md transition-all duration-200">
                {/* Textarea */}
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask a question..."
                  disabled={isStreaming}
                  rows={1}
                  className="flex-1 resize-none bg-transparent py-2.5 pl-4 text-foreground placeholder:text-muted-foreground/50 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed text-[15px] leading-relaxed max-h-32 overflow-y-auto"
                  style={{
                    minHeight: "40px",
                    height: "auto",
                  }}
                  onInput={(e) => {
                    const target = e.target as HTMLTextAreaElement;
                    target.style.height = "auto";
                    target.style.height = `${Math.min(target.scrollHeight, 128)}px`;
                  }}
                />

                {/* Submit button - circular to match pill shape */}
                <button
                  type="submit"
                  disabled={!input.trim() || isStreaming}
                  className="flex-shrink-0 w-9 h-9 rounded-full bg-primary text-primary-foreground flex items-center justify-center disabled:opacity-30 disabled:cursor-not-allowed hover:bg-primary/90 active:scale-95 transition-all duration-150"
                >
                  {isStreaming ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <ArrowUp className="w-4 h-4" />
                  )}
                </button>
              </div>

              {/* Helper text */}
              <p className="text-[11px] text-muted-foreground/40 text-center mt-2.5">
                Enter to send · Shift + Enter for new line
              </p>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}

// Message Row Component
function MessageRow({
  message,
  pendingAnimations,
  isLatest,
}: {
  message: ChatMessage;
  pendingAnimations: PendingAnimation[];
  isLatest: boolean;
}) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="chat-message-user flex justify-end">
        <div className="max-w-[85%]">
          <div className="bg-secondary rounded-2xl rounded-br-md px-4 py-3">
            <p className="text-foreground whitespace-pre-wrap leading-relaxed">
              {message.content}
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Assistant message
  const hasAnimations =
    (message.animations && message.animations.length > 0) ||
    pendingAnimations.length > 0;

  return (
    <div className="chat-message-assistant">
      <div className="flex gap-3">
        {/* Icon - clean sparkle in rounded square */}
        <div className="flex-shrink-0 pt-1">
          <div className="w-8 h-8 rounded-xl bg-secondary flex items-center justify-center">
            <AnimatedSparkle className="w-4 h-4 text-foreground/60" />
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0 space-y-4">
          {/* Main content */}
          {message.content && (
            <div className="prose max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkMath]}
                rehypePlugins={[rehypeKatex]}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}

          {/* Pending animations */}
          {pendingAnimations.length > 0 && (
            <div className="space-y-3">
              {pendingAnimations.map((anim) => (
                <div
                  key={anim.id}
                  className="rounded-xl bg-secondary/50 aspect-video max-w-2xl flex items-center justify-center animate-shimmer"
                >
                  <div className="flex flex-col items-center gap-3 text-muted-foreground">
                    <div className="w-10 h-10 rounded-xl bg-card flex items-center justify-center">
                      <Loader2 className="w-5 h-5 animate-spin text-primary" />
                    </div>
                    <span className="text-sm font-medium">
                      {anim.concept
                        ? `Generating: ${anim.concept}`
                        : "Generating animation..."}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Completed animations */}
          {message.animations && message.animations.length > 0 && (
            <div className="space-y-4">
              {message.animations.map((videoUrl, idx) => (
                <div
                  key={`${message.id}-video-${idx}`}
                  className="rounded-xl overflow-hidden bg-[#101014] max-w-2xl shadow-lg"
                  style={{ contain: "layout" }}
                >
                  <div className="flex items-center gap-2 px-4 py-2.5 bg-[#18181c] text-gray-400 text-sm border-b border-white/5">
                    <Video className="w-4 h-4" />
                    <span className="font-medium">Animation</span>
                  </div>
                  <video
                    src={videoUrl}
                    controls
                    className="w-full aspect-video object-contain"
                    autoPlay
                    muted
                    playsInline
                  />
                </div>
              ))}
            </div>
          )}

          {/* Post-animation content */}
          {message.postAnimationContent && (
            <div className="prose max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkMath]}
                rehypePlugins={[rehypeKatex]}
              >
                {message.postAnimationContent}
              </ReactMarkdown>
            </div>
          )}

          {/* Streaming cursor */}
          {message.isStreaming && isLatest && (
            <span className="inline-block w-0.5 h-5 bg-foreground/70 animate-pulse-soft align-middle ml-0.5" />
          )}
        </div>
      </div>
    </div>
  );
}
