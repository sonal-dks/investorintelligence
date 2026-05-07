import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createSession,
  deleteSession,
  fetchMessages,
  fetchSessions,
  sendMessage,
} from "../lib/api";
import { useAuthStore } from "../stores/auth-store";
import { useChatStore } from "../stores/chat-store";

function useAccessToken() {
  return useAuthStore((s) => s.session?.access_token ?? "");
}

export function useSessions() {
  const token = useAccessToken();
  return useQuery({
    queryKey: ["chat-sessions", token],
    queryFn: () => fetchSessions(token),
    enabled: Boolean(token),
    staleTime: 30_000,
  });
}

export function useMessages(sessionId: string | null) {
  const token = useAccessToken();
  return useQuery({
    queryKey: ["chat-messages", sessionId, token],
    queryFn: () => fetchMessages(token, sessionId!),
    enabled: Boolean(token) && Boolean(sessionId),
    staleTime: 10_000,
  });
}

export function useCreateSession() {
  const token = useAccessToken();
  const qc = useQueryClient();
  const setActiveSession = useChatStore((s) => s.setActiveSession);

  return useMutation({
    mutationFn: () => createSession(token),
    onSuccess: (session) => {
      setActiveSession(session.id);
      void qc.invalidateQueries({ queryKey: ["chat-sessions"] });
    },
  });
}

export function useDeleteSession() {
  const token = useAccessToken();
  const qc = useQueryClient();
  const activeSessionId = useChatStore((s) => s.activeSessionId);
  const setActiveSession = useChatStore((s) => s.setActiveSession);

  return useMutation({
    mutationFn: (sessionId: string) => deleteSession(token, sessionId),
    onSuccess: (_data, sessionId) => {
      if (activeSessionId === sessionId) {
        setActiveSession(null);
      }
      void qc.invalidateQueries({ queryKey: ["chat-sessions"] });
    },
  });
}

export function useSendMessage() {
  const token = useAccessToken();
  const qc = useQueryClient();
  const setSending = useChatStore((s) => s.setSending);

  return useMutation({
    mutationFn: ({ sessionId, content }: { sessionId: string; content: string }) => {
      setSending(true);
      return sendMessage(token, sessionId, content);
    },
    onSettled: (_data, _err, vars) => {
      setSending(false);
      void qc.invalidateQueries({ queryKey: ["chat-messages", vars.sessionId] });
      void qc.invalidateQueries({ queryKey: ["chat-sessions"] });
    },
  });
}
