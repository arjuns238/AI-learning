"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type QuizSectionProps = {
  question: string;
};

export function QuizSection({ question }: QuizSectionProps) {
  const [revealed, setRevealed] = useState(false);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Check Your Understanding</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-lg font-medium text-slate-800">{question}</p>

        <div className="flex items-center gap-4">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setRevealed(!revealed)}
          >
            {revealed ? "Hide hint" : "Need a hint?"}
          </Button>
        </div>

        {revealed && (
          <div
            className={cn(
              "rounded-lg border border-blue-200 bg-blue-50 p-4 text-sm text-blue-800",
              "animate-in fade-in slide-in-from-top-2 duration-300"
            )}
          >
            <p className="font-medium mb-2">Think about:</p>
            <ul className="list-disc list-inside space-y-1">
              <li>What happens at the extremes?</li>
              <li>What assumptions are being made?</li>
              <li>Can you connect this to the concrete example above?</li>
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
