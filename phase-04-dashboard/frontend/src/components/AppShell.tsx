import type { ReactNode } from "react";

import { useAuthStore } from "../stores/auth-store";
import { useUIStore } from "../stores/ui-store";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";

type Props = {
  pageTitle: string;
  children: ReactNode;
  /** Use full-width main (e.g. bookings table). */
  contentMaxWidth?: "default" | "full";
};

export function AppShell({ pageTitle, children, contentMaxWidth = "default" }: Props) {
  const profile = useAuthStore((s) => s.profile);
  const sidebarCollapsed = useUIStore((s) => s.sidebarCollapsed);
  const setSidebarCollapsed = useUIStore((s) => s.setSidebarCollapsed);

  const mainInnerClass =
    contentMaxWidth === "full" ? "w-full px-4 py-6" : "max-w-6xl mx-auto px-6 py-8";

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {!sidebarCollapsed && (
        <>
          <button
            type="button"
            aria-label="Close menu"
            className="fixed inset-0 z-40 bg-black/40 md:hidden"
            onClick={() => setSidebarCollapsed(true)}
          />
          <div className="fixed inset-y-0 left-0 z-50 flex shrink-0 md:static md:z-0">
            <Sidebar role={profile?.role ?? "investor"} />
          </div>
        </>
      )}
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <Topbar pageTitle={pageTitle} displayName={profile?.display_name ?? profile?.email ?? "User"} />
        <main className="flex-1 overflow-y-auto">
          <div className={mainInnerClass}>{children}</div>
        </main>
      </div>
    </div>
  );
}
