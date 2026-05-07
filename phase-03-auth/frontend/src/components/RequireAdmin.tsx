import { Navigate, Outlet } from "react-router-dom";

import { useAuthStore } from "../stores/auth-store";

export function RequireAdmin() {
  const role = useAuthStore((s) => s.profile?.role);
  if (role !== "admin") {
    return <Navigate to="/dashboard" replace />;
  }
  return <Outlet />;
}
