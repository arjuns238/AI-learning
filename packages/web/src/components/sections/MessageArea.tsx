'use client';

import { ReactNode } from 'react';

interface MessageAreaProps {
  children: ReactNode;
}

export function MessageArea({ children }: MessageAreaProps) {
  return (
    <div className="max-w-3xl mx-auto px-6 py-8">
      {children}
    </div>
  );
}
