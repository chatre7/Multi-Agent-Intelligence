import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router';
import { ThreadList } from '../components/threads/ThreadList';
import { ThreadDetail } from '../components/threads/ThreadDetail';
import { apiClient } from '../../infrastructure/api/apiClient';
import { Button } from '../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';

const ThreadsPage: React.FC = () => {
    const { id: urlConversationId } = useParams<{ id: string }>();
    const navigate = useNavigate();

    // UI State
    const [isCreateOpen, setIsCreateOpen] = useState(false);
    const [newTitle, setNewTitle] = useState('');
    const [isCreating, setIsCreating] = useState(false);

    const [viewMode, setViewMode] = useState<'list' | 'detail'>('list');

    useEffect(() => {
        if (urlConversationId) {
            setViewMode('detail');
        } else {
            setViewMode('list');
        }
    }, [urlConversationId]);

    const handleSelectThread = (id: string) => {
        navigate(`/threads/${id}`);
    };

    const handleBack = () => {
        navigate('/threads');
    };

    const handleCreateThread = async () => {
        if (!newTitle.trim()) return;
        setIsCreating(true);
        try {
            // For MVP, choosing a default agent (e.g., 'moderator' or 'storyteller')
            const convo = await apiClient.startConversation('social_simulation', 'moderator');

            // We need to update the title immediately. 
            await apiClient.sendMessage({
                domain_id: 'social_simulation',
                message: newTitle,
                conversation_id: convo.id
            });

            setIsCreateOpen(false);
            setNewTitle('');
            navigate(`/threads/${convo.id}`);
        } catch (e: any) {
            console.error("Failed to create thread:", e);
        } finally {
            setIsCreating(false);
        }
    };

    return (
        <>
            {viewMode === 'detail' && urlConversationId ? (
                <ThreadDetail threadId={urlConversationId} onBack={handleBack} />
            ) : (
                <ThreadList
                    onSelectThread={handleSelectThread}
                    onNewThread={() => setIsCreateOpen(true)}
                />
            )}

            <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Create New Request</DialogTitle>
                        <DialogDescription>
                            Start a new brainstorming session or request.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="grid gap-4 py-4">
                        <div className="grid gap-2">
                            <Label htmlFor="title">Title / Topic</Label>
                            <Input
                                id="title"
                                value={newTitle}
                                onChange={(e) => setNewTitle(e.target.value)}
                                placeholder="e.g., Design a notification system..."
                                autoFocus
                            />
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setIsCreateOpen(false)}>Cancel</Button>
                        <Button onClick={handleCreateThread} disabled={isCreating || !newTitle.trim()}>
                            {isCreating ? 'Creating...' : 'Create Request'}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </>
    );
};

export default ThreadsPage;
