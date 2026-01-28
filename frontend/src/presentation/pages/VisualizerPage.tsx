/**
 * VisualizerPage - Admin page for live workflow visualization
 * Lazy-loaded for bundle optimization
 */
import { useState, useEffect, useCallback, lazy, Suspense } from 'react';
import { ArrowLeft, Radio, RefreshCw, Download } from 'lucide-react';
import { WebSocketClient, type MessageType } from '../../infrastructure/websocket/WebSocketClient';
import { apiClient } from '../../infrastructure/api/apiClient';
import type {
    WorkflowAgentNode,
    WorkflowEdgeData,
    WorkflowEvent,
    AgentStatus
} from '../../domain/types/workflowVisualizer';

// Lazy load React Flow component for bundle optimization
const WorkflowVisualizer = lazy(() => import('../components/visualizer/WorkflowVisualizer'));

interface Conversation {
    id: string;
    domainId: string;
    activeAgent?: string;
}

export function VisualizerPage() {
    // State
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
    const [agents, setAgents] = useState<WorkflowAgentNode[]>([]);
    const [edges, setEdges] = useState<WorkflowEdgeData[]>([]);
    const [activeAgentId, setActiveAgentId] = useState<string | null>(null);
    const [eventLog, setEventLog] = useState<WorkflowEvent[]>([]);
    const [isConnected, setIsConnected] = useState(false);
    const [isLoading, setIsLoading] = useState(true);

    // Get auth token
    const token = localStorage.getItem('auth_token') || '';

    // Fetch existing conversations from API
    useEffect(() => {
        async function fetchConversations() {
            try {
                setIsLoading(true);
                const data = await apiClient.listConversations();
                // Map API response to our Conversation interface
                const mapped: Conversation[] = data.map((c: any) => ({
                    id: c.id,
                    domainId: c.domain_id || c.domainId || 'unknown',
                    activeAgent: c.active_agent || c.activeAgent,
                }));
                setConversations(mapped);
            } catch (error) {
                console.error('[Visualizer] Failed to fetch conversations:', error);
            } finally {
                setIsLoading(false);
            }
        }

        if (token) {
            fetchConversations();
        }
    }, [token]);

    // Initialize WebSocket
    useEffect(() => {
        if (!token) return;

        const client = new WebSocketClient({
            url: '/ws',
            token,
            reconnectAttempts: 5,
            reconnectDelay: 3000,
        });

        // Handle workflow events
        const handlers: { type: MessageType; handler: (data: unknown) => void }[] = [
            {
                type: 'conversation_started',
                handler: (data: unknown) => {
                    const payload = data as { conversationId: string; domainId: string; activeAgent?: string };
                    const newConvo: Conversation = {
                        id: payload.conversationId,
                        domainId: payload.domainId,
                        activeAgent: payload.activeAgent,
                    };
                    setConversations(prev => [...prev, newConvo]);

                    // Initialize agents for this domain
                    if (payload.activeAgent) {
                        setAgents([{
                            id: payload.activeAgent,
                            name: payload.activeAgent,
                            status: 'idle',
                        }]);
                    }
                },
            },
            {
                type: 'agent_selected',
                handler: (data: unknown) => {
                    const payload = data as { agent_id: string; agent_name: string; conversationId: string };
                    if (selectedConversation?.id !== payload.conversationId) return;

                    setActiveAgentId(payload.agent_id);

                    // Add or update agent
                    setAgents(prev => {
                        const exists = prev.find(a => a.id === payload.agent_id);
                        if (exists) {
                            return prev.map(a =>
                                a.id === payload.agent_id
                                    ? { ...a, status: 'active' as AgentStatus, name: payload.agent_name }
                                    : { ...a, status: a.status === 'active' ? 'complete' as AgentStatus : a.status }
                            );
                        }
                        return [
                            ...prev.map(a => ({ ...a, status: a.status === 'active' ? 'complete' as AgentStatus : a.status })),
                            { id: payload.agent_id, name: payload.agent_name, status: 'active' as AgentStatus },
                        ];
                    });
                },
            },
            {
                type: 'workflow_step_start',
                handler: (data: unknown) => {
                    const msg = data as { payload: { agentId: string; agentName: string; conversationId: string; content?: string; metadata?: any; timestamp?: number } };
                    const payload = msg.payload;
                    if (!payload || selectedConversation?.id !== payload.conversationId) return;

                    setActiveAgentId(payload.agentId);
                    setAgents(prev => prev.map(a => ({
                        ...a,
                        status: a.id === payload.agentId ? 'active' : a.status,
                    })));

                    // If content is present, add to event log (e.g. Tool Start)
                    if (payload.content) {
                        setEventLog(prev => [{
                            id: `evt-${Date.now()}-${Math.random()}`,
                            type: 'step_start',
                            timestamp: new Date(payload.timestamp ? payload.timestamp * 1000 : Date.now()).toISOString(),
                            agentId: payload.agentId,
                            agentName: payload.agentName,
                            conversationId: payload.conversationId,
                            content: payload.content,
                            metadata: payload.metadata || {}
                        }, ...prev]);
                    }
                },
            },
            {
                type: 'workflow_step_complete',
                handler: (data: unknown) => {
                    const msg = data as { payload: { agentId: string; durationMs?: number; tokenCount?: number; conversationId: string } };
                    const payload = msg.payload;
                    if (!payload || selectedConversation?.id !== payload.conversationId) return;

                    setAgents(prev => prev.map(a =>
                        a.id === payload.agentId
                            ? {
                                ...a,
                                status: 'complete' as AgentStatus,
                                responseTime: payload.durationMs,
                                tokenCount: payload.tokenCount,
                            }
                            : a
                    ));
                },
            },
            {
                type: 'workflow_handoff',
                handler: (data: unknown) => {
                    const msg = data as { payload: { fromAgentId: string; toAgentId: string; fromAgent: string; toAgent: string; reason?: string; conversationId: string; timestamp?: number } };
                    const payload = msg.payload;
                    if (!payload || selectedConversation?.id !== payload.conversationId) return;

                    // Add edge for handoff
                    setEdges(prev => {
                        const edgeId = `${payload.fromAgentId}-${payload.toAgentId}`;
                        if (prev.find(e => e.id === edgeId)) return prev;
                        return [...prev, {
                            id: edgeId,
                            source: payload.fromAgentId,
                            target: payload.toAgentId,
                            animated: true,
                            label: payload.reason,
                        }];
                    });

                    // Add to event log
                    setEventLog(prev => [{
                        id: `evt-handoff-${Date.now()}`,
                        type: 'handoff',
                        timestamp: new Date(payload.timestamp ? payload.timestamp * 1000 : Date.now()).toISOString(),
                        agentId: payload.fromAgentId,
                        agentName: payload.fromAgent,
                        conversationId: payload.conversationId,
                        metadata: {
                            toAgent: payload.toAgent,
                            reason: payload.reason
                        }
                    }, ...prev]);
                },
            },
            {
                type: 'workflow_thought',
                handler: (data: unknown) => {
                    console.log("[Visualizer] Received thought event:", data);
                    const msg = data as { payload: { agentId: string; agentName: string; conversationId: string; reason: string } };
                    const payload = msg.payload;
                    if (!payload || selectedConversation?.id !== payload.conversationId) return;

                    setEventLog(prev => [{
                        id: `evt-thought-${Date.now()}-${Math.random()}`,
                        type: 'thought' as any,
                        timestamp: new Date().toISOString(),
                        agentId: payload.agentId,
                        agentName: payload.agentName,
                        conversationId: payload.conversationId,
                        content: payload.reason,
                        metadata: {}
                    }, ...prev]);
                },
            },
            {
                type: 'message_complete',
                handler: (data: unknown) => {
                    const payload = data as { agentId?: string; agentName?: string; conversationId: string; payload?: { durationMs?: number; tokenCount?: number; metadata?: { durationMs?: number; tokenCount?: number } } };
                    if (selectedConversation?.id !== payload.conversationId) return;

                    if (payload.agentId) {
                        const meta = payload.payload?.metadata || payload.payload;
                        setAgents(prev => prev.map(a =>
                            a.id === payload.agentId
                                ? {
                                    ...a,
                                    status: 'complete' as AgentStatus,
                                    responseTime: meta?.durationMs,
                                    tokenCount: meta?.tokenCount,
                                }
                                : a
                        ));
                    }
                },
            },
        ];

        // Connect and register handlers
        client.connect()
            .then(() => {
                setIsConnected(true);
                handlers.forEach(({ type, handler }) => {
                    client.on(type, handler);
                });
            })
            .catch(() => setIsConnected(false));

        return () => {
            client.disconnect();
        };
    }, [token, selectedConversation?.id, agents]);

    // Select conversation and load history
    const handleSelectConversation = useCallback(async (convo: Conversation) => {
        setSelectedConversation(convo);
        setEventLog([]);
        setEdges([]);
        setAgents([]);
        setActiveAgentId(null);

        try {
            // Load messages to reconstruct graph
            // Use axios directly or add method to apiClient. simpler here to use apiClient's client if exposed, 
            // but apiClient doesn't expose getting messages easily. Let's use fetch for now or add to apiClient.
            // Actually, let's use apiClient.client if we can or just assume we have access.
            // Better practice: Let's assume we can add getMessages to apiClient? No, let's just fetch here for now 
            // using the token we have.

            const response = await fetch(`/api/v1/conversations/${convo.id}/messages`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (response.ok) {
                const messages: any[] = await response.json();
                console.log("[Visualizer] Loaded messages:", messages);

                // Reconstruct agents and edges from messages
                const foundAgents = new Map<string, WorkflowAgentNode>();
                const foundEdges: WorkflowEdgeData[] = [];
                const historicalEvents: WorkflowEvent[] = [];
                let lastAgentId: string | null = null;

                messages.forEach((msg) => {
                    const agentId = msg.agent_id || msg.agentId;

                    if (agentId) {
                        const agentName = msg.agent_name || msg.agentName || agentId;

                        // Found an agent interaction
                        if (!foundAgents.has(agentId)) {
                            foundAgents.set(agentId, {
                                id: agentId,
                                name: agentName,
                                status: 'complete',
                            });
                        }

                        // Create edge from last agent
                        if (lastAgentId && lastAgentId !== agentId) {
                            const edgeId = `${lastAgentId}-${agentId}`;
                            if (!foundEdges.find(e => e.id === edgeId)) {
                                foundEdges.push({
                                    id: edgeId,
                                    source: lastAgentId,
                                    target: agentId,
                                    animated: false
                                });
                            }

                            // Add handoff event
                            historicalEvents.push({
                                type: 'handoff',
                                timestamp: msg.created_at || new Date().toISOString(),
                                conversationId: convo.id,
                                agentId: lastAgentId, // Handoff IS an event, but the type requires agentId. Using source agent.
                                agentName: foundAgents.get(lastAgentId)?.name || lastAgentId,
                                metadata: {
                                    fromAgentId: lastAgentId,
                                    toAgentId: agentId,
                                    fromAgent: foundAgents.get(lastAgentId)?.name || lastAgentId,
                                    toAgent: agentName,
                                }
                            });
                        }

                        // Add completion event
                        historicalEvents.push({
                            type: 'step_complete',
                            timestamp: msg.created_at || new Date().toISOString(),
                            agentId: agentId,
                            agentName: agentName,
                            conversationId: convo.id,
                            metadata: {
                                content: msg.content?.substring(0, 100) + (msg.content?.length > 100 ? '...' : ''),
                            }
                        });

                        lastAgentId = agentId;
                    }
                });

                console.log("[Visualizer] Reconstructed graph:", {
                    agents: Array.from(foundAgents.values()),
                    edges: foundEdges
                });

                // Update state
                setAgents(Array.from(foundAgents.values()));
                setEdges(foundEdges);

                // Fetch workflow logs from API instead of reconstructing from messages
                fetchWorkflowLogs(convo.id);

                // Set active agent if conversation has one
                if (convo.activeAgent) {
                    setActiveAgentId(convo.activeAgent);
                    // Ensure active agent is in the list
                    if (!foundAgents.has(convo.activeAgent)) {
                        setAgents(prev => {
                            const newAgents = [...prev, {
                                id: convo.activeAgent!,
                                name: convo.activeAgent!,
                                status: 'active' as AgentStatus
                            }];
                            if (lastAgentId && lastAgentId !== convo.activeAgent) {
                                setEdges(e => [...e, {
                                    id: `${lastAgentId}-${convo.activeAgent}`,
                                    source: lastAgentId!,
                                    target: convo.activeAgent!,
                                    animated: true
                                }]);
                            }
                            return newAgents;
                        });
                    } else {
                        setAgents(prev => prev.map(a =>
                            a.id === convo.activeAgent ? { ...a, status: 'active' } : a
                        ));
                    }
                }
            } else {
                console.error("[Visualizer] Failed to load messages:", response.status);
            }
        } catch (error) {
            console.error("Failed to load conversation history:", error);
        }
    }, [token]);

    const fetchWorkflowLogs = useCallback(async (conversationId: string) => {
        try {
            const response = await fetch(`/api/v1/conversations/${conversationId}/workflow-logs`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                const logs: any[] = await response.json();
                const mapped: WorkflowEvent[] = logs.map(l => ({
                    id: l.id,
                    type: l.type as any,
                    timestamp: l.timestamp,
                    agentId: l.agentId,
                    agentName: l.agentName,
                    conversationId: conversationId,
                    content: l.content,
                    metadata: {
                        ...l.metadata,
                        // Normalize snake_case for frontend
                        toAgent: l.metadata?.toAgent || l.metadata?.to_agent,
                        fromAgent: l.metadata?.fromAgent || l.metadata?.from_agent,
                        skillId: l.metadata?.skillId || l.metadata?.skill_id
                    }
                }));
                // Sort by timestamp descending
                setEventLog(mapped.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()));
            }
        } catch (error) {
            console.error("[Visualizer] Failed to fetch workflow logs:", error);
        }
    }, [token]);

    const handleDeleteWorkflowLog = useCallback(async (logId: string) => {
        if (!window.confirm('Are you sure you want to delete this log?')) return;
        try {
            const response = await fetch(`/api/v1/workflow-logs/${logId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                setEventLog(prev => prev.filter(l => l.id !== logId));
            } else {
                console.error("[Visualizer] Failed to delete log:", response.status);
            }
        } catch (error) {
            console.error("[Visualizer] Error deleting log:", error);
        }
    }, [token]);

    // Clear and reset
    const handleReset = useCallback(() => {
        setSelectedConversation(null);
        setAgents([]);
        setEdges([]);
        setActiveAgentId(null);
        setEventLog([]);
    }, []);

    // Export workflow as JSON
    const handleExport = useCallback(() => {
        const data = {
            conversationId: selectedConversation?.id,
            domainId: selectedConversation?.domainId,
            exportedAt: new Date().toISOString(),
            agents: agents.map(a => ({
                id: a.id,
                name: a.name,
                status: a.status,
                responseTime: a.responseTime,
                tokenCount: a.tokenCount,
            })),
            edges: edges.map(e => ({
                id: e.id,
                source: e.source,
                target: e.target,
                label: e.label,
            })),
            eventLog: eventLog,
        };

        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `workflow-${selectedConversation?.id?.slice(0, 8) || 'export'}-${Date.now()}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }, [selectedConversation, agents, edges, eventLog]);

    // Check dark mode
    const isDarkMode = document.documentElement.classList.contains('dark');

    return (
        <div className="h-screen flex flex-col bg-gray-50 dark:bg-gray-950 font-sans">
            {/* Header */}
            <header className="flex items-center justify-between px-6 py-4 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 shadow-sm z-10">
                <div className="flex items-center gap-4">
                    <a
                        href="/"
                        className="p-2 -ml-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100"
                        aria-label="Back to home"
                    >
                        <ArrowLeft strokeWidth={2} className="w-5 h-5" />
                    </a>
                    <div className="flex flex-col">
                        <h1 className="text-lg font-bold text-gray-900 dark:text-white tracking-tight flex items-center gap-2">
                            Workflow Visualizer
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300">Beta</span>
                        </h1>
                        <p className="text-xs text-gray-500 dark:text-gray-400 font-medium">
                            Real-time agent observability & debugging
                        </p>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    {/* Connection Status Badge */}
                    <div className={`px-3 py-1.5 rounded-full border flex items-center gap-2 text-xs font-medium transition-colors ${isConnected
                        ? 'bg-green-50 text-green-700 border-green-200 dark:bg-green-900/20 dark:text-green-400 dark:border-green-800'
                        : 'bg-red-50 text-red-700 border-red-200 dark:bg-red-900/20 dark:text-red-400 dark:border-red-800'
                        }`}>
                        <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
                        {isConnected ? 'Live Connected' : 'Disconnected'}
                    </div>

                    <div className="h-6 w-px bg-gray-200 dark:bg-gray-800 mx-2" />

                    {/* Conversation Selector */}
                    <div className="relative min-w-[240px]">
                        <select
                            value={selectedConversation?.id || ''}
                            onChange={(e) => {
                                const convo = conversations.find(c => c.id === e.target.value);
                                if (convo) handleSelectConversation(convo);
                            }}
                            disabled={isLoading}
                            className="w-full pl-3 pr-8 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-sm font-medium text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none disabled:opacity-50 transition-all hover:bg-white dark:hover:bg-gray-700"
                        >
                            <option value="">
                                {isLoading ? 'Loading...' : conversations.length === 0 ? 'No active sessions' : 'Select a session...'}
                            </option>
                            {conversations.map(c => (
                                <option key={c.id} value={c.id}>
                                    {c.domainId.toUpperCase()} • {c.id.slice(0, 8)}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-1 border-l border-gray-200 dark:border-gray-800 pl-3">
                        <button
                            onClick={handleReset}
                            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
                            title="Reset View"
                        >
                            <RefreshCw className="w-4 h-4" />
                        </button>
                        <button
                            onClick={handleExport}
                            disabled={!selectedConversation || agents.length === 0}
                            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors disabled:opacity-30"
                            title="Export Data"
                        >
                            <Download className="w-4 h-4" />
                        </button>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="flex-1 p-6 overflow-hidden">
                {selectedConversation ? (
                    <Suspense fallback={
                        <div className="h-full flex items-center justify-center">
                            <div className="text-gray-500 dark:text-gray-400">Loading visualizer…</div>
                        </div>
                    }>
                        <div className="h-[calc(100%-80px)]">
                            <WorkflowVisualizer
                                agents={agents}
                                edges={edges}
                                activeAgentId={activeAgentId}
                                eventLog={eventLog}
                                isDarkMode={isDarkMode}
                                onDeleteLog={handleDeleteWorkflowLog}
                            />
                        </div>
                        <div className="mt-4 flex justify-end">
                            <button
                                onClick={() => selectedConversation && fetchWorkflowLogs(selectedConversation.id)}
                                className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-blue-600 hover:text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors"
                            >
                                <RefreshCw className="w-3 h-3" />
                                Refresh Logs
                            </button>
                        </div>
                    </Suspense>
                ) : (
                    <div className="h-full flex flex-col items-center justify-center text-center p-8 bg-white/50 dark:bg-gray-900/50">
                        <div className="relative mb-8 group">
                            <div className="absolute inset-0 bg-blue-500/20 rounded-full blur-2xl group-hover:bg-blue-500/30 transition-all duration-500" />
                            <div className="relative w-24 h-24 rounded-2xl bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-900 border border-gray-200 dark:border-gray-700 shadow-xl flex items-center justify-center">
                                <Radio className="w-10 h-10 text-blue-500 dark:text-blue-400" strokeWidth={1.5} />
                                <div className="absolute -top-2 -right-2 w-8 h-8 bg-green-500 rounded-lg flex items-center justify-center shadow-lg border-2 border-white dark:border-gray-800">
                                    <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
                                </div>
                                <div className="absolute -bottom-2 -left-2 w-8 h-8 bg-purple-500 rounded-lg flex items-center justify-center shadow-lg border-2 border-white dark:border-gray-800">
                                    <RefreshCw className="w-4 h-4 text-white animate-spin-slow" />
                                </div>
                            </div>
                        </div>
                        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
                            Visualizer Connected
                        </h2>
                        <p className="text-gray-500 dark:text-gray-400 max-w-md leading-relaxed text-sm">
                            Select an active conversation from the top bar to inspect agent workflows, latency metrics, and real-time state transitions.
                        </p>
                    </div>
                )}
            </main>
        </div>
    );
}

export default VisualizerPage;
