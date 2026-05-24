-- Phase 09: verbatim user quotes + ranked top themes for ops contract / UI.

alter table public.weekly_pulse
  add column if not exists top_themes jsonb default '[]'::jsonb,
  add column if not exists user_quotes jsonb default '[]'::jsonb;
