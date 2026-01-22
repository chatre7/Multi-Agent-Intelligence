/**
 * Zustand store for conversation state management
 */

import { create } from "zustand";
import type { Conversation, Message } from "../../domain/entities/types";

interface ConversationStore {
  // State
  conversations: Conversation[];
  currentConversation: Conversation | null;
  isLoading: boolean;
  error: string | null;
  isStreaming: boolean;

  // Actions
  setConversations: (conversations: Conversation[]) => void;
  setCurrentConversation: (conversation: Conversation | null) => void;
  addMessage: (message: Message) => void;
  appendMessageDelta: (delta: string) => void;
  setIsLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setIsStreaming: (streaming: boolean) => void;
  startNewConversation: (domainId: string, agentId: string) => void;
  clearError: () => void;
}

export const useConversationStore = create<ConversationStore>((set) => ({
  conversations: [],
  currentConversation: null,
  isLoading: false,
  error: null,
  isStreaming: false,

  setConversations: (conversations) => set({ conversations }),

  setCurrentConversation: (conversation) =>
    set({ currentConversation: conversation }),

  addMessage: (message) =>
    set((state) => {
      if (!state.currentConversation) return state;
      return {
        currentConversation: {
          ...state.currentConversation,
          messages: [...state.currentConversation.messages, message],
        },
      };
    }),

  appendMessageDelta: (delta) =>
    set((state) => {
      if (
        !state.currentConversation ||
        state.currentConversation.messages.length === 0
      ) {
        return state;
      }
      const messages = [...state.currentConversation.messages];
      const lastMessage = messages[messages.length - 1];
      messages[messages.length - 1] = {
        ...lastMessage,
        content: lastMessage.content + delta,
        delta,
      };
      return {
        currentConversation: {
          ...state.currentConversation,
          messages,
        },
      };
    }),

  setIsLoading: (loading) => set({ isLoading: loading }),

  setError: (error) => set({ error }),

  setIsStreaming: (streaming) => set({ isStreaming: streaming }),

  startNewConversation: (domainId, agentId) =>
    set({
      currentConversation: {
        id: `temp-${Date.now()}`,
        domain_id: domainId,
        agent_id: agentId,
        title: "New Conversation",
        messages: [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    }),

  clearError: () => set({ error: null }),
}));
