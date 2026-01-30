/**
 * Main chat container with proper scrolling
 */

import { useEffect, useRef, useState } from "react";
import { useConversationStore } from "../../../infrastructure/stores/conversationStore";
import { WebSocketClient } from "../../../infrastructure/websocket/WebSocketClient";
import { apiClient } from "../../../infrastructure/api/apiClient";
import type { Message } from "../../../domain/entities/types";
import ChatMessage from "./ChatMessage";
import ToolApprovalCard from "./ToolApprovalCard";
import ChatInput from "./ChatInput";
import { resolveWsEndpointUrl } from "../../../infrastructure/config/urls";

interface ChatContainerProps {
  conversationId?: string;
  token: string;
}

export default function ChatContainer({
  conversationId,
  token,
}: ChatContainerProps) {
  const store = useConversationStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocketClient | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [thinkingEnabled, setThinkingEnabled] = useState(false);

  // Initialize WebSocket
  useEffect(() => {
    const initWebSocket = async () => {
      try {
        setIsConnecting(true);
        const wsUrl = resolveWsEndpointUrl();
        console.log("[ChatContainer] Connecting to:", wsUrl);

        wsRef.current = new WebSocketClient({
          url: wsUrl,
          token,
        });

        wsRef.current.on("message_chunk", (data) => {
          store.appendMessageDelta(data.chunk || "");
        });

        wsRef.current.on("message_complete", (data) => {
          store.setIsStreaming(false);
          // Update agent_id from message_complete (handles both casing)
          const agentId = data.agentId || data.agent_id;
          if (agentId) {
            store.updateLastMessageAgentId(agentId);
          }
        });

        wsRef.current.on("tool_approval_required", (data) => {
          const payload = data.payload || data;
          if (payload?.requestId) {
            store.addPendingApproval({
              requestId: payload.requestId,
              toolName: payload.toolName,
              toolArgs: payload.toolArgs,
              description: payload.description,
              agentName: payload.agentName || "System"
            });
          }
        });

        wsRef.current.on("agent_selected", (data) => {
          const agentId = data.agent_id || data.agentId;
          if (agentId) {
            store.updateLastMessageAgentId(agentId);
          }
        });

        wsRef.current.on("workflow_handoff", (data) => {
          const payload = data.payload || data;
          if (payload?.toAgent) {
            store.addHandoffMarker(
              payload.fromAgent || "Router",
              payload.toAgent || "Unknown"
            );
          }
        });

        wsRef.current.on("workflow_thought", (data) => {
          const payload = data.payload || data;
          if (payload?.reason) {
            store.appendThought(payload.reason, payload.agentName || "System");
          }
        });

        wsRef.current.on("error", (data) => {
          console.error("[ChatContainer] WebSocket Error Event:", data);
          store.setError(data.error || "An error occurred");
          store.setIsStreaming(false);
        });

        await wsRef.current.connect();
        setIsConnecting(false);

        if (conversationId) {
          // Check if we already have this conversation loaded with messages
          if (store.currentConversation?.id === conversationId && store.currentConversation.messages.length > 0) {
            console.log("[ChatContainer] Conversation already loaded");
            return;
          }

          try {
            const conversation = await apiClient.getConversation(conversationId);
            store.setCurrentConversation(conversation);
          } catch (error) {
            console.error("Failed to load conversation:", error);
          }
        }
      } catch (error) {
        console.error("WebSocket connection exception:", error);
        store.setError(
          error instanceof Error ? error.message : "Failed to connect to chat service",
        );
        setIsConnecting(false);
      }
    };

    if (token) {
      initWebSocket();
    }

    return () => {
      wsRef.current?.disconnect();
    };
  }, [conversationId, token]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [store.currentConversation?.messages]);

  const handleSendMessage = (content: string) => {
    if (!content.trim() || !wsRef.current?.isConnected()) {
      return;
    }

    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      role: "user",
      content,
      timestamp: new Date().toISOString(),
      created_at: new Date().toISOString(),
    };
    store.addMessage(userMessage);

    store.setIsStreaming(true);
    wsRef.current.send({
      type: "send_message",
      conversationId: conversationId,
      payload: {
        content: content,
        enableThinking: thinkingEnabled,
      },
    } as any);

    const assistantMessage: Message = {
      id: `msg-${Date.now() + 1}`,
      role: "assistant",
      content: "",
      timestamp: new Date().toISOString(),
      created_at: new Date().toISOString(),
    };
    store.addMessage(assistantMessage);
  };

  const handleApprove = (requestId: string) => {
    if (wsRef.current && store.currentConversation) {
      wsRef.current.send({
        type: "approve_tool",
        conversationId: store.currentConversation.id,
        requestId: requestId,
        payload: { approved: true }
      } as any);
      store.removePendingApproval(requestId);
    }
  };

  const handleReject = (requestId: string) => {
    if (wsRef.current && store.currentConversation) {
      wsRef.current.send({
        type: "approve_tool",
        conversationId: store.currentConversation.id,
        requestId: requestId,
        payload: { approved: false, reason: "User rejected via UI" }
      } as any);
      store.removePendingApproval(requestId);
    }
  };

  if (!store.currentConversation) {
    return null;
  }

  if (!store.currentConversation) {
    return null;
  }

  const isEmpty = store.currentConversation.messages.length === 0 && store.pendingApprovals.length === 0;

  return (
    <div className="h-full flex flex-col relative">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto min-h-0 scrollbar-thin scrollbar-thumb-gray-200">
        {isEmpty ? (
          <div className="h-full flex flex-col items-center justify-center p-4">
            <h2 className="text-2xl font-semibold text-gray-800 mb-2">How can I help you today?</h2>
            <p className="text-gray-500 mb-8">Select a capability to get started</p>

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 max-w-[90%] w-full">
              {[
                { label: "Analyze Code", desc: "Review project structure", prompt: "Can you analyze the current project structure?" },
                { label: "Find Bugs", desc: "Debug current file", prompt: "I need help debugging the currently open file." },
                { label: "Plan Feature", desc: "Create implementation plan", prompt: "Draft a plan for a new feature." },
                { label: "Explain Concepts", desc: "Understand architecture", prompt: "Explain the architecture of this system." }
              ].map((chip) => (
                <button
                  key={chip.label}
                  onClick={() => handleSendMessage(chip.prompt)}
                  className="p-4 border border-gray-200 rounded-xl hover:bg-gray-50 hover:border-gray-300 transition-all text-left group"
                >
                  <div className="font-medium text-gray-700 group-hover:text-blue-600 mb-1">{chip.label}</div>
                  <div className="text-xs text-gray-400">{chip.desc}</div>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="pb-32"> {/* Padding for input area */}
            {store.currentConversation.messages.map((message, index) => {
              const messages = store.currentConversation!.messages;
              const isLast = index === messages.length - 1;

              // Smart isStreaming logic
              let isMsgStreaming = store.isStreaming && isLast;
              if (store.isStreaming && message.role === 'assistant') {
                let lastAssistantIndex = -1;
                for (let i = messages.length - 1; i >= 0; i--) {
                  if (messages[i].role === 'assistant') {
                    lastAssistantIndex = i;
                    break;
                  }
                }
                if (index === lastAssistantIndex) isMsgStreaming = true;
              }

              return (
                <ChatMessage
                  key={message.id}
                  message={message}
                  isLast={isLast}
                  isStreaming={isMsgStreaming}
                />
              );
            })}

            {store.pendingApprovals.map((req) => (
              <ToolApprovalCard
                key={req.requestId}
                request={req}
                onApprove={handleApprove}
                onReject={handleReject}
              />
            ))}
            <div ref={messagesEndRef} className="h-4" />
          </div>
        )}
      </div>

      {/* Input Area (Fixed/Floating at bottom) */}
      <div className="absolute bottom-0 left-0 w-full p-4 pointer-events-none">
        {/* Error Banner */}
        {store.error && (
          <div className="max-w-3xl mx-auto mb-2 px-4 py-2 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg flex items-center justify-between shadow-sm pointer-events-auto">
            <span>{store.error}</span>
            <button
              onClick={() => store.clearError()}
              className="ml-4 font-semibold hover:underline"
            >
              Dismiss
            </button>
          </div>
        )}

        <div className="pointer-events-auto">
          <ChatInput
            onSendMessage={handleSendMessage}
            disabled={
              !wsRef.current?.isConnected() || isConnecting || store.isStreaming
            }
            isLoading={isConnecting}
            thinkingEnabled={thinkingEnabled}
            onThinkingChange={setThinkingEnabled}
          />
        </div>
      </div>
    </div>
  );
}
