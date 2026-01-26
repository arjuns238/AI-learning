"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { PedagogicalMetadata, PedagogicalSection } from "@/types/pipeline";

type PedagogyPanelProps = {
  pedagogy: PedagogicalMetadata;
};

function SectionSummaryCard({ section }: { section: PedagogicalSection }) {
  const hasVisual = section.visual?.should_animate;

  return (
    <div className="rounded-lg border bg-white p-3 shadow-sm">
      <div className="flex items-center gap-2 mb-2">
        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-slate-900 text-xs font-medium text-white">
          {section.order}
        </span>
        <span className="font-medium text-slate-900">{section.title}</span>
        {hasVisual && (
          <Badge variant="outline" className="text-xs bg-blue-50 text-blue-700 border-blue-200">
            Has Animation
          </Badge>
        )}
      </div>
      <p className="text-sm text-slate-600 line-clamp-2">{section.content}</p>

      {/* Show structured content indicators */}
      <div className="mt-2 flex gap-2 flex-wrap">
        {section.steps && section.steps.length > 0 && (
          <Badge variant="outline" className="text-xs">
            {section.steps.length} steps
          </Badge>
        )}
        {section.math_expressions && section.math_expressions.length > 0 && (
          <Badge variant="outline" className="text-xs">
            Math
          </Badge>
        )}
        {section.comparison && (
          <Badge variant="outline" className="text-xs">
            Comparison
          </Badge>
        )}
      </div>
    </div>
  );
}

export function PedagogyPanel({ pedagogy }: PedagogyPanelProps) {
  // Sort sections by order
  const sortedSections = [...pedagogy.sections].sort((a, b) => a.order - b.order);
  const visualSections = sortedSections.filter(s => s.visual?.should_animate);

  return (
    <div className="space-y-4">
      {/* Topic and Summary */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-base">
            {pedagogy.topic}
            {pedagogy.difficulty_level && (
              <Badge variant="outline" className="text-xs">
                Level {pedagogy.difficulty_level}/5
              </Badge>
            )}
            {pedagogy.domain && (
              <Badge variant="outline" className="text-xs capitalize">
                {pedagogy.domain}
              </Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-slate-700">{pedagogy.summary}</p>
        </CardContent>
      </Card>

      {/* Sections Overview */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base flex items-center gap-2">
            Sections
            <Badge variant="outline" className="text-xs">
              {sortedSections.length} total
            </Badge>
            {visualSections.length > 0 && (
              <Badge variant="outline" className="text-xs bg-blue-50 text-blue-700 border-blue-200">
                {visualSections.length} with animations
              </Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {sortedSections.map((section) => (
            <SectionSummaryCard key={section.order} section={section} />
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
