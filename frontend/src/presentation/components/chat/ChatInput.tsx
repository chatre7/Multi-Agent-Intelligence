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
    <div className="space-y-2">
      {/* Thinking Mode Indicator */}
      {thinkingEnabled && (
        <div className="flex items-center gap-2 px-3 py-1.5 bg-purple-50 border border-purple-200 rounded-lg text-xs text-purple-700 animate-in fade-in slide-in-from-bottom-1 duration-200">
          <BrainCircuit size={14} className="text-purple-500" />
          <span className="font-medium">Thinking Mode ON</span>
          <span className="opacity-70">– AI will show reasoning process</span>
        </div>
      )}

      <div className="flex gap-2 items-end">
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your message... (Shift+Enter for new line)"
          disabled={disabled || isLoading}
          className="flex-1 p-3 border border-gray-200 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 disabled:bg-gray-100 disabled:text-gray-500 transition-all duration-200 text-sm"
          rows={3}
        />

        <div className="flex flex-col gap-2">
          {/* Thinking Toggle Button */}
          <button
            onClick={toggleThinking}
            type="button"
            title={thinkingEnabled ? "Disable thinking mode" : "Enable thinking mode"}
            aria-pressed={thinkingEnabled}
            aria-label="Toggle thinking mode"
            className={`p-2.5 rounded-xl border transition-all duration-200 ${thinkingEnabled
                ? "bg-purple-100 border-purple-300 text-purple-600 shadow-sm shadow-purple-200/50"
                : "bg-gray-50 border-gray-200 text-gray-400 hover:bg-gray-100 hover:text-gray-600 hover:border-gray-300"
              }`}
          >
            <BrainCircuit size={20} className={thinkingEnabled ? "animate-pulse" : ""} />
          </button>

          {/* Send Button */}
          <button
            onClick={handleSend}
            disabled={disabled || isLoading || !message.trim()}
            className="p-2.5 bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-xl hover:from-blue-600 hover:to-blue-700 disabled:from-gray-300 disabled:to-gray-300 disabled:cursor-not-allowed transition-all duration-200 shadow-sm shadow-blue-500/20 disabled:shadow-none"
          >
            {isLoading ? (
              <span className="animate-spin block w-5 h-5 border-2 border-white/30 border-t-white rounded-full"></span>
            ) : (
              <Send size={20} />
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
