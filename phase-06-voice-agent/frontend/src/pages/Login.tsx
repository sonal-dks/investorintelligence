import { useState } from "react";

import { supabase } from "../lib/supabase";
import { PENDING_ROLE_KEY } from "../stores/auth-store";
import type { UserRole } from "../types";

export function LoginPage() {
  const [role, setRole] = useState<UserRole>("investor");
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    setLoading(true);
    localStorage.setItem(PENDING_ROLE_KEY, role);
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: `${window.location.origin}/voice-agent` },
    });
    if (error) setLoading(false);
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="w-full max-w-sm space-y-6 rounded-xl border border-border bg-card p-8 shadow-sm">
        <div className="text-center">
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Investor Ops</h1>
          <p className="mt-1 text-sm text-muted-foreground">Voice Agent — Sign in to continue</p>
        </div>

        <div className="space-y-2">
          <p className="text-sm font-medium text-foreground">Select your role</p>
          <div className="grid grid-cols-2 gap-2">
            {(["investor", "admin"] as const).map((r) => (
              <button
                key={r}
                type="button"
                onClick={() => setRole(r)}
                className={`rounded-lg border px-3 py-2 text-sm font-medium capitalize transition-colors ${
                  role === r
                    ? "border-primary bg-primary text-primary-foreground"
                    : "border-border bg-background text-foreground hover:bg-muted"
                }`}
              >
                {r}
              </button>
            ))}
          </div>
        </div>

        <button
          type="button"
          onClick={handleLogin}
          disabled={loading}
          className="w-full rounded-lg bg-primary py-2.5 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
        >
          {loading ? "Redirecting…" : "Sign in with Google"}
        </button>
      </div>
    </div>
  );
}
