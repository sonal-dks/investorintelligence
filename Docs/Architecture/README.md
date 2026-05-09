# Investor Ops Intelligence Suite — Architecture Documentation

## Objective

This architecture pack defines the complete phased implementation plan for the Investor Ops Intelligence Suite. It covers 12 sequential phases from data ingestion through deployment, with full backend, frontend, and UI specifications per phase.

## Architecture Files

| File | Purpose |
|------|---------|
| [architecture.md](architecture.md) | Phase list, decisions, tradeoffs, scope, backend/frontend/UI per phase |
| [HLD.md](HLD.md) | High-level component maps, data flows, security, scalability per phase |
| [LLD.md](LLD.md) | APIs, schemas, modules, test plans, edge cases, expected outputs per phase |
| [Evals-Report.md](Evals-Report.md) | Golden dataset, adversarial tests, and evaluation scorecards |

## Phase Criteria Artifacts

Each phase has a dedicated edge-case and success-criteria file:

- `Docs/Architecture/Phase-Criteria/phase-01-edge-cases-success.md`
- `Docs/Architecture/Phase-Criteria/phase-02-edge-cases-success.md`
- `Docs/Architecture/Phase-Criteria/phase-03-edge-cases-success.md`
- `Docs/Architecture/Phase-Criteria/phase-04-edge-cases-success.md`
- `Docs/Architecture/Phase-Criteria/phase-05-edge-cases-success.md`
- `Docs/Architecture/Phase-Criteria/phase-06-edge-cases-success.md`
- `Docs/Architecture/Phase-Criteria/phase-07-edge-cases-success.md`
- `Docs/Architecture/Phase-Criteria/phase-08-edge-cases-success.md`
- `Docs/Architecture/Phase-Criteria/phase-09-edge-cases-success.md`
- `Docs/Architecture/Phase-Criteria/phase-10-edge-cases-success.md`
- `Docs/Architecture/Phase-Criteria/phase-11-edge-cases-success.md`
- `Docs/Architecture/Phase-Criteria/phase-12-edge-cases-success.md`

## Phase Index

| # | Phase | Depends On | Primary Scope |
|---|-------|-----------|---------------|
| 01 | Data Ingestion (Scraping Pipeline) | — | Backend |
| 02 | RAG Pipeline (Embeddings + Vector Store) | Phase 01 | Backend |
| 03 | Authentication + User Management | — | Backend + Frontend |
| 04 | Dashboard + App Shell | Phase 03 | Backend + Frontend |
| 05 | Smart Search (RAG Chatbot) | Phase 02, 03 | Backend + Frontend |
| 06 | Voice Agent | Phase 05 | Backend + Frontend |
| 07 | AI Intent Detection + Approval Center | Phase 05, 06 | Backend + Frontend |
| 08 | Google Calendar + Booking System | Phase 07 | Backend + Frontend |
| 09 | Weekly Pulse (Review Intelligence) | Phase 01 | Backend + Frontend |
| 10 | Mutual Fund Explorer | Phase 01 | Backend + Frontend |
| 11 | Evaluation Suite | Phase 05, 09 | Backend + Frontend |
| 12 | Assembly + Deployment | All prior phases | DevOps |

## Dependency Graph

```
Phase 01 (Data Ingestion)
├── Phase 02 (RAG Pipeline)
│   └── Phase 05 (Smart Search) ← also needs Phase 03
│       ├── Phase 06 (Voice Agent)
│       │   └── Phase 07 (Intent + Approvals) ← also needs Phase 05
│       │       └── Phase 08 (Calendar + Booking)
│       └── Phase 11 (Evaluation Suite) ← also needs Phase 09
├── Phase 09 (Weekly Pulse)
└── Phase 10 (Explorer + Resources)

Phase 03 (Auth)
└── Phase 04 (Dashboard)

Phase 12 (Assembly + Deployment) ← depends on all
```

## Parallel Execution Opportunities

These phases can be built in parallel if multiple developers are available:
- Phase 01 and Phase 03 (no dependencies on each other)
- Phase 09, Phase 10 (both depend only on Phase 01)
- Phase 06 and Phase 09 (independent paths after Phase 05 / Phase 01)

## Tech Stack Summary

| Layer | Technology |
|-------|-----------|
| Frontend | React 19 + TypeScript + Vite + Tailwind CSS v4 + shadcn/ui |
| Backend | Python FastAPI |
| Database | Supabase (PostgreSQL) |
| Vector DB | ChromaDB (embedded) |
| Auth | Supabase Auth + Google OAuth |
| LLM | OpenRouter (Claude 3.5 Sonnet primary, GPT-4o-mini judge, Gemini Flash fallback) |
| Embeddings | BAAI/bge-large-en-v1.5 (primary) |
| TTS | Browser Web Speech API + Edge TTS fallback |
| Scraping | Playwright (Python) + google-play-scraper |
| State | TanStack Query + Zustand |
| Testing | Vitest + Playwright E2E |
| Deployment | Vercel (frontend) + Render (backend) |
| Cron | GitHub Actions |

## Repo Structure

```
investor-ops-suite/
├── Docs/Architecture/
├── phase-01-data-ingestion/
│   ├── backend/
│   ├── tests/
│   └── expected_outputs/
├── phase-02-rag-pipeline/
│   ├── backend/
│   ├── tests/
│   └── expected_outputs/
├── phase-03-auth/
│   ├── backend/
│   ├── frontend/
│   ├── tests/
│   └── expected_outputs/
├── phase-04-dashboard/
│   ├── backend/
│   ├── frontend/
│   ├── tests/
│   └── expected_outputs/
├── phase-05-smart-search/
│   ├── backend/
│   ├── frontend/
│   ├── tests/
│   └── expected_outputs/
├── phase-06-voice-agent/
│   ├── backend/
│   ├── frontend/
│   ├── tests/
│   └── expected_outputs/
├── phase-07-intent-approvals/
│   ├── backend/
│   ├── frontend/
│   ├── tests/
│   └── expected_outputs/
├── phase-08-calendar-booking/
│   ├── backend/
│   ├── frontend/
│   ├── tests/
│   └── expected_outputs/
├── phase-09-weekly-pulse/
│   ├── backend/
│   ├── frontend/
│   ├── tests/
│   └── expected_outputs/
├── phase-10-explorer-resources/
│   ├── backend/
│   ├── frontend/
│   ├── tests/
│   └── expected_outputs/
├── phase-11-evaluation-suite/
│   ├── backend/
│   ├── frontend/
│   ├── tests/
│   └── expected_outputs/
├── phase-12-assembly-deploy/
│   ├── scripts/
│   ├── ci/
│   └── smoke-tests/
├── shared/
│   ├── config/
│   ├── db/
│   ├── types/
│   └── utils/
├── .github/workflows/
└── README.md
```

## Definition of Done (Complete Architecture Pack)

- [ ] architecture.md covers all 12 phases with backend/frontend/UI sections
- [ ] HLD.md covers component maps and data flows for all 12 phases
- [ ] LLD.md covers APIs, schemas, test plans, and edge cases for all 12 phases
- [ ] Every phase has Success Criteria and Exit Criteria
- [ ] Every phase has logging/debug gates
- [ ] Every phase has edge-case inventory and test coverage
- [ ] Every phase has expected output specification
- [ ] All architecture decisions include top 5 options with pros/cons
- [ ] HLD and LLD are aligned with architecture.md
