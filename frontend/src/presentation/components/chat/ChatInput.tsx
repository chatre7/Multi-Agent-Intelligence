/**
 * Chat input component with send button and thinking mode toggle
 */

import React, { useState } from 'react';
import { Send, BrainCircuit } from 'lucide-react';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
  isLoading?: boolean;
  thinkingEnabled?: boolean;
  onThinkingChange?: (enabled: boolean) => void;
}

export default function ChatInput({
  onSendMessage,
  disabled = false,
  isLoading = false,
  thinkingEnabled = false,
  onThinkingChange
}: ChatInputProps) {
  const [message, setMessage] = useState('');

  const handleSend = () => {
    if (message.trim() && !disabled) {
      onSendMessage(message);
      setMessage('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const toggleThinking = () => {
    onThinkingChange?.(!thinkingEnabled);
  };

  return (
    <div className="max-w-[95%] mx-auto w-full">
      {/* Thinking Mode Indicator */}
      {thinkingEnabled && (
        <div className="flex items-center gap-2 px-3 py-1.5 mb-2 bg-purple-50 border border-purple-200 rounded-lg text-xs text-purple-700 animate-in fade-in slide-in-from-bottom-1 duration-200 w-fit mx-auto">
          <BrainCircuit size={14} className="text-purple-500" />
          <span className="font-medium">Thinking Mode</span>
        </div>
      )}

      <div className="relative bg-gray-50 rounded-2xl border border-gray-200 shadow-sm focus-within:ring-2 focus-within:ring-blue-100 focus-within:border-blue-400 focus-within:bg-white transition-all duration-200">
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyPress}
          placeholder="How can I help you today?"
          disabled={disabled || isLoading}
          className="w-full max-h-[200px] py-3.5 pl-4 pr-12 bg-transparent resize-none focus:outline-none text-sm leading-relaxed scrollbar-thin scrollbar-thumb-gray-200"
          rows={1}
          style={{ minHeight: '52px' }}
          onInput={(e) => {
            const target = e.target as HTMLTextAreaElement;
            target.style.height = 'auto'; // Reset height
            target.style.height = `${Math.min(target.scrollHeight, 200)}px`; // Grow up to 200px
          }}
        />

        {/* Actions Area */}
        <div className="absolute bottom-2 right-2 flex items-center gap-1">
          {/* Thinking Toggle */}
          <button
            onClick={toggleThinking}
            type="button"
            className={`p-1.5 rounded-lg transition-colors ${thinkingEnabled
              ? "bg-purple-100 text-purple-600"
              : "text-gray-400 hover:text-gray-600 hover:bg-gray-100"}`}
            title="Enable Thinking"
          >
            <BrainCircuit size={18} />
          </button>

          {/* Send Button */}
          <button
            onClick={handleSend}
            disabled={disabled || isLoading || !message.trim()}
            className={`p-1.5 rounded-lg transition-all duration-200 ${!message.trim() || disabled
              ? "bg-gray-200 text-gray-400 cursor-not-allowed"
              : "bg-black text-white hover:bg-gray-800 shadow-md"
              }`}
          >
            {isLoading ? (
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin m-0.5"></div>
            ) : (
              <Send size={18} />
            )}
          </button>
        </div>
      </div>

      <div className="text-center mt-2">
        <p className="text-[10px] text-gray-400">
          Multi-Agent AI can make mistakes. Check important info.
        </p>
      </div>
    </div>
  );
}
