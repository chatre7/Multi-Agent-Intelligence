import { Home, MessageSquare, BarChart3, Hash, Route as RouteIcon, type LucideIcon } from 'lucide-react';

export interface NavItem {
    label: string;
    path: string;
    icon: LucideIcon;
    exact?: boolean;
}

export const MAIN_NAV_ITEMS: NavItem[] = [
    {
        label: 'Home',
        path: '/',
        icon: Home,
        exact: true
    },
    {
        label: 'Chat',
        path: '/chat',
        icon: MessageSquare,
        exact: true
    },
    {
        label: 'Threads',
        path: '/threads',
        icon: Hash
    },
    {
        label: 'Visualizer',
        path: '/visualizer',
        icon: RouteIcon
    },
    {
        label: 'Admin',
        path: '/admin',
        icon: BarChart3
    }
];
