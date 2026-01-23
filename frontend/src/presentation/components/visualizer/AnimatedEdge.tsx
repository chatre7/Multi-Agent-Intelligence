/**
 * AnimatedEdge - Custom React Flow edge with animation
 * Respects prefers-reduced-motion for accessibility
 */
import { memo } from 'react';
import { BaseEdge, getBezierPath, type EdgeProps } from '@xyflow/react';

interface AnimatedEdgeData {
    animated?: boolean;
    label?: string;
}

function AnimatedEdgeComponent({
    id,
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    data,
    style,
}: EdgeProps) {
    const edgeData = data as AnimatedEdgeData | undefined;
    const [edgePath] = getBezierPath({
        sourceX,
        sourceY,
        sourcePosition,
        targetX,
        targetY,
        targetPosition,
    });

    // Check for reduced motion preference
    const prefersReducedMotion =
        typeof window !== 'undefined' &&
        window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    const isAnimated = edgeData?.animated && !prefersReducedMotion;

    return (
        <>
            <BaseEdge
                id={id}
                path={edgePath}
                style={{
                    ...style,
                    strokeWidth: 2,
                    stroke: isAnimated ? '#3b82f6' : '#9ca3af',
                }}
            />
            {/* Animated flow indicator */}
            {isAnimated && (
                <circle r="4" fill="#3b82f6">
                    <animateMotion
                        dur="1.5s"
                        repeatCount="indefinite"
                        path={edgePath}
                    />
                </circle>
            )}
        </>
    );
}

export const AnimatedEdge = memo(AnimatedEdgeComponent);
export default AnimatedEdge;
