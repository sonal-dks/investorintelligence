import type { ChatMessage, ChatMessageResponse, ChatSession, UserProfile } from "../types";

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
  if (!res.ok) throw new Error(`Request failed: ${path} (${res.status})`);
  const body = await parseJson<T>(res);
  if (!body) throw new Error(`Empty response: ${path}`);
  return body;
}

async function authPost<T>(path: string, accessToken: string, data?: unknown): Promise<T> {
  const res = await fetch(`${base()}${path}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    },
    body: data ? JSON.stringify(data) : undefined,
  });
  if (!res.ok) throw new Error(`Request failed: ${path} (${res.status})`);
  const body = await parseJson<T>(res);
  if (!body) throw new Error(`Empty response: ${path}`);
  return body;
}

async function authDelete(path: string, accessToken: string): Promise<void> {
  const res = await fetch(`${base()}${path}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (!res.ok) throw new Error(`Request failed: ${path} (${res.status})`);
}

export async function fetchMe(accessToken: string): Promise<{ res: Response; body: UserProfile | null }> {
  const res = await fetch(`${base()}/api/users/me`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  const body = await parseJson<UserProfile>(res);
  return { res, body };
}

export async function fetchSessions(accessToken: string): Promise<{ sessions: ChatSession[] }> {
  return authGet<{ sessions: ChatSession[] }>("/api/chat/sessions", accessToken);
}

export async function createSession(accessToken: string): Promise<ChatSession> {
  return authPost<ChatSession>("/api/chat/sessions", accessToken);
}

export async function deleteSession(accessToken: string, sessionId: string): Promise<void> {
  return authDelete(`/api/chat/sessions/${sessionId}`, accessToken);
}

export async function fetchMessages(
  accessToken: string,
  sessionId: string,
): Promise<{ messages: ChatMessage[] }> {
  return authGet<{ messages: ChatMessage[] }>(`/api/chat/sessions/${sessionId}/messages`, accessToken);
}

export async function sendMessage(
  accessToken: string,
  sessionId: string,
  content: string,
): Promise<ChatMessageResponse> {
  return authPost<ChatMessageResponse>("/api/chat/message", accessToken, {
    session_id: sessionId,
    content,
  });
}
