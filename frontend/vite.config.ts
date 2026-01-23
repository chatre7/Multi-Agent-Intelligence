import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// In Docker: use 'backend' hostname, otherwise use localhost
const BACKEND_HOST = process.env.BACKEND_HOST || "localhost"
const DEFAULT_BACKEND_URL = `http://${BACKEND_HOST}:8000`

const stripTrailingSlash = (value: string) => value.replace(/\/+$/, "")

function normalizeProxyTarget(value: string | undefined, fallback: string) {
  if (!value) {
    return fallback
  }
  const trimmed = value.trim()
  if (!trimmed) {
    return fallback
  }
  if (/^https?:\/\//i.test(trimmed)) {
    return stripTrailingSlash(trimmed)
  }
  const wsMatch = trimmed.match(/^wss?:\/\/(.*)$/i)
  if (wsMatch) {
    return stripTrailingSlash(trimmed.replace(/^ws/i, "http"))
  }
  return fallback
}

const apiProxyTarget = normalizeProxyTarget(
  process.env.VITE_API_BASE_URL,
  DEFAULT_BACKEND_URL,
)
const wsProxyTarget = normalizeProxyTarget(
  process.env.VITE_WS_URL,
  apiProxyTarget,
)

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: apiProxyTarget,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
      "/ws": {
        target: wsProxyTarget,
        changeOrigin: true,
        ws: true,
      },
    },
  },
})
