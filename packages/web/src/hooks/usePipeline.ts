"use client";

import { useState, useCallback, useRef } from "react";
import type {
  FullPipelineRequest,
  FullPipelineResponse,
  PipelineProgress,
  AsyncJobResponse,
  JobStatusResponse,
} from "@/types/pipeline";

const API_BASE = "http://localhost:8000";
const POLL_INTERVAL = 1000; // 1 second

export type PipelineState = {
  isLoading: boolean;
  progress: PipelineProgress | null;
  result: FullPipelineResponse | null;
  error: string | null;
};

export function usePipeline() {
  const [state, setState] = useState<PipelineState>({
    isLoading: false,
    progress: null,
    result: null,
    error: null,
  });

  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const clearPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  }, []);

  const reset = useCallback(() => {
    clearPolling();
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setState({
      isLoading: false,
      progress: null,
      result: null,
      error: null,
    });
  }, [clearPolling]);

  /**
   * Generate content using the async endpoint with polling.
   * Better for long-running operations with progress updates.
   */
  const generateAsync = useCallback(async (request: FullPipelineRequest) => {
    reset();
    setState((prev) => ({ ...prev, isLoading: true }));

    abortControllerRef.current = new AbortController();

    try {
      // Start async job
      const startResponse = await fetch(
        `${API_BASE}/api/pipeline/generate/async`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(request),
          signal: abortControllerRef.current.signal,
        }
      );

      if (!startResponse.ok) {
        const errorData = await startResponse.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${startResponse.status}`);
      }

      const { job_id }: AsyncJobResponse = await startResponse.json();

      // Poll for status
      return new Promise<FullPipelineResponse>((resolve, reject) => {
        const pollStatus = async () => {
          try {
            const statusResponse = await fetch(
              `${API_BASE}/api/pipeline/status/${job_id}`,
              { signal: abortControllerRef.current?.signal }
            );

            if (!statusResponse.ok) {
              throw new Error(`Status check failed: ${statusResponse.status}`);
            }

            const status: JobStatusResponse = await statusResponse.json();

            if (status.status === "completed") {
              clearPolling();
              setState({
                isLoading: false,
                progress: null,
                result: status.result,
                error: status.result.error_message || null,
              });
              resolve(status.result);
            } else if (status.status === "failed") {
              clearPolling();
              setState({
                isLoading: false,
                progress: status.progress,
                result: null,
                error: status.error,
              });
              reject(new Error(status.error));
            } else if (status.status === "in_progress") {
              setState((prev) => ({
                ...prev,
                progress: status.progress,
              }));
            }
          } catch (err) {
            if ((err as Error).name === "AbortError") {
              return; // Cancelled, don't reject
            }
            clearPolling();
            const errorMessage =
              err instanceof Error ? err.message : "Polling failed";
            setState((prev) => ({
              ...prev,
              isLoading: false,
              error: errorMessage,
            }));
            reject(err);
          }
        };

        // Start polling
        pollStatus(); // Initial check
        pollIntervalRef.current = setInterval(pollStatus, POLL_INTERVAL);
      });
    } catch (err) {
      if ((err as Error).name === "AbortError") {
        return undefined as unknown as FullPipelineResponse;
      }
      const errorMessage = err instanceof Error ? err.message : "Unknown error";
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }));
      throw err;
    }
  }, [reset, clearPolling]);

  /**
   * Default generate method - uses async with polling for progress.
   */
  const generate = generateAsync;

  return {
    ...state,
    generate,
    generateAsync,
    reset,
  };
}
