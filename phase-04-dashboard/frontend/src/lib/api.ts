import type { BookingSummary, FundStrip, KPIResponse, PulsePreview, UserProfile } from "../types";

const base = () => import.meta.env.VITE_API_BASE ?? "";

async function parseJson<T>(res: Response): Promise<T | null> {
  const text = await res.text();
  if (!text) return null;
  return JSON.parse(text) as T;
}

async function authGet<T>(path: string, accessToken: string): Promise<T> {
  const res = await fetch(`${base()}${path}`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (!res.ok) throw new Error(`Request failed: ${path}`);
  const body = await parseJson<T>(res);
  if (!body) throw new Error(`Empty response: ${path}`);
  return body;
}

export async function fetchMe(accessToken: string): Promise<{ res: Response; body: UserProfile | null }> {
  const res = await fetch(`${base()}/api/users/me`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  const body = await parseJson<UserProfile>(res);
  return { res, body };
}

export async function fetchKPIs(accessToken: string): Promise<KPIResponse> {
  return authGet<KPIResponse>("/api/dashboard/kpis", accessToken);
}

export async function fetchBookingSummary(accessToken: string): Promise<BookingSummary> {
  return authGet<BookingSummary>("/api/dashboard/bookings", accessToken);
}

export async function fetchFundStrip(accessToken: string): Promise<FundStrip> {
  return authGet<FundStrip>("/api/dashboard/fund-strip", accessToken);
}

export async function fetchPulsePreview(accessToken: string): Promise<PulsePreview> {
  return authGet<PulsePreview>("/api/dashboard/pulse-preview", accessToken);
}
