"use client";

import { useRef } from "react";

import type { ManimVideoSpec } from "@/types/lesson";

export function ManimVideoPlayer({ spec }: { spec: ManimVideoSpec }) {
  const videoRef = useRef<HTMLVideoElement | null>(null);

  const handleChapterClick = (time: number) => {
    const video = videoRef.current;
    if (!video) {
      return;
    }

    video.currentTime = time;
    const playPromise = video.play();
    if (playPromise && typeof playPromise.catch === "function") {
      playPromise.catch(() => {});
    }
  };

  return (
    <div className="space-y-3">
      <video
        ref={videoRef}
        controls
        className="w-full rounded-lg border border-slate-200 bg-black"
        poster={spec.poster}
      >
        <source src={spec.src} type="video/mp4" />
        Your browser does not support the video tag.
      </video>
      {spec.chapters?.length ? (
        <div className="flex flex-wrap gap-2">
          {spec.chapters.map((chapter) => (
            <button
              key={`${chapter.label}-${chapter.t}`}
              type="button"
              className="rounded-full border border-slate-200 px-3 py-1 text-xs font-medium text-slate-700 transition hover:bg-slate-50"
              onClick={() => handleChapterClick(chapter.t)}
            >
              {chapter.label}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
