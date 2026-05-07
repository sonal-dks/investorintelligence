import type { Session, User } from "@supabase/supabase-js";
import { create } from "zustand";

import type { UserProfile } from "../types";

type AuthState = {
  session: Session | null;
  user: User | null;
  profile: UserProfile | null;
  isLoading: boolean;
  oauthError: string | null;
  setFromSession: (session: Session | null) => void;
  setProfile: (profile: UserProfile | null) => void;
  setLoading: (v: boolean) => void;
  setOAuthError: (e: string | null) => void;
  reset: () => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  session: null,
  user: null,
  profile: null,
  isLoading: true,
  oauthError: null,
  setFromSession: (session) => set({ session, user: session?.user ?? null }),
  setProfile: (profile) => set({ profile }),
  setLoading: (isLoading) => set({ isLoading }),
  setOAuthError: (oauthError) => set({ oauthError }),
  reset: () =>
    set({
      session: null,
      user: null,
      profile: null,
      isLoading: false,
      oauthError: null,
    }),
}));

export const PENDING_ROLE_KEY = "phase03_pending_role";
