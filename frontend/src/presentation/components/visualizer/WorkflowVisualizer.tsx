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
    onDeleteLog?: (logId: string) => void;
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
    onDeleteLog,
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
            <div className="w-[500px] flex flex-col bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm">
                <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
                    <h3 className="font-semibold text-sm text-gray-900 dark:text-gray-100">
                        Event Log
                    </h3>
                </div>
                <div
                    className="flex-1 overflow-y-auto"
                    role="log"
                    aria-live="polite"
                    aria-label="Workflow event log"
                >
                    {eventLog.length === 0 ? (
                        <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
                            No events yet…
                        </p>
                    ) : (
                        <table className="w-full text-left text-xs border-collapse">
                            <thead className="bg-gray-50 dark:bg-gray-800 sticky top-0 border-b border-gray-200 dark:border-gray-700">
                                <tr>
                                    <th className="px-3 py-2 font-medium text-gray-500 dark:text-gray-400 w-8">St</th>
                                    <th className="px-3 py-2 font-medium text-gray-500 dark:text-gray-400 w-16">Time</th>
                                    <th className="px-3 py-2 font-medium text-gray-500 dark:text-gray-400 w-20">Agent</th>
                                    <th className="px-3 py-2 font-medium text-gray-500 dark:text-gray-400">Message</th>
                                    <th className="px-3 py-2 font-medium text-gray-500 dark:text-gray-400 w-8"></th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                                {eventLog.map((event, index) => {
                                    const timeStr = event.timestamp
                                        ? new Date(event.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
                                        : '--:--:--';

                                    return (
                                        <tr
                                            key={`${event.timestamp}-${index}`}
                                            className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors group"
                                        >
                                            <td className="px-3 py-2 align-top">
                                                <div className={`mt-1 w-2 h-2 rounded-full ${event.type === 'step_start' ? 'bg-blue-500' :
                                                    event.type === 'step_complete' ? 'bg-green-500' :
                                                        event.type === 'thought' ? 'bg-purple-500' :
                                                            'bg-yellow-500'
                                                    }`} title={event.type} />
                                            </td>
                                            <td className="px-3 py-2 align-top text-gray-400 dark:text-gray-500 whitespace-nowrap">
                                                {timeStr}
                                            </td>
                                            <td className="px-3 py-2 align-top font-medium text-gray-900 dark:text-gray-100 break-words">
                                                {event.agentName}
                                            </td>
                                            <td className="px-3 py-2 align-top text-gray-500 dark:text-gray-400 break-words">
                                                {event.type === 'step_start' && (event.content || 'Started processing')}
                                                {event.type === 'step_complete' && (event.content || 'Completed task')}
                                                {event.type === 'handoff' && (event.content || `Handed off`)}
                                                {event.type === 'thought' && (
                                                    <span className="italic text-gray-600 dark:text-gray-300 block">
                                                        "{event.content ||
                                                            (typeof event.metadata?.reason === 'string' ? event.metadata.reason :
                                                                typeof event.metadata?.thought === 'string' ? event.metadata.thought :
                                                                    'Deciding')}"
                                                    </span>
                                                )}
                                            </td>
                                            <td className="px-3 py-2 align-top text-right">
                                                {event.id && (
                                                    <button
                                                        onClick={() => onDeleteLog?.(event.id!)}
                                                        className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 transition-opacity p-1"
                                                        title="Delete log"
                                                    >
                                                        ×
                                                    </button>
                                                )}
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>
        </div>
    );
}

export const WorkflowVisualizer = memo(WorkflowVisualizerComponent);
export default WorkflowVisualizer;
