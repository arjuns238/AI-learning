'use client';

import { Send, Mic, Paperclip, Loader2 } from 'lucide-react';
import { useState } from 'react';

interface ChatInputProps {
  onSend?: (message: string) => void;
  isLoading?: boolean;
  placeholder?: string;
}

export function ChatInput({ onSend, isLoading = false, placeholder = "What would you like to learn?" }: ChatInputProps) {
  const [message, setMessage] = useState('');

  const handleSend = () => {
    if (message.trim() && !isLoading) {
      onSend?.(message);
      setMessage('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <section className="w-full px-6 py-6 fixed bottom-0 left-0 right-0 bg-white border-t border-gray-100">
      <div className="max-w-3xl mx-auto">
        <div className="flex items-center gap-3 bg-gray-50 rounded-2xl px-4 py-3 border border-gray-200 focus-within:border-blue-400 focus-within:bg-white transition-all">
          <button
            className="w-10 h-10 flex items-center justify-center text-gray-400 hover:text-gray-600 transition-colors"
            disabled={isLoading}
          >
            <Paperclip className="w-5 h-5" />
          </button>

          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={isLoading}
            className="flex-1 bg-transparent text-gray-900 placeholder-gray-400 outline-none text-base disabled:opacity-50"
          />

          <button
            className="w-10 h-10 flex items-center justify-center text-gray-400 hover:text-gray-600 transition-colors"
            disabled={isLoading}
          >
            <Mic className="w-5 h-5" />
          </button>

          <button
            onClick={handleSend}
            disabled={isLoading || !message.trim()}
            className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all ${
              message.trim() && !isLoading
                ? 'bg-blue-500 text-white hover:bg-blue-600'
                : 'bg-gray-200 text-gray-400'
            }`}
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>

        <p className="text-center text-xs text-gray-400 mt-3">
          AI can make mistakes. Consider checking important information.
        </p>
      </div>
    </section>
  );
}
