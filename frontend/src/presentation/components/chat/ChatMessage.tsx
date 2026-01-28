/**
 * Individual chat message component - Enhanced with Thoughts & Markdown
 */

import { useState } from "react";
import type { Message } from "../../../domain/entities/types";
import { User, Bot, Code2, Bug, Search, FileText, CheckCircle, Shield, ChevronDown, ChevronRight, BrainCircuit } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

// Agent metadata collection (same as before)
const agentMetadata: Record<string, {
  name: string;
  icon: any;
  avatarBg: string;
  bubbleBg: string;
  bubbleBorder: string;
  bubbleText: string;
  badgeBg: string;
}> = {
  coder: {
    name: "Code Developer",
    icon: Code2,
    avatarBg: "from-blue-500 to-cyan-600",
    bubbleBg: "from-blue-50 to-cyan-50",
    bubbleBorder: "border-blue-200",
    bubbleText: "text-blue-900",
    badgeBg: "bg-blue-600"
  },
  debugger: {
    name: "Debug Specialist",
    icon: Bug,
    avatarBg: "from-red-500 to-orange-600",
    bubbleBg: "from-red-50 to-orange-50",
    bubbleBorder: "border-red-200",
    bubbleText: "text-red-900",
    badgeBg: "bg-red-600"
  },
  tester: {
    name: "Quality Tester",
    icon: CheckCircle,
    avatarBg: "from-green-500 to-emerald-600",
    bubbleBg: "from-green-50 to-emerald-50",
    bubbleBorder: "border-green-200",
    bubbleText: "text-green-900",
    badgeBg: "bg-green-600"
  },
  documenter: {
    name: "Documentation Writer",
    icon: FileText,
    avatarBg: "from-purple-500 to-pink-600",
    bubbleBg: "from-purple-50 to-pink-50",
    bubbleBorder: "border-purple-200",
    bubbleText: "text-purple-900",
    badgeBg: "bg-purple-600"
  },
  planner: {
    name: "Project Planner",
    icon: Search,
    avatarBg: "from-amber-500 to-yellow-600",
    bubbleBg: "from-amber-50 to-yellow-50",
    bubbleBorder: "border-amber-200",
    bubbleText: "text-amber-900",
    badgeBg: "bg-amber-600"
  },
  reviewer: {
    name: "Code Reviewer",
    icon: Shield,
    avatarBg: "from-indigo-500 to-violet-600",
    bubbleBg: "from-indigo-50 to-violet-50",
    bubbleBorder: "border-indigo-200",
    bubbleText: "text-indigo-900",
    badgeBg: "bg-indigo-600"
  }
};

interface ChatMessageProps {
  message: Message;
  isLast?: boolean;
  isStreaming?: boolean;
}

export default function ChatMessage({ message, isLast, isStreaming }: ChatMessageProps) {
  const isUser = message.role === "user";
  const agentId = message.agent_id?.toLowerCase() || "";
  const metadata = agentMetadata[agentId] || {
    name: "Assistant",
    icon: Bot,
    avatarBg: "from-slate-500 to-gray-600",
    bubbleBg: "from-slate-50 to-gray-50",
    bubbleBorder: "border-slate-200",
    bubbleText: "text-slate-900",
    badgeBg: "bg-slate-600"
  };

  const IconComponent = metadata.icon;
  const [thoughtsOpen, setThoughtsOpen] = useState(false);

  // Auto-expand thoughts if streaming and thoughts exist
  // useEffect(() => {
  //   if (isStreaming && message.thoughts && message.thoughts.length > 0) {
  //     setThoughtsOpen(true);
  //   }
  // }, [isStreaming, message.thoughts?.length]);

  if (message.role === "system" && message.metadata?.isHandoff) {
    const fromAgent = message.metadata.fromAgent || "Unknown";
    const toAgent = message.metadata.toAgent || "Unknown";
    return (
      <div className="flex items-center justify-center my-6 px-4">
        <div className="flex items-center gap-3 w-full max-w-md">
          <div className="h-px bg-gray-200 flex-1"></div>
          <div className="flex items-center gap-2 text-xs font-medium text-gray-500 bg-gray-50 px-3 py-1.5 rounded-full border border-gray-200 shadow-sm">
            <span className="text-gray-600">{fromAgent}</span>
            <ChevronRight size={14} className="text-gray-400" />
            <span className="text-blue-600">{toAgent}</span>
          </div>
          <div className="h-px bg-gray-200 flex-1"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="group px-4 py-4 hover:bg-gray-50/50 transition-colors">
      <div className="max-w-4xl mx-auto">
        <div className={`flex gap-3 items-start ${isUser ? "flex-row-reverse" : "flex-row"}`}>
          {/* Avatar */}
          <div className={`flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br ${isUser ? "from-blue-600 to-blue-700" : metadata.avatarBg
            } flex items-center justify-center shadow-lg ring-2 ring-white`}>
            {isUser ? (
              <User size={20} className="text-white" strokeWidth={2.5} />
            ) : (
              <IconComponent size={20} className="text-white" strokeWidth={2.5} />
            )}
          </div>

          {/* Content Wrapper */}
          <div className={`flex-1 min-w-0 max-w-[85%] space-y-1.5 ${isUser ? "items-end" : "items-start"} flex flex-col`}>
            {/* Header */}
            <div className={`flex items-center gap-2 ${isUser ? "flex-row-reverse" : "flex-row"}`}>
              <span className="font-semibold text-sm text-gray-900">
                {isUser ? "You" : metadata.name}
              </span>
              {!isUser && message.agent_id && (
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide ${metadata.badgeBg} text-white shadow-sm`}>
                  {message.agent_id}
                </span>
              )}
            </div>

            {/* Thoughts Accordion */}
            {message.thoughts && message.thoughts.length > 0 && (
              <div className="w-full mb-2">
                <button
                  onClick={() => setThoughtsOpen(!thoughtsOpen)}
                  className="flex items-center gap-2 text-xs font-medium text-gray-500 hover:text-gray-700 transition-colors mb-1 select-none"
                >
                  {thoughtsOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                  <BrainCircuit size={14} />
                  <span>Thought Process ({message.thoughts.length} steps)</span>
                </button>

                {thoughtsOpen && (
                  <div className="bg-gray-50 rounded-lg p-3 border border-gray-200 text-xs text-gray-600 space-y-2 animate-in slide-in-from-top-2 duration-200">
                    {message.thoughts.map((thought, idx) => (
                      <div key={idx} className="border-l-2 border-gray-300 pl-2">
                        <span className="font-semibold text-gray-700 mr-1">{thought.agentName}:</span>
                        {thought.content}
                      </div>
                    ))}
                    {isStreaming && isLast && (
                      <div className="flex gap-1 items-center px-1 h-4">
                        <span className="w-1 h-1 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                        <span className="w-1 h-1 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                        <span className="w-1 h-1 bg-gray-400 rounded-full animate-bounce"></span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Message Bubble */}
            <div className={`rounded-2xl px-4 py-3 shadow-sm w-full ${isUser
              ? "bg-gradient-to-br from-blue-500 to-blue-600 text-white"
              : `bg-gradient-to-br ${metadata.bubbleBg} border ${metadata.bubbleBorder} ${metadata.bubbleText}`
              }`}>
              <div className={`text-sm leading-relaxed prose max-w-none break-words ${isUser ? "prose-invert" : ""}`}>
                {(!message.content && !isUser && (!message.thoughts || message.thoughts.length === 0)) ? (
                  // Loading dots if truly empty and no thoughts
                  <div className="flex gap-1 items-center h-5 px-1">
                    <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                    <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                    <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"></span>
                  </div>
                ) : (
                  <div className={isStreaming && isLast ? "cursor-blink" : ""}>
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {message.content || ""}
                    </ReactMarkdown>
                  </div>
                )}
              </div>

              <time className={`text-[10px] mt-2 block ${isUser ? "text-right text-blue-100" : "text-left text-gray-500 opacity-70"}`}>
                {new Date(message.timestamp).toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </time>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
