/**
 * Main chat page with proper height constraints
 */

import { useState } from "react";
import { useConversationStore } from "../../infrastructure/stores/conversationStore";
import { apiClient } from "../../infrastructure/api/apiClient";
import ChatContainer from "../components/chat/ChatContainer";
import DomainSelector from "../components/selectors/DomainSelector";
import { MessageSquare, Sparkles, PanelLeftClose, PanelLeftOpen } from "lucide-react";

interface ChatPageProps {
  token: string;
}

export default function ChatPage({ token }: ChatPageProps) {
  const store = useConversationStore();
  const [selectedDomainId, setSelectedDomainId] = useState<string>("");
  const [selectedAgentId, setSelectedAgentId] = useState<string>("");
  const [sidebarOpen, setSidebarOpen] = useState(true);

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
    <div className="h-full flex bg-gradient-to-br from-slate-50 via-white to-blue-50 overflow-hidden">
      {/* Sidebar - Collapsible */}
      <aside
        className={`${sidebarOpen ? "w-80" : "w-0"
          } transition-all duration-300 ease-in-out border-r border-gray-200 bg-white/80 backdrop-blur-sm flex flex-col overflow-hidden flex-shrink-0`}
      >
        {sidebarOpen && (
          <div className="h-full flex flex-col p-6 overflow-y-auto">
            {/* Header */}
            <div className="flex-shrink-0 mb-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg">
                  <Sparkles size={20} className="text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                    Multi-Agent AI
                  </h1>
                  <p className="text-xs text-gray-500">Intelligent Collaboration</p>
                </div>
              </div>
              <p className="text-sm text-gray-600 leading-relaxed">
                Select a domain and start collaborating with our specialized AI agents.
              </p>
            </div>

            {/* Domain Selector */}
            <div className="flex-shrink-0 mb-6">
              <DomainSelector
                selectedDomainId={selectedDomainId}
                selectedAgentId={selectedAgentId}
                onDomainSelect={setSelectedDomainId}
                onAgentSelect={setSelectedAgentId}
                onStartConversation={handleStartConversation}
              />
            </div>

            {/* Active Conversation - Push to bottom */}
            {store.currentConversation && (
              <div className="mt-auto flex-shrink-0">
                <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-xl p-4 border border-blue-100/50 shadow-sm">
                  <div className="flex items-center gap-2 mb-2">
                    <MessageSquare size={16} className="text-blue-600" />
                    <h3 className="font-semibold text-gray-900 text-sm">Active Session</h3>
                  </div>
                  <p className="text-sm text-gray-700 mb-1 truncate">
                    {store.currentConversation.title}
                  </p>
                  <div className="flex items-center gap-4 text-xs text-gray-600">
                    <span>{store.currentConversation.messages.length} messages</span>
                    <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span>
                    <span className="text-green-600 font-medium">Active</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </aside>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Toggle Button */}
        <div className="flex-shrink-0 p-4">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 rounded-lg bg-white border border-gray-200 hover:bg-gray-50 hover:shadow-md transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
            aria-label={sidebarOpen ? "Close sidebar" : "Open sidebar"}
          >
            {sidebarOpen ? (
              <PanelLeftClose size={20} className="text-gray-600" />
            ) : (
              <PanelLeftOpen size={20} className="text-gray-600" />
            )}
          </button>
        </div>

        {/* Chat Content - Takes remaining height */}
        <div className="flex-1 min-h-0">
          {store.currentConversation ? (
            <ChatContainer
              conversationId={store.currentConversation.id}
              token={token}
            />
          ) : (
            <div className="h-full flex items-center justify-center">
              <div className="text-center max-w-md px-4">
                <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-blue-100 to-purple-100 flex items-center justify-center">
                  <MessageSquare size={32} className="text-blue-600" />
                </div>
                <h2 className="text-2xl font-bold text-gray-900 mb-3">
                  Welcome to Multi-Agent AI
                </h2>
                <p className="text-gray-600 leading-relaxed">
                  Select a domain and agent from the sidebar to start an intelligent conversation.
                </p>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
