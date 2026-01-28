
import React from 'react';
import { useNavigate, useParams } from 'react-router';
import {
    Home, Search, Heart, User,
    Settings, X, Sparkles, ArrowLeft,
    Clock
} from 'lucide-react';
import { apiClient } from '../../../infrastructure/api/apiClient';
import type { Conversation } from '../../../domain/entities/types';

export type ThreadCategory = 'all' | 'science' | 'philosophy' | 'entertainment' | 'tech';

interface ThreadsSidebarProps {
    activeCategory: ThreadCategory;
    onSelectCategory: (category: ThreadCategory) => void;
    isMobile?: boolean; // If true, render as mobile drawer style overlay
    isOpen?: boolean;   // For mobile state
    onClose?: () => void;
}

const CATEGORIES: { id: ThreadCategory; label: string; icon?: string }[] = [
    { id: 'all', label: 'For You' },
    { id: 'science', label: 'Science' },
    { id: 'tech', label: 'Technology' },
    { id: 'philosophy', label: 'Philosophy' },
    { id: 'entertainment', label: 'Entertainment' },
];

export const ThreadsSidebar: React.FC<ThreadsSidebarProps> = ({
    activeCategory,
    onSelectCategory,
    isMobile = false,
    isOpen = false,
    onClose
}) => {
    const navigate = useNavigate();
    const { id: urlId } = useParams<{ id: string }>();
    const [recentThreads, setRecentThreads] = React.useState<Conversation[]>([]);

    React.useEffect(() => {
        loadRecents();
    }, [urlId]); // Refresh when a new thread is created

    const loadRecents = async () => {
        try {
            const convos = await apiClient.listConversations('social_simulation');
            setRecentThreads(convos.slice(0, 5)); // Show top 5
        } catch (e) {
            console.error("Failed to load recents:", e);
        }
    };

    // If mobile and closed, return null (or handle animation in parent)
    if (isMobile && !isOpen) return null;

    const ContainerClasses = isMobile
        ? "fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-2xl transform transition-transform duration-300 ease-in-out border-r border-gray-100"
        : "hidden sm:flex w-64 shrink-0 flex-col h-full border-r-2 border-gray-200 bg-white z-20";

    const content = (
        <div className="flex flex-col h-full">
            {/* Header / Logo */}
            <div className="h-16 flex items-center justify-start px-6 gap-2">
                <div className="text-2xl font-bold tracking-tighter hover:scale-105 transition-transform cursor-pointer">
                    threads<span className="text-blue-600">.ai</span>
                </div>
                {isMobile && (
                    <button onClick={onClose} className="p-1 rounded-full hover:bg-gray-100 text-gray-500">
                        <X size={20} />
                    </button>
                )}
            </div>

            {/* Standard Nav */}
            <nav className="flex-1 px-3 py-6 space-y-2">
                <NavItem
                    icon={<Home size={26} strokeWidth={1.5} />}
                    label="Home"
                    active={activeCategory === 'all'}
                    onClick={() => {
                        onSelectCategory('all');
                        if (isMobile && onClose) onClose();
                    }}
                />
                <NavItem icon={<Search size={26} strokeWidth={1.5} />} label="Search" />
                <NavItem icon={<Heart size={26} strokeWidth={1.5} />} label="Activity" />
                <NavItem icon={<User size={26} strokeWidth={1.5} />} label="Profile" />
            </nav>

            {/* Recent Threads Section */}
            {recentThreads.length > 0 && (
                <div className="px-5 py-4 border-t border-gray-200">
                    <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                        <Clock size={12} /> Recent Threads
                    </h3>
                    <div className="space-y-2">
                        {recentThreads.map(convo => (
                            <button
                                key={convo.id}
                                onClick={() => {
                                    navigate(`/threads/${convo.id}`);
                                    if (isMobile && onClose) onClose();
                                }}
                                className={`w-full text-left px-3 py-2 rounded-lg text-xs font-medium truncate transition-colors
                                    ${urlId === convo.id
                                        ? 'bg-blue-50 text-blue-700 font-bold'
                                        : 'text-gray-500 hover:bg-gray-100'}`}
                            >
                                {convo.title || convo.id.slice(0, 8)}
                            </button>
                        ))}
                    </div>
                </div>
            )}

            <div className="px-5 py-4 border-t border-gray-200">
                <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4">
                    Topics
                </h3>
                <div className="space-y-1">
                    {CATEGORIES.map(cat => (
                        <button
                            key={cat.id}
                            onClick={() => {
                                onSelectCategory(cat.id);
                                if (isMobile && onClose) onClose();
                            }}
                            className={`w-full text-left px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center justify-between
                                ${activeCategory === cat.id
                                    ? 'bg-black text-white'
                                    : 'text-gray-600 hover:bg-gray-100'}`}
                        >
                            <span>{cat.label}</span>
                            {activeCategory === cat.id && <Sparkles size={12} />}
                        </button>
                    ))}
                </div>
            </div>

            {/* Footer */}
            <div className="p-4 mt-auto border-t border-gray-200 space-y-2">
                <button
                    onClick={() => navigate('/')}
                    className="flex items-center gap-3 p-2 w-full rounded-lg hover:bg-gray-100 text-gray-900 justify-start transition-colors"
                >
                    <ArrowLeft size={24} strokeWidth={1.5} />
                    <span className="text-sm font-bold">Back to Workspace</span>
                </button>

                <button className="flex items-center gap-3 p-2 w-full rounded-lg hover:bg-gray-50 text-gray-500 justify-start">
                    <Settings size={24} strokeWidth={1.5} />
                    <span className="text-sm">Settings</span>
                </button>
            </div>
        </div>
    );

    return (
        <>
            {/* Mobile Backdrop */}
            {isMobile && isOpen && (
                <div
                    className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40 transition-opacity"
                    onClick={onClose}
                />
            )}

            <aside className={ContainerClasses}>
                {content}
            </aside>
        </>
    );
};

const NavItem: React.FC<{ icon: React.ReactNode, label: string, active?: boolean, onClick?: () => void }> = ({ icon, label, active, onClick }) => (
    <button
        onClick={onClick}
        className={`flex items-center gap-4 p-3 rounded-xl w-full transition-all group
        ${active ? 'font-bold text-black' : 'text-gray-500 hover:bg-gray-50 hover:text-gray-900'}
        justify-start`
        }>
        <div className="group-hover:scale-110 transition-transform">
            {icon}
        </div>
        <span className="text-[15px]">{label}</span>
    </button>
);
