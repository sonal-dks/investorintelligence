import { useCallback, useRef, useState } from "react";

import { useAuthStore } from "../stores/auth-store";
import { fetchTTSAudio } from "../lib/api";

type TTSHook = {
  speak: (text: string) => void;
  stop: () => void;
  isSpeaking: boolean;
};

export function useTTS(): TTSHook {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const session = useAuthStore((s) => s.session);

  const stopCurrent = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.src = "";
      audioRef.current = null;
    }
    if (typeof speechSynthesis !== "undefined") {
      speechSynthesis.cancel();
    }
    utteranceRef.current = null;
    setIsSpeaking(false);
  }, []);

  const speakWithBrowserTTS = useCallback(
    (text: string) => {
      if (typeof speechSynthesis === "undefined") return false;

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = "en-IN";
      utterance.rate = 0.95;
      utterance.pitch = 1;

      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);

      utteranceRef.current = utterance;
      speechSynthesis.speak(utterance);
      return true;
    },
    [],
  );

  const speakWithEdgeTTS = useCallback(
    async (text: string) => {
      const accessToken = session?.access_token;
      if (!accessToken) return false;

      try {
        const blob = await fetchTTSAudio(accessToken, text);
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        audioRef.current = audio;

        audio.onplay = () => setIsSpeaking(true);
        audio.onended = () => {
          setIsSpeaking(false);
          URL.revokeObjectURL(url);
        };
        audio.onerror = () => {
          setIsSpeaking(false);
          URL.revokeObjectURL(url);
        };

        await audio.play();
        return true;
      } catch {
        return false;
      }
    },
    [session],
  );

  const speak = useCallback(
    (text: string) => {
      stopCurrent();

      void (async () => {
        const edgeOk = await speakWithEdgeTTS(text);
        if (!edgeOk) {
          speakWithBrowserTTS(text);
        }
      })();
    },
    [stopCurrent, speakWithEdgeTTS, speakWithBrowserTTS],
  );

  return { speak, stop: stopCurrent, isSpeaking };
}
