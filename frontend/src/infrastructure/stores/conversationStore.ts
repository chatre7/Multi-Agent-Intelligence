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
      if (!state.currentConversation || state.currentConversation.messages.length === 0) {
        return state;
      }
      const messages = [...state.currentConversation.messages];

      // Find the last assistant message to append to (ignoring system handoff markers)
      let targetIndex = -1;
      for (let i = messages.length - 1; i >= 0; i--) {
        if (messages[i].role === 'assistant') {
          targetIndex = i;
          break;
        }
      }

      if (targetIndex === -1) return state;

      messages[targetIndex] = {
        ...messages[targetIndex],
        content: messages[targetIndex].content + delta,
        delta,
      };

      return {
        currentConversation: { ...state.currentConversation, messages },
      };
    }),

  updateLastMessageAgentId: (agentId) =>
    set((state) => {
      if (!state.currentConversation || state.currentConversation.messages.length === 0) {
        return state;
      }
      const messages = [...state.currentConversation.messages];

      // Find the last assistant message to update
      let targetIndex = -1;
      for (let i = messages.length - 1; i >= 0; i--) {
        if (messages[i].role === 'assistant') {
          targetIndex = i;
          break;
        }
      }

      if (targetIndex === -1) return state;

      messages[targetIndex] = {
        ...messages[targetIndex],
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
      if (!state.currentConversation || state.currentConversation.messages.length === 0) {
        return state;
      }
      const messages = [...state.currentConversation.messages];

      // Find the last assistant message to attach thoughts to
      let targetIndex = -1;
      for (let i = messages.length - 1; i >= 0; i--) {
        if (messages[i].role === 'assistant') {
          targetIndex = i;
          break;
        }
      }

      if (targetIndex === -1) return state;

      const targetMessage = { ...messages[targetIndex] };
      const thoughts = targetMessage.thoughts ? [...targetMessage.thoughts] : [];

      if (thoughts.length > 0 && thoughts[thoughts.length - 1].agentName === agentName) {
        // Update existing thought
        thoughts[thoughts.length - 1] = {
          ...thoughts[thoughts.length - 1],
          content: (thoughts[thoughts.length - 1].content || "") + thought,
          timestamp: new Date().toISOString(),
        };
      } else {
        // Add new thought entry
        thoughts.push({
          content: thought,
          agentName,
          timestamp: new Date().toISOString(),
        });
      }

      messages[targetIndex] = { ...targetMessage, thoughts };

      return {
        currentConversation: { ...state.currentConversation, messages },
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
