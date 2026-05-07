import { StrictMode, useState } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MutualFundExplorerPage } from "./pages/MutualFundExplorer";
import { ResourceHubPage } from "./pages/ResourceHub";

const queryClient = new QueryClient();

function App() {
  const [page, setPage] = useState<"explorer" | "hub">("explorer");
  return (
    <>
      <header style={{ padding: 12, borderBottom: "1px solid #e5e7eb", display: "flex", gap: 8 }}>
        <button onClick={() => setPage("explorer")}>Mutual Fund Explorer</button>
        <button onClick={() => setPage("hub")}>Resource Hub</button>
      </header>
      {page === "explorer" ? <MutualFundExplorerPage /> : <ResourceHubPage />}
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
