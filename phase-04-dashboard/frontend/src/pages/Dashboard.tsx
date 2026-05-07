import { Bot, CalendarDays, KeyRound, Mic } from "lucide-react";

import { AppShell } from "../components/AppShell";
import { BookingSummary } from "../components/BookingSummary";
import { FundStrip } from "../components/FundStrip";
import { KPICard } from "../components/KPICard";
import { PulsePreview } from "../components/PulsePreview";
import { useBookings, useFundStrip, useKPIs, usePulsePreview } from "../hooks/useDashboard";

export function DashboardPage() {
  const kpis = useKPIs();
  const bookings = useBookings();
  const funds = useFundStrip();
  const pulse = usePulsePreview();
  const k = kpis.data;

  return (
    <AppShell pageTitle="Dashboard">
      <div className="space-y-6">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <KPICard
            label="Login Sessions"
            data={k?.login_sessions ?? { value: 0, trend_pct: 0, trend_direction: "neutral" }}
            icon={<KeyRound className="w-5 h-5" />}
            iconClass="bg-blue-50 text-blue-600"
          />
          <KPICard
            label="Chatbot Sessions"
            data={k?.chatbot_sessions ?? { value: 0, trend_pct: 0, trend_direction: "neutral" }}
            icon={<Bot className="w-5 h-5" />}
            iconClass="bg-emerald-50 text-emerald-600"
          />
          <KPICard
            label="Voice Sessions"
            data={k?.voice_sessions ?? { value: 0, trend_pct: 0, trend_direction: "neutral" }}
            icon={<Mic className="w-5 h-5" />}
            iconClass="bg-amber-50 text-amber-600"
          />
          <KPICard
            label="Bookings"
            data={k?.bookings ?? { value: 0, trend_pct: 0, trend_direction: "neutral" }}
            icon={<CalendarDays className="w-5 h-5" />}
            iconClass="bg-sky-50 text-sky-600"
          />
        </div>

        <FundStrip data={funds.data} isLoading={funds.isLoading} isError={funds.isError} />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <BookingSummary data={bookings.data} isLoading={bookings.isLoading} isError={bookings.isError} />
          <PulsePreview data={pulse.data} isLoading={pulse.isLoading} isError={pulse.isError} />
        </div>
      </div>
    </AppShell>
  );
}
