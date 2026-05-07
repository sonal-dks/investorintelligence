import { create } from "zustand";

type VoiceMode = "voice" | "text";

type VoiceState = {
  mode: VoiceMode;
  isRecording: boolean;
  isSending: boolean;
  activeSessionId: string | null;
  setMode: (m: VoiceMode) => void;
  setRecording: (v: boolean) => void;
  setSending: (v: boolean) => void;
  setActiveSession: (id: string | null) => void;
};

export const useVoiceStore = create<VoiceState>((set) => ({
  mode: "voice",
  isRecording: false,
  isSending: false,
  activeSessionId: null,
  setMode: (mode) => set({ mode }),
  setRecording: (isRecording) => set({ isRecording }),
  setSending: (isSending) => set({ isSending }),
  setActiveSession: (activeSessionId) => set({ activeSessionId }),
}));
