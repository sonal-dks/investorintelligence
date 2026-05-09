export type UserRole = "investor" | "admin";

export type UserProfile = {
  id: string;
  user_id: string;
  email: string | null;
  display_name: string | null;
  role: UserRole;
  first_login_complete: boolean;
  created_at: string;
  updated_at: string;
};

export type KPIItem = {
  value: number;
  trend_pct: number;
  trend_direction: "up" | "down" | "neutral" | "new";
};

export type KPIResponse = {
  login_sessions: KPIItem;
  chatbot_sessions: KPIItem;
  voice_sessions: KPIItem;
  bookings: KPIItem;
};

export type BookingSummary = {
  confirmed: number;
  cancelled: number;
  rescheduled: number;
  total: number;
};

export type FundRow = {
  fund_name: string;
  category: string;
  nav: number;
  nav_date: string | null;
};

export type FundStrip = {
  funds: FundRow[];
  last_scraped_at: string | null;
};

export type PulsePreview = {
  overall_rating: number;
  new_reviews_this_week: number;
  sentiment_summary: string;
};

export type DashboardOverviewKPI = {
  key: string;
  label: string;
  value: number;
  subtitle: string;
};

export type DashboardStockItem = {
  symbol: string;
  name: string;
  price: number;
  change_pct: number;
};

export type DashboardOverview = {
  role: UserRole;
  kpis: DashboardOverviewKPI[];
  stocks: DashboardStockItem[];
  booking_summary: BookingSummary;
  pulse: {
    overall_rating: number;
    new_reviews_this_week: number;
    top_keyword: string;
    top_keyword_mentions: number;
    last_pulse_label: string;
  };
};
