import type { ReactNode } from "react";

import { useAuthStore } from "../stores/auth-store";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";

type Props = {
  pageTitle: string;
  children: ReactNode;
};

export function AppShell({ pageTitle, children }: Props) {
  const profile = useAuthStore((s) => s.profile);
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar role={profile?.role ?? "investor"} />
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <Topbar pageTitle={pageTitle} displayName={profile?.display_name ?? profile?.email ?? "User"} />
        <main className="flex-1 overflow-y-auto">
          <div className="max-w-6xl mx-auto px-6 py-8">{children}</div>
        </main>
      </div>
    </div>
  );
}
