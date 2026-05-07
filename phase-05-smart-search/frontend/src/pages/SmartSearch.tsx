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
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Session sidebar */}
      <div className="w-72 shrink-0 border-r border-border bg-sidebar flex flex-col">
        <div className="px-5 py-5 border-b border-border">
          <h1 className="text-sm font-semibold text-foreground">Smart Search</h1>
          <p className="text-xs text-muted-foreground">AI-powered fund Q&A</p>
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
                <SuggestedQueries onSelect={handleSend} />
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
          <SuggestedQueries onSelect={handleSuggestionSelect} />
        )}
      </div>
    </div>
  );
}
