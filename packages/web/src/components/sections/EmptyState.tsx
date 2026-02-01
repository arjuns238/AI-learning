'use client';

import { Sparkles } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  description?: string;
}

export function EmptyState({
  title = "What would you like to learn?",
  description = "Enter any topic below and I'll create a personalized learning experience with videos, quizzes, and explanations."
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
      <div className="w-16 h-16 bg-blue-100 rounded-2xl flex items-center justify-center mb-6">
        <Sparkles className="w-8 h-8 text-blue-500" />
      </div>
      <h2 className="text-2xl font-semibold text-gray-900 mb-2">
        {title}
      </h2>
      <p className="text-gray-500 max-w-md">
        {description}
      </p>
    </div>
  );
}
