"use client";

import { useState, useRef, useCallback, useEffect } from "react";

interface UseSmartScrollOptions {
  threshold?: number;
  dependencies?: unknown[];
}

export function useSmartScroll({
  threshold = 100,
  dependencies = [],
}: UseSmartScrollOptions = {}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [showScrollButton, setShowScrollButton] = useState(false);
  const isUserScrolling = useRef(false);
  const isAtBottom = useRef(true);

  const checkIfAtBottom = useCallback(() => {
    const container = containerRef.current;
    if (!container) return true;
    const { scrollTop, scrollHeight, clientHeight } = container;
    return scrollHeight - scrollTop - clientHeight <= threshold;
  }, [threshold]);

  const handleScroll = useCallback(() => {
    const container = containerRef.current;
    if (!container) return;

    const atBottom = checkIfAtBottom();

    // Detect user scrolling up
    if (!atBottom) {
      isUserScrolling.current = true;
    }

    // User scrolled back to bottom
    if (atBottom) {
      isUserScrolling.current = false;
    }

    isAtBottom.current = atBottom;
    setShowScrollButton(!atBottom);
  }, [checkIfAtBottom]);

  const scrollToBottom = useCallback((smooth = true) => {
    const container = containerRef.current;
    if (!container) return;

    isUserScrolling.current = false;
    container.scrollTo({
      top: container.scrollHeight,
      behavior: smooth ? "smooth" : "instant",
    });
  }, []);

  // Auto-scroll when dependencies change (only if user hasn't scrolled up)
  useEffect(() => {
    if (!isUserScrolling.current) {
      requestAnimationFrame(() => {
        scrollToBottom(true);
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, dependencies);

  // Attach scroll listener
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    container.addEventListener("scroll", handleScroll, { passive: true });
    return () => container.removeEventListener("scroll", handleScroll);
  }, [handleScroll]);

  return {
    containerRef,
    showScrollButton,
    scrollToBottom,
  };
}
