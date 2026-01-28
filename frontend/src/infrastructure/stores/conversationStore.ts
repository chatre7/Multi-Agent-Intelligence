/**
 * Zustand store for conversation state management
 */

import { create } from "zustand";
import type { Conversation, Message, ToolApprovalRequest } from "../../domain/entities/types";

interface ConversationStore {
  // State
  conversations: Conversation[];
  currentConversation: Conversation | null;
  isLoading: boolean;
  error: string | null;
  isStreaming: boolean;
  pendingApprovals: ToolApprovalRequest[];

  // Actions
  setConversations: (conversations: Conversation[]) => void;
  setCurrentConversation: (conversation: Conversation | null) => void;
  addMessage: (message: Message) => void;
  appendMessageDelta: (delta: string) => void;
  setIsLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setIsStreaming: (streaming: boolean) => void;
  startNewConversation: (domainId: string, agentId: string) => void;
  updateLastMessageAgentId: (agentId: string) => void;
  appendThought: (thought: string, agentName: string) => void;
  addPendingApproval: (request: ToolApprovalRequest) => void;
  removePendingApproval: (requestId: string) => void;
  addHandoffMarker: (fromAgent: string, toAgent: string) => void;
  clearError: () => void;
}

export const useConversationStore = create<ConversationStore>((set) => ({
  conversations: [],
  currentConversation: null,
  isLoading: false,
  error: null,
  isStreaming: false,
  pendingApprovals: [],

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

  updateLastMessageAgentId: (agentId) =>
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
        agent_id: agentId || '',
      };
      return {
        currentConversation: {
          ...(state.currentConversation as Conversation),
          messages,
        },
      };
    }),

  appendThought: (thought, agentName) =>
    set((state) => {
      if (
        !state.currentConversation ||
        state.currentConversation.messages.length === 0
      ) {
        return state;
      }
      const messages = [...state.currentConversation.messages];
      const lastMessage = messages[messages.length - 1];

      const newThought = {
        content: thought,
        agentName,
        timestamp: new Date().toISOString(),
      };

      const updatedThoughts = lastMessage.thoughts
        ? [...lastMessage.thoughts, newThought]
        : [newThought];

      messages[messages.length - 1] = {
        ...lastMessage,
        thoughts: updatedThoughts,
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
      pendingApprovals: [],
    }),

  addPendingApproval: (request) =>
    set((state) => ({
      pendingApprovals: [...state.pendingApprovals, request],
    })),

  removePendingApproval: (requestId) =>
    set((state) => ({
      pendingApprovals: state.pendingApprovals.filter(
        (req) => req.requestId !== requestId
      ),
    })),

  addHandoffMarker: (fromAgent, toAgent) =>
    set((state) => {
      const handoffMsg: Message = {
        id: `handoff-${Date.now()}`,
        role: "system",
        content: `Transferred from ${fromAgent} to ${toAgent}`,
        timestamp: new Date().toISOString(),
        metadata: { isHandoff: true, fromAgent, toAgent },
      };
      if (state.currentConversation) {
        return {
          currentConversation: {
            ...state.currentConversation,
            messages: [...state.currentConversation.messages, handoffMsg],
          },
        };
      }
      return state;
    }),

  clearError: () => set({ error: null }),
}));
