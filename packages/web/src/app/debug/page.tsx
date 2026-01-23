"use client";

import { useState, useEffect } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const API_BASE = "http://localhost:8000";

interface DebugJob {
  job_id: string;
  topic: string;
  status: string;
  total_duration_seconds?: number;
  created_at: string;
}

interface LayerData {
  name: string;
  input: Record<string, unknown> | null;
  output: Record<string, unknown> | null;
  duration_seconds: number | null;
  error: string | null;
}

interface DebugJobDetail {
  job_id: string;
  topic: string;
  status: string;
  created_at: string;
  updated_at: string;
  total_duration_seconds: number | null;
  final_video_path: string | null;
  layers: {
    layer1: LayerData;
    layer2: LayerData;
    layer3: LayerData;
    layer4: LayerData;
  };
}

export default function DebugPage() {
  const [jobs, setJobs] = useState<DebugJob[]>([]);
  const [selectedJob, setSelectedJob] = useState<DebugJobDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedLayers, setExpandedLayers] = useState<Set<string>>(new Set());

  // Fetch jobs list on mount
  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/api/pipeline/debug`);
      if (!response.ok) {
        throw new Error(`Failed to fetch jobs: ${response.status}`);
      }
      const data = await response.json();
      setJobs(data.jobs || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch jobs");
    } finally {
      setLoading(false);
    }
  };

  const fetchJobDetail = async (jobId: string) => {
    setLoadingDetail(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/api/pipeline/debug/${jobId}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch job detail: ${response.status}`);
      }
      const data = await response.json();
      setSelectedJob(data);
      setExpandedLayers(new Set()); // Reset expanded state
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch job detail");
    } finally {
      setLoadingDetail(false);
    }
  };

  const toggleLayer = (layerKey: string) => {
    setExpandedLayers((prev) => {
      const next = new Set(prev);
      if (next.has(layerKey)) {
        next.delete(layerKey);
      } else {
        next.add(layerKey);
      }
      return next;
    });
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, "default" | "outline" | "soft"> = {
      completed: "soft",
      failed: "outline",
      pending: "outline",
      in_progress: "soft",
    };
    const colors: Record<string, string> = {
      completed: "bg-green-100 text-green-800 border-green-200",
      failed: "bg-red-100 text-red-800 border-red-200",
      pending: "bg-yellow-100 text-yellow-800 border-yellow-200",
      in_progress: "bg-blue-100 text-blue-800 border-blue-200",
    };
    return (
      <Badge variant={variants[status] || "outline"} className={colors[status] || ""}>
        {status}
      </Badge>
    );
  };

  const formatDuration = (seconds: number | null | undefined) => {
    if (seconds === null || seconds === undefined) return "—";
    return `${seconds.toFixed(2)}s`;
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString();
  };

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_#fff7e9,_#f7f2ea_55%,_#efe7db_100%)] text-slate-900">
      <main className="mx-auto flex w-full max-w-7xl flex-col gap-8 px-6 py-12 lg:px-12">
        {/* Header */}
        <section className="space-y-4">
          <Badge variant="soft">Pipeline Inspector</Badge>
          <h1 className="font-serif text-3xl font-semibold sm:text-4xl">
            Debug Dashboard
          </h1>
          <p className="text-slate-600">
            Inspect layer-by-layer inputs and outputs for each video generation job.
          </p>
        </section>

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-800">
            {error}
          </div>
        )}

        <div className="grid gap-8 lg:grid-cols-[380px_1fr]">
          {/* Jobs List */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-medium">Recent Jobs</h2>
              <Button variant="outline" size="sm" onClick={fetchJobs} disabled={loading}>
                {loading ? "Loading..." : "Refresh"}
              </Button>
            </div>

            <div className="space-y-2">
              {loading ? (
                <Card>
                  <CardContent className="py-8 text-center text-slate-500">
                    Loading jobs...
                  </CardContent>
                </Card>
              ) : jobs.length === 0 ? (
                <Card>
                  <CardContent className="py-8 text-center text-slate-500">
                    No debug jobs found. Generate a video first!
                  </CardContent>
                </Card>
              ) : (
                jobs.map((job) => (
                  <Card
                    key={job.job_id}
                    className={`cursor-pointer transition-all hover:border-slate-300 hover:shadow-md ${
                      selectedJob?.job_id === job.job_id
                        ? "border-slate-400 bg-white shadow-md"
                        : ""
                    }`}
                    onClick={() => fetchJobDetail(job.job_id)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0 flex-1">
                          <p className="truncate font-medium">{job.topic}</p>
                          <p className="text-xs text-slate-500">
                            {job.job_id} • {formatDate(job.created_at)}
                          </p>
                        </div>
                        {getStatusBadge(job.status)}
                      </div>
                      {job.total_duration_seconds && (
                        <p className="mt-2 text-xs text-slate-500">
                          Duration: {formatDuration(job.total_duration_seconds)}
                        </p>
                      )}
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </div>

          {/* Job Detail */}
          <div className="space-y-6">
            {loadingDetail ? (
              <Card>
                <CardContent className="py-12 text-center text-slate-500">
                  Loading job details...
                </CardContent>
              </Card>
            ) : !selectedJob ? (
              <Card>
                <CardContent className="py-12 text-center text-slate-500">
                  Select a job to view layer details
                </CardContent>
              </Card>
            ) : (
              <>
                {/* Job Summary */}
                <Card>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-xl">{selectedJob.topic}</CardTitle>
                        <p className="mt-1 text-sm text-slate-500">
                          Job ID: {selectedJob.job_id}
                        </p>
                      </div>
                      {getStatusBadge(selectedJob.status)}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
                      <div>
                        <p className="text-slate-500">Created</p>
                        <p className="font-medium">{formatDate(selectedJob.created_at)}</p>
                      </div>
                      <div>
                        <p className="text-slate-500">Updated</p>
                        <p className="font-medium">{formatDate(selectedJob.updated_at)}</p>
                      </div>
                      <div>
                        <p className="text-slate-500">Total Duration</p>
                        <p className="font-medium">
                          {formatDuration(selectedJob.total_duration_seconds)}
                        </p>
                      </div>
                      <div>
                        <p className="text-slate-500">Video Path</p>
                        <p className="truncate font-medium">
                          {selectedJob.final_video_path || "—"}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Layers */}
                {Object.entries(selectedJob.layers).map(([key, layer]) => (
                  <Card key={key}>
                    <CardHeader
                      className="cursor-pointer"
                      onClick={() => toggleLayer(key)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div
                            className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold ${
                              layer.error
                                ? "bg-red-100 text-red-700"
                                : layer.output
                                ? "bg-green-100 text-green-700"
                                : "bg-slate-100 text-slate-500"
                            }`}
                          >
                            {key.replace("layer", "")}
                          </div>
                          <div>
                            <CardTitle className="text-base">{layer.name}</CardTitle>
                            <p className="text-xs text-slate-500">
                              {formatDuration(layer.duration_seconds)}
                              {layer.error && " • Failed"}
                            </p>
                          </div>
                        </div>
                        <span className="text-slate-400">
                          {expandedLayers.has(key) ? "▼" : "▶"}
                        </span>
                      </div>
                    </CardHeader>

                    {expandedLayers.has(key) && (
                      <CardContent className="space-y-4 border-t pt-4">
                        {layer.error && (
                          <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">
                            <strong>Error:</strong> {layer.error}
                          </div>
                        )}

                        <div>
                          <h4 className="mb-2 text-sm font-medium text-slate-700">
                            Input
                          </h4>
                          <pre className="max-h-64 overflow-auto whitespace-pre-wrap break-words rounded-lg bg-slate-100 p-3 text-xs">
                            {layer.input
                              ? JSON.stringify(layer.input, null, 2)
                              : "No input data"}
                          </pre>
                        </div>

                        <div>
                          <h4 className="mb-2 text-sm font-medium text-slate-700">
                            Output
                          </h4>
                          <pre className="max-h-96 overflow-auto whitespace-pre-wrap break-words rounded-lg bg-slate-100 p-3 text-xs">
                            {layer.output
                              ? JSON.stringify(layer.output, null, 2)
                              : "No output data"}
                          </pre>
                        </div>
                      </CardContent>
                    )}
                  </Card>
                ))}
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
