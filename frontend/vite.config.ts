import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The dev server proxies /api to the backend container so the browser only ever
// talks to one origin (no CORS headaches in dev).
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    // Polling makes file-watching reliable inside Docker on macOS/Windows.
    watch: { usePolling: true },
    proxy: {
      "/api": {
        target: "http://backend:8000",
        changeOrigin: true,
      },
    },
  },
});
