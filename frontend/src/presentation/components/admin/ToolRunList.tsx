/**
 * Tool Run List component for displaying and managing tool runs
 */

import { useState, useEffect } from "react";
import { CheckCircle, XCircle, Clock, Loader, Filter } from "lucide-react";
import type { ToolRun } from "../../../domain/entities/types";
import { apiClient } from "../../../infrastructure/api/apiClient";

interface ToolRunListProps {
  onSelect: (toolRun: ToolRun) => void;
  onApprove?: (runId: string) => Promise<void>;
  onReject?: (runId: string, reason: string) => Promise<void>;
  selectedToolRunId?: string;
}

type ToolRunStatus = "PENDING" | "APPROVED" | "REJECTED" | "EXECUTED";

export function ToolRunList({
  onSelect,
  onApprove,
  onReject,
  selectedToolRunId,
}: ToolRunListProps) {
  const [toolRuns, setToolRuns] = useState<ToolRun[]>([]);
  const [filterStatus, setFilterStatus] = useState<ToolRunStatus | "">("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchToolRuns();
    const interval = setInterval(fetchToolRuns, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchToolRuns = async () => {
    try {
      setError(null);
      const data = await apiClient.listToolRuns();
      setToolRuns(data || []);
    } catch (err) {
      console.error("[ToolRunList] Error fetching tool runs:", err);
      setError("Failed to load tool runs");
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "APPROVED":
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case "REJECTED":
        return <XCircle className="h-5 w-5 text-red-500" />;
      case "PENDING":
        return <Clock className="h-5 w-5 text-yellow-500" />;
      case "EXECUTED":
        return <CheckCircle className="h-5 w-5 text-blue-500" />;
      default:
        return <Clock className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const baseClasses =
      "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium";
    switch (status) {
      case "APPROVED":
        return `${baseClasses} bg-green-100 text-green-800`;
      case "REJECTED":
        return `${baseClasses} bg-red-100 text-red-800`;
      case "PENDING":
        return `${baseClasses} bg-yellow-100 text-yellow-800`;
      case "EXECUTED":
        return `${baseClasses} bg-blue-100 text-blue-800`;
      default:
        return `${baseClasses} bg-gray-100 text-gray-800`;
    }
  };

  const filteredToolRuns = toolRuns.filter((run) => {
    if (!filterStatus) return true;
    return run.status === filterStatus;
  });

  return (
    <div className="space-y-4">
      {/* Filter */}
      <div className="flex items-center gap-2">
        <Filter className="h-5 w-5 text-gray-400" />
        <select
          value={filterStatus}
          onChange={(e) =>
            setFilterStatus(e.target.value as ToolRunStatus | "")
          }
          className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="">All Statuses</option>
          <option value="PENDING">Pending</option>
          <option value="APPROVED">Approved</option>
          <option value="REJECTED">Rejected</option>
          <option value="EXECUTED">Executed</option>
        </select>
      </div>

      {/* Error State */}
      {error && (
        <div className="rounded-lg bg-red-50 p-4 text-sm text-red-800">
          {error}
        </div>
      )}

      {/* Loading State */}
      {isLoading ? (
        <div className="flex items-center justify-center py-8">
          <Loader className="h-5 w-5 animate-spin text-gray-400" />
        </div>
      ) : (
        /* Tool Run List */
        <div className="space-y-2">
          {filteredToolRuns.length === 0 ? (
            <div className="rounded-lg border border-gray-200 bg-gray-50 p-8 text-center">
              <p className="text-sm text-gray-500">No tool runs found</p>
            </div>
          ) : (
            filteredToolRuns.map((run) => (
              <button
                key={run.id}
                onClick={() => onSelect(run)}
                className={`w-full rounded-lg border p-4 text-left transition-all ${
                  selectedToolRunId === run.id
                    ? "border-blue-500 bg-blue-50"
                    : "border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50"
                }`}
              >
                <div className="space-y-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h4 className="font-medium text-gray-900">
                        {run.tool_id || "Unknown Tool"}
                      </h4>
                      <p className="mt-1 text-xs text-gray-500">ID: {run.id}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      {getStatusIcon(run.status)}
                      <span className={getStatusBadge(run.status)}>
                        {run.status.toUpperCase()}
                      </span>
                    </div>
                  </div>

                  {run.parameters && (
                    <div className="rounded bg-gray-50 p-2">
                      <p className="text-xs font-medium text-gray-600">
                        Parameters
                      </p>
                      <pre className="mt-1 overflow-auto text-xs text-gray-700">
                        {typeof run.parameters === "string"
                          ? run.parameters
                          : JSON.stringify(run.parameters, null, 2).substring(
                              0,
                              100,
                            )}
                      </pre>
                    </div>
                  )}

                  {/* Action Buttons */}
                  {run.status === "PENDING" && (
                    <div className="flex gap-2 pt-2">
                      {onApprove && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onApprove(run.id);
                          }}
                          className="flex-1 rounded bg-green-100 px-3 py-2 text-xs font-medium text-green-700 hover:bg-green-200"
                        >
                          Approve
                        </button>
                      )}
                      {onReject && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onReject(run.id, "Rejected by admin");
                          }}
                          className="flex-1 rounded bg-red-100 px-3 py-2 text-xs font-medium text-red-700 hover:bg-red-200"
                        >
                          Reject
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}
