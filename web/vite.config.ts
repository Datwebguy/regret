import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

function legalPages() {
  const rewrite: Record<string, string> = {
    "/terms": "/terms.html",
    "/privacy": "/privacy.html",
  };
  return {
    name: "legal-pages",
    configureServer(server: { middlewares: { use: (fn: (req: { url?: string }, _res: unknown, next: () => void) => void) => void } }) {
      server.middlewares.use((req, _res, next) => {
        const path = (req.url || "").split("?")[0];
        if (path && rewrite[path]) {
          req.url = (req.url || "").replace(path, rewrite[path]);
        }
        next();
      });
    },
  };
}

export default defineConfig({
  plugins: [react(), legalPages()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
});
