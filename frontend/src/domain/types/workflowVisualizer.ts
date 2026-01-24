/**
 * Domain types for the Live Workflow Visualizer
 */

export type AgentStatus = 'idle' | 'active' | 'complete' | 'error';

export interface WorkflowAgentNode {
    id: string;
    name: string;
    status: AgentStatus;
    responseTime?: number;
    tokenCount?: number;
}

export interface WorkflowEdgeData {
    id: string;
    source: string;
    target: string;
    animated?: boolean;
    label?: string;
}

export interface WorkflowEvent {
    id?: string;
    type: 'step_start' | 'step_complete' | 'handoff' | 'thought';
    timestamp: string;
    agentId: string;
    agentName: string;
    conversationId: string;
    content?: string;
    metadata?: Record<string, unknown>;
}

export interface WorkflowVisualizerState {
    conversationId: string | null;
    agents: WorkflowAgentNode[];
    edges: WorkflowEdgeData[];
    activeAgentId: string | null;
    eventLog: WorkflowEvent[];
    isConnected: boolean;
}
