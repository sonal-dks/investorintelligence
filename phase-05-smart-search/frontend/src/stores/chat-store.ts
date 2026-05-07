import { create } from "zustand";

type ChatUIState = {
  activeSessionId: string | null;
  isSending: boolean;
  setActiveSession: (id: string | null) => void;
  setSending: (v: boolean) => void;
};

export const useChatStore = create<ChatUIState>((set) => ({
  activeSessionId: null,
  isSending: false,
  setActiveSession: (activeSessionId) => set({ activeSessionId }),
  setSending: (isSending) => set({ isSending }),
}));
