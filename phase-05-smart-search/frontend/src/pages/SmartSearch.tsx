import { useEffect, useRef, useState } from "react";

import { ChatInput } from "../components/ChatInput";
import { MessageBubble, ThinkingBubble } from "../components/MessageBubble";
import { SessionList } from "../components/SessionList";
import { SuggestedQueries } from "../components/SuggestedQueries";
import {
  useCreateSession,
  useDeleteSession,
  useMessages,
  useSendMessage,
  useSessions,
} from "../hooks/useChat";
import { useChatStore } from "../stores/chat-store";
import type { ChatMessage } from "../types";

export function SmartSearchPage() {
  const activeSessionId = useChatStore((s) => s.activeSessionId);
  const setActiveSession = useChatStore((s) => s.setActiveSession);
  const isSending = useChatStore((s) => s.isSending);

  const { data: sessionData } = useSessions();
  const { data: messageData } = useMessages(activeSessionId);
  const createMutation = useCreateSession();
  const deleteMutation = useDeleteSession();
  const sendMutation = useSendMessage();

  const sessions = sessionData?.sessions ?? [];
  const serverMessages = messageData?.messages ?? [];
  const [optimisticMsg, setOptimisticMsg] = useState<ChatMessage | null>(null);

  const messages = optimisticMsg
    ? [...serverMessages, optimisticMsg]
    : serverMessages;

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, isSending]);

  useEffect(() => {
    if (!isSending && optimisticMsg) {
      setOptimisticMsg(null);
    }
  }, [isSending, optimisticMsg]);

  const handleSend = (content: string) => {
    if (!activeSessionId) return;
    setOptimisticMsg({
      id: `optimistic-${Date.now()}`,
      role: "user",
      content,
      citations: [],
      metadata: {},
      created_at: new Date().toISOString(),
    });
    sendMutation.mutate({ sessionId: activeSessionId, content });
  };

  const handleSuggestionSelect = (query: string) => {
    if (!activeSessionId) {
      createMutation.mutate(undefined, {
        onSuccess: (session) => {
          sendMutation.mutate({ sessionId: session.id, content: query });
        },
      });
    } else {
      handleSend(query);
    }
  };

  return (
    <div className="flex h-full min-h-0 overflow-hidden rounded-xl border border-border bg-background">
      {/* Session sidebar */}
      <div className="hidden w-72 shrink-0 border-r border-border bg-sidebar md:flex md:flex-col">
        <div className="px-5 py-5 border-b border-border">
          <h1 className="text-sm font-semibold text-foreground">Smart Search</h1>
          <p className="text-xs text-muted-foreground">RAG-powered fund Q&A</p>
        </div>
        <SessionList
          sessions={sessions}
          activeId={activeSessionId}
          onSelect={setActiveSession}
          onNew={() => createMutation.mutate()}
          onDelete={(id) => deleteMutation.mutate(id)}
          isCreating={createMutation.isPending}
        />
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        {activeSessionId ? (
          <>
            <div className="flex-1 overflow-y-auto px-6 py-4">
              {messages.length === 0 && !isSending ? (
                <div className="mx-auto max-w-3xl">
                  <div className="rounded-2xl border border-border bg-card p-6">
                    <h2 className="text-base font-semibold">Start a grounded search</h2>
                    <p className="mt-1 text-sm text-muted-foreground">
                      Answers are generated only from retrieved fund and fee context.
                    </p>
                    <div className="mt-4">
                      <SuggestedQueries onSelect={handleSend} />
                    </div>
                  </div>
                </div>
              ) : (
                <div className="max-w-3xl mx-auto">
                  {messages.map((msg) => (
                    <MessageBubble key={msg.id} message={msg} />
                  ))}
                  {isSending && <ThinkingBubble />}
                  <div ref={messagesEndRef} />
                </div>
              )}
            </div>
            <ChatInput onSend={handleSend} disabled={isSending} />
          </>
        ) : (
          <div className="flex h-full items-center justify-center p-6">
            <div className="w-full max-w-3xl rounded-2xl border border-border bg-card p-8 text-center">
              <h2 className="text-xl font-semibold">Ask anything about funds</h2>
              <p className="mt-2 text-sm text-muted-foreground">
                Pick a quick prompt or create a new question. Responses stay grounded in your indexed data.
              </p>
              <div className="mt-6">
                <SuggestedQueries onSelect={handleSuggestionSelect} />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
