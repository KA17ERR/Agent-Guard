import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// AgentGuard frontend — Vite config.
// The dev server runs on 5173 by default, which matches the backend's
// default CORS allow-list (see backend/app/core/config.py).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
});
