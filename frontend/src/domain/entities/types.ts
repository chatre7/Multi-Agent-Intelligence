/**
 * Domain entities for the frontend
 */

export interface Agent {
  id: string;
  name: string;
  description: string;
  domain_id: string;
  version: string;
  state: 'DEVELOPMENT' | 'TESTING' | 'PRODUCTION' | 'DEPRECATED' | 'ARCHIVED';
  capabilities: string[];
  keywords: string[];
}

export interface DomainConfig {
  id: string;
  name: string;
  description: string;
  workflow_type: string;
  agents: Agent[];
  active: boolean;
  metadata?: Record<string, any>;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  delta?: string;
  agent_id?: string;
}

export interface Conversation {
  id: string;
  domain_id: string;
  agent_id: string;
  title: string;
  messages: Message[];
  created_at: string;
  updated_at: string;
}

export interface ToolRun {
  id: string;
  tool_id: string;
  parameters: Record<string, unknown>;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'EXECUTED';
  result?: Record<string, unknown>;
  error?: string;
}

export interface User {
  id: string;
  username: string;
  role: 'ADMIN' | 'DEVELOPER' | 'OPERATOR' | 'USER' | 'GUEST';
  permissions: string[];
}
