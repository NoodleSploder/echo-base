import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Proxies /api and /ws to the backend during development so the
// frontend, backend, and browser all agree on one origin -- this keeps
// session cookies same-site without needing permissive CORS.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8088",
        changeOrigin: true,
      },
      "/ws": {
        target: "ws://localhost:8088",
        ws: true,
      },
    },
  },
});
