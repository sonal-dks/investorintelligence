import { Bot, CalendarCheck2, Gauge, LayoutDashboard, LogOut, Mic, ShieldCheck } from "lucide-react";
import { Link, useLocation } from "react-router-dom";

import { supabase } from "../lib/supabase";
import { useAuthActions } from "../providers/AuthProvider";
import type { UserRole } from "../types";

type Props = {
  role: UserRole;
};

type NavItem = {
  to: string;
  label: string;
  icon: typeof LayoutDashboard;
  external?: boolean;
  handoffSession?: boolean;
};

const smartSearchUrl = import.meta.env.VITE_SMART_SEARCH_URL ?? "http://127.0.0.1:5173/smart-search";
const voiceAgentUrl = import.meta.env.VITE_VOICE_AGENT_URL ?? "http://127.0.0.1:5174/voice-agent";
const weeklyPulseUrl = import.meta.env.VITE_WEEKLY_PULSE_URL ?? "http://127.0.0.1:5176";
const bookingsUrl = import.meta.env.VITE_BOOKINGS_URL ?? "http://127.0.0.1:5177";

const commonItems: NavItem[] = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: smartSearchUrl, label: "Smart Search", icon: Bot, external: true, handoffSession: true },
  { to: weeklyPulseUrl, label: "Weekly Pulse", icon: Gauge, external: true, handoffSession: true },
  { to: voiceAgentUrl, label: "Voice Agent", icon: Mic, external: true, handoffSession: true },
  { to: bookingsUrl, label: "Bookings", icon: CalendarCheck2, external: true, handoffSession: true },
];

const adminItems: NavItem[] = [{ to: "/admin", label: "Approval Center", icon: ShieldCheck }];

export function Sidebar({ role }: Props) {
  const { pathname } = useLocation();
  const { signOut } = useAuthActions();
  const items = role === "admin" ? [...commonItems, ...adminItems] : commonItems;

  const handleSessionHandoffClick = async (event: React.MouseEvent<HTMLAnchorElement>, targetUrl: string) => {
    event.preventDefault();
    try {
      const { data } = await supabase.auth.getSession();
      const session = data.session;
      if (!session) {
        window.location.href = targetUrl;
        return;
      }
      const url = new URL(targetUrl);
      url.searchParams.set("access_token", session.access_token);
      url.searchParams.set("refresh_token", session.refresh_token);
      window.location.href = url.toString();
    } catch {
      window.location.href = targetUrl;
    }
  };

  return (
    <aside className="flex flex-col w-64 shrink-0 bg-sidebar border-r border-sidebar-border h-screen sticky top-0">
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
            const active = item.external ? false : pathname === item.to;
            const className = active
              ? "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium bg-primary text-primary-foreground shadow-sm"
              : "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-all duration-150";

            if (item.external) {
              return (
                <a
                  key={item.label}
                  href={item.to}
                  className={className}
                  onClick={item.handoffSession ? (event) => void handleSessionHandoffClick(event, item.to) : undefined}
                >
                  <Icon className="w-4 h-4 shrink-0" />
                  {item.label}
                </a>
              );
            }

            return (
              <Link key={item.label} to={item.to} className={className}>
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
