import { Check, X, ShieldAlert, Terminal } from "lucide-react";
import type { ToolApprovalRequest } from "../../../domain/entities/types";

interface ToolApprovalCardProps {
    request: ToolApprovalRequest;
    onApprove: (requestId: string) => void;
    onReject: (requestId: string) => void;
}

export default function ToolApprovalCard({ request, onApprove, onReject }: ToolApprovalCardProps) {
    return (
        <div className="mx-auto max-w-4xl px-4 py-2">
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 shadow-sm">
                <div className="flex items-start gap-3">
                    <div className="p-2 bg-amber-100 rounded-full text-amber-600">
                        <ShieldAlert size={20} />
                    </div>
                    <div className="flex-1 space-y-2">
                        <div className="flex items-center justify-between">
                            <h3 className="text-sm font-semibold text-amber-900">
                                Tool Approval Required
                            </h3>
                            <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-amber-100 text-amber-700">
                                {request.agentName}
                            </span>
                        </div>

                        <p className="text-sm text-amber-800">
                            Agent is requesting to execute <strong>{request.toolName}</strong>
                        </p>

                        {request.description && (
                            <p className="text-xs text-amber-700 opacity-90">
                                {request.description}
                            </p>
                        )}

                        <div className="bg-white/50 rounded p-2 border border-amber-100 font-mono text-xs text-amber-900 overflow-x-auto">
                            <div className="flex items-center gap-1.5 mb-1 text-amber-500/70 border-b border-amber-100/50 pb-1">
                                <Terminal size={10} />
                                <span>Arguments</span>
                            </div>
                            <pre>{JSON.stringify(request.toolArgs, null, 2)}</pre>
                        </div>

                        <div className="flex gap-2 pt-1">
                            <button
                                onClick={() => onApprove(request.requestId)}
                                className="flex items-center gap-1.5 px-3 py-1.5 bg-green-600 text-white text-xs font-medium rounded hover:bg-green-700 transition-colors shadow-sm"
                            >
                                <Check size={14} />
                                Approve & Execute
                            </button>
                            <button
                                onClick={() => onReject(request.requestId)}
                                className="flex items-center gap-1.5 px-3 py-1.5 bg-white text-red-600 border border-red-200 text-xs font-medium rounded hover:bg-red-50 transition-colors shadow-sm"
                            >
                                <X size={14} />
                                Reject
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
