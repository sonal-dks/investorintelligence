import { Navigate } from "react-router-dom";

import { supabase } from "../lib/supabase";
import { PENDING_ROLE_KEY, useAuthStore } from "../stores/auth-store";
import { useState } from "react";
import { RoleSelector } from "../components/RoleSelector";
import type { UserRole } from "../types";

export function LoginPage() {
  const session = useAuthStore((s) => s.session);
  const profile = useAuthStore((s) => s.profile);
  const isLoading = useAuthStore((s) => s.isLoading);
  const [role, setRole] = useState<UserRole>("investor");

  if (session && profile) return <Navigate to="/dashboard" replace />;

  async function signIn() {
    localStorage.setItem(PENDING_ROLE_KEY, role);
    await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: `${window.location.origin}/login` },
    });
  }

  if (isLoading && session && !profile) {
    return (
      <div className="flex min-h-screen items-center justify-center text-muted-foreground">
        Completing sign-in…
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <div className="w-full max-w-lg rounded-xl border border-border bg-card p-6">
        <h1 className="text-xl font-bold text-foreground">Sign in</h1>
        <p className="text-sm text-muted-foreground mt-0.5">Select role and continue with Google.</p>
        <div className="mt-6">
          <RoleSelector value={role} onChange={setRole} />
        </div>
        <button
          type="button"
          onClick={() => void signIn()}
          className="mt-6 h-11 w-full rounded-lg bg-primary text-primary-foreground text-sm font-medium"
        >
          Sign in with Google
        </button>
      </div>
    </div>
  );
}
