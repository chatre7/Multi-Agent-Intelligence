/**
 * Domain List component for displaying all domains
 */

import { useState, useEffect } from "react";
import { Search, ChevronRight, Loader } from "lucide-react";
import type { DomainConfig } from "../../../domain/entities/types";
import { apiClient } from "../../../infrastructure/api/apiClient";

interface DomainListProps {
  onSelect: (domain: DomainConfig) => void;
  selectedDomainId?: string;
}

export function DomainList({ onSelect, selectedDomainId }: DomainListProps) {
  const [domains, setDomains] = useState<DomainConfig[]>([]);
  const [search, setSearch] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDomains();
  }, []);

  const fetchDomains = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await apiClient.listDomains();
      setDomains(data || []);
    } catch (err) {
      console.error("[DomainList] Error fetching domains:", err);
      setError("Failed to load domains");
    } finally {
      setIsLoading(false);
    }
  };

  const filteredDomains = domains.filter((domain) =>
    domain.name?.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <div className="space-y-4">
      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          placeholder="Search domains..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full rounded-lg border border-gray-300 bg-white py-2 pl-10 pr-4 text-sm text-gray-900 placeholder-gray-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
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
        /* Domain List */
        <div className="space-y-2">
          {filteredDomains.length === 0 ? (
            <div className="rounded-lg border border-gray-200 bg-gray-50 p-8 text-center">
              <p className="text-sm text-gray-500">No domains found</p>
            </div>
          ) : (
            filteredDomains.map((domain) => (
              <button
                key={domain.id}
                onClick={() => onSelect(domain)}
                className={`w-full rounded-lg border p-4 text-left transition-all ${
                  selectedDomainId === domain.id
                    ? "border-blue-500 bg-blue-50"
                    : "border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900">
                      {domain.name}
                    </h3>
                    <p className="mt-1 text-sm text-gray-500">
                      {domain.description || "No description"}
                    </p>
                    <div className="mt-2 flex gap-4">
                      <span className="text-xs text-gray-600">
                        ID: {domain.id}
                      </span>
                    </div>
                  </div>
                  <ChevronRight
                    className={`h-5 w-5 transition-transform ${
                      selectedDomainId === domain.id
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
