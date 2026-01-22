/**
 * Domain Detail panel for viewing domain information
 */

import { X, Copy } from "lucide-react";
import type { DomainConfig, Agent } from "../../../domain/entities/types";
import { useEffect, useState } from "react";
import { apiClient } from "../../../infrastructure/api/apiClient";

interface DomainDetailProps {
  domain: DomainConfig;
  onClose: () => void;
}

export function DomainDetail({ domain, onClose }: DomainDetailProps) {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (domain.id) {
      fetchAgents();
    }
  }, [domain.id]);

  const fetchAgents = async () => {
    try {
      setIsLoading(true);
      const data = await apiClient.listAgents(domain.id);
      setAgents(data || []);
    } catch (err) {
      console.error("[DomainDetail] Error fetching agents:", err);
    } finally {
      setIsLoading(false);
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
              <h2 className="text-2xl font-bold text-gray-900">
                {domain.name}
              </h2>
              <p className="mt-1 text-sm text-gray-500">{domain.description}</p>
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
          {/* Domain Info */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Information</h3>

            <div className="space-y-3">
              <div className="rounded-lg bg-gray-50 p-4">
                <label className="text-xs font-medium text-gray-600">
                  Domain ID
                </label>
                <div className="mt-2 flex items-center justify-between">
                  <code className="text-sm text-gray-900">{domain.id}</code>
                  <button
                    onClick={() => copyToClipboard(domain.id)}
                    className="rounded p-1 hover:bg-gray-200"
                  >
                    <Copy className="h-4 w-4 text-gray-500" />
                  </button>
                </div>
              </div>

              {domain.workflow_type && (
                <div className="rounded-lg bg-gray-50 p-4">
                  <label className="text-xs font-medium text-gray-600">
                    Workflow Type
                  </label>
                  <p className="mt-2 text-sm text-gray-900">
                    {domain.workflow_type}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Agents Section */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">Agents</h3>
              <span className="inline-flex items-center rounded-full bg-blue-100 px-3 py-1 text-sm font-medium text-blue-800">
                {agents.length}
              </span>
            </div>

            {isLoading ? (
              <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 text-center text-sm text-gray-500">
                Loading agents...
              </div>
            ) : agents.length === 0 ? (
              <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 text-center text-sm text-gray-500">
                No agents in this domain
              </div>
            ) : (
              <div className="space-y-2">
                {agents.map((agent) => (
                  <div
                    key={agent.id}
                    className="rounded-lg border border-gray-200 p-3"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900">
                          {agent.name}
                        </h4>
                        <div className="mt-1 flex gap-2">
                          <span className="inline-flex items-center rounded bg-gray-100 px-2 py-1 text-xs font-medium text-gray-800">
                            {agent.version || "1.0.0"}
                          </span>
                          {agent.state && (
                            <span
                              className={`inline-flex items-center rounded px-2 py-1 text-xs font-medium ${
                                agent.state === "PRODUCTION"
                                  ? "bg-green-100 text-green-800"
                                  : "bg-yellow-100 text-yellow-800"
                              }`}
                            >
                              {agent.state}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Metadata */}
          <div className="space-y-4 border-t border-gray-200 pt-6">
            <h3 className="text-lg font-semibold text-gray-900">Metadata</h3>
            <div className="rounded-lg bg-gray-50 p-4">
              <pre className="overflow-auto text-xs text-gray-600">
                {JSON.stringify(domain, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
