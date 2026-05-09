import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";

import { useAuthStore } from "../stores/auth-store";

type Props = {
  children: ReactNode;
};

export function AdminOnly({ children }: Props) {
  const role = useAuthStore((s) => s.profile?.role);
  if (role !== "admin") return <Navigate to="/dashboard" replace />;
  return children;
}
