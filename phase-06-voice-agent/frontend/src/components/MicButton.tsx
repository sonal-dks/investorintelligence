import { Mic, MicOff } from "lucide-react";

type MicButtonProps = {
  isListening: boolean;
  isSupported: boolean;
  onToggle: () => void;
  disabled?: boolean;
};

export function MicButton({ isListening, isSupported, onToggle, disabled }: MicButtonProps) {
  if (!isSupported) {
    return (
      <div className="flex flex-col items-center gap-2 text-muted-foreground">
        <div className="flex h-20 w-20 items-center justify-center rounded-full bg-muted">
          <MicOff className="h-8 w-8" />
        </div>
        <p className="text-xs">Voice not supported in this browser</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-3">
      <div className="relative">
        {isListening && (
          <div className="absolute inset-0 rounded-full bg-red-400/30 animate-pulse-ring" style={{ margin: "-8px" }} />
        )}
        <button
          type="button"
          onClick={onToggle}
          disabled={disabled}
          className={`relative flex h-20 w-20 items-center justify-center rounded-full transition-all ${
            isListening
              ? "bg-red-500 text-white shadow-lg shadow-red-500/30 scale-105"
              : "bg-primary text-primary-foreground hover:scale-105 shadow-md"
          } disabled:opacity-50 disabled:cursor-not-allowed`}
          aria-label={isListening ? "Stop recording" : "Start recording"}
        >
          <Mic className="h-8 w-8" />
        </button>
      </div>
      <p className="text-xs text-muted-foreground">
        {isListening ? "Listening… tap to stop" : "Tap to speak"}
      </p>
    </div>
  );
}
