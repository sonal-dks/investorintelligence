-- Phase 09: Supabase persistence for LLM-first pulse generation
-- Adds explicit LLM vs deterministic comparison fields and keyword storage.

create table if not exists public.weekly_pulse (
  id uuid primary key default gen_random_uuid(),
  week_start date not null unique,
  overall_rating numeric(3,2),
  total_reviews integer default 0,
  positive_count integer default 0,
  neutral_count integer default 0,
  negative_count integer default 0,
  summary_text text,
  action_items jsonb default '[]'::jsonb,
  themes jsonb default '[]'::jsonb,
  generated_at timestamptz not null default now()
);

alter table public.weekly_pulse
  add column if not exists llm_themes jsonb default '[]'::jsonb,
  add column if not exists deterministic_themes jsonb default '[]'::jsonb,
  add column if not exists llm_summary_text text,
  add column if not exists deterministic_summary_text text,
  add column if not exists model_path text,
  add column if not exists model_used text,
  add column if not exists deterministic_algorithm text;

create index if not exists idx_weekly_pulse_week_start on public.weekly_pulse (week_start desc);
create index if not exists idx_weekly_pulse_generated_at on public.weekly_pulse (generated_at desc);

create table if not exists public.review_keywords (
  id uuid primary key default gen_random_uuid(),
  keyword text not null,
  week_start date not null,
  mention_count integer default 0,
  wow_change_pct numeric(6,2),
  unique (keyword, week_start)
);

create index if not exists idx_review_keywords_week_start on public.review_keywords (week_start desc);

alter table public.weekly_pulse enable row level security;
alter table public.review_keywords enable row level security;

do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'weekly_pulse' and policyname = 'Public read weekly_pulse'
  ) then
    create policy "Public read weekly_pulse"
      on public.weekly_pulse for select
      using (true);
  end if;
end
$$;

do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'review_keywords' and policyname = 'Public read review_keywords'
  ) then
    create policy "Public read review_keywords"
      on public.review_keywords for select
      using (true);
  end if;
end
$$;
