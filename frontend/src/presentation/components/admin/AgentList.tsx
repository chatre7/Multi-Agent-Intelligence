/**
 * Agent List component for displaying all agents
 */

import { useState, useEffect } from "react";
import { Search, ChevronRight, Loader } from "lucide-react";
import type { Agent, DomainConfig } from "../../../domain/entities/types";
import { apiClient } from "../../../infrastructure/api/apiClient";
import { StateBadge } from "./StateBadge";

interface AgentListProps {
  onSelect: (agent: Agent) => void;
  selectedAgentId?: string;
}

type AgentState =
  | "DEVELOPMENT"
  | "TESTING"
  | "PRODUCTION"
  | "DEPRECATED"
  | "ARCHIVED";

export function AgentList({ onSelect, selectedAgentId }: AgentListProps) {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [domains, setDomains] = useState<DomainConfig[]>([]);
  const [search, setSearch] = useState("");
  const [filterDomain, setFilterDomain] = useState("");
  const [filterState, setFilterState] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const [agentData, domainData] = await Promise.all([
        apiClient.listAgents(),
        apiClient.listDomains(),
      ]);
      setAgents(agentData || []);
      setDomains(domainData || []);
    } catch (err) {
      console.error("[AgentList] Error fetching data:", err);
      setError("Failed to load agents");
    } finally {
      setIsLoading(false);
    }
  };

  const getDomainName = (domainId: string | undefined) => {
    if (!domainId) return "Unknown";
    const domain = domains.find((d) => d.id === domainId);
    return domain?.name || domainId;
  };

  const filteredAgents = agents.filter((agent) => {
    const matchesSearch = agent.name
      ?.toLowerCase()
      .includes(search.toLowerCase());
    const matchesDomain = !filterDomain || agent.domain_id === filterDomain;
    const matchesState = !filterState || agent.state === filterState;
    return matchesSearch && matchesDomain && matchesState;
  });

  return (
    <div className="space-y-4">
      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          placeholder="Search agents..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full rounded-lg border border-gray-300 bg-white py-2 pl-10 pr-4 text-sm text-gray-900 placeholder-gray-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
      </div>

      {/* Filters */}
      <div className="grid grid-cols-2 gap-3">
        <select
          value={filterDomain}
          onChange={(e) => setFilterDomain(e.target.value)}
          className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="">All Domains</option>
          {domains.map((domain) => (
            <option key={domain.id} value={domain.id}>
              {domain.name}
            </option>
          ))}
        </select>

        <select
          value={filterState}
          onChange={(e) => setFilterState(e.target.value)}
          className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="">All States</option>
          <option value="DEVELOPMENT">Development</option>
          <option value="TESTING">Testing</option>
          <option value="PRODUCTION">Production</option>
          <option value="DEPRECATED">Deprecated</option>
          <option value="ARCHIVED">Archived</option>
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
        /* Agent List */
        <div className="space-y-2">
          {filteredAgents.length === 0 ? (
            <div className="rounded-lg border border-gray-200 bg-gray-50 p-8 text-center">
              <p className="text-sm text-gray-500">No agents found</p>
            </div>
          ) : (
            filteredAgents.map((agent) => (
              <button
                key={agent.id}
                onClick={() => onSelect(agent)}
                className={`w-full rounded-lg border p-4 text-left transition-all ${
                  selectedAgentId === agent.id
                    ? "border-blue-500 bg-blue-50"
                    : "border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900">{agent.name}</h3>
                    <div className="mt-2 flex flex-wrap gap-2">
                      <span className="text-xs text-gray-600">
                        Domain: {getDomainName(agent.domain_id)}
                      </span>
                      {agent.version && (
                        <span className="text-xs text-gray-600">
                          v{agent.version}
                        </span>
                      )}
                      {agent.state && (
                        <StateBadge
                          state={agent.state as AgentState}
                          size="sm"
                        />
                      )}
                    </div>
                  </div>
                  <ChevronRight
                    className={`h-5 w-5 transition-transform ${
                      selectedAgentId === agent.id
                        ? "text-blue-500"
                        : "text-gray-400"
                    }`}
                  />
                </div>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}
