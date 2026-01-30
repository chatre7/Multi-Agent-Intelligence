import React, { useEffect, useState } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { apiClient } from '../../../infrastructure/api/apiClient';
import type { Conversation } from '../../../domain/entities/types';
import { ThreadStatusBadge } from './ThreadStatusBadge';
import { Button } from '../ui/button';
import { Search, Loader2 } from 'lucide-react';

interface ThreadListProps {
    onSelectThread: (threadId: string) => void;
    onNewThread: () => void;
}

export const ThreadList: React.FC<ThreadListProps> = ({ onSelectThread, onNewThread }) => {
    const [threads, setThreads] = useState<Conversation[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        loadThreads();
    }, []);

    const loadThreads = async () => {
        try {
            setIsLoading(true);
            const data = await apiClient.listConversations('social_simulation');
            setThreads(data);
        } catch (e: any) {
            console.error("Failed to load threads:", e);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="h-full flex flex-col p-4 md:p-8 max-w-5xl mx-auto w-full">
            {/* Context Header */}
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Requests</h1>
                <p className="text-gray-500">Track and manage your brainstorming sessions.</p>
            </div>

            {/* Content Area */}
            <div className="flex-1 overflow-hidden flex flex-col min-h-0 bg-white rounded-2xl border border-gray-200 shadow-sm">
                {/* Toolbar */}
                <div className="p-4 border-b border-gray-100 flex items-center justify-between gap-4">
                    <div className="relative flex-1 max-w-md">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
                        <input
                            type="text"
                            placeholder="Search requests..."
                            className="w-full pl-9 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
                        />
                    </div>
                    <div className="flex bg-gray-100 p-1 rounded-lg">
                        {['Open', 'Merged', 'Closed'].map((status) => (
                            <button
                                key={status}
                                className="px-3 py-1.5 text-xs font-medium rounded-md text-gray-600 hover:text-gray-900 hover:bg-white/50 transition-all"
                            >
                                {status}
                            </button>
                        ))}
                    </div>
                </div>

                {/* List */}
                <div className="flex-1 overflow-y-auto min-h-0">
                    {isLoading ? (
                        <div className="h-full flex flex-col items-center justify-center text-gray-400">
                            <Loader2 size={32} className="animate-spin mb-2" />
                            <p>Loading requests...</p>
                        </div>
                    ) : threads.length === 0 ? (
                        <div className="h-full flex flex-col items-center justify-center text-gray-400">
                            <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mb-4">
                                <Search size={24} className="text-gray-300" />
                            </div>
                            <p className="font-medium text-gray-600">No requests found</p>
                            <Button variant="link" onClick={onNewThread} className="text-blue-600">
                                Create your first request
                            </Button>
                        </div>
                    ) : (
                        <div className="divide-y divide-gray-50">
                            {threads.map((thread) => (
                                <div
                                    key={thread.id}
                                    onClick={() => onSelectThread(thread.id)}
                                    className="p-5 flex items-start gap-4 hover:bg-blue-50/30 cursor-pointer transition-all group"
                                >
                                    <div className="mt-1 flex-shrink-0">
                                        <ThreadStatusBadge status={thread.status || 'open'} />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center justify-between mb-1">
                                            <h3 className="text-base font-semibold text-gray-900 group-hover:text-blue-600 transition-colors truncate pr-4">
                                                {thread.title || "Untitled Request"}
                                            </h3>
                                            <span className="text-xs text-gray-400 flex-shrink-0">
                                                {formatDistanceToNow(new Date(thread.updated_at))} ago
                                            </span>
                                        </div>
                                        <p className="text-sm text-gray-500 line-clamp-2">
                                            {/* We could show a preview of the last message here if we had it */}
                                            Opened inside Project • {thread.id.substring(0, 8)}
                                        </p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
