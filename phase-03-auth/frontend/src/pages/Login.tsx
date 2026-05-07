import { useEffect, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";

import { RoleSelector } from "../components/RoleSelector";
import { supabase } from "../lib/supabase";
import { PENDING_ROLE_KEY, useAuthStore } from "../stores/auth-store";
import type { UserRole } from "../types";

export function LoginPage() {
  const navigate = useNavigate();
  const session = useAuthStore((s) => s.session);
  const profile = useAuthStore((s) => s.profile);
  const isLoading = useAuthStore((s) => s.isLoading);
  const oauthError = useAuthStore((s) => s.oauthError);
  const setOAuthError = useAuthStore((s) => s.setOAuthError);

  const [role, setRole] = useState<UserRole>("investor");
  const [busy, setBusy] = useState(false);
  const [hint, setHint] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoading && session && profile) {
      navigate("/dashboard", { replace: true });
    }
  }, [isLoading, session, profile, navigate]);

  async function onGoogleClick() {
    setOAuthError(null);
    setHint(null);
    localStorage.setItem(PENDING_ROLE_KEY, role);
    setBusy(true);
    const redirectTo = `${window.location.origin}/`;
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo },
    });
    setBusy(false);
    if (error) {
      setOAuthError(error.message);
      setHint(
        "If the browser blocked the redirect, allow pop-ups or try again. You can also check Google OAuth configuration in Supabase.",
      );
    }
  }

  if (!isLoading && session && profile) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-4">
      <div className="w-full max-w-lg rounded-2xl border border-neutral-800 bg-neutral-900/40 p-8 shadow-2xl">
        <h1 className="text-2xl font-bold tracking-tight text-white">Sign in</h1>
        <p className="mt-2 text-sm text-neutral-400">
          Choose your role, then continue with Google. Role is stored with your profile (not in the
          JWT).
        </p>
        <div className="mt-8">
          <RoleSelector value={role} onChange={setRole} disabled={busy} />
        </div>
        <button
          type="button"
          onClick={onGoogleClick}
          disabled={busy}
          className="mt-8 flex w-full items-center justify-center gap-2 rounded-xl bg-white py-3 text-sm font-semibold text-neutral-900 hover:bg-neutral-100 disabled:opacity-60"
        >
          {busy ? "Redirecting…" : "Sign in with Google"}
        </button>
        {oauthError ? (
          <p className="mt-4 text-sm text-red-400" role="alert">
            {oauthError}
          </p>
        ) : null}
        {hint ? <p className="mt-2 text-sm text-amber-200/90">{hint}</p> : null}
        <p className="mt-6 text-center text-xs text-neutral-500">
          Demo: configure Google provider + redirect URLs in Supabase before live OAuth works.
        </p>
      </div>
    </div>
  );
}
