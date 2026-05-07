import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { ProtectedLayout } from "./components/ProtectedLayout";
import { LoginPage } from "./pages/Login";
import { VoiceAgentPage } from "./pages/VoiceAgent";
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
              <Route path="/voice-agent" element={<VoiceAgentPage />} />
            </Route>
            <Route path="/" element={<Navigate to="/voice-agent" replace />} />
            <Route path="*" element={<Navigate to="/voice-agent" replace />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
