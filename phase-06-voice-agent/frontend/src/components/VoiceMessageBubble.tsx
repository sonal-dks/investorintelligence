import { Mic, Type, Volume2 } from "lucide-react";

import type { VoiceMessage } from "../types";

type VoiceMessageBubbleProps = {
  message: VoiceMessage;
  onSpeak?: (text: string) => void;
  isSpeaking?: boolean;
};

export function VoiceMessageBubble({ message, onSpeak, isSpeaking }: VoiceMessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm ${
          isUser
            ? "bg-primary text-primary-foreground rounded-br-md"
            : "bg-muted text-card-foreground rounded-bl-md"
        }`}
      >
        <div className="flex items-center gap-1.5 mb-1">
          {message.input_mode === "voice" ? (
            <Mic className="h-3 w-3 opacity-60" />
          ) : (
            <Type className="h-3 w-3 opacity-60" />
          )}
          <span className="text-xs opacity-60">{message.input_mode}</span>
        </div>

        <p className="whitespace-pre-wrap">{message.content}</p>

        {message.citations.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {message.citations.map((c, i) => (
              <a
                key={i}
                href={c.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center rounded-full bg-blue-50 px-2 py-0.5 text-xs text-blue-700 hover:bg-blue-100 transition-colors"
              >
                {c.fund}
              </a>
            ))}
          </div>
        )}

        {!isUser && onSpeak && (
          <button
            type="button"
            onClick={() => onSpeak(message.content)}
            className={`mt-1.5 flex items-center gap-1 text-xs transition-colors ${
              isSpeaking ? "text-blue-500" : "text-muted-foreground hover:text-foreground"
            }`}
            aria-label="Read aloud"
          >
            <Volume2 className="h-3 w-3" />
            {isSpeaking ? "Speaking…" : "Listen"}
          </button>
        )}
      </div>
    </div>
  );
}
