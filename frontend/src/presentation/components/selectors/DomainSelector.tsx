/**
 * Domain and Agent selector component
 */

import { useEffect, useState } from "react";
import type { DomainConfig, Agent } from "../../../domain/entities/types";
import { apiClient } from "../../../infrastructure/api/apiClient";

interface DomainSelectorProps {
  onDomainSelect: (domainId: string) => void;
  onAgentSelect: (agentId: string) => void;
  selectedDomainId?: string;
  selectedAgentId?: string;
  onStartConversation?: () => void;
}

export default function DomainSelector({
  onDomainSelect,
  onAgentSelect,
  selectedDomainId,
  selectedAgentId,
  onStartConversation,
}: DomainSelectorProps) {
  const [domains, setDomains] = useState<DomainConfig[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load domains on mount
  useEffect(() => {
    const loadDomains = async () => {
      try {
        setIsLoading(true);
        const data = await apiClient.listDomains();
        setDomains(data);
        setError(null);
      } catch (err) {
        console.error("Failed to load domains:", err);
        setError("Failed to load domains");
      } finally {
        setIsLoading(false);
      }
    };

    loadDomains();
  }, []);

  // Load agents when domain changes
  useEffect(() => {
    if (!selectedDomainId) {
      setAgents([]);
      return;
    }

    const loadAgents = async () => {
      try {
        setIsLoading(true);
        const data = await apiClient.listAgents(selectedDomainId);
        setAgents(data);
        setError(null);
      } catch (err) {
        console.error("Failed to load agents:", err);
        setError("Failed to load agents");
      } finally {
        setIsLoading(false);
      }
    };

    loadAgents();
  }, [selectedDomainId]);

  const handleDomainChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const domainId = e.target.value;
    onDomainSelect(domainId);
    onAgentSelect(""); // Reset agent selection
  };

  const handleAgentChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onAgentSelect(e.target.value);
  };

  return (
    <div className="bg-white rounded-lg shadow p-4 space-y-4">
      <h2 className="text-lg font-semibold">Select Domain & Agent</h2>

      {error && (
        <div className="p-3 bg-red-100 text-red-700 text-sm rounded">
          {error}
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Domain
        </label>
        <select
          value={selectedDomainId || ""}
          onChange={handleDomainChange}
          disabled={isLoading}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
        >
          <option value="">Select a domain...</option>
          {domains.map((domain) => (
            <option key={domain.id} value={domain.id}>
              {domain.name}
            </option>
          ))}
        </select>
      </div>

      {selectedDomainId && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Agent
          </label>
          <select
            value={selectedAgentId || ""}
            onChange={handleAgentChange}
            disabled={isLoading || agents.length === 0}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
          >
            <option value="">Select an agent...</option>
            {agents.map((agent) => (
              <option key={agent.id} value={agent.id}>
                {agent.name} (v{agent.version})
              </option>
            ))}
          </select>
        </div>
      )}

      <button
        onClick={onStartConversation}
        disabled={!selectedDomainId || !selectedAgentId || isLoading}
        className="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors font-medium"
      >
        {isLoading ? "Loading..." : "Start Conversation"}
      </button>
    </div>
  );
}
