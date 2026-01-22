/**
 * Main chat page
 */

import { useState } from "react";
import { useConversationStore } from "../../infrastructure/stores/conversationStore";
import { apiClient } from "../../infrastructure/api/apiClient";
import ChatContainer from "../components/chat/ChatContainer";
import DomainSelector from "../components/selectors/DomainSelector";

interface ChatPageProps {
  token: string;
}

export default function ChatPage({ token }: ChatPageProps) {
  const store = useConversationStore();
  const [selectedDomainId, setSelectedDomainId] = useState<string>("");
  const [selectedAgentId, setSelectedAgentId] = useState<string>("");

  const handleStartConversation = async () => {
    if (!selectedDomainId || !selectedAgentId) {
      return;
    }

    try {
      const conversation = await apiClient.startConversation(
        selectedDomainId,
        selectedAgentId,
      );
      store.setCurrentConversation(conversation);
    } catch (error) {
      console.error("Failed to start conversation:", error);
      store.setError("Failed to start conversation");
    }
  };

  return (
    <div className="flex gap-4 h-screen bg-gray-50 p-4">
      {/* Sidebar */}
      <div className="w-80 flex flex-col gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            Multi-Agent Chat
          </h1>
          <p className="text-sm text-gray-600 mb-4">
            Select a domain and agent to start chatting with the multi-agent
            system.
          </p>
        </div>

        <DomainSelector
          selectedDomainId={selectedDomainId}
          selectedAgentId={selectedAgentId}
          onDomainSelect={setSelectedDomainId}
          onAgentSelect={setSelectedAgentId}
          onStartConversation={handleStartConversation}
        />

        {/* Conversation history */}
        {store.currentConversation && (
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="font-semibold text-gray-900 mb-2">Conversation</h3>
            <p className="text-sm text-gray-600">
              {store.currentConversation.title}
            </p>
            <p className="text-xs text-gray-500 mt-2">
              {store.currentConversation.messages.length} messages
            </p>
          </div>
        )}
      </div>

      {/* Chat area */}
      <div className="flex-1 bg-white rounded-lg shadow overflow-hidden flex flex-col">
        {store.currentConversation ? (
          <ChatContainer
            conversationId={store.currentConversation.id}
            token={token}
          />
        ) : (
          <div className="flex items-center justify-center h-full text-gray-400">
            <p>Select a domain and agent to start chatting</p>
          </div>
        )}
      </div>
    </div>
  );
}
