import { Bell, PanelLeftClose, PanelLeftOpen, Wifi } from "lucide-react";

import { useUIStore } from "../stores/ui-store";

type Props = {
  pageTitle: string;
  displayName: string;
};

export function Topbar({ pageTitle, displayName }: Props) {
  const sidebarCollapsed = useUIStore((s) => s.sidebarCollapsed);
  const setSidebarCollapsed = useUIStore((s) => s.setSidebarCollapsed);

  return (
    <header className="h-16 bg-background border-b border-border flex items-center justify-between px-4 md:px-6 shrink-0 sticky top-0 z-30">
      <div className="flex items-center gap-2 md:gap-3 min-w-0">
        <button
          type="button"
          aria-expanded={!sidebarCollapsed}
          aria-label={sidebarCollapsed ? "Open sidebar" : "Close sidebar"}
          className="rounded-lg border border-border p-2 text-foreground hover:bg-muted shrink-0"
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
        >
          {sidebarCollapsed ? <PanelLeftOpen className="w-4 h-4" /> : <PanelLeftClose className="w-4 h-4" />}
        </button>
        <h1 className="text-sm font-semibold text-foreground truncate">{pageTitle}</h1>
        <span className="hidden sm:inline-flex bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-medium items-center gap-1.5 rounded-full px-2.5 py-1 shrink-0">
          <Wifi className="w-3 h-3" />
          Active
        </span>
      </div>
      <div className="flex items-center gap-2 md:gap-3 shrink-0">
        <span className="hidden md:inline text-xs text-muted-foreground">Live dashboard</span>
        <button type="button" className="rounded-lg border border-border p-2" aria-label="Notifications">
          <Bell className="w-4 h-4" />
        </button>
        <div className="rounded-full bg-muted px-2 md:px-3 py-1 text-xs font-medium max-w-[140px] truncate">{displayName}</div>
      </div>
    </header>
  );
}
