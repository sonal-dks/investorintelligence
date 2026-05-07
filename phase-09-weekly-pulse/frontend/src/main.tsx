import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { WeeklyPulsePage } from "./pages/WeeklyPulse";

const queryClient = new QueryClient();

function stripSessionHandoffParams() {
  const url = new URL(window.location.href);
  const accessToken = url.searchParams.get("access_token");
  const refreshToken = url.searchParams.get("refresh_token");
  if (!accessToken || !refreshToken) return;
  url.searchParams.delete("access_token");
  url.searchParams.delete("refresh_token");
  window.history.replaceState({}, document.title, `${url.pathname}${url.search}${url.hash}`);
}

stripSessionHandoffParams();

const el = document.getElementById("root");
if (!el) throw new Error("root missing");

createRoot(el).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <WeeklyPulsePage />
    </QueryClientProvider>
  </StrictMode>,
);
