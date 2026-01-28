/**
 * WebSocket client for real-time communication with backend
 */

export type MessageType =
  | "SEND_MESSAGE"
  | "MESSAGE_CHUNK"
  | "MESSAGE_COMPLETE"
  | "AGENT_TRANSITION"
  | "TOOL_APPROVAL_REQUIRED"
  | "TOOL_EXECUTED"
  | "TOOL_REJECTED"
  | "ERROR"
  | "PONG"
  | "PING"
  | "send_message"
  | "message_chunk"
  | "message_complete"
  | "tool_approval_required"
  | "tool_executed"
  | "tool_rejected"
  | "error"
  | "start_conversation"
  | "agent_selected"
  | "workflow_step_start"
  | "workflow_step_complete"
  | "workflow_handoff"
  | "workflow_thought"
  | "conversation_started";

export interface WebSocketMessage {
  type: MessageType;
  data?: Record<string, unknown>;
  error?: string;
}

export interface WebSocketClientConfig {
  url: string;
  token: string;
  reconnectAttempts?: number;
  reconnectDelay?: number;
}

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private config: WebSocketClientConfig;
  private messageHandlers: Map<MessageType, Set<(data: any) => void>> =
    new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts: number;
  private reconnectDelay: number;
  private isManualClose = false;

  constructor(config: WebSocketClientConfig) {
    this.config = config;
    this.maxReconnectAttempts = config.reconnectAttempts ?? 5;
    this.reconnectDelay = config.reconnectDelay ?? 3000;
  }

  private buildWsUrlWithToken(rawUrl: string, token: string): string {
    try {
      // Handle absolute URLs (ws:// or wss://)
      if (rawUrl.startsWith("ws://") || rawUrl.startsWith("wss://")) {
        const url = new URL(rawUrl);
        url.searchParams.set("token", token);
        return url.toString();
      }

      // Handle relative URLs (/ws)
      if (rawUrl.startsWith("/")) {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const host = window.location.host; // includes port
        const fullUrl = `${protocol}//${host}${rawUrl}`;
        const url = new URL(fullUrl);
        url.searchParams.set("token", token);
        return url.toString();
      }

      // Fallback for non-standard inputs
      const base = typeof window !== "undefined" ? window.location.href : undefined;
      const url = base ? new URL(rawUrl, base) : new URL(rawUrl);
      if (url.protocol === "http:") url.protocol = "ws:";
      if (url.protocol === "https:") url.protocol = "wss:";
      url.searchParams.set("token", token);
      return url.toString();
    } catch (error) {
      console.error("[WebSocket] Failed to build URL:", error);
      const joiner = rawUrl.includes("?") ? "&" : "?";
      return `${rawUrl}${joiner}token=${encodeURIComponent(token)}`;
    }
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const wsUrl = this.buildWsUrlWithToken(this.config.url, this.config.token);
        this.ws = new WebSocket(wsUrl);
        let opened = false;
        let settled = false;
        const settle = (fn: () => void) => {
          if (settled) return;
          settled = true;
          fn();
        };

        this.ws.onopen = () => {
          console.log("[WebSocket] Connected");
          opened = true;
          this.reconnectAttempts = 0;
          this.sendPing();
          settle(resolve);
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error("[WebSocket] Failed to parse message:", error);
          }
        };

        this.ws.onerror = (error) => {
          // Browser error events are intentionally opaque; details usually appear in onclose.
          console.error("[WebSocket] Error:", error);
          if (!opened) {
            // Don't reject here; onclose typically follows with a close code (e.g. 1006).
          }
        };

        this.ws.onclose = (event) => {
          console.log(
            "[WebSocket] Disconnected",
            `code=${event.code}`,
            `reason=${event.reason || "n/a"}`,
            `clean=${event.wasClean}`,
          );
          if (!opened) {
            const hint =
              event.code === 1008
                ? " (likely auth: missing/invalid token)"
                : event.code === 1006
                  ? " (likely network/proxy/backend not reachable)"
                  : "";
            settle(
              () =>
                reject(
                  new Error(
                    `WebSocket closed before open (code=${event.code}, reason=${event.reason || "n/a"})${hint}`,
                  ),
                ),
            );
          }
          if (!this.isManualClose) {
            this.attemptReconnect();
          }
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  private handleMessage(message: WebSocketMessage): void {
    const handlers = this.messageHandlers.get(message.type);
    if (handlers) {
      // Backend sends 'payload', but also support 'data' for compatibility.
      // If neither exists, pass the whole message (handles root-level fields like agent_id).
      const messageData = (message as any).payload || message.data || message;
      handlers.forEach((handler) => handler(messageData));
    }
  }

  private sendPing(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.send({ type: "PING" });
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(
        `[WebSocket] Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`,
      );
      setTimeout(
        () => this.connect().catch(console.error),
        this.reconnectDelay,
      );
    } else {
      console.error("[WebSocket] Max reconnection attempts reached");
    }
  }

  send(message: WebSocketMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn("[WebSocket] Connection not ready");
    }
  }

  on(type: MessageType, handler: (data: any) => void): () => void {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, new Set());
    }
    this.messageHandlers.get(type)!.add(handler);

    // Return unsubscribe function
    return () => {
      const handlers = this.messageHandlers.get(type);
      if (handlers) {
        handlers.delete(handler);
      }
    };
  }

  disconnect(): void {
    this.isManualClose = true;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}
