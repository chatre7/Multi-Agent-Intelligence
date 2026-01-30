import { useState, useEffect } from "react";
import type { Message } from "../../../domain/entities/types";
import { ChevronRight, BrainCircuit } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { AgentAvatar } from "../ui/AgentAvatar";

interface ChatMessageProps {
  message: Message;
  isLast?: boolean;
  isStreaming?: boolean;
}

export default function ChatMessage({ message, isLast, isStreaming }: ChatMessageProps) {
  const isUser = message.role === "user";
  const agentId = message.agent_id || "";
  const agentName = message.agent_id || "Assistant";

  const [thoughtsOpen, setThoughtsOpen] = useState(false);
  const [hasAutoExpanded, setHasAutoExpanded] = useState(false);

  useEffect(() => {
    if (isStreaming && !hasAutoExpanded && ((message.thoughts?.length ?? 0) > 0 || (message.metadata?.thoughts?.length ?? 0) > 0)) {
      setThoughtsOpen(true);
      setHasAutoExpanded(true);
    }
  }, [isStreaming, hasAutoExpanded, message.thoughts?.length, message.metadata?.thoughts?.length]);

  if (message.role === "system" && message.metadata?.isHandoff) {
    return (
      <div className="flex items-center justify-center my-4 opacity-60">
        <span className="text-xs text-gray-400 bg-gray-100 px-3 py-1 rounded-full border border-gray-200">
          {message.content}
        </span>
      </div>
    );
  }

  return (
    <div className={`w-full max-w-[95%] mx-auto flex ${isUser ? "justify-end" : "justify-start"} mb-6 px-4 md:px-6`}>

      {/* AI Avatar (Left only) */}
      {!isUser && (
        <div className="flex-shrink-0 mr-3 mt-1">
          <AgentAvatar agentId={agentId} />
        </div>
      )}

      {/* Bubble */}
      <div
        className={`max-w-[85%] md:max-w-[75%] rounded-2xl px-5 py-3.5 shadow-sm text-sm md:text-base leading-relaxed overflow-hidden relative group
            ${isUser
            ? "bg-blue-50/80 text-gray-800 rounded-tr-none border border-blue-100"
            : "bg-gray-100/70 text-gray-800 rounded-tl-none border border-gray-200"
          }
        `}
      >
        {/* Helper Header for AI */}
        {!isUser && (
          <div className="flex items-center gap-2 mb-1.5 opacity-60">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">{agentName}</span>
          </div>
        )}

        {/* Thoughts */}
        {!isUser && (message.thoughts?.length || (message.metadata?.thoughts?.length) || isStreaming) && (
          <div className="mb-3">
            <button
              onClick={() => setThoughtsOpen(!thoughtsOpen)}
              className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-700 bg-black/5 px-2 py-1 rounded-md transition-colors"
            >
              {isStreaming ? <BrainCircuit size={12} className="animate-pulse" /> : <ChevronRight size={12} className={thoughtsOpen ? "rotate-90 transition-transform" : ""} />}
              <span className="font-medium">{isStreaming ? "Thinking..." : "Thought Process"}</span>
            </button>

            {thoughtsOpen && (
              <div className="mt-2 text-xs text-gray-500 bg-black/5 rounded-lg p-3 font-mono border-l-2 border-gray-300">
                {(message.thoughts || message.metadata?.thoughts || []).map((thought: any, idx: number) => (
                  <div key={idx} className="whitespace-pre-wrap mb-1">{thought.content}</div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Markdown Content */}
        <div className="prose prose-sm max-w-none break-words">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              img: ({ node, ...props }) => <img {...props} className="max-w-full rounded-lg my-2" />,
              table: ({ node, ...props }) => <div className="overflow-x-auto my-3"><table {...props} className="min-w-full divide-y divide-gray-300 border border-gray-300 rounded text-xs" /></div>,
              pre: ({ node, ...props }) => <pre {...props} className="bg-gray-900 text-gray-100 p-3 rounded-lg overflow-x-auto my-2 text-xs font-mono" />,
              code: ({ node, ...props }: any) =>
                props.inline
                  ? <code {...props} className="bg-black/10 px-1 py-0.5 rounded text-[0.9em] font-mono text-pink-600" />
                  : <code {...props} />,
              a: ({ node, ...props }) => <a {...props} className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer" />
            }}
          >
            {message.content || ""}
          </ReactMarkdown>
        </div>

        {/* Loading Indicator */}
        {isStreaming && isLast && !message.content && !thoughtsOpen && (
          <div className="flex gap-1 h-4 items-center">
            <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"></span>
            <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:0.2s]"></span>
            <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:0.4s]"></span>
          </div>
        )}
      </div>
    </div>
  );
}
