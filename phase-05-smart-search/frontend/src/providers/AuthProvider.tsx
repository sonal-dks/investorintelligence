import type { Session } from "@supabase/supabase-js";
import { type ReactNode, createContext, useContext, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";

import { supabase } from "../lib/supabase";
import { PENDING_ROLE_KEY, useAuthStore } from "../stores/auth-store";
import type { UserProfile, UserRole } from "../types";

type AuthContextValue = {
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

function mapProfile(row: Record<string, unknown>): UserProfile {
  return {
    id: String(row.id),
    user_id: String(row.user_id),
    email: (row.email as string | null) ?? null,
    display_name: (row.display_name as string | null) ?? null,
    role: row.role === "admin" ? "admin" : "investor",
    first_login_complete: Boolean(row.first_login_complete),
    created_at: String(row.created_at),
    updated_at: String(row.updated_at),
  };
}

function fallbackProfileFromSession(session: Session): UserProfile {
  const pending = localStorage.getItem(PENDING_ROLE_KEY);
  const role: UserRole = pending === "admin" ? "admin" : "investor";
  const nowIso = new Date().toISOString();
  return {
    id: session.user.id,
    user_id: session.user.id,
    email: session.user.email ?? null,
    display_name: (session.user.user_metadata?.full_name as string | undefined) ?? null,
    role,
    first_login_complete: true,
    created_at: nowIso,
    updated_at: nowIso,
  };
}

async function ensureProfile(session: Session): Promise<UserProfile> {
  const userId = session.user.id;
  const { data, error } = await supabase.from("user_profiles").select("*").eq("user_id", userId).maybeSingle();
  if (error) return fallbackProfileFromSession(session);
  if (data) return mapProfile(data);

  const pending = localStorage.getItem(PENDING_ROLE_KEY);
  const role: UserRole = pending === "admin" ? "admin" : "investor";
  const inserted = await supabase
    .from("user_profiles")
    .insert({
      user_id: userId,
      role,
      email: session.user.email ?? null,
      display_name: (session.user.user_metadata?.full_name as string | undefined) ?? null,
      first_login_complete: true,
    })
    .select("*")
    .maybeSingle();
  if (inserted.error || !inserted.data) return fallbackProfileFromSession(session);
  localStorage.removeItem(PENDING_ROLE_KEY);
  return mapProfile(inserted.data);
}

export function useAuthActions() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuthActions must be used within AuthProvider");
  return ctx;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const navRef = useRef(navigate);
  navRef.current = navigate;
  const setFromSession = useAuthStore((s) => s.setFromSession);
  const setProfile = useAuthStore((s) => s.setProfile);
  const setLoading = useAuthStore((s) => s.setLoading);
  const reset = useAuthStore((s) => s.reset);

  useEffect(() => {
    let cancelled = false;
    const handoffSessionFromUrl = async () => {
      const url = new URL(window.location.href);
      const accessToken = url.searchParams.get("access_token");
      const refreshToken = url.searchParams.get("refresh_token");
      if (!accessToken || !refreshToken) return;
      await supabase.auth.setSession({
        access_token: accessToken,
        refresh_token: refreshToken,
      });
      url.searchParams.delete("access_token");
      url.searchParams.delete("refresh_token");
      window.history.replaceState({}, document.title, `${url.pathname}${url.search}${url.hash}`);
    };

    const hardStopTimer = window.setTimeout(() => {
      if (cancelled) return;
      const activeSession = useAuthStore.getState().session;
      if (activeSession && !useAuthStore.getState().profile) {
        setProfile(fallbackProfileFromSession(activeSession));
      }
      setLoading(false);
    }, 8000);

    const run = async (session: Session | null) => {
      setFromSession(session);
      if (!session) {
        setProfile(null);
        setLoading(false);
        return;
      }
      setLoading(true);
      try {
        const profile = await ensureProfile(session);
        if (!cancelled) setProfile(profile);
      } catch {
        if (!cancelled) setProfile(fallbackProfileFromSession(session));
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    const { data } = supabase.auth.onAuthStateChange(async (_event, session) => {
      try {
        if (!session) {
          reset();
          navRef.current("/login", { replace: true });
          return;
        }
        await run(session);
      } catch {
        if (!cancelled) setLoading(false);
      }
    });
    void handoffSessionFromUrl()
      .then(() => supabase.auth.getSession())
      .then(({ data: d }) => run(d.session))
      .catch(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
      window.clearTimeout(hardStopTimer);
      data.subscription.unsubscribe();
    };
  }, [reset, setFromSession, setLoading, setProfile]);

  const signOut = async () => {
    await supabase.auth.signOut();
    reset();
    navRef.current("/login", { replace: true });
  };

  return <AuthContext.Provider value={{ signOut }}>{children}</AuthContext.Provider>;
}
