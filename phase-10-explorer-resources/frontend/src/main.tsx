import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MutualFundExplorerPage } from "./pages/MutualFundExplorer";

const queryClient = new QueryClient();

function App() {
  return (
    <>
      <header style={{ padding: 12, borderBottom: "1px solid #e5e7eb", display: "flex", gap: 8 }}>
        <strong>Mutual Fund Explorer</strong>
      </header>
      <MutualFundExplorerPage />
    </>
  );
}

const el = document.getElementById("root");
if (!el) throw new Error("root missing");

createRoot(el).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </StrictMode>,
);
