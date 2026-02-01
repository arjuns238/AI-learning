"use client";

import { useState, useRef, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useChat, ChatMessage, PendingAnimation } from "@/hooks/useChat";
import { Loader2, Send, Sparkles, Video } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";

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
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when messages update
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, pendingAnimations]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;

    sendMessage(input.trim());
    setInput("");
  };

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* Header */}
      <header className="border-b px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-semibold text-gray-900">Learning Assistant</h1>
              <p className="text-sm text-gray-500">
                {sessionId ? `Session: ${sessionId.slice(0, 8)}...` : "New session"}
              </p>
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={reset}>
            New Chat
          </Button>
        </div>
      </header>

      {/* Messages Area */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-6 py-8">
          {/* Empty state */}
          {messages.length === 0 && (
            <div className="text-center py-20">
              <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-gradient-to-br from-blue-100 to-purple-100 flex items-center justify-center">
                <Sparkles className="w-10 h-10 text-blue-500" />
              </div>
              <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                What would you like to learn?
              </h2>
              <p className="text-gray-500 max-w-md mx-auto">
                Ask me about any technical concept - machine learning, math, algorithms, and more. I can explain with text and generate animations when they help.
              </p>

              {/* Suggested prompts */}
              <div className="mt-8 flex flex-wrap justify-center gap-3">
                {[
                  "Explain gradient descent",
                  "How does backpropagation work?",
                  "What is a neural network?",
                  "Explain matrix multiplication visually",
                ].map((prompt) => (
                  <Button
                    key={prompt}
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setInput(prompt);
                      sendMessage(prompt);
                    }}
                    className="text-gray-600"
                  >
                    {prompt}
                  </Button>
                ))}
              </div>
            </div>
          )}

          {/* Messages */}
          <div className="space-y-6">
            {messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
                pendingAnimations={
                  message.role === "assistant" && message.isStreaming
                    ? pendingAnimations
                    : []
                }
              />
            ))}

            {/* Scroll anchor */}
            <div ref={messagesEndRef} />
          </div>
        </div>
      </main>

      {/* Error display */}
      {error && (
        <div className="max-w-4xl mx-auto px-6 pb-4">
          <Card className="border-red-200 bg-red-50">
            <CardContent className="py-3">
              <p className="text-red-600 text-sm">{error}</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Input area */}
      <div className="border-t bg-white">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <form onSubmit={handleSubmit} className="flex gap-3">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question..."
              disabled={isStreaming}
              className="flex-1"
            />
            <Button
              type="submit"
              disabled={!input.trim() || isStreaming}
              className="px-4"
            >
              {isStreaming ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}

// Message Bubble Component
function MessageBubble({
  message,
  pendingAnimations,
}: {
  message: ChatMessage;
  pendingAnimations: PendingAnimation[];
}) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-5 py-4 ${
          isUser
            ? "bg-blue-500 text-white"
            : "bg-gray-100 text-gray-900"
        }`}
      >
        {/* Message content */}
        {isUser ? (
          <p>{message.content}</p>
        ) : (
          <div className="prose prose-sm max-w-none">
            <ReactMarkdown
              remarkPlugins={[remarkMath]}
              rehypePlugins={[rehypeKatex]}
            >
              {message.content}
            </ReactMarkdown>

            {/* Streaming indicator */}
            {message.isStreaming && (
              <span className="inline-block w-2 h-4 bg-gray-400 animate-pulse ml-1" />
            )}
          </div>
        )}

        {/* Pending animations */}
        {pendingAnimations.length > 0 && (
          <div className="mt-4 space-y-2">
            {pendingAnimations.map((anim) => (
              <div
                key={anim.id}
                className="flex items-center gap-2 text-sm text-gray-500 bg-white/50 rounded-lg px-3 py-2"
              >
                <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
                <span>Generating animation{anim.concept ? `: ${anim.concept}` : ""}...</span>
              </div>
            ))}
          </div>
        )}

        {/* Completed animations */}
        {message.animations && message.animations.length > 0 && (
          <div className="mt-4 space-y-3">
            {message.animations.map((videoUrl, idx) => (
              <div
                key={`${message.id}-video-${idx}`}
                className="rounded-lg overflow-hidden bg-gray-900"
              >
                <div className="flex items-center gap-2 px-3 py-2 bg-gray-800 text-gray-300 text-sm">
                  <Video className="w-4 h-4" />
                  <span>Animation</span>
                </div>
                <video
                  src={videoUrl}
                  controls
                  className="w-full"
                  autoPlay
                  muted
                />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
