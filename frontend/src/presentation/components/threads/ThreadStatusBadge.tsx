import React from 'react';
import { Badge } from '../../components/ui/badge';
import { cn } from '../../utils/cn';
import { GitMerge, GitPullRequest, CheckCircle2, Circle } from 'lucide-react';

export type ThreadStatus = 'open' | 'review_requested' | 'merged' | 'closed';

interface ThreadStatusBadgeProps {
    status: ThreadStatus | string;
    className?: string;
}

export const ThreadStatusBadge: React.FC<ThreadStatusBadgeProps> = ({ status, className }) => {
    const normalizedStatus = (status || 'open').toLowerCase();

    const config = {
        open: {
            label: 'Open',
            icon: GitPullRequest,
            variant: 'default', // Usually primary/black
            iconClass: 'text-green-500',
            badgeClass: 'bg-green-100 text-green-800 hover:bg-green-200 border-green-200'
        },
        review_requested: {
            label: 'Review Requested',
            icon: Circle,
            variant: 'secondary',
            iconClass: 'text-yellow-500',
            badgeClass: 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200 border-yellow-200'
        },
        merged: {
            label: 'Merged',
            icon: GitMerge,
            variant: 'secondary',
            iconClass: 'text-purple-500',
            badgeClass: 'bg-purple-100 text-purple-800 hover:bg-purple-200 border-purple-200'
        },
        closed: {
            label: 'Closed',
            icon: CheckCircle2,
            variant: 'outline',
            iconClass: 'text-gray-500',
            badgeClass: 'bg-gray-100 text-gray-800 hover:bg-gray-200 border-gray-200'
        }
    };

    const current = config[normalizedStatus as keyof typeof config] || config.open;
    const Icon = current.icon;

    return (
        <Badge
            variant="outline"
            className={cn(
                "gap-1.5 px-2.5 py-0.5 font-medium border transition-colors",
                current.badgeClass,
                className
            )}
        >
            <Icon className={cn("h-3.5 w-3.5", current.iconClass)} />
            {current.label}
        </Badge>
    );
};
