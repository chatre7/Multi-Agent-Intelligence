/**
 * Tool Approval Modal component for viewing and approving/rejecting tool runs
 */

import { X, CheckCircle, AlertCircle } from "lucide-react";
import type { ToolRun } from "../../../domain/entities/types";
import { useState } from "react";

interface ToolApprovalModalProps {
  toolRun: ToolRun;
  onClose: () => void;
  onApprove?: (runId: string) => Promise<void>;
  onReject?: (runId: string, reason: string) => Promise<void>;
}

export function ToolApprovalModal({
  toolRun,
  onClose,
  onApprove,
  onReject,
}: ToolApprovalModalProps) {
  const [isProcessing, setIsProcessing] = useState(false);
  const [rejectionReason, setRejectionReason] = useState("");
  const [showRejectForm, setShowRejectForm] = useState(false);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  const handleApprove = async () => {
    if (!onApprove) return;

    try {
      setIsProcessing(true);
      setMessage(null);
      await onApprove(toolRun.id);
      setMessage({ type: "success", text: "Tool run approved successfully" });
      setTimeout(() => onClose(), 1500);
    } catch (err) {
      console.error("[ToolApprovalModal] Approval error:", err);
      setMessage({
        type: "error",
        text: err instanceof Error ? err.message : "Failed to approve",
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleReject = async () => {
    if (!onReject) return;

    try {
      setIsProcessing(true);
      setMessage(null);
      await onReject(toolRun.id, rejectionReason || "Rejected by admin");
      setMessage({ type: "success", text: "Tool run rejected successfully" });
      setTimeout(() => onClose(), 1500);
    } catch (err) {
      console.error("[ToolApprovalModal] Rejection error:", err);
      setMessage({
        type: "error",
        text: err instanceof Error ? err.message : "Failed to reject",
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const isApprovalPending = toolRun.status === "PENDING";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg bg-white shadow-xl">
        {/* Header */}
        <div className="sticky top-0 border-b border-gray-200 bg-white p-6">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">
                Tool Execution Request
              </h2>
              <p className="mt-1 text-sm text-gray-500">
                Review and approve or reject this tool run
              </p>
            </div>
            <button
              onClick={onClose}
              className="rounded-lg p-2 hover:bg-gray-100"
            >
              <X className="h-5 w-5 text-gray-500" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Status Messages */}
          {message && (
            <div
              className={`rounded-lg p-4 ${
                message.type === "success"
                  ? "bg-green-50 text-green-800"
                  : "bg-red-50 text-red-800"
              }`}
            >
              <div className="flex items-center gap-2">
                {message.type === "success" ? (
                  <CheckCircle className="h-5 w-5" />
                ) : (
                  <AlertCircle className="h-5 w-5" />
                )}
                <span className="text-sm font-medium">{message.text}</span>
              </div>
            </div>
          )}

          {/* Tool Information */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">
              Tool Information
            </h3>

            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-lg bg-gray-50 p-4">
                <label className="text-xs font-medium text-gray-600">
                  Tool ID
                </label>
                <p className="mt-2 text-sm font-medium text-gray-900">
                  {toolRun.tool_id || "Unknown"}
                </p>
              </div>

              <div className="rounded-lg bg-gray-50 p-4">
                <label className="text-xs font-medium text-gray-600">
                  Status
                </label>
                <p className="mt-2 text-sm font-medium text-gray-900">
                  {toolRun.status?.toUpperCase()}
                </p>
              </div>

              <div className="rounded-lg bg-gray-50 p-4">
                <label className="text-xs font-medium text-gray-600">
                  Run ID
                </label>
                <p className="mt-2 text-xs font-mono text-gray-700">
                  {toolRun.id}
                </p>
              </div>
            </div>
          </div>

          {/* Parameters */}
          {toolRun.parameters && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">
                Parameters
              </h3>
              <div className="rounded-lg bg-gray-50 p-4">
                <pre className="overflow-auto text-xs text-gray-700">
                  {typeof toolRun.parameters === "string"
                    ? toolRun.parameters
                    : JSON.stringify(toolRun.parameters, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {/* Approval/Rejection Section */}
          {isApprovalPending && (
            <div className="space-y-4 border-t border-gray-200 pt-6">
              <h3 className="text-lg font-semibold text-gray-900">Decision</h3>

              {!showRejectForm ? (
                <div className="grid grid-cols-2 gap-3">
                  <button
                    onClick={handleApprove}
                    disabled={isProcessing}
                    className="rounded-lg bg-green-600 px-4 py-3 font-medium text-white hover:bg-green-700 disabled:opacity-50 transition-colors"
                  >
                    {isProcessing ? "Processing..." : "✓ Approve"}
                  </button>
                  <button
                    onClick={() => setShowRejectForm(true)}
                    disabled={isProcessing}
                    className="rounded-lg bg-red-600 px-4 py-3 font-medium text-white hover:bg-red-700 disabled:opacity-50 transition-colors"
                  >
                    ✕ Reject
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  <textarea
                    value={rejectionReason}
                    onChange={(e) => setRejectionReason(e.target.value)}
                    placeholder="Enter rejection reason (optional)"
                    className="w-full rounded-lg border border-gray-300 p-3 text-sm focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500"
                    rows={3}
                  />
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      onClick={() => setShowRejectForm(false)}
                      disabled={isProcessing}
                      className="rounded-lg border border-gray-300 px-4 py-2 font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleReject}
                      disabled={isProcessing}
                      className="rounded-lg bg-red-600 px-4 py-2 font-medium text-white hover:bg-red-700 disabled:opacity-50 transition-colors"
                    >
                      {isProcessing ? "Processing..." : "Confirm Rejection"}
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* View Result Section */}
          {toolRun.result && (
            <div className="space-y-4 border-t border-gray-200 pt-6">
              <h3 className="text-lg font-semibold text-gray-900">Result</h3>
              <div className="rounded-lg bg-green-50 p-4">
                <pre className="overflow-auto text-xs text-green-900">
                  {typeof toolRun.result === "string"
                    ? toolRun.result
                    : JSON.stringify(toolRun.result, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {/* Error Section */}
          {toolRun.error && (
            <div className="space-y-4 border-t border-gray-200 pt-6">
              <h3 className="text-lg font-semibold text-gray-900">Error</h3>
              <div className="rounded-lg bg-red-50 p-4">
                <pre className="overflow-auto text-xs text-red-900">
                  {typeof toolRun.error === "string"
                    ? toolRun.error
                    : JSON.stringify(toolRun.error, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
