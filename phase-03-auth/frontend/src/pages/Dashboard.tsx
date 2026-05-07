import { Link } from "react-router-dom";

import { useAuthActions } from "../providers/AuthProvider";
import { useAuthStore } from "../stores/auth-store";

export function DashboardPage() {
  const profile = useAuthStore((s) => s.profile);
  const { signOut } = useAuthActions();

  return (
    <div className="min-h-screen bg-neutral-950 px-6 py-10">
      <header className="mx-auto flex max-w-3xl items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-white">Dashboard</h1>
          <p className="text-sm text-neutral-400">
            Signed in as {profile?.display_name ?? profile?.email ?? "user"} ({profile?.role})
          </p>
        </div>
        <div className="flex gap-3">
          {profile?.role === "admin" ? (
            <Link
              to="/admin"
              className="rounded-lg border border-neutral-600 px-3 py-2 text-sm text-neutral-200 hover:bg-neutral-800"
            >
              Admin area
            </Link>
          ) : null}
          <button
            type="button"
            onClick={() => void signOut()}
            className="rounded-lg bg-neutral-800 px-3 py-2 text-sm text-neutral-100 hover:bg-neutral-700"
          >
            Sign out
          </button>
        </div>
      </header>
      <main className="mx-auto mt-10 max-w-3xl rounded-2xl border border-neutral-800 bg-neutral-900/30 p-8">
        <p className="text-neutral-300">
          Phase 03 shell only — KPIs and navigation arrive in Phase 04. Session and role are wired;
          refresh the page to confirm persistence.
        </p>
      </main>
    </div>
  );
}
