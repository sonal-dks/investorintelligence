create table if not exists public.evaluation_runs (
  id uuid primary key,
  run_type text not null check (run_type in ('scheduled', 'manual')),
  rag_faithfulness_pct numeric(5,2),
  rag_relevance_pct numeric(5,2),
  safety_pass_pct numeric(5,2),
  pulse_word_count integer,
  action_items_count integer,
  total_cases integer,
  passed_cases integer,
  started_at timestamptz not null default now(),
  completed_at timestamptz
);

create table if not exists public.evaluation_cases (
  id uuid primary key,
  run_id uuid not null references public.evaluation_runs(id) on delete cascade,
  case_type text not null check (case_type in ('rag_faithfulness', 'rag_relevance', 'safety', 'ux')),
  query text,
  expected_behavior text,
  actual_output text,
  passed boolean,
  judge_reasoning text,
  created_at timestamptz not null default now()
);

create index if not exists idx_evaluation_runs_started_at on public.evaluation_runs (started_at desc);
create index if not exists idx_evaluation_cases_run_id on public.evaluation_cases (run_id);
create index if not exists idx_evaluation_cases_type on public.evaluation_cases (case_type);

alter table public.evaluation_runs enable row level security;
alter table public.evaluation_cases enable row level security;

do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'evaluation_runs' and policyname = 'Public read evaluation_runs'
  ) then
    create policy "Public read evaluation_runs"
      on public.evaluation_runs for select
      using (true);
  end if;
end $$;

do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'evaluation_cases' and policyname = 'Public read evaluation_cases'
  ) then
    create policy "Public read evaluation_cases"
      on public.evaluation_cases for select
      using (true);
  end if;
end $$;
