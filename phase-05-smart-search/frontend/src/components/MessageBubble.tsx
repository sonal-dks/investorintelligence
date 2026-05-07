import { ExternalLink } from "lucide-react";

import type { ChatMessage } from "../types";

type Props = {
  message: ChatMessage;
};

export function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div
        className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
          isUser
            ? "bg-primary text-primary-foreground rounded-br-md"
            : "bg-muted text-foreground rounded-bl-md"
        }`}
      >
        <div className="whitespace-pre-wrap">{message.content}</div>

        {message.citations && message.citations.length > 0 && (
          <div className="mt-3 pt-2 border-t border-border/30 space-y-1.5">
            {message.citations.map((c, i) => (
              <a
                key={i}
                href={c.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 text-xs opacity-80 hover:opacity-100 transition-opacity"
              >
                <ExternalLink className="w-3 h-3 shrink-0" />
                <span className="truncate">{c.fund}</span>
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export function ThinkingBubble() {
  return (
    <div className="flex justify-start mb-4">
      <div className="bg-muted rounded-2xl rounded-bl-md px-4 py-3">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <div className="flex gap-1">
            <span className="w-2 h-2 rounded-full bg-muted-foreground/40 animate-bounce" style={{ animationDelay: "0ms" }} />
            <span className="w-2 h-2 rounded-full bg-muted-foreground/40 animate-bounce" style={{ animationDelay: "150ms" }} />
            <span className="w-2 h-2 rounded-full bg-muted-foreground/40 animate-bounce" style={{ animationDelay: "300ms" }} />
          </div>
          <span>Searching…</span>
        </div>
      </div>
    </div>
  );
}
