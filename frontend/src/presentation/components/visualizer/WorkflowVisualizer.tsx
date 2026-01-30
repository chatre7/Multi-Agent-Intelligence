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
import { Zap } from 'lucide-react';
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
                className="flex-1 rounded-xl border border-gray-200 bg-gray-50 overflow-hidden shadow-inner relative"
                style={{ colorScheme: 'light' }}
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
                        showInteractive={false}
                        className="!bg-white !border-gray-200 !shadow-sm !rounded-lg overflow-hidden [&>button]:!border-b-gray-100 [&>button]:!text-gray-600 [&>button:hover]:!bg-gray-50"
                    />
                    <MiniMap
                        className="!bg-white !border-gray-200 !shadow-sm !rounded-lg overflow-hidden bottom-4 right-4"
                        nodeColor={(node) => {
                            const data = node.data as AgentNodeData | undefined;
                            if (data?.status === 'active') return '#3b82f6';
                            if (data?.status === 'complete') return '#22c55e';
                            if (data?.status === 'error') return '#ef4444';
                            return '#e5e7eb';
                        }}
                        maskColor={'rgba(243, 244, 246, 0.7)'}
                    />
                    <Background
                        variant={BackgroundVariant.Dots}
                        gap={24}
                        size={1.5}
                        color={'#d1d5db'}
                    />
                </ReactFlow>
            </div>

            {/* Event Log Sidebar */}
            <div className="w-[450px] flex flex-col bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
                <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
                    <h3 className="font-semibold text-sm text-gray-900 flex items-center gap-2">
                        Event Log
                        <span className="text-xs font-normal text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
                            {eventLog.length}
                        </span>
                    </h3>
                </div>

                <div
                    className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-200 scrollbar-track-transparent"
                    role="log"
                    aria-live="polite"
                >
                    {eventLog.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-full text-center px-6 py-8">
                            <div className="w-16 h-16 rounded-full bg-blue-50 flex items-center justify-center mb-4 ring-8 ring-blue-50/50">
                                <span className="text-2xl animate-pulse">📋</span>
                            </div>
                            <h4 className="text-sm font-semibold text-gray-900 mb-1">Event Log Empty</h4>
                            <p className="text-xs text-gray-500 mt-1 max-w-[200px]">Waiting for agents to start processing tasks...</p>
                        </div>
                    ) : (
                        <div className="divide-y divide-gray-100">
                            {eventLog.map((event, index) => {
                                const timeStr = event.timestamp
                                    ? new Date(event.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
                                    : '--:--:--';

                                const isStart = event.type === 'step_start';
                                const isEnd = event.type === 'step_complete';
                                const isThought = event.type === 'thought';
                                const isHandoff = event.type === 'handoff';

                                return (
                                     <div
                                         key={`${event.timestamp}-${index}`}
                                        className="relative group p-4 hover:bg-gray-50/80 transition-all font-mono text-xs"
                                     >
                                         <div className="flex items-start gap-3">
                                            {/* Status Dot */}
                                            <div className="mt-1.5 flex-shrink-0 relative">
                                                <div className={`w-2.5 h-2.5 rounded-full ring-2 ring-white ${isStart ? 'bg-blue-500' :
                                                    isEnd ? 'bg-green-500' :
                                                        isThought ? 'bg-purple-400' :
                                                            'bg-amber-400'
                                                    }`} />
                                                {index !== eventLog.length - 1 && (
                                                    <div className="absolute top-3 left-1.5 w-px h-[calc(100%+1rem)] bg-gray-100 -z-10" />
                                                )}
                                            </div>

                                            <div className="flex-1 min-w-0 space-y-1">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-gray-400 select-none">
                                                        {timeStr}
                                                    </span>
                                                    <span className={`font-semibold  ${isStart ? 'text-blue-700' :
                                                        isEnd ? 'text-green-700' :
                                                            isThought ? 'text-purple-700' :
                                                                'text-amber-700'
                                                        }`}>
                                                        {event.agentName}
                                                        {typeof event.metadata?.skill_id === 'string' && (
                                                            <span className="ml-2 inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] bg-amber-100 text-amber-700 border border-amber-200">
                                                                <Zap size={10} className="fill-amber-500 text-amber-600" />
                                                                {String(event.metadata?.skill_id)}
                                                            </span>
                                                        )}
                                                    </span>
                                                </div>

                                                <div className="text-gray-600 break-words leading-relaxed">
                                                    {isStart && (typeof event.content === 'string' ? event.content : JSON.stringify(event.content) || 'Started processing')}
                                                    {isEnd && (typeof event.content === 'string' ? event.content : JSON.stringify(event.content) || 'Completed task')}
                                                    {isHandoff && (
                                                        <span className="flex items-center gap-1.5 text-amber-600">
                                                            <span>Handed off to</span>
                                                            <strong className="px-1.5 py-0.5 bg-amber-50 rounded">
                                                                {typeof event.metadata?.toAgent === 'string' ? String(event.metadata?.toAgent) : "Next Agent"}
                                                            </strong>
                                                        </span>
                                                    )}
                                                    {isThought && (
                                                        <div className="mt-1 pl-3 border-l-2 border-purple-100 italic opacity-90">
                                                            {typeof event.content === 'string' ? event.content :
                                                                typeof event.metadata?.reason === 'string' ? String(event.metadata?.reason) :
                                                                    typeof event.metadata?.thought === 'string' ? String(event.metadata?.thought) :
                                                                        "Thinking..."}
                                                        </div>
                                                    )}
                                                </div>
                                            </div>

                                            {/* Actions */}
                                            <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                                                {event.id && (
                                                    <button
                                                        onClick={() => onDeleteLog?.(event.id!)}
                                                        className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                                                        title="Delete log entry"
                                                        aria-label="Delete log entry"
                                                    >
                                                        ×
                                                    </button>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export const WorkflowVisualizer = memo(WorkflowVisualizerComponent);
export default WorkflowVisualizer;
