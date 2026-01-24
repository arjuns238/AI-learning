"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

type ExploreDeeperProps = {
  prompts: string[];
  onExplore: (prompt: string) => void;
};

export function ExploreDeeper({ prompts, onExplore }: ExploreDeeperProps) {
  if (!prompts || prompts.length === 0) {
    return null;
  }

  return (
    <Card className="bg-gradient-to-br from-purple-50 to-blue-50 border-purple-200/50">
      <CardHeader>
        <CardTitle className="text-lg text-slate-800">
          Want to explore deeper?
        </CardTitle>
        <p className="text-sm text-slate-600">
          Click any question below to learn more about related concepts
        </p>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-2">
          {prompts.map((prompt, i) => (
            <Button
              key={i}
              variant="outline"
              size="sm"
              onClick={() => onExplore(prompt)}
              className="text-left h-auto py-2 px-3 whitespace-normal bg-white/80 hover:bg-white border-purple-200/50 hover:border-purple-300"
            >
              <span className="mr-2 text-purple-500">→</span>
              {prompt}
            </Button>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
