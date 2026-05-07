import { useState } from "react";

import { supabase } from "../lib/supabase";
import { PENDING_ROLE_KEY } from "../stores/auth-store";
import type { UserRole } from "../types";

export function LoginPage() {
  const [role, setRole] = useState<UserRole>("investor");
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async () => {
    setIsLoading(true);
    localStorage.setItem(PENDING_ROLE_KEY, role);
    await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: `${window.location.origin}/smart-search` },
    });
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="w-full max-w-sm space-y-6 p-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Investor Ops</h1>
          <p className="text-sm text-muted-foreground mt-1">Intelligence Suite</p>
        </div>

        <div className="space-y-3">
          {(["investor", "admin"] as const).map((r) => (
            <button
              key={r}
              type="button"
              onClick={() => setRole(r)}
              className={`w-full rounded-xl border px-4 py-3 text-sm text-left transition-all ${
                role === r
                  ? "border-primary bg-primary/5 font-medium"
                  : "border-border hover:border-primary/30"
              }`}
            >
              {r === "investor" ? "Investor" : "Admin"}
            </button>
          ))}
        </div>

        <button
          type="button"
          onClick={() => void handleLogin()}
          disabled={isLoading}
          className="w-full rounded-xl bg-primary text-primary-foreground py-3 text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
        >
          {isLoading ? "Redirecting…" : "Sign in with Google"}
        </button>
      </div>
    </div>
  );
}
