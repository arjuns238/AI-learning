"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";

import type { Lesson, LessonRequest } from "@/types/lesson";
import { LessonRenderer } from "@/components/lesson/LessonRenderer";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";

const defaultLessonTopics = [
  "Attention mechanism",
  "BatchNorm",
  "Gradient descent",
];

export default function Home() {
  const [topic, setTopic] = useState("");
  const [level, setLevel] = useState<LessonRequest["level"]>("Beginner");
  const [style, setStyle] = useState<LessonRequest["style"]>("Visual-first");
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [isDefaultVisual, setIsDefaultVisual] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async (event: FormEvent) => {
    event.preventDefault();
    if (!topic.trim()) {
      setError("Pick a topic to generate a lesson.");
      return;
    }

    setLoading(true);
    setError(null);
    setLesson(null);

    try {
      const response = await fetch("/api/lesson", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic, level, style }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data?.error ?? "Lesson generation failed.");
      }

      setLesson(data.lesson as Lesson);
      setIsDefaultVisual(Boolean(data.isDefaultVisual));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_#fff7e9,_#f7f2ea_55%,_#efe7db_100%)] text-slate-900">
      <main className="mx-auto flex w-full max-w-6xl flex-col gap-10 px-6 py-12 lg:px-12">
        <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="space-y-6">
            <Badge variant="soft">ML lesson loom</Badge>
            <h1 className="text-4xl font-semibold leading-tight text-slate-900 sm:text-5xl">
              Structured, visual-first ML lessons without prompt crafting.
            </h1>
            <p className="text-lg text-slate-700">
              Type a topic once. Get a consistent intuition, a grounded example,
              a single visual, and a mini quiz to check your understanding.
            </p>
            <Link
              href="/learn"
              className="inline-flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-700"
            >
              Try the full video pipeline →
            </Link>
          </div>
          <Card className="border-slate-200/60 bg-white/90">
            <CardHeader>
              <CardTitle>Generate a lesson</CardTitle>
            </CardHeader>
            <CardContent>
              <form className="space-y-4" onSubmit={handleGenerate}>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-700">
                    ML topic
                  </label>
                  <Input
                    placeholder="e.g., Attention mechanism"
                    value={topic}
                    onChange={(event) => setTopic(event.target.value)}
                  />
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-700">
                      Explanation level
                    </label>
                    <Select
                      value={level}
                      onValueChange={(value) =>
                        setLevel(value as LessonRequest["level"])
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Beginner" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Beginner">Beginner</SelectItem>
                        <SelectItem value="Practical">Practical</SelectItem>
                        <SelectItem value="Mathy">Mathy</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-700">
                      Style
                    </label>
                    <Select
                      value={style}
                      onValueChange={(value) =>
                        setStyle(value as LessonRequest["style"])
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Visual-first" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Visual-first">Visual-first</SelectItem>
                        <SelectItem value="Text-first">Text-first</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <Button className="w-full" type="submit" disabled={loading}>
                  {loading ? "Generating lesson..." : "Generate lesson"}
                </Button>
                {error ? (
                  <p className="text-sm text-rose-600">{error}</p>
                ) : null}
              </form>
            </CardContent>
          </Card>
        </section>

        <section className="space-y-6">
          {lesson ? (
            <div className="space-y-3">
              {isDefaultVisual ? (
                <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
                  Showing a default visual because the model response was
                  missing a valid attention heatmap spec.
                </div>
              ) : null}
              <LessonRenderer lesson={lesson} />
            </div>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>Lesson output</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 text-slate-700">
                <p>
                  Your lesson will appear here with a fixed structure: intuition,
                  example, one visual, and a quiz.
                </p>
                <div className="flex flex-wrap gap-2">
                  {defaultLessonTopics.map((item) => (
                    <Button
                      key={item}
                      type="button"
                      variant="outline"
                      onClick={() => setTopic(item)}
                    >
                      {item}
                    </Button>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </section>
      </main>
    </div>
  );
}
