import { useEffect, useState, useMemo } from "react";
import { useConversationStore } from "../../../infrastructure/stores/conversationStore";
import { apiClient } from "../../../infrastructure/api/apiClient";
import { Plus, MessageSquare, Search, User, LogOut, Settings, Trash2 } from "lucide-react";
import { isToday, isYesterday, isThisWeek } from "date-fns";
import { useAuthStore } from "../../../infrastructure/stores/authStore";
import type { Conversation } from "../../../domain/entities/types";
import { Link, useLocation } from "react-router";
import { MAIN_NAV_ITEMS } from "../../config/appNavigation";

type ChatSidebarMode = "full" | "nav";

interface ChatSidebarProps {
    mode?: ChatSidebarMode;
    onSelectConversation?: (id: string, domainId: string) => void; // Updated signature
    onNewChat?: () => void;
    isOpen: boolean;
    selectedId?: string; // Add selectedId prop to highlight active chat properly
}

export default function ChatSidebar({
    mode = "full",
    onSelectConversation,
    onNewChat,
    isOpen,
    selectedId,
}: ChatSidebarProps) {
    const { conversations, setConversations, deleteConversation, currentConversation } = useConversationStore();
    const { user, logout } = useAuthStore();
    const [searchQuery, setSearchQuery] = useState("");
    const [isLoadingHistory, setIsLoadingHistory] = useState(false);
    const location = useLocation();

    // Load conversations on mount
    useEffect(() => {
        if (mode !== "full") return;
        const loadConversations = async () => {
            setIsLoadingHistory(true);
            try {
                const data = await apiClient.listConversations();
                // Sort by updated_at desc
                const sorted = data.sort((a: Conversation, b: Conversation) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());
                setConversations(sorted);
            } catch (err) {
                console.error("Failed to load history:", err);
            } finally {
                setIsLoadingHistory(false);
            }
        };
        // Only load if not already loaded? Or always refresh? 
        // For simplicity, reload.
        loadConversations();
    }, [mode, setConversations]);

    const filteredConversations = useMemo(() => {
        if (mode !== "full") return [];
        if (!searchQuery) return conversations;
        return conversations.filter((c: Conversation) =>
            (c.title || "New Conversation").toLowerCase().includes(searchQuery.toLowerCase())
        );
    }, [mode, conversations, searchQuery]);

    const groupedConversations = useMemo(() => {
        if (mode !== "full") {
            return {
                Today: [],
                Yesterday: [],
                "Previous 7 Days": [],
                Older: [],
            } satisfies Record<string, Conversation[]>;
        }
        const groups: Record<string, Conversation[]> = {
            "Today": [],
            "Yesterday": [],
            "Previous 7 Days": [],
            "Older": []
        };

        filteredConversations.forEach((c: Conversation) => {
            if (!c.updated_at) return;
            const date = new Date(c.updated_at);
            if (isToday(date)) {
                groups["Today"].push(c);
            } else if (isYesterday(date)) {
                groups["Yesterday"].push(c);
            } else if (isThisWeek(date)) { // isThisWeek handles "Previous 7 days" roughly
                groups["Previous 7 Days"].push(c);
            } else {
                groups["Older"].push(c);
            }
        });
        return groups;
    }, [mode, filteredConversations]);

    const handleLogout = () => {
        logout();
        apiClient.clearToken();
    };

    // Helper for Nav Links
    const MenuLink = ({ to, icon: Icon, label, active }: { to: string, icon: any, label: string, active: boolean }) => (
        <Link
            to={to}
            className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${active
                ? "bg-white text-blue-600 shadow-sm border border-gray-100"
                : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                }`}
        >
            <Icon size={18} />
            <span>{label}</span>
        </Link>
    );

    return (
        <div className={`w-[320px] h-full bg-gray-50 flex flex-col border-r border-gray-200 shadow-sm flex-shrink-0 transition-all duration-300 ${isOpen ? "ml-0" : "-ml-[320px]"}`}>

            {/* 1. Header: Logo + New Chat */}
            <div className="p-4 space-y-4 flex-shrink-0 bg-gray-50">
                {/* Logo Area */}
                <div className="flex items-center gap-2 px-1 mb-2">
                    <div className="w-8 h-8 bg-black rounded-lg flex items-center justify-center text-white">
                        <MessageSquare size={18} fill="currentColor" />
                    </div>
                    <span className="font-bold text-lg tracking-tight text-gray-900">
                        Multi-Agent<span className="text-blue-600">.ai</span>
                    </span>
                </div>

                {mode === "full" && (
                    <>
                        {/* New Chat Button */}
                        <button
                            onClick={() => onNewChat?.()}
                            className="w-full flex items-center gap-3 px-4 py-3 bg-white hover:bg-gray-50 text-gray-900 rounded-xl transition-all duration-200 border border-gray-200 shadow-sm hover:shadow-md group active:scale-[0.98]"
                        >
                            <div className="w-8 h-8 bg-blue-50 text-blue-600 rounded-lg flex items-center justify-center group-hover:bg-blue-600 group-hover:text-white transition-colors">
                                <Plus size={18} strokeWidth={2.5} />
                            </div>
                            <span className="font-semibold">New Chat</span>
                        </button>

                        {/* Search */}
                        <div className="relative group">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-blue-500 transition-colors" size={16} />
                            <input
                                type="text"
                                placeholder="Search chats..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="w-full pl-9 pr-4 py-2 bg-gray-100 border border-transparent focus:bg-white focus:border-blue-500/30 focus:shadow-sm rounded-lg text-sm focus:outline-none transition-all placeholder:text-gray-400"
                            />
                        </div>
                    </>
                )}
            </div>

            {/* 2. Chat History List */}
            {mode === "full" && (
                <div className="flex-1 overflow-y-auto px-3 py-0 space-y-4 scrollbar-thin scrollbar-thumb-gray-200">
                    {isLoadingHistory ? (
                        <div className="flex justify-center py-8">
                            <div className="w-6 h-6 border-2 border-gray-200 border-t-blue-500 rounded-full animate-spin"></div>
                        </div>
                    ) : (
                        Object.entries(groupedConversations).map(([label, items]) => (
                            items.length > 0 && (
                                <div key={label}>
                                    <h3 className="text-xs font-semibold text-gray-400 px-3 py-2 sticky top-0 bg-gray-50 z-10 uppercase tracking-wider backdrop-blur-sm bg-opacity-90">
                                        {label}
                                    </h3>
                                    <div className="space-y-1">
                                        {items.map((conv) => (
                                            <div
                                                key={conv.id}
                                                onClick={() => onSelectConversation?.(conv.id, conv.domain_id)}
                                                className={`group flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all cursor-pointer relative ${selectedId === conv.id || (!selectedId && currentConversation?.id === conv.id) // Fallback check
                                                    ? "bg-white text-blue-600 shadow-sm font-medium border border-gray-100"
                                                    : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                                                    }`}
                                            >
                                                <span className="truncate flex-1 pr-6">{conv.title || "New Chat"}</span>

                                                {/* Delete Action */}
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        deleteConversation(conv.id);
                                                    }}
                                                    className="absolute right-2 p-1.5 rounded-md text-gray-400 hover:text-red-500 hover:bg-red-50 opacity-0 group-hover:opacity-100 transition-all"
                                                    title="Delete Chat"
                                                >
                                                    <Trash2 size={14} />
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )
                        ))
                    )}
                    {!isLoadingHistory && conversations.length === 0 && (
                        <div className="text-center py-8 px-4 text-gray-400 text-sm">
                            No conversations found.
                        </div>
                    )}
                </div>
            )}

            {/* 3. Footer: Global Nav + User */}
            <div className="p-3 border-t border-gray-200 bg-gray-100/50 space-y-1 mt-auto">
                {MAIN_NAV_ITEMS.map((item) => (
                    <MenuLink
                        key={item.path}
                        to={item.path}
                        icon={item.icon}
                        label={item.label}
                        active={item.exact ? location.pathname === item.path : location.pathname.startsWith(item.path)}
                    />
                ))}

                <div className="h-px bg-gray-200 my-2 mx-2" />

                <div className="flex items-center justify-between p-2 rounded-lg hover:bg-white transition-all cursor-pointer group border border-transparent hover:border-gray-200 hover:shadow-sm">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-600 to-purple-600 flex items-center justify-center text-white font-bold text-xs ring-2 ring-white">
                            {user?.username?.[0]?.toUpperCase() || <User size={14} />}
                        </div>
                        <div className="flex flex-col">
                            <span className="text-sm font-semibold text-gray-700">{user?.username || "User"}</span>
                        </div>
                    </div>
                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button className="p-1.5 hover:bg-gray-100 rounded-md text-gray-500" title="Settings">
                            <Settings size={16} />
                        </button>
                        <button onClick={handleLogout} className="p-1.5 hover:bg-red-50 hover:text-red-600 rounded-md text-gray-500" title="Logout">
                            <LogOut size={16} />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
