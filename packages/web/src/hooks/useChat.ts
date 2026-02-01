"use client";

import { useState, useCallback, useRef, useEffect } from "react";

const API_BASE = "http://localhost:8000";

// ============ Types ============

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  animations?: string[];  // Video URLs from animation tool
  isStreaming?: boolean;
}

export interface PendingAnimation {
  id: string;
  tool: string;
  concept?: string;
}

export interface ChatState {
  messages: ChatMessage[];
  isStreaming: boolean;
  pendingAnimations: PendingAnimation[];
  sessionId: string | null;
  error: string | null;
}

// SSE Event types from the backend
interface TextEvent {
  type: "text";
  content: string;
}

interface ToolStartEvent {
  type: "tool_start";
  tool: string;
  id: string;
  arguments?: Record<string, unknown>;
}

interface ToolResultEvent {
  type: "tool_result";
  tool: string;
  id: string;
  success: boolean;
  result: {
    video_url?: string;
    video_path?: string;
    error?: string;
  };
  error?: string;
}

interface DoneEvent {
  type: "done";
  session_id: string;
}

interface ErrorEvent {
  type: "error";
  message: string;
}

type SSEEvent = TextEvent | ToolStartEvent | ToolResultEvent | DoneEvent | ErrorEvent;

// ============ Hook ============

export function useChat() {
  const [state, setState] = useState<ChatState>({
    messages: [],
    isStreaming: false,
    pendingAnimations: [],
    sessionId: null,
    error: null,
  });

  const abortControllerRef = useRef<AbortController | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  // Generate unique message ID
  const generateId = () => `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

  // Cleanup function
  const cleanup = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => cleanup();
  }, [cleanup]);

  // Send a message
  const sendMessage = useCallback(async (content: string) => {
    // Cleanup any existing streams
    cleanup();

    // Add user message
    const userMessage: ChatMessage = {
      id: generateId(),
      role: "user",
      content,
      timestamp: new Date(),
    };

    // Create placeholder for assistant response
    const assistantMessage: ChatMessage = {
      id: generateId(),
      role: "assistant",
      content: "",
      timestamp: new Date(),
      animations: [],
      isStreaming: true,
    };

    setState((prev) => ({
      ...prev,
      messages: [...prev.messages, userMessage, assistantMessage],
      isStreaming: true,
      error: null,
    }));

    try {
      // Create abort controller for fetch
      abortControllerRef.current = new AbortController();

      // Use fetch with POST for SSE (EventSource only supports GET)
      const response = await fetch(`${API_BASE}/api/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: content,
          session_id: state.sessionId,
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("No response body");
      }

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Process complete SSE events (separated by double newlines)
        const events = buffer.split("\n\n");
        buffer = events.pop() || "";  // Keep incomplete event in buffer

        for (const eventStr of events) {
          if (!eventStr.trim()) continue;

          // Parse SSE format: "data: {...}"
          const lines = eventStr.split("\n");
          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data: SSEEvent = JSON.parse(line.slice(6));
                handleSSEEvent(data, assistantMessage.id);
              } catch (e) {
                console.error("Failed to parse SSE event:", e);
              }
            }
          }
        }
      }
    } catch (error) {
      if ((error as Error).name === "AbortError") {
        return; // Cancelled, don't update state
      }

      const errorMessage = error instanceof Error ? error.message : "Unknown error";
      setState((prev) => ({
        ...prev,
        isStreaming: false,
        error: errorMessage,
        messages: prev.messages.map((msg) =>
          msg.id === assistantMessage.id
            ? { ...msg, isStreaming: false }
            : msg
        ),
      }));
    }
  }, [state.sessionId, cleanup]);

  // Handle SSE events
  const handleSSEEvent = useCallback((event: SSEEvent, messageId: string) => {
    switch (event.type) {
      case "text":
        // Append text to the assistant message
        setState((prev) => ({
          ...prev,
          messages: prev.messages.map((msg) =>
            msg.id === messageId
              ? { ...msg, content: msg.content + event.content }
              : msg
          ),
        }));
        break;

      case "tool_start":
        // Add to pending animations
        setState((prev) => ({
          ...prev,
          pendingAnimations: [
            ...prev.pendingAnimations,
            {
              id: event.id,
              tool: event.tool,
              concept: (event.arguments as { concept?: string })?.concept,
            },
          ],
        }));
        break;

      case "tool_result":
        // Remove from pending, add video URL if successful
        setState((prev) => ({
          ...prev,
          pendingAnimations: prev.pendingAnimations.filter(
            (a) => a.id !== event.id
          ),
          messages: prev.messages.map((msg) =>
            msg.id === messageId && event.success && event.result.video_url
              ? {
                  ...msg,
                  animations: [...(msg.animations || []), event.result.video_url],
                }
              : msg
          ),
        }));
        break;

      case "done":
        // Stream complete
        setState((prev) => ({
          ...prev,
          isStreaming: false,
          sessionId: event.session_id,
          messages: prev.messages.map((msg) =>
            msg.id === messageId
              ? { ...msg, isStreaming: false }
              : msg
          ),
        }));
        break;

      case "error":
        setState((prev) => ({
          ...prev,
          isStreaming: false,
          error: event.message,
          messages: prev.messages.map((msg) =>
            msg.id === messageId
              ? { ...msg, isStreaming: false }
              : msg
          ),
        }));
        break;
    }
  }, []);

  // Reset the chat
  const reset = useCallback(() => {
    cleanup();
    setState({
      messages: [],
      isStreaming: false,
      pendingAnimations: [],
      sessionId: null,
      error: null,
    });
  }, [cleanup]);

  // Cancel current stream
  const cancel = useCallback(() => {
    cleanup();
    setState((prev) => ({
      ...prev,
      isStreaming: false,
      messages: prev.messages.map((msg) =>
        msg.isStreaming ? { ...msg, isStreaming: false } : msg
      ),
    }));
  }, [cleanup]);

  return {
    ...state,
    sendMessage,
    reset,
    cancel,
  };
}
