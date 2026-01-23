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

                    // Add event
                    setEventLog(prev => [{
                        type: 'step_start',
                        timestamp: new Date().toISOString(),
                        agentId: payload.agent_id,
                        agentName: payload.agent_name,
                        conversationId: payload.conversationId,
                    }, ...prev.slice(0, 49)]); // Keep last 50
                },
            },
            {
                type: 'workflow_step_start',
                handler: (data: unknown) => {
                    const msg = data as { payload: { agentId: string; agentName: string; conversationId: string } };
                    const payload = msg.payload;
                    if (!payload || selectedConversation?.id !== payload.conversationId) return;

                    setActiveAgentId(payload.agentId);
                    setAgents(prev => prev.map(a => ({
                        ...a,
                        status: a.id === payload.agentId ? 'active' : a.status,
                    })));

                    setEventLog(prev => [{
                        type: 'step_start',
                        timestamp: new Date().toISOString(),
                        agentId: payload.agentId,
                        agentName: payload.agentName,
                        conversationId: payload.conversationId,
                        metadata: {}
                    }, ...prev.slice(0, 49)]);
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

                    const agent = agents.find(a => a.id === payload.agentId);
                    setEventLog(prev => [{
                        type: 'step_complete',
                        timestamp: new Date().toISOString(),
                        agentId: payload.agentId,
                        agentName: agent?.name || payload.agentId,
                        conversationId: payload.conversationId,
                        metadata: { durationMs: payload.durationMs, tokenCount: payload.tokenCount },
                    }, ...prev.slice(0, 49)]);
                },
            },
            {
                type: 'workflow_handoff',
                handler: (data: unknown) => {
                    const msg = data as { payload: { fromAgentId: string; toAgentId: string; fromAgent: string; toAgent: string; reason?: string; conversationId: string } };
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

                    setEventLog(prev => [{
                        type: 'handoff',
                        timestamp: new Date().toISOString(),
                        agentId: payload.toAgentId,
                        agentName: payload.toAgent,
                        conversationId: payload.conversationId,
                        metadata: { fromAgent: payload.fromAgent, reason: payload.reason },
                    }, ...prev.slice(0, 49)]);
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
                setEventLog(historicalEvents.reverse());

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
                            // If this is the only agent, it's fine. If we had others, maybe link last to active?
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
                } else if (foundAgents.size === 0) {
                    console.log("[Visualizer] No agents found in history");
                }
            } else {
                console.error("[Visualizer] Failed to load messages:", response.status);
            }
        } catch (error) {
            console.error("Failed to load conversation history:", error);
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
        <div className="h-screen flex flex-col bg-gray-50 dark:bg-gray-950">
            {/* Header */}
            <header className="flex items-center justify-between px-6 py-4 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
                <div className="flex items-center gap-4">
                    <a
                        href="/"
                        className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors focus-visible:ring-2 focus-visible:ring-blue-500"
                        aria-label="Back to home"
                    >
                        <ArrowLeft className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                    </a>
                    <div>
                        <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                            Live Workflow Visualizer
                        </h1>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                            Real-time agent observability
                        </p>
                    </div>
                </div>

                <div className="flex items-center gap-4">
                    {/* Connection Status */}
                    <div className="flex items-center gap-2">
                        <Radio
                            className={`w-4 h-4 ${isConnected ? 'text-green-500' : 'text-red-500'}`}
                            aria-hidden="true"
                        />
                        <span className="text-sm text-gray-600 dark:text-gray-400">
                            {isConnected ? 'Connected' : 'Disconnected'}
                        </span>
                    </div>

                    {/* Conversation Selector */}
                    <select
                        value={selectedConversation?.id || ''}
                        onChange={(e) => {
                            const convo = conversations.find(c => c.id === e.target.value);
                            if (convo) handleSelectConversation(convo);
                        }}
                        disabled={isLoading}
                        className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm focus-visible:ring-2 focus-visible:ring-blue-500 disabled:opacity-50"
                        aria-label="Select conversation"
                    >
                        <option value="">
                            {isLoading ? 'Loading…' : conversations.length === 0 ? 'No conversations' : 'Select Conversation…'}
                        </option>
                        {conversations.map(c => (
                            <option key={c.id} value={c.id}>
                                {c.domainId} - {c.id.slice(0, 8)}
                            </option>
                        ))}
                    </select>

                    {/* Reset Button */}
                    <button
                        onClick={handleReset}
                        className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors focus-visible:ring-2 focus-visible:ring-blue-500"
                        aria-label="Reset visualization"
                    >
                        <RefreshCw className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                    </button>

                    {/* Export Button */}
                    <button
                        onClick={handleExport}
                        disabled={!selectedConversation || agents.length === 0}
                        className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors focus-visible:ring-2 focus-visible:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                        aria-label="Export workflow as JSON"
                    >
                        <Download className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                    </button>
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
                        <WorkflowVisualizer
                            agents={agents}
                            edges={edges}
                            activeAgentId={activeAgentId}
                            eventLog={eventLog}
                            isDarkMode={isDarkMode}
                        />
                    </Suspense>
                ) : (
                    <div className="h-full flex flex-col items-center justify-center text-center">
                        <div className="w-16 h-16 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center mb-4">
                            <Radio className="w-8 h-8 text-gray-400" />
                        </div>
                        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
                            No Conversation Selected
                        </h2>
                        <p className="text-gray-500 dark:text-gray-400 max-w-md">
                            Start a conversation in the Chat page, then select it here to visualize the agent workflow in real-time.
                        </p>
                    </div>
                )}
            </main>
        </div>
    );
}

export default VisualizerPage;
