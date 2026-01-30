/**
 * AgentNode - Custom React Flow node for displaying agent status
 * Follows Web Interface Guidelines: focus states, accessibility
 */
import { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import type { AgentStatus } from '../../../domain/types/workflowVisualizer';

export interface AgentNodeData extends Record<string, unknown> {
    name: string;
    status: AgentStatus;
    responseTime?: number;
    tokenCount?: number;
}

const statusColors: Record<AgentStatus, { bg: string; ring: string; text: string }> = {
    idle: { bg: 'bg-gray-100', ring: 'ring-gray-300', text: 'text-gray-600' },
    active: { bg: 'bg-blue-50', ring: 'ring-blue-500 animate-pulse', text: 'text-blue-600' },
    complete: { bg: 'bg-green-50', ring: 'ring-green-500', text: 'text-green-600' },
    error: { bg: 'bg-red-50', ring: 'ring-red-500', text: 'text-red-600' },
};

const statusLabels: Record<AgentStatus, string> = {
    idle: 'Idle',
    active: 'Processing…',
    complete: 'Complete',
    error: 'Error',
};

function AgentNodeComponent({ data }: NodeProps) {
    const nodeData = data as AgentNodeData;
    const { name, status, responseTime, tokenCount } = nodeData;
    const colors = statusColors[status] || statusColors.idle;

    return (
        <div
            className={`
        relative px-4 py-3 rounded-xl shadow-lg border-2 min-w-[140px]
        ${colors.bg} ring-2 ${colors.ring}
        transition-all duration-300
        focus-visible:ring-4 focus-visible:ring-offset-2 focus-visible:ring-blue-500
        motion-reduce:animate-none
      `}
            role="button"
            tabIndex={0}
            aria-label={`Agent ${name} - Status: ${statusLabels[status] || 'Unknown'}`}
        >
            {/* Input Handle */}
            <Handle
                type="target"
                position={Position.Left}
                className="!w-3 !h-3 !bg-gray-400"
            />

            {/* Agent Info */}
            <div className="flex items-center gap-2">
                {/* Status Indicator */}
                <div
                    className={`w-3 h-3 rounded-full ${status === 'active' ? 'bg-blue-500 animate-pulse motion-reduce:animate-none' :
                            status === 'complete' ? 'bg-green-500' :
                                status === 'error' ? 'bg-red-500' : 'bg-gray-400'
                        }`}
                    aria-hidden="true"
                />
                {/* Name */}
                <span className={`font-semibold text-sm ${colors.text}`}>
                    {name}
                </span>
            </div>

            {/* Metrics */}
            {(responseTime !== undefined || tokenCount !== undefined) && (
                <div className="mt-2 text-xs text-gray-500 flex gap-2">
                    {responseTime !== undefined && (
                        <span>{responseTime}ms</span>
                    )}
                    {tokenCount !== undefined && (
                        <span>{tokenCount} tokens</span>
                    )}
                </div>
            )}

            {/* Output Handle */}
            <Handle
                type="source"
                position={Position.Right}
                className="!w-3 !h-3 !bg-gray-400"
            />
        </div>
    );
}

export const AgentNode = memo(AgentNodeComponent);
export default AgentNode;
