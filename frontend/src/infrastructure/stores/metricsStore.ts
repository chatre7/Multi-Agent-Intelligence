/**
 * Zustand store for metrics and system data
 */

import { create } from "zustand";
import type {
  MetricsData,
  HealthDetails,
  SystemStats,
} from "../api/metricsApi";
import {
  fetchMetrics,
  fetchHealthDetails,
  fetchSystemStats,
} from "../api/metricsApi";

interface MetricsStore {
  // State
  metrics: MetricsData | null;
  health: HealthDetails | null;
  stats: SystemStats | null;
  isLoading: boolean;
  error: string | null;
  lastUpdated: Date | null;
  autoRefreshInterval: ReturnType<typeof setInterval> | null;

  // Actions
  fetchMetrics: () => Promise<void>;
  fetchHealth: () => Promise<void>;
  fetchStats: () => Promise<void>;
  refreshAll: () => Promise<void>;
  startAutoRefresh: (intervalMs: number) => void;
  stopAutoRefresh: () => void;
  clearError: () => void;
}

export const useMetricsStore = create<MetricsStore>((set, get) => ({
  metrics: null,
  health: null,
  stats: null,
  isLoading: false,
  error: null,
  lastUpdated: null,
  autoRefreshInterval: null,

  fetchMetrics: async () => {
    set({ isLoading: true, error: null });
    try {
      const data = await fetchMetrics();
      set({
        metrics: data,
        lastUpdated: new Date(),
        isLoading: false,
      });
    } catch (error) {
      set({
        error: `Failed to fetch metrics: ${error instanceof Error ? error.message : "Unknown error"}`,
        isLoading: false,
      });
    }
  },

  fetchHealth: async () => {
    try {
      const data = await fetchHealthDetails();
      set({ health: data });
    } catch (error) {
      console.error("Failed to fetch health:", error);
    }
  },

  fetchStats: async () => {
    try {
      const data = await fetchSystemStats();
      set({ stats: data });
    } catch (error) {
      console.error("Failed to fetch stats:", error);
    }
  },

  refreshAll: async () => {
    set({ isLoading: true, error: null });
    try {
      const [metrics, health, stats] = await Promise.all([
        fetchMetrics(),
        fetchHealthDetails(),
        fetchSystemStats(),
      ]);

      set({
        metrics,
        health,
        stats,
        lastUpdated: new Date(),
        isLoading: false,
      });
    } catch (error) {
      set({
        error: `Failed to refresh metrics: ${error instanceof Error ? error.message : "Unknown error"}`,
        isLoading: false,
      });
    }
  },

  startAutoRefresh: (intervalMs: number = 5000) => {
    // Clear existing interval if any
    const state = get();
    if (state.autoRefreshInterval) {
      clearInterval(state.autoRefreshInterval);
    }

    // Fetch immediately
    get().refreshAll();

    // Set up periodic refresh
    const interval = setInterval(() => {
      get().refreshAll();
    }, intervalMs);

    set({ autoRefreshInterval: interval });
  },

  stopAutoRefresh: () => {
    const state = get();
    if (state.autoRefreshInterval) {
      clearInterval(state.autoRefreshInterval);
      set({ autoRefreshInterval: null });
    }
  },

  clearError: () => set({ error: null }),
}));
