import React, { useState } from 'react';
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
    const [isCreateOpen, setIsCreateOpen] = useState(false);
    const [newTitle, setNewTitle] = useState('');
    const [isCreating, setIsCreating] = useState(false);

    // Derived state for view mode
    const viewMode = urlConversationId ? 'detail' : 'list';

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
            // Ideally, we'd have a dropdown to pick initial agent or "assignee"
            const convo = await apiClient.startConversation('social_simulation', 'moderator'); // Using moderator as default starter

            // We need to update the title immediately. 
            // Currently startConversation doesn't take title. 
            // We can assume first message sets title or we update it.
            // Let's send the first message as the title/description.
            await apiClient.sendMessage({
                domain_id: 'social_simulation',
                message: newTitle,
                conversation_id: convo.id
            });

            // If we added a specific "Update Title" endpoint, we'd use it here.

            setIsCreateOpen(false);
            setNewTitle('');
            navigate(`/threads/${convo.id}`);
        } catch (e: any) {
            console.error("Failed to create thread:", e);
        } finally {
            setIsCreating(false);
        }
    };

    if (viewMode === 'detail' && urlConversationId) {
        return <ThreadDetail threadId={urlConversationId} onBack={handleBack} />;
    }

    return (
        <div className="h-full bg-gray-50 dark:bg-zinc-950/30 overflow-y-auto">
            <ThreadList
                onSelectThread={handleSelectThread}
                onNewThread={() => setIsCreateOpen(true)}
            />

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
        </div>
    );
};

export default ThreadsPage;
