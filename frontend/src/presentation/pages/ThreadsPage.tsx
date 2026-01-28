
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router';
import {
    Heart, MessageCircle,
    MoreHorizontal, Check, Pause,
    Menu
} from 'lucide-react';
import { apiClient } from '../../infrastructure/api/apiClient';
import { ThreadsSidebar } from '../components/threads/ThreadsSidebar';
import type { ThreadCategory } from '../components/threads/ThreadsSidebar';

// --- Types ---
interface SocialPost {
    id: string;
    author: {
        id: string;
        name: string;
        avatar?: string;
        handle: string;
    };
    content: string;
    timestamp: string;
    metrics: {
        likes: number;
        replies: number;
        views?: string;
    };
    hasThreadLine?: boolean;
}

interface BackendMessage {
    role: string;
    content: string;
    agent_id?: string;
}

// --- Mock Agents ---
const MOCK_AGENTS = [
    { id: 'storyteller', name: 'Storyteller', handle: '@story_teller', role: 'Creative' },
    { id: 'coder', name: 'Dev Bot', handle: '@tech_lead', role: 'Engineer' },
    { id: 'critic', name: 'The Critic', handle: '@honesty_hour', role: 'Reviewer' },
];

const ThreadCard: React.FC<{ post: SocialPost }> = ({ post }) => {
    return (
        <div className="flex gap-4 p-4 border-b border-gray-100 hover:bg-gray-50/50 transition-colors cursor-pointer group">
            {/* Avatar Column */}
            <div className="flex flex-col items-center">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-sm ${post.author.avatar || 'bg-black'} shadow-sm`}>
                    {post.author.name[0]}
                </div>
                {post.hasThreadLine && (
                    <div className="w-0.5 flex-1 bg-gray-200 my-2 rounded-full" />
                )}
            </div>

            {/* Content Column */}
            <div className="flex-1 space-y-2">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <span className="font-bold text-[15px] text-black leading-none">{post.author.handle}</span>
                        <span className="text-gray-400 text-xs mt-0.5">{post.timestamp}</span>
                    </div>
                    <button className="text-gray-400 hover:text-black">
                        <MoreHorizontal size={18} />
                    </button>
                </div>

                <p className="text-[15px] text-gray-900 leading-relaxed whitespace-pre-wrap font-normal">
                    {post.content}
                </p>

                <div className="flex items-center gap-6 pt-1">
                    <button className="group flex items-center gap-1.5 focus:outline-none">
                        <Heart size={20} className="text-gray-400 group-hover:text-red-500 transition-colors stroke-[1.5px]" />
                        {post.metrics.likes > 0 && <span className="text-sm text-gray-400 group-hover:text-red-500">{post.metrics.likes}</span>}
                    </button>
                    <button className="group flex items-center gap-1.5 focus:outline-none">
                        <MessageCircle size={20} className="text-gray-400 group-hover:text-black transition-colors stroke-[1.5px]" />
                        {post.metrics.replies > 0 && <span className="text-sm text-gray-400 group-hover:text-black">{post.metrics.replies}</span>}
                    </button>
                </div>
            </div>
        </div>
    );
};

const ThreadsPage: React.FC = () => {
    const { id: urlConversationId } = useParams<{ id: string }>();
    const navigate = useNavigate();

    const [topic, setTopic] = useState('');
    const [activeCategory, setActiveCategory] = useState<ThreadCategory>('all');
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    const [isSimulating, setIsSimulating] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [feed, setFeed] = useState<SocialPost[]>([]);
    const [selectedAgents, setSelectedAgents] = useState<string[]>(['storyteller', 'coder', 'critic']);

    const toggleAgent = (id: string) => {
        if (selectedAgents.includes(id)) {
            setSelectedAgents(prev => prev.filter(a => a !== id));
        } else {
            setSelectedAgents(prev => [...prev, id]);
        }
    };

    // --- History Loading ---
    useEffect(() => {
        if (urlConversationId) {
            loadThreadHistory(urlConversationId);
        }
    }, [urlConversationId]);

    const loadThreadHistory = async (convoId: string) => {
        setIsLoading(true);
        try {
            const messages = await apiClient.listConversationMessages(convoId);
            const historyPosts: SocialPost[] = [];

            messages.forEach((msg: any, index: number) => {
                if (msg.role === 'user') {
                    // Seed topic from first user message
                    if (index === 0) setTopic(msg.content);

                    historyPosts.push({
                        id: msg.id || `msg_${index}`,
                        author: { id: 'admin', name: 'Admin', handle: '@admin', avatar: 'bg-black' },
                        content: msg.content,
                        timestamp: 'Hist',
                        metrics: { likes: 0, replies: 0 },
                        hasThreadLine: true
                    });
                } else if (msg.role === 'assistant') {
                    try {
                        const data = JSON.parse(msg.content);
                        let avatarColor = 'bg-gray-500';
                        const agentId = data.author?.id || msg.metadata?.agent_id;

                        if (agentId === 'storyteller') avatarColor = 'bg-purple-600';
                        else if (agentId === 'coder') avatarColor = 'bg-blue-600';
                        else if (agentId === 'critic') avatarColor = 'bg-pink-600';

                        historyPosts.push({
                            id: data.item_id || msg.id || `msg_${index}`,
                            author: {
                                id: data.author?.id || agentId || 'assistant',
                                name: data.author?.name || 'Assistant',
                                handle: data.author?.handle || `@${agentId || 'assistant'}`,
                                avatar: avatarColor
                            },
                            content: data.content,
                            timestamp: 'Hist',
                            metrics: {
                                likes: data.likes || 0,
                                replies: 0
                            },
                            hasThreadLine: true
                        });
                    } catch (e) {
                        // Support non-JSON messages if any
                        historyPosts.push({
                            id: msg.id || `msg_${index}`,
                            author: { id: 'assistant', name: 'Assistant', handle: '@assistant', avatar: 'bg-gray-500' },
                            content: msg.content,
                            timestamp: 'Hist',
                            metrics: { likes: 0, replies: 0 },
                            hasThreadLine: true
                        });
                    }
                }
            });

            setFeed(historyPosts);
            setIsSimulating(true); // Treat as active thread since we have history
        } catch (err) {
            console.error("Failed to load history:", err);
        } finally {
            setIsLoading(false);
        }
    };

    const handleStartSimulation = async () => {
        if (!topic) return;

        setIsSimulating(true);
        setIsLoading(true);
        setFeed([]);

        try {
            // Initial User Post
            const initialPost: SocialPost = {
                id: 'root',
                author: { id: 'admin', name: 'Admin', handle: '@admin', avatar: 'bg-black' },
                content: topic,
                timestamp: 'Now',
                metrics: { likes: 0, replies: 0 },
                hasThreadLine: true
            };
            setFeed([initialPost]);

            // Inject Category Context
            const contextPrefix = activeCategory !== 'all'
                ? `[Context: ${activeCategory.toUpperCase()} thread] `
                : '';

            const messagePayload = `${contextPrefix}${topic}`;

            // Call Backend
            const response = await apiClient.sendMessage({
                message: messagePayload,
                domain_id: 'social_simulation',
            });

            // Process Response
            const newPosts: SocialPost[] = [];
            response.messages.forEach((msg: BackendMessage, index: number) => {
                if (msg.role === 'assistant') {
                    try {
                        const data = JSON.parse(msg.content);
                        let avatarColor = 'bg-gray-500';
                        if (data.author.id === 'storyteller') avatarColor = 'bg-purple-600';
                        if (data.author.id === 'coder') avatarColor = 'bg-blue-600';
                        if (data.author.id === 'critic') avatarColor = 'bg-pink-600';

                        newPosts.push({
                            id: data.item_id || `msg_${index}`,
                            author: {
                                id: data.author.id,
                                name: data.author.name,
                                handle: data.author.handle,
                                avatar: avatarColor
                            },
                            content: data.content,
                            timestamp: `${index + 1}m`,
                            metrics: {
                                likes: data.likes || 0,
                                replies: 0
                            },
                            hasThreadLine: true
                        });
                    } catch (e) {
                        console.warn("Failed to parse social post JSON:", e);
                    }
                }
            });

            setFeed(prev => [...prev, ...newPosts]);

            // Sync URL with Conversation ID
            if (response.conversation_id && !urlConversationId) {
                navigate(`/threads/${response.conversation_id}`, { replace: true });
            }
        } catch (error) {
            console.error("Simulation failed:", error);
            alert("Simulation failed. Check console.");
            setIsSimulating(false);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex h-screen bg-white text-gray-900 font-sans">

            {/* Desktop Sidebar */}
            <ThreadsSidebar
                activeCategory={activeCategory}
                onSelectCategory={setActiveCategory}
            />

            {/* Mobile Sidebar (Drawer) */}
            <ThreadsSidebar
                isMobile
                isOpen={isMobileMenuOpen}
                onClose={() => setIsMobileMenuOpen(false)}
                activeCategory={activeCategory}
                onSelectCategory={setActiveCategory}
            />

            {/* Middle: Content Feed */}
            <main className="flex-1 flex justify-center border-r border-gray-100 overflow-hidden relative min-w-0">
                <div className="w-full max-w-[600px] flex flex-col h-full bg-white relative">
                    {/* Header */}
                    <header className="h-16 flex items-center justify-between px-4 border-b border-gray-100 shrink-0 sticky top-0 bg-white/80 backdrop-blur-md z-10">
                        {/* Mobile Menu Button */}
                        <button
                            className="md:hidden p-2 -ml-2 text-gray-500 hover:bg-gray-100 rounded-full"
                            onClick={() => setIsMobileMenuOpen(true)}
                        >
                            <Menu size={24} />
                        </button>

                        <div className="flex-1 flex justify-center">
                            <span className="font-bold text-lg tracking-tight md:hidden">threads.ai</span>
                            <span className="font-bold text-lg tracking-tight hidden md:inline">For You</span>
                        </div>

                        <div className="w-10 flex justify-end"> {/* Spacer or Action */}
                            {isSimulating && !isLoading ? (
                                <button className="p-2 bg-black text-white rounded-full hover:scale-105 transition-transform" onClick={() => setIsSimulating(false)}>
                                    <Pause size={18} fill="currentColor" />
                                </button>
                            ) : (
                                <button
                                    className={`px-4 py-1.5 bg-black text-white text-sm font-bold rounded-full hover:bg-gray-800 transition-all ${(!topic || isLoading) ? 'opacity-50 cursor-not-allowed' : ''}`}
                                    onClick={handleStartSimulation}
                                    disabled={!topic || isLoading}
                                >
                                    {isLoading ? '...' : 'Start'}
                                </button>
                            )}
                        </div>
                    </header>

                    {/* Scrollable Feed */}
                    <div className="flex-1 overflow-y-auto no-scrollbar pb-20">
                        {/* New Thread Composer */}
                        {!isSimulating && (
                            <div className="p-4 border-b border-gray-100">
                                <div className="flex gap-4">
                                    <div className="flex flex-col items-center">
                                        <div className="w-10 h-10 rounded-full bg-black text-white flex items-center justify-center font-bold">A</div>
                                        <div className="w-0.5 flex-1 bg-gray-200 my-2 rounded-full min-h-[40px]" />
                                    </div>
                                    <div className="flex-1 space-y-4 pt-2">
                                        <div className="flex justify-between items-center">
                                            <span className="font-bold text-[15px]">@admin</span>
                                            {activeCategory !== 'all' && (
                                                <span className="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-1 rounded-full">{activeCategory}</span>
                                            )}
                                        </div>
                                        <textarea
                                            value={topic}
                                            onChange={(e) => setTopic(e.target.value)}
                                            placeholder={`Start a ${activeCategory !== 'all' ? activeCategory + ' ' : ''}thread...`}
                                            className="w-full text-[15px] placeholder:text-gray-400 border-none focus:ring-0 p-0 resize-none min-h-[60px] focus:outline-none"
                                            rows={2}
                                        />
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Feed Items */}
                        {(isSimulating || feed.length > 0) ? (
                            <div className="animate-in fade-in active-feed">
                                {feed.map(post => (
                                    <ThreadCard key={post.id} post={post} />
                                ))}
                            </div>
                        ) : (
                            <div className="flex flex-col items-center justify-center py-20 text-gray-300 space-y-4 opacity-50">
                                <MessageCircle size={48} strokeWidth={1} />
                                <p className="text-sm font-medium">Your feed is empty.</p>
                            </div>
                        )}
                    </div>
                </div>
            </main>

            {/* RIGHT: Agent Sidebar (Hidden on smaller screens, visible on XL) */}
            <aside className="w-80 border-l border-gray-100 bg-gray-50/50 p-6 hidden xl:block">
                <div className="sticky top-6 space-y-8">
                    <div>
                        <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4">Active Personas</h3>
                        <div className="space-y-3">
                            {MOCK_AGENTS.map(agent => (
                                <div
                                    key={agent.id}
                                    onClick={() => toggleAgent(agent.id)}
                                    className={`flex items-center gap-3 p-2 rounded-xl cursor-pointer transition-all ${selectedAgents.includes(agent.id)
                                        ? 'bg-white shadow-sm ring-1 ring-gray-100'
                                        : 'opacity-50 hover:opacity-80'
                                        }`}
                                >
                                    <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white text-xs font-bold shadow-sm 
                                        ${agent.id === 'storyteller' ? 'bg-purple-600' :
                                            agent.id === 'coder' ? 'bg-blue-600' : 'bg-pink-600'}`}>
                                        {agent.handle[1].toUpperCase()}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-bold text-gray-900 truncate">{agent.name}</p>
                                    </div>
                                    {selectedAgents.includes(agent.id) && <Check size={16} className="text-black" />}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </aside>
        </div>
    );
};

export default ThreadsPage;
