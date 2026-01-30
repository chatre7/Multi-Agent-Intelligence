import { useCallback, useEffect, useState } from "react";
import { Outlet } from "react-router";
import ChatLayout from "../components/layout/ChatLayout";
import { useConversationStore } from "../../infrastructure/stores/conversationStore";
import { apiClient } from "../../infrastructure/api/apiClient";

export default function ChatRouteLayout() {
  const store = useConversationStore();
  const [selectedDomainId, setSelectedDomainId] = useState<string>("");
  const [selectedAgentId, setSelectedAgentId] = useState<string>("");
  const [sidebarOpen, setSidebarOpen] = useState(true);

  useEffect(() => {
    if (selectedDomainId && selectedAgentId && !store.currentConversation) {
      store.startNewConversation(selectedDomainId, selectedAgentId);
    }
  }, [selectedDomainId, selectedAgentId, store.currentConversation]);

  const handleNewChat = useCallback(() => {
    store.setCurrentConversation(null);
  }, [store]);

  const handleSelectConversation = useCallback(
    async (id: string, domainId?: string) => {
      try {
        if (domainId) {
          setSelectedDomainId(domainId);
        }
        const conv = await apiClient.getConversation(id);
        store.setCurrentConversation(conv);
        setSelectedDomainId(conv.domain_id);
        setSelectedAgentId(conv.agent_id);
      } catch (err) {
        console.error("Failed to load conversation", err);
      }
    },
    [store],
  );

  return (
    <ChatLayout
      sidebarOpen={sidebarOpen}
      setSidebarOpen={setSidebarOpen}
      selectedDomainId={selectedDomainId}
      selectedAgentId={selectedAgentId}
      onDomainSelect={setSelectedDomainId}
      onAgentSelect={setSelectedAgentId}
      onSelectConversation={handleSelectConversation}
      onNewChat={handleNewChat}
    >
      <Outlet />
    </ChatLayout>
  );
}

