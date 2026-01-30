import { Bot, Code2, Bug, Search, FileText, CheckCircle, Shield, BookOpen, Scroll, Laugh, Heart, Share2, type LucideIcon } from "lucide-react";

// Map of Agent IDs to their Icons
const AGENT_ICONS: Record<string, LucideIcon> = {
    coder: Code2,
    debugger: Bug,
    tester: CheckCircle,
    documenter: FileText,
    planner: Search,
    reviewer: Shield,
    storyteller: BookOpen,
    philosopher: Scroll,
    comedian: Laugh,
    empath: Heart,
    router: Share2
};

interface AgentAvatarProps {
    agentId?: string;
    isUser?: boolean;
    className?: string;
}

export const AgentAvatar = ({ agentId, isUser = false, className = "" }: AgentAvatarProps) => {
    // If User, we render the generic user avatar styling in parent or here?
    // The previous implementation had user logic inline. Let's support it here.

    if (isUser) {
        // User Avatar Logic (simplified if needed, or pass isUser=true)
        // But wait, the original code had User icon imported. 
        // We'll trust the caller handles the "User" Icon if needed or we export a UserAvatar separately?
        // Let's keep it simple: This is AGENT avatar.
        return null;
    }

    const id = agentId?.toLowerCase() || "";
    const Icon = AGENT_ICONS[id] || Bot;

    return (
        <div className={`w-8 h-8 rounded-full bg-white border border-gray-200 flex items-center justify-center shadow-sm text-gray-600 ${className}`}>
            <Icon size={16} />
        </div>
    );
};
