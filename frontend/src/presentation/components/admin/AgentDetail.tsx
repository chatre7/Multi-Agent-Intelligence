/**
 * Agent Detail panel for viewing and managing agent information
 */

import { X, Copy } from "lucide-react";
import type { Agent } from "../../../domain/entities/types";
import { useState } from "react";
import { StateBadge } from "./StateBadge";

interface AgentDetailProps {
  agent: Agent;
  onClose: () => void;
  onPromote?: (agentId: string, newState: string) => Promise<void>;
}

type AgentState =
  | "DEVELOPMENT"
  | "TESTING"
  | "PRODUCTION"
  | "DEPRECATED"
  | "ARCHIVED";

const stateTransitions: Record<string, AgentState[]> = {
  DEVELOPMENT: ["TESTING"],
  TESTING: ["PRODUCTION", "DEVELOPMENT"],
  PRODUCTION: ["DEPRECATED"],
  DEPRECATED: ["ARCHIVED"],
  ARCHIVED: [],
};

export function AgentDetail({ agent, onClose, onPromote }: AgentDetailProps) {
  const [isPromoting, setIsPromoting] = useState(false);
  const [promoteError, setPromoteError] = useState<string | null>(null);
  const [promoteSuccess, setPromoteSuccess] = useState(false);

  const currentState = (agent.state || "DEVELOPMENT") as AgentState;
  const availableTransitions = stateTransitions[currentState] || [];

  const handlePromote = async (newState: string) => {
    if (!onPromote) return;

    try {
      setIsPromoting(true);
      setPromoteError(null);
      setPromoteSuccess(false);
      await onPromote(agent.id, newState);
      setPromoteSuccess(true);
      setTimeout(() => setPromoteSuccess(false), 3000);
    } catch (err) {
      console.error("[AgentDetail] Promotion error:", err);
      setPromoteError(
        err instanceof Error ? err.message : "Failed to promote agent",
      );
    } finally {
      setIsPromoting(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="fixed inset-0 right-0 top-0 bottom-0 h-full w-full overflow-hidden bg-black/50 transition-opacity duration-200 sm:w-96">
      <div className="relative h-full w-full overflow-y-auto bg-white shadow-lg">
        {/* Header */}
        <div className="sticky top-0 border-b border-gray-200 bg-white p-6">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">{agent.name}</h2>
              <p className="mt-1 text-sm text-gray-500">
                {agent.description || "No description"}
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
          {/* State Section */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">State</h3>

            <div className="rounded-lg bg-gray-50 p-4">
              <label className="text-xs font-medium text-gray-600">
                Current State
              </label>
              <div className="mt-2">
                <StateBadge state={currentState} size="md" />
              </div>
            </div>

            {/* Promotion Messages */}
            {promoteSuccess && (
              <div className="rounded-lg bg-green-50 p-4 text-sm text-green-800">
                ✓ Agent promoted successfully
              </div>
            )}
            {promoteError && (
              <div className="rounded-lg bg-red-50 p-4 text-sm text-red-800">
                {promoteError}
              </div>
            )}

            {/* State Transitions */}
            {availableTransitions.length > 0 && (
              <div className="space-y-2">
                <label className="text-xs font-medium text-gray-600">
                  Promote to
                </label>
                {availableTransitions.map((nextState) => (
                  <button
                    key={nextState}
                    onClick={() => handlePromote(nextState)}
                    disabled={isPromoting}
                    className="w-full rounded-lg border border-blue-300 bg-blue-50 px-4 py-2 font-medium text-blue-700 hover:bg-blue-100 disabled:opacity-50 transition-colors"
                  >
                    {isPromoting ? "Promoting..." : `Promote to ${nextState}`}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Agent Info */}
          <div className="space-y-4 border-t border-gray-200 pt-6">
            <h3 className="text-lg font-semibold text-gray-900">Information</h3>

            <div className="space-y-3">
              <div className="rounded-lg bg-gray-50 p-4">
                <label className="text-xs font-medium text-gray-600">
                  Agent ID
                </label>
                <div className="mt-2 flex items-center justify-between">
                  <code className="text-sm text-gray-900">{agent.id}</code>
                  <button
                    onClick={() => copyToClipboard(agent.id)}
                    className="rounded p-1 hover:bg-gray-200"
                  >
                    <Copy className="h-4 w-4 text-gray-500" />
                  </button>
                </div>
              </div>

              {agent.version && (
                <div className="rounded-lg bg-gray-50 p-4">
                  <label className="text-xs font-medium text-gray-600">
                    Version
                  </label>
                  <p className="mt-2 text-sm text-gray-900">{agent.version}</p>
                </div>
              )}

              {agent.domain_id && (
                <div className="rounded-lg bg-gray-50 p-4">
                  <label className="text-xs font-medium text-gray-600">
                    Domain ID
                  </label>
                  <p className="mt-2 text-sm text-gray-900">
                    {agent.domain_id}
                  </p>
                </div>
              )}

              {agent.description && (
                <div className="rounded-lg bg-gray-50 p-4">
                  <label className="text-xs font-medium text-gray-600">
                    Description
                  </label>
                  <p className="mt-2 text-sm text-gray-900">
                    {agent.description}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Capabilities */}
          {agent.capabilities && agent.capabilities.length > 0 && (
            <div className="space-y-4 border-t border-gray-200 pt-6">
              <h3 className="text-lg font-semibold text-gray-900">
                Capabilities
              </h3>
              <div className="space-y-2">
                {agent.capabilities.map((capability) => (
                  <div
                    key={capability}
                    className="flex items-center gap-2 rounded-lg border border-gray-200 p-3"
                  >
                    <span className="h-2 w-2 rounded-full bg-blue-500" />
                    <span className="text-sm text-gray-900">{capability}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Metadata */}
          <div className="space-y-4 border-t border-gray-200 pt-6">
            <h3 className="text-lg font-semibold text-gray-900">Metadata</h3>
            <div className="rounded-lg bg-gray-50 p-4">
              <pre className="overflow-auto text-xs text-gray-600">
                {JSON.stringify(agent, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
