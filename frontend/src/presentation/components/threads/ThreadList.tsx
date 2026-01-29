import React, { useEffect, useState } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { apiClient } from '../../../infrastructure/api/apiClient';
import type { Conversation } from '../../../domain/entities/types';
import { ThreadStatusBadge } from './ThreadStatusBadge';
import { Button } from '../ui/button';
import { Plus } from 'lucide-react';

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
            // 'brainstorming' domain or generic 'social_simulation'? 
            // Using generic list without domain filter for now to show everything, or filtering by 'social_simulation' if that's the default.
            // Based on previous code, domain_id was 'social_simulation'.
            const data = await apiClient.listConversations('social_simulation');
            setThreads(data);
        } catch (e: any) {
            console.error("Failed to load threads:", e);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="h-full bg-gray-50 flex flex-col">
            {/* Header - Matching Admin Template */}
            <div className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-10">
                <div className="max-w-7xl mx-auto px-4 py-8 md:px-8">
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Requests</h1>
                            <p className="text-gray-600 mt-1">Manage and review agent brainstorming threads.</p>
                        </div>
                        <Button
                            onClick={onNewThread}
                            className="bg-blue-500 text-white hover:bg-blue-600 shadow-sm"
                        >
                            <Plus className="mr-2 h-4 w-4" />
                            New Request
                        </Button>
                    </div>
                </div>
            </div>

            <div className="flex-1 overflow-y-auto w-full">
                <div className="max-w-7xl mx-auto p-4 md:p-8 space-y-4">

                    <div className="rounded-md border bg-card">
                        <div className="p-4 border-b bg-muted/40 flex justify-between items-center">
                            <div className="flex gap-4 text-sm font-medium text-muted-foreground">
                                <span className="hover:text-foreground cursor-pointer">Open</span>
                                <span className="hover:text-foreground cursor-pointer">Merged</span>
                                <span className="hover:text-foreground cursor-pointer">Closed</span>
                            </div>
                        </div>

                        {isLoading ? (
                            <div className="p-8 text-center text-muted-foreground">Loading threads...</div>
                        ) : threads.length === 0 ? (
                            <div className="p-16 text-center text-muted-foreground flex flex-col items-center gap-2">
                                <p>No requests found.</p>
                                <Button variant="outline" onClick={onNewThread}>Create your first request</Button>
                            </div>
                        ) : (
                            <div className="divide-y">
                                {threads.map((thread) => (
                                    <div
                                        key={thread.id}
                                        className="p-4 flex items-start gap-4 hover:bg-muted/50 cursor-pointer transition-colors group"
                                        onClick={() => onSelectThread(thread.id)}
                                    >
                                        <div className="mt-1">
                                            <ThreadStatusBadge status={thread.status || 'open'} />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <h3 className="text-base font-semibold leading-none group-hover:text-primary transition-colors mb-1.5">
                                                {thread.title || "Untitled Request"}
                                            </h3>
                                            <div className="text-sm text-muted-foreground flex items-center gap-2">
                                                <span>#{thread.id.substring(0, 7)}</span>
                                                <span>•</span>
                                                <span>opened {formatDistanceToNow(new Date(thread.created_at))} ago by {thread.created_by_role || 'User'}</span>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-4 text-sm text-muted-foreground">
                                            {/* Assignees/Reviewers avatars could go here */}
                                            <div className="hidden md:block">
                                                {formatDistanceToNow(new Date(thread.updated_at))}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};
