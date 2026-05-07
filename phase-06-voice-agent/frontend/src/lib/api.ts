import type { VoiceMessage, VoiceMessageResponse, VoiceSession, UserProfile } from "../types";

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

export async function fetchVoiceSessions(accessToken: string): Promise<{ sessions: VoiceSession[] }> {
  return authGet<{ sessions: VoiceSession[] }>("/api/voice/sessions", accessToken);
}

export async function createVoiceSession(accessToken: string): Promise<VoiceSession> {
  return authPost<VoiceSession>("/api/voice/sessions", accessToken);
}

export async function deleteVoiceSession(accessToken: string, sessionId: string): Promise<void> {
  return authDelete(`/api/voice/sessions/${sessionId}`, accessToken);
}

export async function fetchVoiceMessages(
  accessToken: string,
  sessionId: string,
): Promise<{ messages: VoiceMessage[] }> {
  return authGet<{ messages: VoiceMessage[] }>(`/api/voice/sessions/${sessionId}/messages`, accessToken);
}

export async function sendVoiceMessage(
  accessToken: string,
  sessionId: string,
  content: string,
  inputMode: "voice" | "text" = "text",
): Promise<VoiceMessageResponse> {
  return authPost<VoiceMessageResponse>("/api/voice/message", accessToken, {
    session_id: sessionId,
    content,
    input_mode: inputMode,
  });
}

export async function fetchTTSAudio(
  accessToken: string,
  text: string,
  voice?: string,
): Promise<Blob> {
  const res = await fetch(`${base()}/api/voice/tts`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ text, voice: voice ?? "en-IN-NeerjaNeural" }),
  });
  if (!res.ok) throw new Error(`TTS request failed (${res.status})`);
  return res.blob();
}
