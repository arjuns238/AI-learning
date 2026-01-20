"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { PedagogicalMetadata } from "@/types/pipeline";

type PedagogyPanelProps = {
  pedagogy: PedagogicalMetadata;
};

export function PedagogyPanel({ pedagogy }: PedagogyPanelProps) {
  return (
    <div className="space-y-4">
      {/* Core Question */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-base">
            Core Question
            {pedagogy.difficulty_level && (
              <Badge variant="outline" className="text-xs">
                Level {pedagogy.difficulty_level}/5
              </Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-lg italic text-slate-700">
            {pedagogy.core_question}
          </p>
        </CardContent>
      </Card>

      {/* Target Mental Model */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Target Mental Model</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-slate-700">{pedagogy.target_mental_model}</p>
        </CardContent>
      </Card>

      {/* Common Misconception */}
      <Card className="border-amber-200/70 bg-amber-50/50">
        <CardHeader className="pb-2">
          <CardTitle className="text-base text-amber-800">
            Common Misconception
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-amber-900">{pedagogy.common_misconception}</p>
        </CardContent>
      </Card>

      {/* Key Distinction */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Key Distinction</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-slate-700">{pedagogy.disambiguating_contrast}</p>
        </CardContent>
      </Card>

      {/* Concrete Example */}
      <Card className="border-emerald-200/70 bg-emerald-50/50">
        <CardHeader className="pb-2">
          <CardTitle className="text-base text-emerald-800">
            Concrete Example
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-emerald-900">{pedagogy.concrete_anchor}</p>
        </CardContent>
      </Card>

      {/* Visual Metaphor (if present) */}
      {pedagogy.spatial_metaphor && (
        <Card className="border-blue-200/70 bg-blue-50/50">
          <CardHeader className="pb-2">
            <CardTitle className="text-base text-blue-800">
              Visual Metaphor
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-blue-900">{pedagogy.spatial_metaphor}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
