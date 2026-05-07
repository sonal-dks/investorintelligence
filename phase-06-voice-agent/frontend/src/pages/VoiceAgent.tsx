import { useCallback, useEffect, useRef, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Loader2, Send } from "lucide-react";

import { useAuthStore } from "../stores/auth-store";
import { useVoiceStore } from "../stores/voice-store";
import { useSpeechRecognition } from "../hooks/useSpeechRecognition";
import { useTTS } from "../hooks/useTTS";
import {
  createVoiceSession,
  deleteVoiceSession,
  fetchVoiceMessages,
  fetchVoiceSessions,
  sendVoiceMessage,
} from "../lib/api";
import type { VoiceMessage } from "../types";

import { LiveTranscript } from "../components/LiveTranscript";
import { MicButton } from "../components/MicButton";
import { ModeToggle } from "../components/ModeToggle";
import { VoiceMessageBubble } from "../components/VoiceMessageBubble";
import { VoiceSessionList } from "../components/VoiceSessionList";

const SUGGESTED_QUERIES = [
  "What is the exit load of Mirae Asset Large Cap?",
  "Tell me the expense ratio of Mirae Flexi Cap Fund",
  "Compare the returns of Large Cap and Mid Cap funds",
];

export function VoiceAgentPage() {
  const session = useAuthStore((s) => s.session);
  const accessToken = session?.access_token ?? "";
  const queryClient = useQueryClient();

  const mode = useVoiceStore((s) => s.mode);
  const setMode = useVoiceStore((s) => s.setMode);
  const activeSessionId = useVoiceStore((s) => s.activeSessionId);
  const setActiveSession = useVoiceStore((s) => s.setActiveSession);
  const isSending = useVoiceStore((s) => s.isSending);
  const setSending = useVoiceStore((s) => s.setSending);

  const { start, stop, isListening, transcript, interimTranscript, isSupported, error: speechError } = useSpeechRecognition();
  const { speak, stop: stopTTS, isSpeaking } = useTTS();

  const [textInput, setTextInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const prevTranscript = useRef("");

  useEffect(() => {
    if (!isSupported && mode === "voice") {
      setMode("text");
    }
  }, [isSupported, mode, setMode]);

  const sessionsQuery = useQuery({
    queryKey: ["voiceSessions"],
    queryFn: () => fetchVoiceSessions(accessToken),
    enabled: !!accessToken,
  });

  const messagesQuery = useQuery({
    queryKey: ["voiceMessages", activeSessionId],
    queryFn: () => fetchVoiceMessages(accessToken, activeSessionId!),
    enabled: !!accessToken && !!activeSessionId,
  });

  const messages = messagesQuery.data?.messages ?? [];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  const createMutation = useMutation({
    mutationFn: () => createVoiceSession(accessToken),
    onSuccess: (data) => {
      setActiveSession(data.id);
      queryClient.invalidateQueries({ queryKey: ["voiceSessions"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteVoiceSession(accessToken, id),
    onSuccess: (_, id) => {
      if (activeSessionId === id) setActiveSession(null);
      queryClient.invalidateQueries({ queryKey: ["voiceSessions"] });
    },
  });

  const sendMutation = useMutation({
    mutationFn: ({ content, inputMode }: { content: string; inputMode: "voice" | "text" }) =>
      sendVoiceMessage(accessToken, activeSessionId!, content, inputMode),
    onMutate: () => setSending(true),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ["voiceMessages", activeSessionId] });
      queryClient.invalidateQueries({ queryKey: ["voiceSessions"] });
      if (mode === "voice" && response.voice_hint === "concise") {
        speak(response.content);
      }
    },
    onSettled: () => setSending(false),
  });

  const handleSend = useCallback(
    (content: string, inputMode: "voice" | "text" = "text") => {
      const trimmed = content.trim();
      if (!trimmed || !activeSessionId || isSending) return;
      sendMutation.mutate({ content: trimmed, inputMode });
      setTextInput("");
    },
    [activeSessionId, isSending, sendMutation],
  );

  useEffect(() => {
    if (!isListening && transcript && transcript !== prevTranscript.current) {
      prevTranscript.current = transcript;
      handleSend(transcript, "voice");
    }
  }, [isListening, transcript, handleSend]);

  const handleMicToggle = () => {
    stopTTS();
    if (isListening) {
      stop();
    } else {
      prevTranscript.current = "";
      start();
    }
  };

  const handleTextSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSend(textInput, "text");
  };

  return (
    <div className="flex h-screen">
      {/* Session sidebar */}
      <div className="w-64 shrink-0">
        <VoiceSessionList
          sessions={sessionsQuery.data?.sessions ?? []}
          activeSessionId={activeSessionId}
          onSelect={setActiveSession}
          onCreate={() => createMutation.mutate()}
          onDelete={(id) => deleteMutation.mutate(id)}
        />
      </div>

      {/* Main area */}
      <div className="flex flex-1 flex-col">
        {/* Header */}
        <header className="flex items-center justify-between border-b border-border px-6 py-3">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground">Voice Agent</h1>
            <p className="text-sm text-muted-foreground">Ask about mutual funds using voice or text</p>
          </div>
          <ModeToggle />
        </header>

        {!activeSessionId ? (
          <div className="flex flex-1 flex-col items-center justify-center gap-4 text-muted-foreground">
            <p>Select a session or create a new one to begin.</p>
            <button
              type="button"
              onClick={() => createMutation.mutate()}
              className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90"
            >
              New Voice Session
            </button>
          </div>
        ) : (
          <>
            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
              {messages.length === 0 && !isSending && (
                <div className="flex flex-col items-center justify-center gap-4 py-12 text-center">
                  <p className="text-muted-foreground">Start the conversation with a question or try:</p>
                  <div className="flex flex-wrap justify-center gap-2">
                    {SUGGESTED_QUERIES.map((q) => (
                      <button
                        key={q}
                        type="button"
                        onClick={() => handleSend(q, mode === "voice" ? "voice" : "text")}
                        className="rounded-lg border border-border bg-card px-3 py-2 text-sm text-card-foreground hover:bg-muted transition-colors"
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {messages.map((m: VoiceMessage) => (
                <VoiceMessageBubble
                  key={m.id}
                  message={m}
                  onSpeak={m.role === "assistant" ? speak : undefined}
                  isSpeaking={isSpeaking}
                />
              ))}

              {isSending && (
                <div className="flex justify-start">
                  <div className="flex items-center gap-2 rounded-2xl bg-muted px-4 py-3 text-sm text-muted-foreground">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Searching…
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Speech error banner */}
            {speechError && (
              <div className="mx-6 mb-2 flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700">
                <AlertTriangle className="h-3.5 w-3.5" />
                {speechError}
              </div>
            )}

            {/* Input area */}
            <div className="border-t border-border px-6 py-4">
              {mode === "voice" ? (
                <div className="flex flex-col items-center gap-4">
                  <MicButton
                    isListening={isListening}
                    isSupported={isSupported}
                    onToggle={handleMicToggle}
                    disabled={isSending}
                  />
                  <LiveTranscript
                    transcript={transcript}
                    interimTranscript={interimTranscript}
                    isListening={isListening}
                  />
                </div>
              ) : (
                <form onSubmit={handleTextSubmit} className="flex gap-2">
                  <input
                    type="text"
                    value={textInput}
                    onChange={(e) => setTextInput(e.target.value)}
                    placeholder="Type your question…"
                    disabled={isSending}
                    className="flex-1 rounded-lg border border-border bg-background px-4 py-2.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 disabled:opacity-50"
                  />
                  <button
                    type="submit"
                    disabled={!textInput.trim() || isSending}
                    className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
                    aria-label="Send message"
                  >
                    <Send className="h-4 w-4" />
                  </button>
                </form>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
