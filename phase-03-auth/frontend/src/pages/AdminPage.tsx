import { Link } from "react-router-dom";

import { useAuthActions } from "../providers/AuthProvider";

export function AdminPage() {
  const { signOut } = useAuthActions();

  return (
    <div className="min-h-screen bg-neutral-950 px-6 py-10">
      <header className="mx-auto flex max-w-3xl items-center justify-between">
        <h1 className="text-xl font-semibold text-amber-100">Admin</h1>
        <div className="flex gap-3">
          <Link
            to="/dashboard"
            className="rounded-lg border border-neutral-600 px-3 py-2 text-sm text-neutral-200 hover:bg-neutral-800"
          >
            Dashboard
          </Link>
          <button
            type="button"
            onClick={() => void signOut()}
            className="rounded-lg bg-neutral-800 px-3 py-2 text-sm text-neutral-100 hover:bg-neutral-700"
          >
            Sign out
          </button>
        </div>
      </header>
      <main className="mx-auto mt-10 max-w-3xl rounded-2xl border border-amber-900/40 bg-amber-950/20 p-8">
        <p className="text-neutral-200">
          Admin-only route. Investors are redirected to the dashboard (URL guard for Phase 03).
        </p>
      </main>
    </div>
  );
}
