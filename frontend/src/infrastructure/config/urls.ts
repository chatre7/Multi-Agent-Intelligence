/**
 * Runtime URL helpers.
 *
 * Supports:
 * - Docker/nginx: VITE_API_BASE_URL=/api, VITE_WS_URL=/ws
 * - Local dev:    VITE_API_BASE_URL=http://localhost:8000, VITE_WS_URL=ws://localhost:8000
 */

function stripTrailingSlash(value: string): string {
  return value.length > 1 ? value.replace(/\/+$/, "") : value;
}

export function resolveApiBaseUrl(): string {
  const raw = (import.meta as any).env?.VITE_API_BASE_URL as string | undefined;
  const base = stripTrailingSlash(raw?.trim() || "/api");
  return `${base}/v1`;
}

export function resolveWsEndpointUrl(): string {
  const raw = (import.meta as any).env?.VITE_WS_URL as string | undefined;
  const fallback = "/ws";
  const trimmed = raw?.trim();

  if (!trimmed) {
    return fallback;
  }

  // Allow relative path like "/ws"
  if (trimmed.startsWith("/")) {
    return trimmed;
  }

  try {
    const url = new URL(trimmed);
    // If VITE_WS_URL is provided as a base (e.g. ws://localhost:8000), default to /ws
    if (!url.pathname || url.pathname === "/") {
      url.pathname = "/ws";
    }
    return url.toString();
  } catch {
    // Best-effort fallback for non-standard inputs
    return trimmed || fallback;
  }
}

