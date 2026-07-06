import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Proxies /api and /ws to the backend during development so the
// frontend, backend, and browser all agree on one origin -- this keeps
// session cookies same-site without needing permissive CORS.
//
// Backend host/port are overridable via env vars (see start.sh) since
// the default port isn't always free on a given machine.
const backendHost = process.env.ECHO_BASE_BACKEND_HOST ?? "localhost";
const backendPort = process.env.ECHO_BASE_BACKEND_PORT ?? "8088";

// Extra hostnames to accept, e.g. when reached through a reverse proxy
// or tunnel (config/config.yaml's server.allowed_hosts, passed through
// by start.sh). Comma-separated, blank/unset means "just localhost".
const allowedHosts = (process.env.ECHO_BASE_ALLOWED_HOSTS ?? "")
  .split(",")
  .map((host) => host.trim())
  .filter(Boolean);

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    ...(allowedHosts.length > 0 ? { allowedHosts } : {}),
    proxy: {
      "/api": {
        target: `http://${backendHost}:${backendPort}`,
        changeOrigin: true,
      },
      "/ws": {
        target: `ws://${backendHost}:${backendPort}`,
        ws: true,
      },
    },
  },
});
