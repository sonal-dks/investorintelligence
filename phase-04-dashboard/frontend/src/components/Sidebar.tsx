import { Bot, CalendarCheck2, Gauge, LayoutDashboard, LogOut, Mic, Search, ShieldCheck } from "lucide-react";
import { Link, useLocation } from "react-router-dom";

import { useAuthActions } from "../providers/AuthProvider";
import { useUIStore } from "../stores/ui-store";
import type { UserRole } from "../types";

type Props = {
  role: UserRole;
};

type NavItem = {
  to: string;
  label: string;
  icon: typeof LayoutDashboard;
};

const commonItems: NavItem[] = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/smart-search", label: "Smart Search", icon: Bot },
  { to: "/weekly-pulse", label: "Weekly Pulse", icon: Gauge },
  { to: "/voice-agent", label: "Voice Agent", icon: Mic },
  { to: "/bookings", label: "Bookings", icon: CalendarCheck2 },
  { to: "/explorer", label: "Fund Explorer", icon: Search },
];

const adminItems: NavItem[] = [
  { to: "/admin", label: "Approval Center", icon: ShieldCheck },
  { to: "/evaluation-suite", label: "Evaluation Suite", icon: Gauge },
];

export function Sidebar({ role }: Props) {
  const { pathname } = useLocation();
  const { signOut } = useAuthActions();
  const setSidebarCollapsed = useUIStore((s) => s.setSidebarCollapsed);
  const items = role === "admin" ? [...commonItems, ...adminItems] : commonItems;

  const handleNav = () => {
    if (typeof window !== "undefined" && window.matchMedia("(max-width: 767px)").matches) {
      setSidebarCollapsed(true);
    }
  };

  return (
    <aside className="flex flex-col w-64 shrink-0 bg-sidebar border-r border-sidebar-border h-screen">
      <div className="px-5 py-5 border-b border-sidebar-border">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
            <span className="text-primary-foreground text-xs font-bold">IO</span>
          </div>
          <div>
            <p className="text-sm font-semibold text-sidebar-foreground">Investor Ops</p>
            <p className="text-xs text-muted-foreground">Intelligence Suite</p>
          </div>
        </div>
      </div>
      <div className="p-3">
        <p className="px-3 mb-2 text-xs font-medium text-muted-foreground uppercase tracking-wider">Navigation</p>
        <nav className="space-y-1">
          {items.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.to || pathname.startsWith(`${item.to}/`);
            const className = active
              ? "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium bg-primary text-primary-foreground shadow-sm"
              : "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-all duration-150";

            return (
              <Link key={item.label} to={item.to} className={className} onClick={handleNav}>
                <Icon className="w-4 h-4 shrink-0" />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>
      <div className="mt-auto p-3">
        <button
          type="button"
          onClick={() => void signOut()}
          className="w-full flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm"
        >
          <LogOut className="w-4 h-4" />
          Sign out
        </button>
      </div>
    </aside>
  );
}
