/**
 * Metrics API client for fetching system metrics and health data
 */

import { apiClient } from './apiClient';

export interface MetricsData {
  chatMessages: number;
  toolRunsRequested: number;
  toolRunsApproved: number;
  toolRunsRejected: number;
  toolRunsExecuted: number;
}

export interface HealthDetails {
  ok: boolean;
  auth_mode: string;
  conversation_repo: string;
  tool_run_repo: string;
  config_counts: {
    domains: number;
    agents: number;
    tools: number;
  };
  version: string;
}

export interface SystemStats {
  totalConversations: number;
  totalToolRuns: number;
  activeAgents: number;
  totalDomains: number;
  pendingApprovals: number;
}

/**
 * Parse Prometheus text format metrics into structured data
 */
function parsePrometheusMetrics(text: string): MetricsData {
  const metrics: MetricsData = {
    chatMessages: 0,
    toolRunsRequested: 0,
    toolRunsApproved: 0,
    toolRunsRejected: 0,
    toolRunsExecuted: 0,
  };

  const lines = text.split('\n');
  for (const line of lines) {
    if (line.startsWith('#')) continue; // Skip comments
    if (!line.trim()) continue; // Skip empty lines

    if (line.includes('multi_agent_chat_messages_total')) {
      const match = line.match(/(\d+)$/);
      if (match) metrics.chatMessages = parseInt(match[1], 10);
    } else if (line.includes('multi_agent_tool_runs_requested_total')) {
      const match = line.match(/(\d+)$/);
      if (match) metrics.toolRunsRequested = parseInt(match[1], 10);
    } else if (line.includes('multi_agent_tool_runs_approved_total')) {
      const match = line.match(/(\d+)$/);
      if (match) metrics.toolRunsApproved = parseInt(match[1], 10);
    } else if (line.includes('multi_agent_tool_runs_rejected_total')) {
      const match = line.match(/(\d+)$/);
      if (match) metrics.toolRunsRejected = parseInt(match[1], 10);
    } else if (line.includes('multi_agent_tool_runs_executed_total')) {
      const match = line.match(/(\d+)$/);
      if (match) metrics.toolRunsExecuted = parseInt(match[1], 10);
    }
  }

  return metrics;
}

/**
 * Fetch raw metrics from Prometheus endpoint
 */
export async function fetchMetrics(): Promise<MetricsData> {
  try {
    const response = await apiClient.getMetrics();

    // If response is already parsed JSON
    if (typeof response === 'object') {
      return response as MetricsData;
    }

    // If response is Prometheus text format
    if (typeof response === 'string') {
      return parsePrometheusMetrics(response);
    }

    // Fallback: return default values
    return {
      chatMessages: 0,
      toolRunsRequested: 0,
      toolRunsApproved: 0,
      toolRunsRejected: 0,
      toolRunsExecuted: 0,
    };
  } catch (error) {
    console.error('Failed to fetch metrics:', error);
    throw error;
  }
}

/**
 * Fetch health details from backend
 */
export async function fetchHealthDetails(): Promise<HealthDetails> {
  try {
    const response = await apiClient.getHealth();
    return response as HealthDetails;
  } catch (error) {
    console.error('Failed to fetch health details:', error);
    throw error;
  }
}

/**
 * Fetch system statistics by aggregating data from multiple endpoints
 */
export async function fetchSystemStats(): Promise<SystemStats> {
  try {
    const [conversations, toolRuns, agents, domains] = await Promise.all([
      apiClient.listConversations().catch(() => []),
      apiClient.listToolRuns().catch(() => []),
      apiClient.listAgents().catch(() => []),
      apiClient.listDomains().catch(() => []),
    ]);

    // Count pending tool run approvals
    const pendingApprovals = (toolRuns as any[]).filter(
      (run: any) => run.status === 'PENDING' || run.status === 'pending_approval'
    ).length;

    return {
      totalConversations: (conversations as any[]).length,
      totalToolRuns: (toolRuns as any[]).length,
      activeAgents: (agents as any[]).filter((a: any) => a.state === 'PRODUCTION').length,
      totalDomains: (domains as any[]).length,
      pendingApprovals,
    };
  } catch (error) {
    console.error('Failed to fetch system stats:', error);
    throw error;
  }
}

/**
 * Fetch all metrics data at once
 */
export async function fetchAllMetricsData() {
  try {
    const [metrics, health, stats] = await Promise.all([
      fetchMetrics(),
      fetchHealthDetails(),
      fetchSystemStats(),
    ]);

    return {
      metrics,
      health,
      stats,
    };
  } catch (error) {
    console.error('Failed to fetch all metrics data:', error);
    throw error;
  }
}
