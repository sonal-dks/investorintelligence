import { useQuery } from "@tanstack/react-query";

import { fetchBookingSummary, fetchDashboardOverview, fetchFundStrip, fetchKPIs, fetchPulsePreview } from "../lib/api";
import { useAuthStore } from "../stores/auth-store";

function useAccessToken() {
  return useAuthStore((s) => s.session?.access_token ?? "");
}

export function useKPIs() {
  const token = useAccessToken();
  return useQuery({
    queryKey: ["kpis", token],
    queryFn: () => fetchKPIs(token),
    enabled: Boolean(token),
    staleTime: 60_000,
  });
}

export function useBookings() {
  const token = useAccessToken();
  return useQuery({
    queryKey: ["bookings", token],
    queryFn: () => fetchBookingSummary(token),
    enabled: Boolean(token),
    staleTime: 60_000,
  });
}

export function useDashboardOverview() {
  const token = useAccessToken();
  return useQuery({
    queryKey: ["dashboard-overview", token],
    queryFn: () => fetchDashboardOverview(token),
    enabled: Boolean(token),
    staleTime: 30_000,
  });
}

export function useFundStrip() {
  const token = useAccessToken();
  return useQuery({
    queryKey: ["fund-strip", token],
    queryFn: () => fetchFundStrip(token),
    enabled: Boolean(token),
    staleTime: 60_000,
  });
}

export function usePulsePreview() {
  const token = useAccessToken();
  return useQuery({
    queryKey: ["pulse-preview", token],
    queryFn: () => fetchPulsePreview(token),
    enabled: Boolean(token),
    staleTime: 60_000,
  });
}
