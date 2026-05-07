import { Navigate, Outlet } from "react-router-dom";

import { useAuthStore } from "../stores/auth-store";

export function ProtectedLayout() {
  const session = useAuthStore((s) => s.session);
  const profile = useAuthStore((s) => s.profile);
  const isLoading = useAuthStore((s) => s.isLoading);

  if (isLoading) {
    return <div className="flex min-h-screen items-center justify-center text-muted-foreground">Loading…</div>;
  }
  if (!session) return <Navigate to="/login" replace />;
  if (!profile) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-2 text-muted-foreground">
        <p>Finishing sign-in…</p>
        <button type="button" onClick={() => window.location.reload()} className="rounded-lg border border-border px-3 py-1.5 text-sm">
          Reload
        </button>
      </div>
    );
  }
  return <Outlet />;
}
