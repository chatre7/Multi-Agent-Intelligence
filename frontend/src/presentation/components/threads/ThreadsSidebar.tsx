import React, { useState, useEffect } from 'react';
import { useNavigate, useParams, Link, useLocation } from 'react-router';
import {
    Home,
    Clock, Plus, MessageSquare, Sparkles, Settings
} from 'lucide-react';
import { MAIN_NAV_ITEMS } from '../../config/appNavigation';
import { apiClient } from '../../../infrastructure/api/apiClient';
import type { Conversation } from '../../../domain/entities/types';

export type ThreadCategory = 'all' | 'requests' | 'brainstorming' | 'archived';

interface ThreadsSidebarProps {
    activeCategory: ThreadCategory;
    onSelectCategory: (category: ThreadCategory) => void;
    isMobile?: boolean;
    isOpen?: boolean;
    onClose?: () => void;
    onNewRequest?: () => void;
}

const CATEGORIES: { id: ThreadCategory; label: string; icon: React.ReactNode }[] = [
    { id: 'all', label: 'All Requests', icon: <Home size={18} /> },
    { id: 'requests', label: 'Open Requests', icon: <MessageSquare size={18} /> },
    { id: 'brainstorming', label: 'Brainstorming', icon: <Sparkles size={18} /> },
    { id: 'archived', label: 'Archived', icon: <Clock size={18} /> },
];

export const ThreadsSidebar: React.FC<ThreadsSidebarProps> = ({
    activeCategory,
    onSelectCategory,
    isMobile = false,
    isOpen = false,
    onClose,
    onNewRequest
}) => {
    const navigate = useNavigate();
    const { id: urlId } = useParams<{ id: string }>();
    const [recentThreads, setRecentThreads] = useState<Conversation[]>([]);
    const location = useLocation();

    useEffect(() => {
        loadRecents();
    }, [urlId]);

    const loadRecents = async () => {
        try {
            const convos = await apiClient.listConversations('social_simulation');
            setRecentThreads(convos.slice(0, 5));
        } catch (e) {
            console.error("Failed to load recents:", e);
        }
    };

    const mobileClasses = isMobile
        ? `fixed inset-y-0 left-0 z-50 w-80 bg-white shadow-2xl transform transition-transform duration-300 ease-in-out border-r border-gray-100 ${isOpen ? 'translate-x-0' : '-translate-x-full'}`
        : "flex flex-col h-full w-full";

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

    const content = (
        <div className="flex flex-col h-full bg-slate-50/50">
            {/* Header */}
            <div className="p-4 bg-white border-b border-gray-100">
                <Link to="/" className="flex items-center gap-2 px-1 mb-4">
                    <div className="w-8 h-8 bg-black rounded-lg flex items-center justify-center text-white">
                        <MessageSquare size={18} fill="currentColor" />
                    </div>
                    <span className="font-bold text-lg tracking-tight text-gray-900">
                        Multi-Agent<span className="text-blue-600">.ai</span>
                    </span>
                </Link>
                <button
                    onClick={onNewRequest}
                    className="w-full flex items-center gap-3 px-4 py-3 bg-white hover:bg-gray-50 text-gray-900 rounded-xl transition-all duration-200 border border-gray-200 shadow-sm hover:shadow-md group active:scale-[0.98]"
                >
                    <div className="w-8 h-8 bg-blue-50 text-blue-600 rounded-lg flex items-center justify-center group-hover:bg-blue-600 group-hover:text-white transition-colors">
                        <Plus size={18} strokeWidth={2.5} />
                    </div>
                    <span className="font-semibold">New Request</span>
                </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-6">

                {/* Categories */}
                <div>
                    <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3 px-2">
                        Views
                    </h3>
                    <div className="space-y-1">
                        {CATEGORIES.map(cat => (
                            <button
                                key={cat.id}
                                onClick={() => {
                                    onSelectCategory(cat.id);
                                    if (isMobile && onClose) onClose();
                                }}
                                className={`w-full text-left px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-3
                                    ${activeCategory === cat.id
                                        ? 'bg-white text-blue-600 shadow-sm border border-gray-100'
                                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'}`}
                            >
                                {cat.icon}
                                <span>{cat.label}</span>
                            </button>
                        ))}
                    </div>
                </div>

                {/* Recent Threads */}
                {recentThreads.length > 0 && (
                    <div>
                        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3 px-2">
                            Recent Activity
                        </h3>
                        <div className="space-y-1">
                            {recentThreads.map(convo => (
                                <button
                                    key={convo.id}
                                    onClick={() => {
                                        navigate(`/threads/${convo.id}`);
                                        if (isMobile && onClose) onClose();
                                    }}
                                    className={`w-full text-left px-3 py-2.5 rounded-lg text-sm transition-all group border border-transparent 
                                        ${urlId === convo.id
                                            ? 'bg-blue-50 border-blue-100 text-blue-700 shadow-sm'
                                            : 'text-gray-600 hover:bg-white hover:border-gray-200 hover:shadow-sm'}`}
                                >
                                    <div className="font-medium truncate mb-0.5">
                                        {convo.title || "Untitled Request"}
                                    </div>
                                    <div className="text-xs text-gray-400 truncate flex items-center gap-1">
                                        <Clock size={10} />
                                        <span>{convo.id.slice(0, 8)}</span>
                                    </div>
                                </button>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* Footer */}
            <div className="p-3 border-t border-gray-200 bg-gray-100/50 space-y-1">
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

                <div className="flex items-center justify-between px-3 py-2 text-sm text-gray-500 hover:text-gray-900 cursor-pointer rounded-lg hover:bg-white transition-colors">
                    <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded-full bg-gray-300 flex items-center justify-center text-[10px] text-white font-bold">U</div>
                        <span>User</span>
                    </div>
                    <Settings size={16} />
                </div>
            </div>
        </div>
    );

    if (isMobile) {
        return (
            <>
                {isOpen && (
                    <div
                        className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40 transition-opacity"
                        onClick={onClose}
                    />
                )}
                <div className={mobileClasses}>
                    {content}
                </div>
            </>
        )
    }

    return content;
};
