import { useState, type ReactNode } from "react";
import { useNavigate } from "react-router";
import ChatSidebar from "../chat/ChatSidebar"; // Or generic Sidebar if refactored
import { useConversationStore } from "../../../infrastructure/stores/conversationStore";
import { SidebarLayoutProvider } from "./SidebarLayoutContext";

// Using ChatSidebar for consistency, even on Admin page
// We need to handle the props it expects. 
// Ideally we would split ChatSidebar into "NavSidebar" and "ChatHistorySidebar"
// For now, we'll pass dummy props or logic to allow it to render.

interface PageLayoutProps {
    children: ReactNode;
}

export default function PageLayout({ children }: PageLayoutProps) {
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const store = useConversationStore();
    const navigate = useNavigate();

    return (
        <SidebarLayoutProvider value={{ sidebarOpen, setSidebarOpen }}>
            <div className="flex-1 min-h-0 w-full flex bg-gradient-to-br from-slate-50 via-white to-blue-50 overflow-hidden">
                {/* Sidebar */}
                <div
                    className={`${sidebarOpen ? "w-80 opacity-100" : "w-0 opacity-0"
                        } transition-all duration-300 ease-in-out flex-shrink-0 relative border-r border-gray-200 bg-white/80 backdrop-blur-sm`}
                >
                    <ChatSidebar
                        isOpen={sidebarOpen}
                        mode="nav"
                        onSelectConversation={(id) => {
                            // If checking history on Admin page, maybe navigate?
                            // For now, minimal support
                            console.log("Selected from Admin:", id);
                        }}
                        onNewChat={() => {
                            store.setCurrentConversation(null);
                            navigate("/chat");
                        }}
                    />
                </div>

                {/* Main Content */}
                <main className="flex-1 min-w-0 min-h-0 flex flex-col relative">
                    <div className="flex-1 min-h-0 overflow-hidden relative flex flex-col">
                        {children}
                    </div>
                </main>
            </div>
        </SidebarLayoutProvider>
    );
}
