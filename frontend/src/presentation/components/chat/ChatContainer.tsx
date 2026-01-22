/**
 * Main chat container component
 */

import { useEffect, useRef, useState } from "react";
import { useConversationStore } from "../../../infrastructure/stores/conversationStore";
import { WebSocketClient } from "../../../infrastructure/websocket/WebSocketClient";
import { apiClient } from "../../../infrastructure/api/apiClient";
import type { Message } from "../../../domain/entities/types";
import ChatMessage from "./ChatMessage";
import ChatInput from "./ChatInput";

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
        const wsUrl = `ws://localhost:8000/ws/chat/${conversationId || "new"}`;
        wsRef.current = new WebSocketClient({
          url: wsUrl,
          token,
        });

        wsRef.current.on("MESSAGE_CHUNK", (data) => {
          store.appendMessageDelta(data.chunk || "");
        });

        wsRef.current.on("MESSAGE_COMPLETE", () => {
          store.setIsStreaming(false);
        });

        wsRef.current.on("TOOL_APPROVAL_REQUIRED", (data) => {
          console.log("Tool approval required:", data);
          // Handle tool approval UI
        });

        wsRef.current.on("ERROR", (data) => {
          store.setError(data.error || "An error occurred");
          store.setIsStreaming(false);
        });

        await wsRef.current.connect();
        setIsConnecting(false);

        // Load existing conversation if ID provided
        if (conversationId) {
          try {
            const conversation =
              await apiClient.getConversation(conversationId);
            store.setCurrentConversation(conversation);
          } catch (error) {
            console.error("Failed to load conversation:", error);
          }
        }
      } catch (error) {
        console.error("WebSocket connection failed:", error);
        store.setError("Failed to connect to chat service");
        setIsConnecting(false);
      }
    };

    if (token) {
      initWebSocket();
    }

    return () => {
      wsRef.current?.disconnect();
    };
  }, [conversationId, token, store]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [store.currentConversation?.messages]);

  const handleSendMessage = (content: string) => {
    if (!content.trim() || !wsRef.current?.isConnected()) {
      return;
    }

    // Add user message to store
    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      role: "user",
      content,
      timestamp: new Date().toISOString(),
    };
    store.addMessage(userMessage);

    // Send via WebSocket
    store.setIsStreaming(true);
    wsRef.current.send({
      type: "SEND_MESSAGE",
      data: {
        message: content,
      },
    });

    // Add assistant message placeholder
    const assistantMessage: Message = {
      id: `msg-${Date.now() + 1}`,
      role: "assistant",
      content: "",
      timestamp: new Date().toISOString(),
    };
    store.addMessage(assistantMessage);
  };

  if (!store.currentConversation) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <p className="text-gray-500 mb-4">
            Select a domain and agent to start chatting
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {store.currentConversation.messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-400">
            <p>Start a conversation</p>
          </div>
        ) : (
          <>
            {store.currentConversation.messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Error message */}
      {store.error && (
        <div className="px-4 py-2 bg-red-100 text-red-700 text-sm rounded">
          {store.error}
          <button
            onClick={() => store.clearError()}
            className="ml-2 font-bold hover:underline"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Input */}
      <ChatInput
        onSendMessage={handleSendMessage}
        disabled={
          !wsRef.current?.isConnected() || isConnecting || store.isStreaming
        }
        isLoading={isConnecting}
      />
    </div>
  );
}
