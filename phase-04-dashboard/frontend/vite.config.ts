import fs from "node:fs";
import path from "node:path";

import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import type { Plugin } from "vite";
import { defineConfig } from "vitest/config";

/** Repo root: `phase-04-dashboard/frontend` is two levels down; `frontend-deploy` is one level down. */
function resolveRepoRoot(): string {
  const twoUp = path.resolve(__dirname, "../..");
  if (fs.existsSync(path.join(twoUp, "phase-05-smart-search"))) return twoUp;
  const oneUp = path.resolve(__dirname, "..");
  if (fs.existsSync(path.join(oneUp, "phase-05-smart-search"))) return oneUp;
  return twoUp;
}

const repoRoot = resolveRepoRoot();
const dashboardSrc = path.resolve(__dirname, "src/main.tsx");

/** Bare imports resolved from dashboard node_modules for embedded phase frontends. */
const SHARED_DEPS = [
  "react",
  "react-dom",
  "react/jsx-runtime",
  "@tanstack/react-query",
  "@supabase/supabase-js",
  "zustand",
  "lucide-react",
  "react-router-dom",
];

function sharedDepsFromDashboard(): Plugin {
  return {
    name: "shared-deps-from-dashboard",
    enforce: "pre",
    async resolveId(source, importer, options) {
      if (!importer?.includes(`${path.sep}phase-`)) return null;
      const isShared =
        SHARED_DEPS.includes(source) || SHARED_DEPS.some((d) => source.startsWith(`${d}/`));
      if (!isShared) return null;
      return this.resolve(source, dashboardSrc, { ...options, skipSelf: true });
    },
  };
}

const splitProxy = process.env.VITE_USE_SPLIT_API_PROXY === "1";
const assembledTarget = process.env.VITE_ASSEMBLED_API_URL ?? "http://127.0.0.1:8012";

const assembledProxy: Record<string, { target: string; changeOrigin: boolean }> = {
  "^/(api|health)": { target: assembledTarget, changeOrigin: true },
};

const splitProxies: Record<string, { target: string; changeOrigin: boolean }> = {
  "/api/rag": { target: "http://127.0.0.1:8002", changeOrigin: true },
  "/api/users": { target: "http://127.0.0.1:8003", changeOrigin: true },
  "/api/dashboard": { target: "http://127.0.0.1:8004", changeOrigin: true },
  "/api/chat": { target: "http://127.0.0.1:8005", changeOrigin: true },
  "/api/voice": { target: "http://127.0.0.1:8006", changeOrigin: true },
  "/api/intents": { target: "http://127.0.0.1:8007", changeOrigin: true },
  "/api/approvals": { target: "http://127.0.0.1:8007", changeOrigin: true },
  "/api/bookings": { target: "http://127.0.0.1:8008", changeOrigin: true },
  "/api/calendar": { target: "http://127.0.0.1:8008", changeOrigin: true },
  "/api/pulse": { target: "http://127.0.0.1:8009", changeOrigin: true },
  "/api/funds": { target: "http://127.0.0.1:8010", changeOrigin: true },
  "/api/eval": { target: "http://127.0.0.1:8011", changeOrigin: true },
};

export default defineConfig({
  plugins: [sharedDepsFromDashboard(), react(), tailwindcss()],
  resolve: {
    dedupe: SHARED_DEPS,
    alias: {
      "@phase05": path.resolve(repoRoot, "phase-05-smart-search/frontend/src"),
      "@phase06": path.resolve(repoRoot, "phase-06-voice-agent/frontend/src"),
      "@phase07": path.resolve(repoRoot, "phase-07-intent-approvals/frontend/src"),
      "@phase08": path.resolve(repoRoot, "phase-08-calendar-booking/frontend/src"),
      "@phase09": path.resolve(repoRoot, "phase-09-weekly-pulse/frontend/src"),
      "@phase10": path.resolve(repoRoot, "phase-10-explorer-resources/frontend/src"),
    },
  },
  server: {
    port: 5180,
    fs: {
      allow: [path.resolve(__dirname, ".."), repoRoot],
    },
    proxy: splitProxy ? splitProxies : assembledProxy,
  },
  test: {
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts",
    globals: true,
  },
});
