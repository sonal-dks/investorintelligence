import { Bell, Wifi } from "lucide-react";

type Props = {
  pageTitle: string;
  displayName: string;
};

export function Topbar({ pageTitle, displayName }: Props) {
  return (
    <header className="h-16 bg-background border-b border-border flex items-center justify-between px-6 shrink-0 sticky top-0 z-30">
      <div className="flex items-center gap-3">
        <h1 className="text-sm font-semibold text-foreground">{pageTitle}</h1>
        <span className="bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-medium flex items-center gap-1.5 rounded-full px-2.5 py-1">
          <Wifi className="w-3 h-3" />
          Active
        </span>
      </div>
      <div className="flex items-center gap-3">
        <span className="text-xs text-muted-foreground">Live dashboard</span>
        <button type="button" className="rounded-lg border border-border p-2">
          <Bell className="w-4 h-4" />
        </button>
        <div className="rounded-full bg-muted px-3 py-1 text-xs font-medium">{displayName}</div>
      </div>
    </header>
  );
}
