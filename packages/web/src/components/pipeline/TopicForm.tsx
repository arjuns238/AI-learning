"use client";

import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { FullPipelineRequest } from "@/types/pipeline";

const SUGGESTED_TOPICS = [
  "Gradient Descent",
  "Attention Mechanism",
  "Backpropagation",
  "Convolution",
  "Decision Trees",
];

type TopicFormProps = {
  onSubmit: (request: FullPipelineRequest) => void;
  isLoading: boolean;
};

export function TopicForm({ onSubmit, isLoading }: TopicFormProps) {
  const [topic, setTopic] = useState("");
  const [resolution, setResolution] = useState<"480p15" | "720p30" | "1080p60">(
    "480p15"
  );

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (!topic.trim()) return;

    onSubmit({
      topic: topic.trim(),
      video_resolution: resolution,
      include_generated_code: false,
    });
  };

  return (
    <Card className="border-slate-200/60 bg-white/90">
      <CardHeader>
        <CardTitle>Generate Educational Video</CardTitle>
      </CardHeader>
      <CardContent>
        <form className="space-y-4" onSubmit={handleSubmit}>
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">
              Learning Topic
            </label>
            <Input
              placeholder="e.g., Gradient Descent"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              disabled={isLoading}
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">
              Video Quality
            </label>
            <Select
              value={resolution}
              onValueChange={(v) =>
                setResolution(v as "480p15" | "720p30" | "1080p60")
              }
              disabled={isLoading}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select quality" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="480p15">Fast (480p)</SelectItem>
                <SelectItem value="720p30">Medium (720p)</SelectItem>
                <SelectItem value="1080p60">High (1080p)</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-xs text-slate-500">
              Lower quality renders faster. Good for testing.
            </p>
          </div>

          <Button className="w-full" type="submit" disabled={isLoading || !topic.trim()}>
            {isLoading ? "Generating..." : "Generate Video"}
          </Button>
        </form>

        {!isLoading && !topic && (
          <div className="mt-4 space-y-2">
            <p className="text-sm text-slate-500">Try one of these topics:</p>
            <div className="flex flex-wrap gap-2">
              {SUGGESTED_TOPICS.map((suggestedTopic) => (
                <Button
                  key={suggestedTopic}
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setTopic(suggestedTopic)}
                >
                  {suggestedTopic}
                </Button>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
