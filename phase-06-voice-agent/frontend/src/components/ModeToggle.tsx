import { Mic, Type } from "lucide-react";

import { useVoiceStore } from "../stores/voice-store";

export function ModeToggle() {
  const mode = useVoiceStore((s) => s.mode);
  const setMode = useVoiceStore((s) => s.setMode);

  return (
    <div className="inline-flex rounded-lg border border-border p-0.5 bg-muted">
      <button
        type="button"
        onClick={() => setMode("voice")}
        className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
          mode === "voice"
            ? "bg-background text-foreground shadow-sm"
            : "text-muted-foreground hover:text-foreground"
        }`}
        aria-pressed={mode === "voice"}
      >
        <Mic className="h-4 w-4" />
        Voice
      </button>
      <button
        type="button"
        onClick={() => setMode("text")}
        className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
          mode === "text"
            ? "bg-background text-foreground shadow-sm"
            : "text-muted-foreground hover:text-foreground"
        }`}
        aria-pressed={mode === "text"}
      >
        <Type className="h-4 w-4" />
        Text
      </button>
    </div>
  );
}
