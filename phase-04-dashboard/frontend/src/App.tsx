import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AdminOnly } from "./components/AdminOnly";
import { AppShell } from "./components/AppShell";
import { PhaseAuthSync } from "./components/PhaseAuthSync";
import { ProtectedLayout } from "./components/ProtectedLayout";
import { AuthProvider } from "./providers/AuthProvider";
import { DashboardPage } from "./pages/Dashboard";
import { LoginPage } from "./pages/Login";

import { SmartSearchPage } from "@phase05/pages/SmartSearch";
import { VoiceAgentPage } from "@phase06/pages/VoiceAgent";
import { ApprovalCenterPage } from "@phase07/pages/ApprovalCenter";
import { App as BookingsApp } from "@phase08/App";
import { WeeklyPulsePage } from "@phase09/pages/WeeklyPulse.tsx";
import { MutualFundExplorerPage } from "@phase10/pages/MutualFundExplorer";
import { EvaluationSuitePage } from "./pages/EvaluationSuite";

const queryClient = new QueryClient();

function SmartSearchRoute() {
  return (
    <>
      <PhaseAuthSync target="phase05" />
      <SmartSearchPage />
    </>
  );
}

function VoiceAgentRoute() {
  return (
    <>
      <PhaseAuthSync target="phase06" />
      <VoiceAgentPage />
    </>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route element={<ProtectedLayout />}>
              <Route
                path="/dashboard"
                element={
                  <AppShell pageTitle="Dashboard">
                    <DashboardPage />
                  </AppShell>
                }
              />
              <Route
                path="/smart-search"
                element={
                  <AppShell pageTitle="Smart Search">
                    <SmartSearchRoute />
                  </AppShell>
                }
              />
              <Route
                path="/voice-agent"
                element={
                  <AppShell pageTitle="Voice Agent">
                    <VoiceAgentRoute />
                  </AppShell>
                }
              />
              <Route
                path="/weekly-pulse"
                element={
                  <AppShell pageTitle="Weekly Pulse">
                    <WeeklyPulsePage />
                  </AppShell>
                }
              />
              <Route
                path="/bookings"
                element={
                  <AppShell pageTitle="Bookings" contentMaxWidth="full">
                    <BookingsApp />
                  </AppShell>
                }
              />
              <Route
                path="/explorer"
                element={
                  <AppShell pageTitle="Mutual Fund Explorer" contentMaxWidth="full">
                    <MutualFundExplorerPage />
                  </AppShell>
                }
              />
              <Route
                path="/admin"
                element={
                  <AdminOnly>
                    <AppShell pageTitle="Approval Center">
                      <ApprovalCenterPage />
                    </AppShell>
                  </AdminOnly>
                }
              />
              <Route
                path="/evaluation-suite"
                element={
                  <AdminOnly>
                    <AppShell pageTitle="Evaluation Suite">
                      <EvaluationSuitePage />
                    </AppShell>
                  </AdminOnly>
                }
              />
            </Route>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
