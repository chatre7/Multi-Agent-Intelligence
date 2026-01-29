import React, { useState, useEffect } from 'react';
import { formatDistanceToNow } from 'date-fns';
import {
    GitMerge, MoreHorizontal,
    Heart, UserPlus, FileText
} from 'lucide-react';
import { apiClient } from '../../../infrastructure/api/apiClient';
import type { Conversation } from '../../../domain/entities/types';
import { ThreadStatusBadge } from './ThreadStatusBadge';
import { Button } from '../ui/button';
import { Separator } from '../ui/separator';
import { Textarea } from '../ui/textarea';
import { cn } from '../../utils/cn';

interface ThreadDetailProps {
    threadId: string;
    onBack: () => void;
}

// Reuse existing types from original ThreadsPage for now, but should ideally move to shared types
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
    };
    hasThreadLine?: boolean;
}

export const ThreadDetail: React.FC<ThreadDetailProps> = ({ threadId, onBack }) => {
    const [thread, setThread] = useState<Conversation | null>(null);
    const [posts, setPosts] = useState<SocialPost[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isMerging, setIsMerging] = useState(false);
    const [replyContent, setReplyContent] = useState('');

    useEffect(() => {
        loadThreadData();
    }, [threadId]);

    const loadThreadData = async () => {
        setIsLoading(true);
        try {
            const [convo, messages] = await Promise.all([
                apiClient.getConversation(threadId),
                apiClient.listConversationMessages(threadId)
            ]);
            setThread(convo);

            // Map messages to posts (reuse logic from original page)
            const mappedPosts: SocialPost[] = messages.map((msg, index) => {
                let author = { id: 'unknown', name: 'Unknown', handle: '@unknown', avatar: 'bg-gray-500' };
                let content = msg.content;

                if (msg.role === 'user') {
                    author = { id: 'admin', name: 'Admin', handle: '@admin', avatar: 'bg-black' };
                } else if (msg.role === 'assistant') {
                    try {
                        const data = JSON.parse(msg.content);
                        content = data.content;
                        const agentId = data.author?.id || 'assistant';

                        let avatarColor = 'bg-gray-500';
                        if (agentId === 'storyteller') avatarColor = 'bg-purple-600';
                        else if (agentId === 'coder') avatarColor = 'bg-blue-600';
                        else if (agentId === 'critic') avatarColor = 'bg-pink-600';

                        author = {
                            id: agentId,
                            name: data.author?.name || 'Assistant',
                            handle: data.author?.handle || `@${agentId}`,
                            avatar: avatarColor
                        };
                    } catch (e) {
                        // Fallback for non-JSON content
                    }
                }

                return {
                    id: msg.id,
                    author,
                    content,
                    timestamp: formatDistanceToNow(new Date(msg.created_at)) + ' ago',
                    metrics: { likes: 0, replies: 0 },
                    hasThreadLine: index < messages.length - 1
                };
            });
            setPosts(mappedPosts);
        } catch (e) {
            console.error("Failed to load thread detail:", e);
        } finally {
            setIsLoading(false);
        }
    };

    const handleMerge = async () => {
        if (!thread) return;
        setIsMerging(true);
        try {
            await apiClient.mergeThread(thread.id);
            // Reload to get new status
            const updated = await apiClient.getConversation(thread.id);
            setThread(updated);
        } catch (e) {
            console.error("Merge failed:", e);
            alert("Failed to merge thread.");
        } finally {
            setIsMerging(false);
        }
    };

    const handleReply = async () => {
        if (!replyContent.trim() || !thread) return;

        // This simulates a user reply. Logic needs to be expanded to actually trigger agent response loop if desired.
        // For now, just sending message to backend.
        try {
            await apiClient.sendMessage({
                domain_id: thread.domain_id,
                message: replyContent,
                conversation_id: thread.id
            });
            setReplyContent('');
            loadThreadData(); // Refresh to see new message
        } catch (e) {
            console.error("Reply failed:", e);
        }
    };

    if (isLoading) return <div className="p-8 text-center text-muted-foreground">Loading thread...</div>;
    if (!thread) return <div className="p-8 text-center text-muted-foreground">Thread not found.</div>;

    return (
        <div className="flex flex-col h-full bg-gray-50 dark:bg-zinc-950 overflow-hidden">
            {/* Header - Matching Admin Template */}
            <div className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-10 px-6 py-4 flex items-start justify-between">
                <div className="space-y-1">
                    <div className="flex items-center gap-2">
                        <h1 className="text-xl font-semibold tracking-tight">{thread.title || 'Untitled Request'}</h1>
                        <span className="text-muted-foreground text-lg text-zinc-400">#{thread.id.substring(0, 5)}</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                        <ThreadStatusBadge status={thread.status || 'open'} />
                        <span className="text-gray-500">
                            <span className="font-medium text-gray-900">{thread.created_by_role || 'User'}</span> opened this request {formatDistanceToNow(new Date(thread.created_at))} ago
                        </span>
                    </div>
                </div>
                <div className="flex gap-2">
                    <Button variant="outline" onClick={onBack}>Back</Button>
                    {/* Only show Merge if Open */}
                    {(thread.status === 'open' || thread.status === 'review_requested') && (
                        <Button
                            onClick={handleMerge}
                            disabled={isMerging}
                            className="bg-green-600 hover:bg-green-700 text-white gap-2"
                        >
                            <GitMerge className="h-4 w-4" />
                            {isMerging ? 'Merging...' : 'Merge Request'}
                        </Button>
                    )}
                    {thread.status === 'merged' && (
                        <Button variant="secondary" disabled className="gap-2 text-purple-700 bg-purple-100 dark:bg-purple-900/20 dark:text-purple-400">
                            <GitMerge className="h-4 w-4" /> Merged
                        </Button>
                    )}
                </div>
            </div>

            <div className="flex-1 flex overflow-hidden">
                {/* Left: Chat Stream */}
                <div className="flex-1 overflow-y-auto p-6 space-y-8">
                    {/* Description/Initial Post (Optional: Could be first message) */}

                    {/* Timeline */}
                    <div className="relative space-y-6 pl-4 border-l-2 border-zinc-200 dark:border-zinc-800 ml-4">
                        {posts.map((post) => (
                            <div key={post.id} className="relative group">
                                {/* Avatar Bubble */}
                                <div className={cn(
                                    "absolute -left-[27px] top-0 h-10 w-10 rounded-full border-4 border-gray-50 dark:border-zinc-950 flex items-center justify-center text-xs font-bold text-white shadow-sm z-10",
                                    post.author.avatar
                                )}>
                                    {post.author.name[0]}
                                </div>

                                <div className="ml-6 rounded-lg border bg-card text-card-foreground shadow-sm overflow-hidden">
                                    <div className="px-4 py-3 border-b bg-muted/30 flex justify-between items-center text-xs">
                                        <div className="flex items-center gap-2">
                                            <span className="font-semibold text-sm">{post.author.name}</span>
                                            <span className="text-muted-foreground mb-[-2px]">commented {post.timestamp}</span>
                                        </div>
                                        <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <Button variant="ghost" size="icon" className="h-6 w-6"><Heart className="h-3.5 w-3.5" /></Button>
                                            <Button variant="ghost" size="icon" className="h-6 w-6"><MoreHorizontal className="h-3.5 w-3.5" /></Button>
                                        </div>
                                    </div>
                                    <div className="p-4 text-sm leading-relaxed whitespace-pre-wrap">
                                        {post.content}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Reply Box */}
                    {thread.status !== 'merged' && thread.status !== 'closed' && (
                        <div className="pt-6 relative pl-4 border-l-2 border-zinc-200 dark:border-zinc-800 ml-4">
                            <div className="ml-6 border rounded-lg overflow-hidden bg-background focus-within:ring-1 focus-within:ring-ring">
                                <div className="bg-muted/30 px-3 py-2 border-b text-xs font-medium text-muted-foreground">
                                    Add a comment or request review
                                </div>
                                <Textarea
                                    placeholder="Leave a comment..."
                                    className="min-h-[100px] border-none focus-visible:ring-0 resize-none rounded-none p-4"
                                    value={replyContent}
                                    onChange={(e) => setReplyContent(e.target.value)}
                                />
                                <div className="flex justify-end p-2 bg-muted/10 border-t">
                                    <Button size="sm" onClick={handleReply} disabled={!replyContent.trim()}>Comment</Button>
                                </div>
                            </div>
                        </div>
                    )}

                    {thread.status === 'merged' && (
                        <div className="mt-8 flex justify-center pb-8">
                            <div className="flex flex-col items-center gap-2 text-muted-foreground p-8 bg-muted/20 rounded-xl border border-dashed">
                                <div className="h-12 w-12 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center">
                                    <GitMerge className="h-6 w-6" />
                                </div>
                                <div className="text-center">
                                    <p className="font-medium text-foreground">Thread Merged!</p>
                                    <p className="text-sm">This discussion has been recorded in the Knowledge Base.</p>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Right: Sidebar */}
                <div className="w-80 border-l border-gray-200 bg-white/50 dark:bg-zinc-900/10 p-4 hidden xl:block space-y-6">
                    <div>
                        <h3 className="text-xs font-semibold text-muted-foreground mb-3 flex items-center justify-between">
                            Reviewers <UserPlus className="h-3.5 w-3.5 cursor-pointer hover:text-foreground" />
                        </h3>
                        <div className="space-y-2">
                            {(thread.reviewers?.length ? thread.reviewers : ['No reviewers']).map(r => (
                                <div key={r} className="flex items-center gap-2 text-sm">
                                    <div className="h-5 w-5 rounded-full bg-zinc-200" />
                                    <span>{r}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    <Separator />

                    <div>
                        <h3 className="text-xs font-semibold text-muted-foreground mb-3">Assignees</h3>
                        <div className="text-sm text-muted-foreground">No one assigned</div>
                    </div>

                    <Separator />

                    <div>
                        <h3 className="text-xs font-semibold text-muted-foreground mb-3">Artifacts</h3>
                        <div className="text-sm text-muted-foreground flex items-center gap-2">
                            {/* Future: File list */}
                            <FileText className="h-4 w-4 text-zinc-400" />
                            <span className="italic">None generated</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
