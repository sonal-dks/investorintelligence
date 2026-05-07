import type { UserProfile } from "../types";

const base = () => import.meta.env.VITE_API_BASE ?? "";

export type ProfileUpsertBody = {
  role?: "investor" | "admin";
  email?: string | null;
  display_name?: string | null;
  first_login_complete?: boolean;
};

async function parseJson(res: Response): Promise<unknown> {
  const text = await res.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

export async function fetchMe(accessToken: string): Promise<{ res: Response; body: UserProfile | null }> {
  const res = await fetch(`${base()}/api/users/me`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  const raw = await parseJson(res);
  return { res, body: res.ok && raw && typeof raw === "object" ? (raw as UserProfile) : null };
}

export async function upsertProfile(
  accessToken: string,
  body: ProfileUpsertBody,
): Promise<{ res: Response; body: UserProfile | null }> {
  const res = await fetch(`${base()}/api/users/profile`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  const raw = await parseJson(res);
  return { res, body: res.ok && raw && typeof raw === "object" ? (raw as UserProfile) : null };
}
