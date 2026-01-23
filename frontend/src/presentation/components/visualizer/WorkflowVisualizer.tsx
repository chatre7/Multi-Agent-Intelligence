/**
 * WorkflowVisualizer - Main React Flow canvas for agent workflow visualization
 * Features: real-time updates, custom nodes/edges, minimap, controls
 */
import { memo, useCallback, useMemo, useEffect } from 'react';
import {
    ReactFlow,
    Controls,
    MiniMap,
    Background,
    BackgroundVariant,
    useNodesState,
    useEdgesState,
    type Node,
    type Edge,
    type NodeTypes,
    type EdgeTypes,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { AgentNode, type AgentNodeData } from './AgentNode';
import { AnimatedEdge } from './AnimatedEdge';
import type { WorkflowAgentNode, WorkflowEdgeData, WorkflowEvent } from '../../../domain/types/workflowVisualizer';

// Register custom node types
const nodeTypes: NodeTypes = {
    agent: AgentNode,
};

// Register custom edge types  
const edgeTypes: EdgeTypes = {
    animated: AnimatedEdge,
};

interface WorkflowVisualizerProps {
    agents: WorkflowAgentNode[];
    edges: WorkflowEdgeData[];
    activeAgentId: string | null;
    eventLog: WorkflowEvent[];
    isDarkMode?: boolean;
}

// Convert domain agents to React Flow nodes with auto-layout
function agentsToNodes(agents: WorkflowAgentNode[], activeAgentId: string | null): Node<AgentNodeData>[] {
    const spacing = 200;
    return agents.map((agent, index) => ({
        id: agent.id,
        type: 'agent',
        position: { x: index * spacing, y: 100 },
        data: {
            name: agent.name,
            status: agent.id === activeAgentId ? 'active' : agent.status,
            responseTime: agent.responseTime,
            tokenCount: agent.tokenCount,
        } as AgentNodeData,
    }));
}

// Convert domain edges to React Flow edges
function edgesToFlowEdges(edges: WorkflowEdgeData[], activeAgentId: string | null): Edge[] {
    return edges.map((edge) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        type: 'animated',
        data: {
            animated: edge.target === activeAgentId,
            label: edge.label,
        },
    }));
}

function WorkflowVisualizerComponent({
    agents,
    edges: domainEdges,
    activeAgentId,
    eventLog,
    isDarkMode = false,
}: WorkflowVisualizerProps) {
    // Convert domain models to React Flow format
    const initialNodes = useMemo(() => agentsToNodes(agents, activeAgentId), [agents, activeAgentId]);
    const initialEdges = useMemo(() => edgesToFlowEdges(domainEdges, activeAgentId), [domainEdges, activeAgentId]);

    const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
    const [flowEdges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

    // Update nodes when agents change
    useEffect(() => {
        setNodes(agentsToNodes(agents, activeAgentId));
    }, [agents, activeAgentId, setNodes]);

    // Update edges when domain edges change
    useEffect(() => {
        setEdges(edgesToFlowEdges(domainEdges, activeAgentId));
    }, [domainEdges, activeAgentId, setEdges]);

    const onConnect = useCallback(() => {
        // Connections handled by backend, not user
    }, []);

    return (
        <div className="flex h-full w-full gap-4">
            {/* Main Canvas */}
            <div
                className="flex-1 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden"
                style={{ colorScheme: isDarkMode ? 'dark' : 'light' }}
            >
                <ReactFlow
                    nodes={nodes}
                    edges={flowEdges}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                    onConnect={onConnect}
                    nodeTypes={nodeTypes}
                    edgeTypes={edgeTypes}
                    fitView
                    attributionPosition="bottom-left"
                    className="touch-manipulation"
                >
                    <Controls
                        className="!bg-white dark:!bg-gray-800 !border-gray-200 dark:!border-gray-700"
                        aria-label="Zoom controls"
                    />
                    <MiniMap
                        className="!bg-gray-50 dark:!bg-gray-900"
                        nodeColor={(node) => {
                            const data = node.data as AgentNodeData | undefined;
                            return data?.status === 'active' ? '#3b82f6' : '#9ca3af';
                        }}
                        aria-label="Workflow minimap"
                    />
                    <Background
                        variant={BackgroundVariant.Dots}
                        gap={16}
                        size={1}
                        color={isDarkMode ? '#374151' : '#e5e7eb'}
                    />
                </ReactFlow>
            </div>

            {/* Event Log Sidebar */}
            <div className="w-64 flex flex-col bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
                <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                    <h3 className="font-semibold text-sm text-gray-900 dark:text-gray-100">
                        Event Log
                    </h3>
                </div>
                <div
                    className="flex-1 overflow-y-auto p-2"
                    role="log"
                    aria-live="polite"
                    aria-label="Workflow event log"
                >
                    {eventLog.length === 0 ? (
                        <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
                            No events yet…
                        </p>
                    ) : (
                        <ul className="space-y-1">
                            {eventLog.map((event, index) => (
                                <li
                                    key={`${event.timestamp}-${index}`}
                                    className="event-item text-xs p-2 rounded bg-gray-50 dark:bg-gray-800"
                                    style={{ contentVisibility: 'auto', containIntrinsicSize: '0 40px' }}
                                >
                                    <div className="flex items-center gap-2">
                                        <span className={`w-2 h-2 rounded-full ${event.type === 'step_start' ? 'bg-blue-500' :
                                                event.type === 'step_complete' ? 'bg-green-500' :
                                                    'bg-yellow-500'
                                            }`} />
                                        <span className="font-medium text-gray-900 dark:text-gray-100">
                                            {event.agentName}
                                        </span>
                                    </div>
                                    <p className="text-gray-500 dark:text-gray-400 mt-1">
                                        {event.type === 'step_start' && 'Started processing'}
                                        {event.type === 'step_complete' && 'Completed'}
                                        {event.type === 'handoff' && `Handed off`}
                                    </p>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
            </div>
        </div>
    );
}

export const WorkflowVisualizer = memo(WorkflowVisualizerComponent);
export default WorkflowVisualizer;
