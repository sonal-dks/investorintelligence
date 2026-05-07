import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { ProtectedLayout } from "./components/ProtectedLayout";
import { LoginPage } from "./pages/Login";
import { SmartSearchPage } from "./pages/SmartSearch";
import { AuthProvider } from "./providers/AuthProvider";

const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route element={<ProtectedLayout />}>
              <Route path="/smart-search" element={<SmartSearchPage />} />
            </Route>
            <Route path="/" element={<Navigate to="/smart-search" replace />} />
            <Route path="*" element={<Navigate to="/smart-search" replace />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
