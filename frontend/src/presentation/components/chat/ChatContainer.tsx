/**
 * Main chat container with proper scrolling
 */

import { useEffect, useRef, useState } from "react";
import { useConversationStore } from "../../../infrastructure/stores/conversationStore";
import { WebSocketClient } from "../../../infrastructure/websocket/WebSocketClient";
import { apiClient } from "../../../infrastructure/api/apiClient";
import type { Message } from "../../../domain/entities/types";
import ChatMessage from "./ChatMessage";
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
          // Update agent_id from message_complete payload
          if (data.agentId) {
            store.updateLastMessageAgentId(data.agentId);
          }
        });

        wsRef.current.on("tool_approval_required", (data) => {
          console.log("Tool approval required:", data);
        });

        wsRef.current.on("agent_selected", (data) => {
          if (data.agent_id) {
            store.updateLastMessageAgentId(data.agent_id);
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
    };
    store.addMessage(userMessage);

    store.setIsStreaming(true);
    wsRef.current.send({
      type: "send_message",
      conversationId: conversationId,
      payload: {
        content: content,
      },
    } as any);

    const assistantMessage: Message = {
      id: `msg-${Date.now() + 1}`,
      role: "assistant",
      content: "",
      timestamp: new Date().toISOString(),
    };
    store.addMessage(assistantMessage);
  };

  if (!store.currentConversation) {
    return null;
  }

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Messages - Fixed height with scroll */}
      <div className="flex-1 overflow-y-auto min-h-0">
        {store.currentConversation.messages.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center px-4">
              <p className="text-gray-400 text-sm">Start a conversation…</p>
            </div>
          </div>
        ) : (
          <>
            {store.currentConversation.messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
            <div ref={messagesEndRef} className="h-4" />
          </>
        )}
      </div>

      {/* Error Banner */}
      {store.error && (
        <div className="mx-4 mb-3 px-4 py-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-xl flex items-center justify-between shadow-sm">
          <span>{store.error}</span>
          <button
            onClick={() => store.clearError()}
            className="ml-4 font-semibold hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-400 focus-visible:ring-offset-2 rounded px-2 py-1"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Input - Fixed at bottom */}
      <div className="border-t border-gray-200 bg-white p-4">
        <ChatInput
          onSendMessage={handleSendMessage}
          disabled={
            !wsRef.current?.isConnected() || isConnecting || store.isStreaming
          }
          isLoading={isConnecting}
        />
      </div>
    </div>
  );
}
