import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App } from "./App";
import "./index.css";

const client = new QueryClient();

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

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={client}>
      <App />
    </QueryClientProvider>
  </StrictMode>,
);
