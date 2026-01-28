/**
 * Individual chat message component - Enhanced with Thoughts & Markdown
 */

import { useState, useEffect } from "react";
import type { Message } from "../../../domain/entities/types";
import { User, Bot, Code2, Bug, Search, FileText, CheckCircle, Shield, ChevronRight, BrainCircuit, Zap, BookOpen, Scroll, Laugh, Heart, Share2 } from "lucide-react";
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
  },
  storyteller: {
    name: "Storyteller",
    icon: BookOpen,
    avatarBg: "from-amber-400 to-orange-500",
    bubbleBg: "from-amber-50/50 to-orange-50/50",
    bubbleBorder: "border-amber-200",
    bubbleText: "text-amber-900",
    badgeBg: "bg-amber-600"
  },
  philosopher: {
    name: "Philosopher",
    icon: Scroll,
    avatarBg: "from-blue-600 to-indigo-700",
    bubbleBg: "from-blue-50/50 to-indigo-50/50",
    bubbleBorder: "border-blue-200",
    bubbleText: "text-blue-900",
    badgeBg: "bg-blue-600"
  },
  comedian: {
    name: "Comedian",
    icon: Laugh,
    avatarBg: "from-pink-500 to-rose-600",
    bubbleBg: "from-pink-50/50 to-rose-50/50",
    bubbleBorder: "border-pink-200",
    bubbleText: "text-pink-900",
    badgeBg: "bg-pink-600"
  },
  empath: {
    name: "Empath",
    icon: Heart,
    avatarBg: "from-emerald-400 to-teal-500",
    bubbleBg: "from-emerald-50/50 to-teal-50/50",
    bubbleBorder: "border-emerald-200",
    bubbleText: "text-emerald-900",
    badgeBg: "bg-emerald-600"
  },
  router: {
    name: "System Router",
    icon: Share2,
    avatarBg: "from-slate-600 to-gray-700",
    bubbleBg: "from-slate-50 to-gray-50",
    bubbleBorder: "border-slate-300",
    bubbleText: "text-slate-900",
    badgeBg: "bg-slate-700"
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
  const [hasAutoExpanded, setHasAutoExpanded] = useState(false);

  // Auto-expand thoughts if streaming and thoughts exist (only once)
  // This satisfies the user request "ค้างไว้ก่อนได้ไหม" (keep it open)
  useEffect(() => {
    if (isStreaming && !hasAutoExpanded && ((message.thoughts?.length ?? 0) > 0 || (message.metadata?.thoughts?.length ?? 0) > 0)) {
      setThoughtsOpen(true);
      setHasAutoExpanded(true);
    }
  }, [isStreaming, hasAutoExpanded, message.thoughts?.length, message.metadata?.thoughts?.length]);

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
              <User size={20} className="text-white" strokeWidth={2.5} aria-hidden="true" />
            ) : (
              <IconComponent size={20} className="text-white" strokeWidth={2.5} aria-hidden="true" />
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
              {message.metadata?.skill_id && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-700 border border-amber-200 shadow-sm" title="Skill Used">
                  <Zap size={10} className="fill-amber-500 text-amber-600" />
                  {message.metadata.skill_id}
                </span>
              )}
            </div>

            {/* Message Bubble */}
            <div className={`rounded-2xl px-5 py-3.5 shadow-sm w-full relative overflow-hidden transition-[background-color,border-color,box-shadow,opacity] duration-300 border ${isUser
              ? "bg-gradient-to-br from-blue-600 to-blue-700 text-white shadow-blue-500/10 border-blue-500/20"
              : `bg-gradient-to-br ${metadata.bubbleBg} ${metadata.bubbleBorder} ${metadata.bubbleText} shadow-gray-200/40 backdrop-blur-[2px]`
              }`}>

              {/* Integrated Thoughts (Deep Research Style) */}
              {!isUser && (message.thoughts?.length || (message.metadata?.thoughts?.length) || isStreaming) && (
                <div className="mb-4">
                  <div className="flex items-center gap-2 mb-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setThoughtsOpen(!thoughtsOpen);
                      }}
                      aria-expanded={thoughtsOpen}
                      aria-label={thoughtsOpen ? "Collapse thinking process" : "Expand thinking process"}
                      className={`flex items-center gap-2 text-[10px] font-bold uppercase tracking-wider transition-colors duration-200 py-1 px-2 rounded-md ${thoughtsOpen
                        ? "bg-black/5 dark:bg-white/5 opacity-80"
                        : "hover:bg-black/5 dark:hover:bg-white/5 opacity-60 hover:opacity-90"
                        }`}
                    >
                      <BrainCircuit aria-hidden="true" size={12} className={isStreaming ? "animate-pulse text-purple-600" : ""} />
                      <span>Thinking Process</span>
                      <ChevronRight aria-hidden="true" size={12} className={`transition-transform duration-300 ${thoughtsOpen ? "rotate-90" : "rotate-0"}`} />
                    </button>

                    {isStreaming ? (
                      <span className="flex items-center gap-1.5 animate-in fade-in duration-500">
                        <span className="w-1 h-1 bg-current rounded-full animate-ping"></span>
                        <span className="text-[10px] font-medium italic opacity-70">Reasoning…</span>
                      </span>
                    ) : ((message.thoughts?.length ?? 0) > 0 || (message.metadata?.thoughts?.length ?? 0) > 0) && (
                      <span className="flex items-center gap-1 text-[10px] font-bold opacity-60">
                        <CheckCircle aria-hidden="true" size={10} className="text-emerald-600" />
                        <span>Reasoned</span>
                      </span>
                    )}
                  </div>

                  {thoughtsOpen && (
                    <div className="bg-black/5 dark:bg-white/5 rounded-xl p-3.5 mb-3 border border-black/5 dark:border-white/5 text-[13px] leading-relaxed opacity-90 space-y-3 animate-in fade-in slide-in-from-top-1 duration-300">
                      {(message.thoughts || message.metadata?.thoughts || []).map((thought: any, idx: number) => (
                        <div key={idx} className="relative pl-3 border-l-2 border-current/20 last:mb-0">
                          <div className="whitespace-pre-wrap font-serif italic text-pretty">
                            {thought.content}
                          </div>
                        </div>
                      ))}
                      {isStreaming && (
                        <div className="flex gap-1.5 items-center px-1">
                          <span className="w-1 h-1 bg-current opacity-40 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                          <span className="w-1 h-1 bg-current opacity-40 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                          <span className="w-1 h-1 bg-current opacity-40 rounded-full animate-bounce"></span>
                        </div>
                      )}
                    </div>
                  )}

                  {message.content && <div className="h-px bg-current opacity-10 w-full mb-4" />}
                </div>
              )}

              <div className={`text-sm leading-relaxed prose max-w-none [overflow-wrap:anywhere] [word-break:break-word] text-pretty ${isUser ? "prose-invert" : ""}`}>
                {(!message.content && !isUser && (!message.thoughts || message.thoughts.length === 0)) ? (
                  // Loading dots if truly empty and no thoughts
                  <div className="flex gap-1 items-center h-5 px-1 py-4">
                    <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                    <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                    <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"></span>
                  </div>
                ) : (
                  <div className={`${isStreaming && isLast ? "cursor-blink" : ""} overflow-x-auto`}>
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        // Ensure images and tables don't break layout
                        img: ({ node, ...props }) => <img {...props} className="max-w-full rounded-lg shadow-sm my-2" />,
                        table: ({ node, ...props }) => <div className="overflow-x-auto my-4"><table {...props} className="min-w-full divide-y divide-gray-200 border border-gray-200 rounded-lg text-xs" /></div>,
                        pre: ({ node, ...props }) => <pre {...props} className="bg-gray-900 text-gray-100 p-4 rounded-xl overflow-x-auto my-3 text-xs shadow-inner border border-gray-800" />,
                        code: ({ node, ...props }: any) =>
                          props.inline
                            ? <code {...props} className="bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded text-pink-600 font-mono text-[0.9em]" />
                            : <code {...props} />
                      }}
                    >
                      {message.content || ""}
                    </ReactMarkdown>
                  </div>
                )}
              </div>

              <time className={`text-[10px] mt-2 block font-variant-numeric-tabular-nums ${isUser ? "text-right text-blue-100" : "text-left text-gray-500 opacity-70"}`}>
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
