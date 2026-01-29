/**
 * Admin panel page with metrics dashboard
 */

import { useEffect, useState } from "react";
import { Settings, BarChart3, Users, Package, RefreshCw, Database } from "lucide-react";
import StatCard from "../components/admin/StatCard";
import MetricsChart from "../components/admin/MetricsChart";
import ActivityFeed from "../components/admin/ActivityFeed";
import { DomainList } from "../components/admin/DomainList";
import { DomainDetail } from "../components/admin/DomainDetail";
import { AgentList } from "../components/admin/AgentList";
import { AgentDetail } from "../components/admin/AgentDetail";
import { ToolRunList } from "../components/admin/ToolRunList";
import { ToolApprovalModal } from "../components/admin/ToolApprovalModal";
import { useMetricsStore } from "../../infrastructure/stores/metricsStore";
import type { DomainConfig, Agent, ToolRun } from "../../domain/entities/types";
import { apiClient } from "../../infrastructure/api/apiClient";
import { KnowledgeUpload } from "../components/admin/KnowledgeUpload";
import { KnowledgeList } from "../components/admin/KnowledgeList";

import { useKnowledge } from "../hooks/useKnowledge";

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState("overview");
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [selectedDomain, setSelectedDomain] = useState<DomainConfig | null>(
    null,
  );
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [selectedToolRun, setSelectedToolRun] = useState<ToolRun | null>(null);

  // Use Custom Hook for Knowledge Logic
  const {
    documents,
    isLoading: isDocsLoading,
    fetchDocuments,
    deleteDocument
  } = useKnowledge();

  const {
    metrics,
    health,
    stats,
    isLoading,
    error,
    lastUpdated,
    startAutoRefresh,
    stopAutoRefresh,
    refreshAll,
  } = useMetricsStore();

  // Fetch documents when Knowledge tab is active
  useEffect(() => {
    if (activeTab === "knowledge") {
      fetchDocuments();
    }
  }, [activeTab, fetchDocuments]);

  // Start auto-refresh on mount
  useEffect(() => {
    startAutoRefresh(5000); // Refresh every 5 seconds

    return () => {
      stopAutoRefresh();
    };
  }, [startAutoRefresh, stopAutoRefresh]);

  const handleManualRefresh = async () => {
    setIsRefreshing(true);
    await refreshAll();
    setIsRefreshing(false);
  };

  const tabs = [
    { id: "overview", label: "Overview", icon: BarChart3 },
    { id: "domains", label: "Domains", icon: Package },
    { id: "agents", label: "Agents", icon: Users },
    { id: "knowledge", label: "Knowledge", icon: Database },
    { id: "tools", label: "Tool Approval", icon: BarChart3 },
    { id: "settings", label: "Settings", icon: Settings },
  ];

  const chartData = metrics
    ? [
      {
        label: "Requested",
        value: metrics.toolRunsRequested,
        color: "#3b82f6",
      },
      {
        label: "Approved",
        value: metrics.toolRunsApproved,
        color: "#10b981",
      },
      {
        label: "Rejected",
        value: metrics.toolRunsRejected,
        color: "#ef4444",
      },
      {
        label: "Executed",
        value: metrics.toolRunsExecuted,
        color: "#8b5cf6",
      },
    ]
    : [];

  return (
    <div className="h-full bg-gray-50 overflow-y-auto">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Admin Panel</h1>
              <p className="text-gray-600 mt-1">
                Manage domains, agents, and system configuration
              </p>
            </div>
            <button
              onClick={handleManualRefresh}
              disabled={isRefreshing}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 transition-colors flex items-center gap-2"
            >
              <RefreshCw
                size={18}
                className={isRefreshing ? "animate-spin" : ""}
              />
              Refresh
            </button>
          </div>

          {lastUpdated && (
            <p className="text-xs text-gray-500 mt-4">
              Last updated: {lastUpdated.toLocaleTimeString()}
            </p>
          )}

          {error && (
            <div className="mt-2 p-2 bg-red-100 text-red-700 text-sm rounded">
              {error}
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 bg-white sticky top-[120px] z-9">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex gap-8 overflow-x-auto">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors flex items-center gap-2 whitespace-nowrap ${activeTab === tab.id
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700"
                    }`}
                >
                  <Icon size={18} />
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {activeTab === "overview" && (
          <div className="space-y-6">
            {/* Stat Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard
                title="Total Domains"
                value={stats?.totalDomains || 0}
                icon={<Package size={24} />}
                color="blue"
                isLoading={isLoading}
              />
              <StatCard
                title="Total Agents"
                value={stats?.activeAgents || 0}
                icon={<Users size={24} />}
                color="green"
                isLoading={isLoading}
              />
              <StatCard
                title="Active Conversations"
                value={stats?.totalConversations || 0}
                icon={<BarChart3 size={24} />}
                color="yellow"
                isLoading={isLoading}
              />
              <StatCard
                title="Pending Approvals"
                value={stats?.pendingApprovals || 0}
                icon={<Settings size={24} />}
                color="red"
                isLoading={isLoading}
              />
            </div>

            {/* Charts and Health */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <MetricsChart
                title="Tool Run Status Distribution"
                data={chartData}
                type="bar"
                isLoading={isLoading}
              />

              {/* Health Status */}
              <div className="rounded-lg border border-gray-200 bg-white p-6">
                <p className="mb-4 text-lg font-semibold text-gray-900">
                  System Health
                </p>

                {isLoading ? (
                  <div className="space-y-3">
                    {[1, 2, 3, 4].map((i) => (
                      <div
                        key={i}
                        className="h-6 bg-gray-100 animate-pulse rounded"
                      />
                    ))}
                  </div>
                ) : health ? (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Status</span>
                      <span
                        className={`text-sm font-semibold ${health.ok ? "text-green-600" : "text-red-600"}`}
                      >
                        {health.ok ? "✅ Healthy" : "❌ Unhealthy"}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Auth Mode</span>
                      <span className="text-sm font-semibold text-gray-900">
                        {health.auth_mode}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">
                        Conversation Store
                      </span>
                      <span className="text-sm font-semibold text-gray-900">
                        {health.conversation_repo}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">
                        Tool Run Store
                      </span>
                      <span className="text-sm font-semibold text-gray-900">
                        {health.tool_run_repo}
                      </span>
                    </div>
                    <div className="border-t border-gray-200 pt-3 mt-3">
                      <p className="text-sm font-semibold text-gray-900 mb-2">
                        Configuration
                      </p>
                      <div className="space-y-1 text-sm">
                        <div className="text-gray-600">
                          Domains:{" "}
                          <span className="font-semibold">
                            {health.config_counts?.domains ?? 0}
                          </span>
                        </div>
                        <div className="text-gray-600">
                          Agents:{" "}
                          <span className="font-semibold">
                            {health.config_counts?.agents ?? 0}
                          </span>
                        </div>
                        <div className="text-gray-600">
                          Tools:{" "}
                          <span className="font-semibold">
                            {health.config_counts?.tools ?? 0}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="border-t border-gray-200 pt-3 mt-3">
                      <span className="text-xs text-gray-500">
                        Version: {health.version}
                      </span>
                    </div>
                  </div>
                ) : null}
              </div>
            </div>

            {/* Activity Feed */}
            <ActivityFeed isLoading={isLoading} />

            {/* Metrics Summary */}
            <div className="rounded-lg border border-gray-200 bg-white p-6">
              <p className="mb-4 text-lg font-semibold text-gray-900">
                Metrics Summary
              </p>

              {isLoading ? (
                <div className="space-y-2">
                  {[1, 2, 3, 4].map((i) => (
                    <div
                      key={i}
                      className="h-6 bg-gray-100 animate-pulse rounded"
                    />
                  ))}
                </div>
              ) : metrics ? (
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div className="p-3 bg-blue-50 rounded-lg">
                    <p className="text-xs text-gray-600 mb-1">Chat Messages</p>
                    <p className="text-2xl font-bold text-blue-600">
                      {metrics.chatMessages}
                    </p>
                  </div>
                  <div className="p-3 bg-blue-50 rounded-lg">
                    <p className="text-xs text-gray-600 mb-1">
                      Tool Runs Requested
                    </p>
                    <p className="text-2xl font-bold text-blue-600">
                      {metrics.toolRunsRequested}
                    </p>
                  </div>
                  <div className="p-3 bg-green-50 rounded-lg">
                    <p className="text-xs text-gray-600 mb-1">Approved</p>
                    <p className="text-2xl font-bold text-green-600">
                      {metrics.toolRunsApproved}
                    </p>
                  </div>
                  <div className="p-3 bg-red-50 rounded-lg">
                    <p className="text-xs text-gray-600 mb-1">Rejected</p>
                    <p className="text-2xl font-bold text-red-600">
                      {metrics.toolRunsRejected}
                    </p>
                  </div>
                  <div className="p-3 bg-purple-50 rounded-lg">
                    <p className="text-xs text-gray-600 mb-1">Executed</p>
                    <p className="text-2xl font-bold text-purple-600">
                      {metrics.toolRunsExecuted}
                    </p>
                  </div>
                </div>
              ) : null}
            </div>
          </div>
        )}

        {activeTab === "domains" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">Domain Management</h2>
              <DomainList
                onSelect={setSelectedDomain}
                selectedDomainId={selectedDomain?.id}
              />
            </div>
            {selectedDomain && (
              <DomainDetail
                domain={selectedDomain}
                onClose={() => setSelectedDomain(null)}
              />
            )}
          </div>
        )}

        {activeTab === "agents" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">Agent Management</h2>
              <AgentList
                onSelect={setSelectedAgent}
                selectedAgentId={selectedAgent?.id}
              />
            </div>
            {selectedAgent && (
              <AgentDetail
                agent={selectedAgent}
                onClose={() => setSelectedAgent(null)}
                onPromote={async (agentId, newState) => {
                  await apiClient.promoteAgent(agentId, newState);
                  setSelectedAgent(null);
                }}
              />
            )}
          </div>
        )}

        {activeTab === "tools" && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Tool Approval Queue</h2>
            <ToolRunList
              onSelect={setSelectedToolRun}
              selectedToolRunId={selectedToolRun?.id}
              onApprove={async (runId) => {
                await apiClient.approveToolRun(runId);
                setSelectedToolRun(null);
              }}
              onReject={async (runId, reason) => {
                await apiClient.rejectToolRun(runId, reason);
                setSelectedToolRun(null);
              }}
            />
            {selectedToolRun && (
              <ToolApprovalModal
                toolRun={selectedToolRun}
                onClose={() => setSelectedToolRun(null)}
                onApprove={async (runId) => {
                  await apiClient.approveToolRun(runId);
                  setSelectedToolRun(null);
                }}
                onReject={async (runId, reason) => {
                  await apiClient.rejectToolRun(runId, reason);
                  setSelectedToolRun(null);
                }}
              />
            )}
          </div>
        )}

        {activeTab === "knowledge" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-1">
              <div className="bg-white rounded-lg shadow p-6 mb-6">
                <h2 className="text-lg font-semibold mb-4">Upload Documents</h2>
                <KnowledgeUpload onUploadComplete={fetchDocuments} />
              </div>
            </div>
            <div className="lg:col-span-2">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold">Knowledge Base</h2>
                  <button onClick={fetchDocuments} className="text-sm text-blue-600 hover:underline">Refresh</button>
                </div>
                <KnowledgeList
                  documents={documents}
                  onDelete={deleteDocument}
                  isLoading={isDocsLoading}
                />
              </div>
            </div>
          </div>
        )}

        {activeTab === "settings" && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">System Settings</h2>
            <p className="text-gray-600">Settings management coming soon...</p>
          </div>
        )}
      </div>
    </div>
  );
}
