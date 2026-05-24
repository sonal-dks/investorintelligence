-- Phase 09: grouped-theme judge scoring + weekly notes log

alter table public.weekly_pulse
  add column if not exists judge_overall_score numeric(6,2) default 0,
  add column if not exists judge_metrics jsonb default '{}'::jsonb,
  add column if not exists judge_rationale text;

create table if not exists public.weekly_pulse_notes (
  id uuid primary key default gen_random_uuid(),
  date date not null,
  weekly_pulse text,
  fee_scenario text,
  explanation_bullets jsonb default '[]'::jsonb,
  source_links jsonb default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_weekly_pulse_notes_date on public.weekly_pulse_notes (date desc);

alter table public.weekly_pulse_notes enable row level security;

do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'weekly_pulse_notes' and policyname = 'Public read weekly_pulse_notes'
  ) then
    create policy "Public read weekly_pulse_notes"
      on public.weekly_pulse_notes for select
      using (true);
  end if;
end
$$;
