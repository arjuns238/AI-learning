"use client";

import { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import type { VideoMetadata } from "@/types/pipeline";

const API_BASE = "http://localhost:8000";

type VideoPlayerProps = {
  video: VideoMetadata;
  jobId: string;
};

export function VideoPlayer({ video, jobId }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const videoUrl = video.video_url?.startsWith("http")
    ? video.video_url
    : `${API_BASE}${video.video_url || `/api/pipeline/video/${jobId}`}`;

  const handlePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleError = () => {
    setError("Failed to load video. The video might still be processing.");
  };

  return (
    <div className="space-y-4">
      <div className="relative overflow-hidden rounded-lg bg-slate-900">
        {error ? (
          <div className="flex h-64 items-center justify-center text-white">
            <p>{error}</p>
          </div>
        ) : (
          <video
            ref={videoRef}
            className="aspect-video w-full"
            controls
            autoPlay
            loop
            muted
            playsInline
            onPlay={() => setIsPlaying(true)}
            onPause={() => setIsPlaying(false)}
            onError={handleError}
          >
            <source src={videoUrl} type="video/mp4" />
            Your browser does not support the video tag.
          </video>
        )}
      </div>

      <div className="flex items-center justify-between text-sm text-slate-500">
        <span>Resolution: {video.resolution}</span>
        <span>Render time: {video.execution_time_seconds.toFixed(1)}s</span>
      </div>

      <div className="flex gap-2">
        <Button variant="outline" size="sm" onClick={handlePlay}>
          {isPlaying ? "Pause" : "Play"}
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => window.open(videoUrl, "_blank")}
        >
          Download
        </Button>
      </div>
    </div>
  );
}
