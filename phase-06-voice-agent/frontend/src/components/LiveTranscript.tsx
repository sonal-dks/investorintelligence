type LiveTranscriptProps = {
  transcript: string;
  interimTranscript: string;
  isListening: boolean;
};

export function LiveTranscript({ transcript, interimTranscript, isListening }: LiveTranscriptProps) {
  const hasContent = transcript || interimTranscript;

  if (!isListening && !hasContent) return null;

  return (
    <div className="w-full max-w-md rounded-lg border border-border bg-muted/50 p-3 text-sm">
      {hasContent ? (
        <p>
          {transcript && <span className="text-foreground">{transcript}</span>}
          {interimTranscript && <span className="text-muted-foreground italic">{interimTranscript}</span>}
        </p>
      ) : (
        <p className="text-muted-foreground italic flex items-center gap-2">
          <span className="inline-block h-2 w-2 rounded-full bg-red-500 animate-pulse" />
          Listening…
        </p>
      )}
    </div>
  );
}
