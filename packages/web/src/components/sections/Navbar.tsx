'use client';

import { BookOpen } from 'lucide-react';

export function Navbar() {
  return (
    <nav className="w-full px-6 py-4 flex items-center justify-between bg-white fixed top-0 left-0 right-0 z-50 border-b border-gray-100">
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
          <BookOpen className="w-5 h-5 text-white" />
        </div>
        <span className="text-xl font-semibold text-gray-900">AI Learning</span>
      </div>

      <div className="flex items-center gap-8">
        <a href="#" className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors">
          Learn
        </a>
        <a href="#" className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors">
          History
        </a>
      </div>
    </nav>
  );
}
