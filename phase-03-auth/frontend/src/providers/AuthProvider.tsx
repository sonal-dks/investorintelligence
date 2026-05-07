import type { Session } from "@supabase/supabase-js";
import { useQueryClient } from "@tanstack/react-query";
import { type ReactNode, createContext, useCallback, useContext, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";

import { fetchMe, upsertProfile } from "../lib/api";
import { supabase } from "../lib/supabase";
import { PENDING_ROLE_KEY, useAuthStore } from "../stores/auth-store";
import type { UserProfile } from "../types";

type AuthContextValue = {
  signOut: () => Promise<void>;
  refreshProfile: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuthActions() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuthActions must be used within AuthProvider");
  return ctx;
}

async function loadOrCreateProfile(session: Session): Promise<UserProfile> {
  const token = session.access_token;
  let { res, body } = await fetchMe(token);

  if (res.status === 404) {
    const pending = localStorage.getItem(PENDING_ROLE_KEY) as "investor" | "admin" | null;
    const role = pending === "admin" || pending === "investor" ? pending : "investor";
    const meta = session.user.user_metadata as Record<string, string | undefined> | undefined;
    const displayName = meta?.full_name ?? meta?.name ?? meta?.display_name ?? null;
    const post = await upsertProfile(token, {
      role,
      email: session.user.email ?? null,
      display_name: displayName,
      first_login_complete: false,
    });
    if (!post.res.ok) {
      const errText = await post.res.clone().text();
      throw new Error(errText || "Could not create profile");
    }
    localStorage.removeItem(PENDING_ROLE_KEY);
    ({ res, body } = await fetchMe(token));
  }

  if (!res.ok || !body) {
    throw new Error("Could not load profile");
  }
  return body;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const navRef = useRef(navigate);
  navRef.current = navigate;

  const setFromSession = useAuthStore((s) => s.setFromSession);
  const setProfile = useAuthStore((s) => s.setProfile);
  const setLoading = useAuthStore((s) => s.setLoading);
  const reset = useAuthStore((s) => s.reset);
  const setOAuthError = useAuthStore((s) => s.setOAuthError);

  const refreshProfile = useCallback(async () => {
    const {
      data: { session },
    } = await supabase.auth.getSession();
    if (!session) {
      setProfile(null);
      return;
    }
    const profile = await loadOrCreateProfile(session);
    setProfile(profile);
    await queryClient.invalidateQueries({ queryKey: ["profile"] });
  }, [queryClient, setProfile]);

  const signOut = useCallback(async () => {
    await supabase.auth.signOut();
    reset();
    queryClient.clear();
    navRef.current("/login", { replace: true });
  }, [queryClient, reset]);

  useEffect(() => {
    let cancelled = false;

    async function syncSession(session: Session | null) {
      setFromSession(session);
      if (!session) {
        setProfile(null);
        setLoading(false);
        return;
      }
      setLoading(true);
      try {
        const profile = await loadOrCreateProfile(session);
        if (!cancelled) setProfile(profile);
      } catch {
        if (!cancelled) {
          setProfile(null);
          setOAuthError("Session or profile sync failed. Try signing in again.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (event, session) => {
      if (cancelled) return;
      if (event === "SIGNED_OUT" || !session) {
        reset();
        setLoading(false);
        navRef.current("/login", { replace: true });
        return;
      }
      if (
        event === "SIGNED_IN" ||
        event === "INITIAL_SESSION" ||
        event === "TOKEN_REFRESHED" ||
        event === "USER_UPDATED"
      ) {
        await syncSession(session);
      }
    });

    return () => {
      cancelled = true;
      subscription.unsubscribe();
    };
  }, [reset, setFromSession, setLoading, setProfile, setOAuthError]);

  return (
    <AuthContext.Provider value={{ signOut, refreshProfile }}>{children}</AuthContext.Provider>
  );
}
