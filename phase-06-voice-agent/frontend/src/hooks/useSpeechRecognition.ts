import { useCallback, useEffect, useRef, useState } from "react";

interface SpeechRecognitionInstance extends EventTarget {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  maxAlternatives: number;
  onstart: (() => void) | null;
  onresult: ((event: { results: SpeechRecognitionResultList }) => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
  abort(): void;
}

type SpeechRecognitionHook = {
  start: () => void;
  stop: () => void;
  isListening: boolean;
  transcript: string;
  interimTranscript: string;
  isSupported: boolean;
  error: string | null;
};

const SpeechRecognitionAPI =
  typeof window !== "undefined"
    ? ((window as unknown as Record<string, unknown>).SpeechRecognition ??
      (window as unknown as Record<string, unknown>).webkitSpeechRecognition) as (new () => SpeechRecognitionInstance) | undefined
    : undefined;

export function useSpeechRecognition(): SpeechRecognitionHook {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [interimTranscript, setInterimTranscript] = useState("");
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);
  const isSupported = SpeechRecognitionAPI != null;

  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try { recognitionRef.current.abort(); } catch { /* cleanup */ }
      }
    };
  }, []);

  const start = useCallback(() => {
    if (!SpeechRecognitionAPI) {
      setError("Speech recognition not supported in this browser");
      return;
    }

    setError(null);
    setTranscript("");
    setInterimTranscript("");

    const recognition = new SpeechRecognitionAPI!();
    recognition.lang = "en-IN";
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => setIsListening(true);

    recognition.onresult = (event) => {
      let interim = "";
      let finalText = "";
      for (let i = 0; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          finalText += result[0].transcript;
        } else {
          interim += result[0].transcript;
        }
      }
      if (finalText) setTranscript(finalText);
      setInterimTranscript(interim);
    };

    recognition.onerror = (event) => {
      const code = event.error;
      if (code === "not-allowed") {
        setError("Microphone permission denied. Please allow microphone access.");
      } else if (code === "no-speech") {
        setError("No speech detected. Please try again.");
      } else if (code === "network") {
        setError("Network error during speech recognition.");
      } else if (code === "aborted") {
        // User-initiated stop — not an error
      } else {
        setError(`Speech recognition error: ${code}`);
      }
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
      setInterimTranscript("");
    };

    recognitionRef.current = recognition;

    try {
      recognition.start();
    } catch {
      setError("Failed to start speech recognition.");
    }
  }, []);

  const stop = useCallback(() => {
    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch { /* already stopped */ }
    }
    setIsListening(false);
  }, []);

  return { start, stop, isListening, transcript, interimTranscript, isSupported, error };
}
