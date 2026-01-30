import type { ReactNode } from "react";
import ChatSidebar from "../chat/ChatSidebar";
import ChatHeader from "../chat/ChatHeader";

interface ChatLayoutProps {
    children: ReactNode;
    sidebarOpen: boolean;
    setSidebarOpen: (open: boolean) => void;
    selectedDomainId: string;
    selectedAgentId: string;
    onDomainSelect: (id: string) => void;
    onAgentSelect: (id: string) => void;
    onSelectConversation: (id: string) => void;
    onNewChat: () => void;
}

export default function ChatLayout({
    children,
    sidebarOpen,
    setSidebarOpen,
    selectedDomainId,
    selectedAgentId,
    onDomainSelect,
    onAgentSelect,
    onSelectConversation,
    onNewChat,
}: ChatLayoutProps) {
    return (
        <div className="flex-1 min-h-0 w-full flex bg-gradient-to-br from-slate-50 via-white to-blue-50 overflow-hidden">
            {/* Sidebar */}
            <div
                className={`${sidebarOpen ? "w-80 opacity-100" : "w-0 opacity-0"
                    } transition-all duration-300 ease-in-out flex-shrink-0 relative border-r border-gray-200 bg-white/80 backdrop-blur-sm`}
            >
                <ChatSidebar
                    isOpen={sidebarOpen}
                    onSelectConversation={onSelectConversation}
                    onNewChat={onNewChat}
                />
            </div>

            {/* Main Content Area */}
            <div className="flex-1 min-w-0 min-h-0 flex flex-col relative">
                <ChatHeader
                    sidebarOpen={sidebarOpen}
                    setSidebarOpen={setSidebarOpen}
                    selectedDomainId={selectedDomainId}
                    selectedAgentId={selectedAgentId}
                    onDomainSelect={onDomainSelect}
                    onAgentSelect={onAgentSelect}
                />

                <main className="flex-1 min-h-0 overflow-hidden relative flex flex-col">
                    {children}
                </main>
            </div>
        </div>
    );
}
