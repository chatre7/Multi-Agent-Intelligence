/**
 * Axios-based API client for backend communication
 */

import axios, { AxiosError } from "axios";
import type { AxiosInstance } from "axios";
import type {
  Conversation,
  DomainConfig,
  Agent,
  ToolRun,
  Skill,
  Message,
} from "../../domain/entities/types";
import { resolveApiBaseUrl } from "../config/urls";

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  status: number;
}

export class ApiClient {
  private client: AxiosInstance;
  private token: string | null = null;

  constructor(baseURL = "/api/v1") {
    this.client = axios.create({
      baseURL,
      headers: {
        "Content-Type": "application/json",
      },
    });

    // Add token to requests
    this.client.interceptors.request.use((config) => {
      if (this.token) {
        config.headers.Authorization = `Bearer ${this.token}`;
      }
      return config;
    });

    // Handle errors
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        console.error(
          "[API] Error:",
          error.response?.status,
          error.response?.data,
        );
        throw error;
      },
    );
  }

  setToken(token: string): void {
    this.token = token;
  }

  clearToken(): void {
    this.token = null;
  }

  // Auth endpoints
  async login(
    username: string,
    password: string,
  ): Promise<{ access_token: string; token_type: string }> {
    const response = await this.client.post("/auth/login", {
      username,
      password,
    });
    return response.data;
  }

  async getMe(): Promise<any> {
    const response = await this.client.get("/auth/me");
    return response.data;
  }

  // Domain endpoints
  async listDomains(): Promise<DomainConfig[]> {
    const response = await this.client.get<DomainConfig[]>("/domains");
    return response.data;
  }

  async getDomain(id: string): Promise<DomainConfig> {
    const response = await this.client.get<DomainConfig>(`/domains/${id}`);
    return response.data;
  }

  // Agent endpoints
  async listAgents(domainId?: string): Promise<Agent[]> {
    const response = await this.client.get<Agent[]>("/agents", {
      params: domainId ? { domain_id: domainId } : {},
    });
    return response.data;
  }

  async getAgent(id: string): Promise<Agent> {
    const response = await this.client.get<Agent>(`/agents/${id}`);
    return response.data;
  }

  // Conversation endpoints
  async startConversation(
    domainId: string,
    agentId: string,
  ): Promise<Conversation> {
    const response = await this.client.post<Conversation>("/conversations", {
      domain_id: domainId,
      agent_id: agentId,
    });
    return response.data;
  }

  async getConversation(id: string): Promise<Conversation> {
    const response = await this.client.get<Conversation>(
      `/conversations/${id}`,
    );
    return response.data;
  }

  async listConversations(domainId?: string): Promise<Conversation[]> {
    const response = await this.client.get<Conversation[]>("/conversations", {
      params: domainId ? { domain_id: domainId } : {},
    });
    return response.data;
  }

  async listConversationMessages(id: string): Promise<Message[]> {
    const response = await this.client.get<Message[]>(
      `/conversations/${id}/messages`,
    );
    return response.data;
  }

  // Tool run endpoints
  async listToolRuns(): Promise<ToolRun[]> {
    const response = await this.client.get<ToolRun[]>("/tool-runs");
    return response.data;
  }

  async getToolRun(id: string): Promise<ToolRun> {
    const response = await this.client.get<ToolRun>(`/tool-runs/${id}`);
    return response.data;
  }

  async approveToolRun(id: string): Promise<ToolRun> {
    const response = await this.client.post<ToolRun>(
      `/tool-runs/${id}/approve`,
    );
    return response.data;
  }

  async rejectToolRun(id: string, reason: string): Promise<ToolRun> {
    const response = await this.client.post<ToolRun>(
      `/tool-runs/${id}/reject`,
      { reason },
    );
    return response.data;
  }

  // Metrics endpoints
  async getMetrics(): Promise<any> {
    const response = await this.client.get("/metrics");
    return response.data;
  }

  async getHealth(): Promise<any> {
    const response = await this.client.get("/health");
    return response.data;
  }

  async getHealthDetails(): Promise<any> {
    const response = await this.client.get("/health/details");
    return response.data;
  }

  async promoteAgent(agentId: string, newState: string): Promise<Agent> {
    const response = await this.client.post<Agent>(
      `/agents/${agentId}/promote`,
      { new_state: newState },
    );
    return response.data;
  }

  async importSkill(url: string, branch?: string): Promise<{ id: string, name: string, version: string }> {
    const response = await this.client.post("/skills/import", {
      url,
      branch
    });
    return response.data;
  }

  async listSkills(): Promise<Skill[]> {
    const response = await this.client.get<Skill[]>("/skills");
    return response.data;
  }

  async getAgentSkills(agentId: string): Promise<Skill[]> {
    const response = await this.client.get<Skill[]>(`/agents/${agentId}/skills`);
    return response.data;
  }

  async attachSkill(agentId: string, skillId: string): Promise<void> {
    await this.client.post(`/agents/${agentId}/skills`, { skill_id: skillId });
  }

  async detachSkill(agentId: string, skillId: string): Promise<void> {
    await this.client.delete(`/agents/${agentId}/skills/${skillId}`);
  }

  // Chat endpoints
  async sendMessage(request: {
    domain_id: string;
    message: string;
    conversation_id?: string;
    enable_thinking?: boolean;
  }): Promise<any> {
    const response = await this.client.post("/chat/send", request);
    return response.data;
  }
}

export const apiClient = new ApiClient(resolveApiBaseUrl());
