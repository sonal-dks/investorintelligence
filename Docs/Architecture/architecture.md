# Architecture Blueprint

## Inputs
- `Docs/Problemstatement.md`
- `Docs/PRD.md`
- `Docs/UIguidelines.md`

## Phase Index
1. Phase 01 - Data Ingestion (Scraping Pipeline)
2. Phase 02 - RAG Pipeline (Embeddings + Vector Store)
3. Phase 03 - Authentication + User Management
4. Phase 04 - Dashboard + App Shell
5. Phase 05 - Smart Search (RAG Chatbot)
6. Phase 06 - Voice Agent
7. Phase 07 - AI Intent Detection + Approval Center
8. Phase 08 - Google Calendar + Booking System
9. Phase 09 - Weekly Pulse (Review Intelligence)
10. Phase 10 - Mutual Fund Explorer + Resource Hub
11. Phase 11 - Evaluation Suite
12. Phase 12 - Assembly + Deployment

Before starting any phase, configure **Live execution prerequisites (all phases)** (section below): env vars, accounts, and upstream data so work runs against real services—not mocks—for integration and E2E paths.

---

## Structured data and the RAG retrieval layer

Groww (and similar sources) are **messy at the origin** (HTML, mixed copy). Phase 01 **normalizes** that into **structured rows** in Supabase (`mutual_fund_data`, `app_reviews`): typed fields, validation, and a durable source of truth for dashboards, explorers, and jobs.

**RAG does not require storing everything as unstructured blobs.** Retrieval needs **text that can be chunked and embedded**. Phase 02 adds a **retrieval-oriented layer on top of structured storage**: chunking turns structured columns and selected long-text fields (for example exit load / tax copy, and later review bodies) into passages; those passages are embedded and indexed (for example in ChromaDB). The vector store is **derived from** Postgres; **Supabase remains canonical**.

The same pattern applies to other structured product data (for example fee explainer rows): **persist relationally**, **materialize chunk text** when building or refreshing the embedding index.

---

## Live execution prerequisites (all phases)

**Purpose:** Run each phase against **real services and data**, not mocks or stubs. Use this section before starting work on any phase so required accounts, env vars, and upstream data are in place.

**Policy (verification):**

- **Unit tests** may use small fixtures only for **pure logic** (e.g. parsing, validation rules) where no network or credentials are involved.
- **Integration and E2E** checks for a phase must exercise **live** dependencies listed under that phase (real Supabase, real OpenRouter, real browser APIs, etc.) once prerequisites are configured.
- If a prerequisite is missing, **stop** and configure it; do not substitute dummy data for “done” in production paths.

**Cumulative environment variable registry**

Set these in local `.env` (backend), `.env` / Vite env (frontend), and GitHub Actions / hosting dashboards as needed. Values are never committed.

| Variable | Used in phases | Purpose |
|----------|----------------|---------|
| `SUPABASE_URL` | 01–12 | Supabase project URL (REST + Auth). |
| `SUPABASE_ANON_KEY` | 03–12 (frontend + some backend) | Public key for client SDK; RLS-scoped. |
| `SUPABASE_SERVICE_ROLE_KEY` | 01–12 (backend jobs, admin bypass) | Service role for batch writes, server-only operations. |
| `OPENROUTER_API_KEY` | 05–11 | LLM calls (primary, judge, fallback). |
| `OPENROUTER_PRIMARY_MODEL` | 05–11 | e.g. `anthropic/claude-3.5-sonnet`. |
| `OPENROUTER_JUDGE_MODEL` | 09, 11 | e.g. `openai/gpt-4o-mini`. |
| `OPENROUTER_FALLBACK_MODEL` | 05–06 | e.g. `google/gemini-2.0-flash`. |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | 03 | Configured in Supabase Auth (Google provider); not always in app env. |
| `VITE_SUPABASE_URL` | 03–12 | Frontend Supabase URL. |
| `VITE_SUPABASE_ANON_KEY` | 03–12 | Frontend anon key. |
| `VITE_API_BASE_URL` | 04–12 | Backend API origin. |
| `ALLOWED_ORIGINS` | 04–12 | CORS allowlist for backend. |
| `CHROMA_PERSIST_DIR` | 02, 05–06, 11 | Persistent path for embedded ChromaDB. |
| `EMBEDDING_MODEL` | 02 | e.g. `BAAI/bge-large-en-v1.5` (requires download RAM). |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | 08 | JSON string or path pattern per deployment for Calendar API. |
| `GOOGLE_CALENDAR_ID` | 08 | Calendar ID for advisor availability/events. |
| `GMAIL_CLIENT_ID` | 08 (email extension) | OAuth2 client ID for Gmail API used by the FastMCP `gmail.send` tool. |
| `GMAIL_CLIENT_SECRET` | 08 (email extension) | OAuth2 client secret paired with `GMAIL_CLIENT_ID`. |
| `GMAIL_REFRESH_TOKEN` | 08 (email extension) | Long-lived refresh token granted once via OAuth2 desktop flow; used to mint access tokens server-side. |
| `GMAIL_FROM_ADDRESS` | 08 (email extension) | Sender address shown in the From header (must match the consenting Gmail account). |
| `ADVISOR_EMAIL` | 08 (email extension) | Static recipient for the advisor-side booking-confirmation email; not in code. |
| `PHASE08_USE_MOCK_CALENDAR` | 08 | `1` (default in sample `.env`) uses mock Calendar tool; set `0` for live Google Calendar API. |
| `PHASE08_USE_MOCK_GMAIL` | 08 | `1` (default in sample `.env`) uses mock Gmail tool; set `0` for live Gmail API. |
| `PHASE08_TEST_USER_EMAIL` | 08 (tests / local) | When set, resolves booking recipient email without Supabase Auth admin call. |
| `MCP_ACTION_SERVER_URL` | 08+ (optional) | Only if MCP tools run out-of-process; default implementation uses in-process `McpBridge` in `phase-08-calendar-booking/backend`. |
| GitHub `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` secrets | 01 (workflow) | Weekly scrape Action writes to Supabase. |

### Supabase MCP and Cursor agent skills

**What an agent can and cannot do**

- **In Cursor on your machine:** After you add the [Supabase MCP](https://supabase.com/docs/guides/getting-started/mcp) server and complete any **login / OAuth** step Supabase shows, agents in Cursor can use MCP tools (e.g. run SQL, inspect schema) **when those tools are connected and visible** for the chat.
- **From a sandboxed or external agent:** There is no access to your Supabase session or MCP bridge, so that environment **cannot** replace you completing MCP auth or running the dashboard yourself.

**This repository**

- **MCP config:** `.cursor/mcp.json` — defines the hosted Supabase MCP URL including `project_ref`. If you create a **new** Supabase project, update `project_ref` in that file (or merge the same `mcpServers.supabase` block into **Cursor Settings → MCP** if you prefer user-level config). Restart Cursor or reload MCP after changes.
- **Agent Skills (official):** Installed from `supabase/agent-skills` into `.agents/skills/` and symlinked into `.cursor/skills/` as `supabase` and `supabase-postgres-best-practices` so they sit alongside other project skills. Re-install or refresh with:
  - `npx skills add supabase/agent-skills --skill supabase --skill supabase-postgres-best-practices --agent cursor -y`
- **Applying migrations:** MCP can help run SQL once connected; you can still run `phase-01-data-ingestion/migrations/001_create_tables.sql` manually in the Supabase SQL Editor (same outcome).

---

### Phase 01 — Data ingestion (scraping pipeline)

| Item | Requirement |
|------|-------------|
| **Depends on** | Nothing (first phase). |
| **Infra** | Supabase project; SQL migration applied (`mutual_fund_data`, `app_reviews`). |
| **Local / CI** | Python 3.12+; `playwright install chromium`; outbound HTTPS to Groww and Google Play. |
| **Env** | `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`. |
| **GitHub Actions** | Repository secrets for the same vars if using `weekly-scrape.yml`. |
| **Live verification** | Run `phase-01-data-ingestion/run_scraper.py` (not `--dry-run`); confirm rows in Supabase Table Editor and logs show attempted URLs with pass/fail per URL. |

---

### Phase 02 — RAG pipeline (embeddings + vector store)

| Item | Requirement |
|------|-------------|
| **Depends on** | Phase 01: `mutual_fund_data` populated with real scrapes (latest rows per fund). |
| **Infra** | Disk for model weights + `CHROMA_PERSIST_DIR`; ~2 GB RAM recommended for `bge-large-en-v1.5`. |
| **Env** | `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` (or read-capable key), `CHROMA_PERSIST_DIR`, `EMBEDDING_MODEL`. |
| **Live verification** | Refresh/build collection from Supabase; query endpoint returns chunks grounded in real fund rows; no static JSON substitute for corpus. |

---

### Phase 03 — Authentication + user management

| Item | Requirement |
|------|-------------|
| **Depends on** | Supabase Auth enabled; `user_profiles` table + RLS per LLD. |
| **Infra** | Google Cloud OAuth consent + redirect URLs pointing to Supabase Auth callback. |
| **Env (frontend)** | `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`. |
| **Env (backend)** | `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` or JWT verification using Supabase JWKS. |
| **Live verification** | Complete Google sign-in in browser; profile row created/updated in Supabase; session survives refresh. |

---

### Phase 04 — Dashboard + app shell

| Item | Requirement |
|------|-------------|
| **Depends on** | Phase 03; backend serving dashboard APIs; tables `activity_log`, `bookings`, `mutual_fund_data` (can be sparse but real DB). |
| **Env** | `VITE_API_BASE_URL`, auth env from Phase 03, `ALLOWED_ORIGINS` on backend. |
| **Live verification** | Logged-in user loads dashboard from deployed or local stack; KPIs and fund strip read from live Supabase, not hardcoded demo JSON. |

---

### Phase 05 — Smart search (RAG chatbot)

| Item | Requirement |
|------|-------------|
| **Depends on** | Phases 02–03; Chroma populated; OpenRouter account funded. |
| **Env** | `OPENROUTER_API_KEY`, model vars; Supabase keys; Chroma path; backend URL on frontend. |
| **Live verification** | Send a real chat message; retrieval uses live vector store; LLM response via OpenRouter with citations tied to real `source_url` data. |

---

### Phase 06 — Voice agent

| Item | Requirement |
|------|-------------|
| **Depends on** | Phase 05 pipeline (same RAG + LLM); HTTPS origin for mic permissions. |
| **Env** | Same as Phase 05; optional Edge TTS env if backend TTS is used. |
| **Client** | Chromium-based browser (Web Speech API); mic permission. |
| **Live verification** | Voice or text turn hits live `/api/voice/message` (or equivalent); TTS path exercised against real backend when enabled. |

---

### Phase 07 — AI intent detection + approval center

| Item | Requirement |
|------|-------------|
| **Depends on** | Phases 05–06; `approvals` table; OpenRouter for intent model (e.g. Gemini Flash). |
| **Env** | `OPENROUTER_*`; Supabase; admin role in `user_profiles`. |
| **Live verification** | Conversation creates or updates real `approvals` rows; admin UI reads/writes live Supabase. |

---

### Phase 08 — Google Calendar + booking system

| Item | Requirement |
|------|-------------|
| **Depends on** | Phase 07 (approval-gated booking); Google Cloud Calendar API (when `PHASE08_USE_MOCK_CALENDAR=0`). **Implementation:** `phase-08-calendar-booking/`. |
| **Env** | See cumulative table: Calendar, Gmail, `ADVISOR_EMAIL`, mock toggles, optional `PHASE08_TEST_USER_EMAIL`. |
| **Live verification** | `cd phase-08-calendar-booking && PYTHONPATH=. pytest tests/` (14 tests, mock tools). With mocks off: booking CRUD + `POST /api/bookings/{id}/send-email`; apply `migrations/001_bookings_and_booking_emails.sql` for Supabase persistence. |
| **Email extension** | Admin-triggered `gmail.send` via `McpBridge` / FastMCP `server.py`. **Send** gated on `status=confirmed` (optional `notice=1` for cancelled/reschedule notices). Weekly Pulse block is **optional** (footnote when missing / stale). |

---

### Phase 09 — Weekly pulse (review intelligence)

| Item | Requirement |
|------|-------------|
| **Depends on** | Phase 01: `app_reviews` with real reviews; Phase 05+ optional for triggering from app. |
| **Env** | `OPENROUTER_API_KEY`, judge model; Supabase keys; tables `weekly_pulse`, `review_keywords` per LLD. |
| **Live verification** | Generation reads real `app_reviews`; summary persisted to Supabase; judge step uses live LLM. |

---

### Phase 10 — Mutual fund explorer + resource hub

| Item | Requirement |
|------|-------------|
| **Depends on** | Phase 01: `mutual_fund_data`; `fee_explainer_data` populated (scrape or curated seed from real sources). |
| **Env** | Standard API + Supabase + auth from prior phases. |
| **Live verification** | UI lists funds from live latest-per-slug query; fee sections from real `fee_explainer_data` rows. |

---

### Phase 11 — Evaluation suite

| Item | Requirement |
|------|-------------|
| **Depends on** | Phases 05–06–09 in working state; test cases in DB or fixtures that **drive the real chat/RAG/pulse** endpoints. |
| **Env** | `OPENROUTER_*` (judge + primary); Supabase for `evaluation_runs` / `evaluation_cases`. |
| **Live verification** | Eval run invokes real pipeline; results persisted; report reflects live metrics (e.g. `Docs/Architecture/Evals-Report.md` updated from run output). |

---

### Phase 12 — Assembly + deployment

| Item | Requirement |
|------|-------------|
| **Depends on** | All prior phases’ env vars available in **production** hosting (Vercel, Render, etc.). |
| **Infra** | GitHub repo; Vercel + Render (or chosen hosts); secrets not in git. |
| **Env** | Full set from cumulative table; `ALLOWED_ORIGINS` matches production frontend URL. |
| **Live verification** | Smoke tests against **production** URLs; health check; login; one chat; fund explorer load — all against live backends. |

---

## Global Architecture Decisions

### Decision 1: Embedding Model Selection

| # | Model | Dims | MTEB Avg | Size | Pros | Cons |
|---|-------|------|----------|------|------|------|
| 1 | BAAI/bge-large-en-v1.5 | 1024 | 64.23 | 1.34 GB | Top MTEB performer, excellent retrieval, well-maintained | Large model size, slower inference |
| 2 | nomic-ai/nomic-embed-text-v1.5 | 768 | 62.28 | 548 MB | Good quality, Matryoshka dims (can truncate to 256), Apache 2.0 | Slightly lower quality than bge-large |
| 3 | sentence-transformers/all-MiniLM-L6-v2 | 384 | 56.26 | 91 MB | Tiny, extremely fast, widely used | Lower retrieval quality for complex queries |
| 4 | intfloat/e5-large-v2 | 1024 | 62.18 | 1.34 GB | Strong, instruction-tuned, good for Q&A | Requires "query:" prefix, same size as bge-large |
| 5 | BAAI/bge-m3 | 1024 | 63.55 | 2.27 GB | Multilingual, dense+sparse+colbert | Overkill for English-only, largest model |

**Decision:** BAAI/bge-large-en-v1.5
**Rationale:** Best retrieval quality for English fund FAQ domain. Mutual fund questions are precise (exit load, expense ratio, specific fund names) — retrieval precision matters more than speed at demo scale. 1024-dim vectors in ChromaDB are fine for 30 funds.
**Fallback:** all-MiniLM-L6-v2 if GPU/memory is constrained.

### Decision 2: LLM Model Selection (via OpenRouter)

| # | Model | Use Case | Cost (per 1M tokens) | Pros | Cons |
|---|-------|----------|---------------------|------|------|
| 1 | anthropic/claude-3.5-sonnet | Primary RAG | $3 in / $15 out | Best grounding, follows citations well, refuses advice naturally | Higher cost |
| 2 | openai/gpt-4o-mini | Judge LLM | $0.15 in / $0.60 out | Fast, cheap, good eval capability | Slightly less nuanced than Sonnet for judgment |
| 3 | google/gemini-2.0-flash | Fallback | $0.10 in / $0.40 out | Extremely cheap, fast, good for simple Q&A | Weaker at complex grounding |
| 4 | meta-llama/llama-3.1-70b-instruct | Alternative primary | Free on some providers | Free, open-source, strong reasoning | Less reliable citation following |
| 5 | deepseek/deepseek-chat | Budget alternative | $0.14 in / $0.28 out | Very cheap, strong coding/reasoning | Less tested for financial compliance |

**Decision:** Claude 3.5 Sonnet (primary), GPT-4o-mini (judge), Gemini Flash (fallback)
**Rationale:** Financial compliance requires precise grounding — Claude excels at "answer only from provided context." Judge needs to be fast and cheap (many eval runs). Fallback must be reliable for degraded mode.
**Env Config:** All models configurable via `OPENROUTER_PRIMARY_MODEL`, `OPENROUTER_JUDGE_MODEL`, `OPENROUTER_FALLBACK_MODEL`.

### Decision 3: Scraping Approach

| # | Approach | Pros | Cons |
|---|----------|------|------|
| 1 | Playwright (Python) | Handles JS rendering, reliable for SPAs, headless Chrome | Slower, heavier, needs browser install |
| 2 | Cheerio + httpx | Fast, lightweight, low resource | Cannot handle JS-rendered content (Groww is SPA) |
| 3 | Scrapy + Splash | Powerful framework, handles JS via Splash | Complex setup, overkill for 30 URLs |
| 4 | Apify (cloud service) | Managed, reliable, handles anti-bot | Costs money, external dependency |
| 5 | requests-html (Python) | Built-in JS rendering via Pyppeteer | Unmaintained, less reliable than Playwright |

**Decision:** Playwright (Python)
**Rationale:** Groww fund pages are JavaScript-rendered SPAs. Static scraping (Cheerio/httpx) cannot extract data. Playwright is the most reliable headless browser automation for Python, well-maintained, and runs in GitHub Actions with `playwright install chromium`.

For Google Play reviews: `google-play-scraper` Python package (JoMingyu/google-play-scraper). It handles review extraction without needing a browser.

### Decision 4: Frontend State Management

| # | Approach | Pros | Cons |
|---|----------|------|------|
| 1 | TanStack Query + Zustand | Best for server-heavy apps, automatic cache/refetch, Zustand for UI | Two libraries to learn |
| 2 | SWR + React Context | Simpler API, lighter, Vercel-maintained | Less powerful cache control than TanStack |
| 3 | Redux Toolkit + RTK Query | Enterprise standard, built-in API layer | Heavy boilerplate, overkill for demo |
| 4 | Jotai + TanStack Query | Atomic UI state + server state | Jotai has smaller community |
| 5 | Zustand only | One library for everything | Manual server state management (no auto-refetch, stale handling) |

**Decision:** TanStack Query (server state) + Zustand (UI state)
**Rationale:** This app is heavily server-driven (Supabase queries for funds, messages, approvals, KPIs). TanStack Query handles all fetching, caching, background refetch, loading/error states automatically. Zustand handles lightweight global UI state (auth, sidebar, voice recording status) with minimal boilerplate.

### Decision 5: Vector Database Hosting

| # | Approach | Pros | Cons |
|---|----------|------|------|
| 1 | ChromaDB embedded | Zero infrastructure, runs in-process, simplest | Data on disk, tied to backend instance |
| 2 | ChromaDB Docker (server) | Separate service, survives backend restarts | Extra container to manage |
| 3 | Chroma Cloud | Managed, auto-scaling | Beta, costs money, external dependency |
| 4 | Supabase pgvector | Same DB for everything, no extra service | Slower vector search than dedicated DBs |
| 5 | Pinecone | Best performance, managed, scalable | Costs money ($70+/month for starter), vendor lock-in |

**Decision:** ChromaDB embedded
**Rationale:** For a demo project with 30 funds (~300-500 chunks), embedded ChromaDB is more than sufficient. Data persists to disk/volume on Render. No extra infrastructure. If scaling is needed later, migration to ChromaDB server or Pinecone is straightforward (same API).

---

## Phase 01: Data Ingestion (Scraping Pipeline)

### Objective
Build automated scrapers to ingest mutual fund data from 30 configured Groww URLs and app reviews from Google Play Store, storing structured results in Supabase.

### Scope
#### In Scope
- Playwright-based scraper for 30 Groww mutual fund pages
- Google Play review scraper for Groww app
- Supabase table creation (mutual_fund_data, app_reviews)
- GitHub Action for weekly automated scraping
- Error handling for individual URL failures (partial success allowed)
- Data validation before insert

#### Out of Scope
- RAG chunking/embedding (Phase 02)
- UI display of scraped data (Phase 04, 10)
- Trend analysis logic (Phase 09)

### PRD / Problem Mapping
- Features: Feature 5 (Weekly Pulse data source), Feature 6 (Mutual Fund Explorer data source), Feature 3 (RAG knowledge base source)
- Problem statement: Problem 1 (self-serve fund info), Problem 2 (review intelligence)
- Constraints: Data from configured Groww links only; public reviews from Google Play only

### Architecture Decisions
- Decision: Append-only inserts with `scraped_at` timestamp
  - Rationale: Enables trend analysis (4-week rating trends, NAV history) required by Dashboard and Weekly Pulse
  - Tradeoff: More storage over time, but trivial at 30 funds * 52 weeks/year
- Decision: Partial success model (scraper continues if single URL fails)
  - Rationale: One fund page being down should not block all other data
  - Tradeoff: Need monitoring to detect persistent per-URL failures

### Backend Architecture
- Services:
  - `MutualFundScraper` — navigates Groww pages, extracts fund data fields
  - `ReviewScraper` — uses google-play-scraper to fetch latest reviews
  - `DataValidator` — validates scraped data against expected schema before insert
  - `SupabaseWriter` — batch inserts validated data to Supabase
- APIs: None exposed (this is a batch job, not an API service)
- Data:
  - `mutual_fund_data` table: fund_slug, fund_name, category, nav, nav_date, aum_cr, expense_ratio, min_sip, risk_level, returns_1m, returns_6m, returns_1y, returns_3y, returns_5y, exit_load_text, tax_text, source_url, scraped_at
  - `app_reviews` table: review_id, reviewer_name, rating, review_text, review_date, thumbs_up, app_version, scraped_at
  - `fee_explainer_data` (Phase 10): curated explanation rows (`fee_type`, `category`, `description`, …) — **not scraped in Phase 01**, but Phase 02 RAG refresh reads this table from Supabase when (re)building the vector index
- Jobs/events:
- GitHub Action `daily-mf-scrape.yml`: runs daily at 6 AM IST for mutual-fund scraping (`--skip-reviews`)
- GitHub Action `weekly-scrape.yml`: runs every Monday at 6 AM IST for app-review scraping (`--skip-funds`)
  - Manual trigger via workflow_dispatch for on-demand scraping
  - Optional: `python phase-01-data-ingestion/run_scraper.py --refresh-rag` after a successful scrape to rebuild Phase 02 Chroma (mutual fund chunks + fee explainer narrative chunks)
- Security/compliance:
  - No PII scraped (reviews are public, fund data is public)
  - Respectful scraping: 2-second delay between page loads
  - User-Agent identifies the bot

### Frontend Architecture
- Routes/pages: None (Phase 01 is backend-only)
- State/data-flow: N/A
- Client integration contracts: N/A
- Failure states: N/A

### UI Architecture
- Information architecture: N/A
- Component structure: N/A
- Core interactions: N/A
- Accessibility/responsive notes: N/A

### Risks and Mitigations
- Risk: Groww changes their page structure, breaking the scraper
  - Mitigation: Scraper uses CSS selectors stored in config (not hardcoded). Validation catches empty/null fields. Alert on >50% field extraction failure.
- Risk: Google Play scraper library breaks (unofficial)
  - Mitigation: Pin library version. Fallback: manual CSV import until fixed.
- Risk: GitHub Actions timeout on 30 pages
  - Mitigation: Parallel scraping (5 concurrent pages). Total budget: 10 minutes max.

### Deliverables
- `phase-01-data-ingestion/backend/scrapers/mutual_fund_scraper.py`
- `phase-01-data-ingestion/backend/scrapers/review_scraper.py`
- `phase-01-data-ingestion/backend/validators/data_validator.py`
- `phase-01-data-ingestion/backend/db/supabase_writer.py`
- `.github/workflows/weekly-scrape.yml`
- `phase-01-data-ingestion/tests/`
- `phase-01-data-ingestion/expected_outputs/`
- Supabase migration SQL for tables

### Success Criteria
- All 30 fund URLs scraped successfully with all required fields populated
- At least 50 reviews scraped per run from Google Play
- Data appears in Supabase tables with correct types and timestamps
- GitHub Action completes within 10 minutes
- Validation rejects malformed data (does not insert nulls for required fields)

### Exit Criteria
- [ ] mutual_fund_data table populated with 30 rows from latest scrape
- [ ] app_reviews table populated with 50+ reviews
- [ ] GitHub Action runs successfully (manual trigger test)
- [ ] Validation tests pass for both valid and invalid data
- [ ] Expected output JSON fixtures match actual scraped structure

### Phase Logging and Debug Gates
- Checks Run:
  - ReadLints: All Python files pass flake8/ruff
  - Focused tests: `pytest phase-01-data-ingestion/tests/` — all pass
  - Build/type check: `mypy` on scraper modules
  - Runtime sanity check: Run scraper on 3 URLs, verify Supabase insert
- Debug Notes: Log per-URL success/failure with timing
- Result: PASS | FAIL
- Next Step: Phase 02 (RAG Pipeline)

### Edge Cases and Test Coverage
#### Edge Inventory
- Inputs: Groww URL returns 404; page loads but fund data section missing; NAV field contains non-numeric text; review has empty text body
- System: Supabase insert timeout; ChromaDB connection refused (not relevant yet); duplicate scrape within same day
- Dependencies: Playwright browser fails to launch; google-play-scraper rate limited; Supabase API rate limit
- User behavior: N/A (batch job, no user interaction)
- Environment: GitHub Actions runner has no persistent state; timezone differences for `scraped_at`
- AI-specific: N/A (no AI in this phase)

#### Prioritization (Impact x Likelihood)
- High impact/high likelihood: Groww page structure changes (breaks all scraping)
- High impact/low likelihood: Supabase outage during scrape window
- Low impact/high likelihood: Single URL 404 (one fund temporarily unavailable)
- Low impact/low likelihood: GitHub Actions runner IP blocked

#### Failure Containment and Guardrails
- Graceful failure/fallback: Individual URL failure does not stop batch; partial results are inserted
- Defensive controls: Schema validation before insert; retry with backoff (max 3 attempts per URL)
- Observability signals: Log total URLs attempted/succeeded/failed; GitHub Action summary annotation

#### Edge-Case Test Plan
- Unit: Test data validator with null fields, wrong types, extreme values (NAV=0, AUM=-1)
- Integration: Test scraper against a mock HTML fixture (saved page snapshot)
- E2E: Full scrape of 3 live URLs + insert to Supabase test project

---

## Phase 02: RAG Pipeline (Embeddings + Vector Store)

### Objective
Transform scraped mutual fund data into a queryable vector store that returns relevant context chunks for any fund-related question.

### Scope
#### In Scope
- Hybrid chunking: structured facts (key-value) + paragraph descriptions per fund
- Fee explainer **narrative chunks** derived from `fee_explainer_data` (one embeddable passage per `fee_type`, with source URL and `last_updated` in metadata)
- Embedding generation using BAAI/bge-large-en-v1.5
- ChromaDB collection creation and population
- Retrieval service with top-k similarity search
- Refresh logic: rebuild collection from latest scraped data

#### Out of Scope
- Chat UI (Phase 05)
- LLM response generation (Phase 05)
- Voice input (Phase 06)
- Curating or editing fee-explainer **source rows** in Supabase (owned by Phase 10 / ops); Phase 02 only **indexes** them into the vector store alongside fund chunks

### PRD / Problem Mapping
- Features: Feature 3 (Smart Search knowledge base), Feature 4 (Voice Agent corpus)
- Problem statement: Problem 1 (investors cannot self-serve fund questions)
- Constraints: Data only from configured Groww links; no third-party blogs

### Architecture Decisions
- Decision: Hybrid chunking strategy
  - Rationale: Structured facts ("Exit load of Mirae Asset Large Cap: 1% if redeemed before 1 year") enable precise retrieval for specific questions. Paragraph chunks capture descriptive context.
  - Tradeoff: More chunks per fund (~10-15), but better precision than single-document approach
- Decision: Full rebuild on refresh (not incremental)
  - Rationale: 30 funds * 15 chunks = ~450 vectors. Full rebuild takes <30 seconds. Incremental adds complexity for negligible benefit at this scale.
  - Tradeoff: Brief unavailability during rebuild (acceptable for weekly refresh)

### Backend Architecture
- Services:
  - `ChunkingService` — splits fund data into hybrid chunks (facts + a combined description); regex-extracts the active exit-load and tax rule lines from Groww's run-together copy; builds fee-explainer markdown chunks from `fee_explainer_data`
  - `EmbeddingService` — primary `BAAI/bge-large-en-v1.5` (1024-dim) with `all-MiniLM-L6-v2` fallback (384-dim); lazy load + dimension validation
  - `ChromaService` — manages the persistent `mutual_fund_knowledge` collection (cosine; delete-and-recreate on refresh)
  - `LexicalIndex` — in-memory BM25 sidecar built from Chroma's documents
  - `EntityResolver` — rapidfuzz token-set match over stop-word-stripped haystack to resolve fund mentions to canonical `fund_slug`
  - `RetrievalService` — hybrid retrieval (vector + BM25 fused via Reciprocal Rank Fusion), dynamic-k confidence widening, fund-filter scoping, optional **`corpus_filter`** (`mutual_fund` | `fee_explainer`) for intent-scoped retrieval (Phase 05 uses intent-first routing with low-confidence unified fallback)
  - `RAGPipeline` — orchestrator for `refresh()` and `get_retrieval()`; rebuilds BM25 + EntityResolver after each refresh and after process restart
- APIs:
  - `POST /api/rag/query` — hybrid retrieval; returns top-k chunks + diagnostics (`resolved_fund_slug`, `used_dynamic_k`, `embedding_model_used`); optional `corpus_filter` in the JSON body scopes results to mutual-fund vs fee-explainer chunks
  - `POST /api/rag/refresh` — triggers re-embedding from latest Supabase data; 409 if a refresh is already running
  - `GET /api/rag/health` — collection size, collection name, currently loaded embedding model
- Data:
  - ChromaDB collection: `mutual_fund_knowledge` (cosine distance)
  - Chunk metadata: `fund_slug`, `chunk_type` (`fact`|`description`), `source_field`, `scraped_at`, `corpus` (`mutual_fund`|`fee_explainer`), optional `fee_type`, optional `source_url` (Groww citation for citations UI)
  - Source of truth: Supabase `mutual_fund_data` (latest row per `fund_slug`) **and** `fee_explainer_data`; the vector store is **derived** from Postgres
- Jobs/events:
  - Triggered after weekly scrape completes (GitHub Action will call the refresh endpoint in Phase 12)
- Security/compliance:
  - No user data in vector store (only public fund information)

### Frontend Architecture
- Routes/pages: None (Phase 02 is backend-only)
- State/data-flow: N/A
- Client integration contracts: N/A
- Failure states: N/A

### UI Architecture
- N/A (backend-only phase)

### Risks and Mitigations
- Risk: Embedding model too large for Render free tier memory
  - Mitigation: Use all-MiniLM-L6-v2 (91MB) as fallback; bge-large needs ~2GB RAM
- Risk: ChromaDB data lost on Render redeploy
  - Mitigation: Persist to Render disk volume; rebuild from Supabase if lost (source of truth is Supabase)
- Risk: Retrieval returns irrelevant chunks for ambiguous queries
  - Mitigation: Tune top-k (start with 5); add metadata filtering by fund_slug when query mentions specific fund

### Deliverables
- `phase-02-rag-pipeline/backend/config/settings.py`
- `phase-02-rag-pipeline/backend/models/schemas.py`
- `phase-02-rag-pipeline/backend/services/chunking_service.py`
- `phase-02-rag-pipeline/backend/services/embedding_service.py` (primary BGE + MiniLM fallback)
- `phase-02-rag-pipeline/backend/services/chroma_service.py`
- `phase-02-rag-pipeline/backend/services/lexical_index.py` (BM25 sidecar)
- `phase-02-rag-pipeline/backend/services/entity_resolver.py` (rapidfuzz)
- `phase-02-rag-pipeline/backend/services/supabase_reader.py`
- `phase-02-rag-pipeline/backend/services/retrieval_service.py` (hybrid + dynamic-k + RRF)
- `phase-02-rag-pipeline/backend/services/rag_pipeline.py` (refresh + retrieval orchestrator)
- `phase-02-rag-pipeline/backend/routers/rag_router.py`
- `phase-02-rag-pipeline/backend/app.py` (FastAPI app for local serving)
- `phase-02-rag-pipeline/run_refresh.py` / `run_query.py` / `run_benchmark.py` CLIs
- `phase-02-rag-pipeline/tests/` (35 unit + integration tests)
- `phase-02-rag-pipeline/expected_outputs/` (retrieval/refresh/chunk/benchmark fixtures)

### Success Criteria
- Query "What is the exit load of Mirae Asset Large Cap?" returns chunk containing "1% if redeemed before 1 year"
- Top-3 retrieval precision > 80% on 20 hand-crafted test queries
- Full rebuild completes in <60 seconds for 30 funds
- Refresh endpoint returns 200 and updates collection timestamp

### Exit Criteria
- [ ] ChromaDB collection populated with chunks from all 30 funds
- [ ] Retrieval service returns relevant results for test queries
- [ ] Precision benchmark passes (>80% on test set)
- [ ] Refresh endpoint works end-to-end (Supabase → chunks → embeddings → ChromaDB)
- [ ] Expected output fixtures validate chunk structure

### Phase Logging and Debug Gates
- Checks Run:
  - ReadLints: ruff check on all Python files
  - Focused tests: `pytest phase-02-rag-pipeline/tests/`
  - Build/type check: mypy on service modules
  - Runtime sanity check: Query 5 test questions, verify top-3 contains correct fund
- Debug Notes: Log chunk count per fund, embedding generation time, collection size
- Result: PASS | FAIL
- Next Step: Phase 03 (Auth) or Phase 05 (Smart Search) depending on parallel track

### Edge Cases and Test Coverage
#### Edge Inventory
- Inputs: Fund with missing fields (no returns_5y for new funds); extremely long exit_load_text; fund name with special characters
- System: ChromaDB collection already exists on refresh (need delete-then-create); embedding model OOM
- Dependencies: sentence-transformers download fails; Supabase returns empty dataset
- User behavior: N/A (no user interaction in this phase)
- Environment: Render disk full; Python version mismatch for sentence-transformers
- AI-specific: Embedding model produces degenerate vectors for very short text; semantic similarity fails for abbreviation queries ("ER" for expense ratio)

#### Prioritization (Impact x Likelihood)
- High impact/high likelihood: Missing fund fields produce incomplete chunks
- High impact/low likelihood: Embedding model OOM on Render
- Low impact/high likelihood: Short text produces low-quality embeddings
- Low impact/low likelihood: ChromaDB corruption

#### Failure Containment and Guardrails
- Graceful failure/fallback: If embedding fails for one fund, skip and continue; log the failure
- Defensive controls: Validate chunk minimum length (>10 chars); validate embedding dimension matches expected
- Observability signals: Log total chunks generated, embedding time per batch, ChromaDB collection stats

#### Edge-Case Test Plan
- Unit: Chunking with missing fields; chunking with extreme text lengths; embedding dimension validation
- Integration: Full pipeline from mock Supabase data → ChromaDB → retrieval
- E2E: Query 20 test questions against live ChromaDB, measure precision

---

## Phase 03: Authentication + User Management

### Objective
Implement Google OAuth login via Supabase Auth with role selection (Investor/Admin), session persistence, and first-login email capture.

### Scope
#### In Scope
- Login page with role selector
- Google OAuth via Supabase Auth
- First-login email capture modal
- Session persistence (survives page refresh)
- Sign-out with full state reset
- user_profiles table and RLS policies

#### Out of Scope
- Role-based navigation rendering (Phase 04)
- Dashboard content (Phase 04)
- Any feature pages beyond login

### PRD / Problem Mapping
- Features: Feature 1 (Authentication and Role Management)
- Problem statement: Prerequisite for all user-facing features
- Constraints: No PII collection beyond email; mock-auth pattern per UI guidelines

### Architecture Decisions
- Decision: Supabase Auth with Google OAuth provider
  - Rationale: Already using Supabase; built-in OAuth, session management, JWT handling. Zero additional cost.
  - Tradeoff: Tied to Supabase ecosystem (acceptable since DB is already there)
- Decision: Role stored in user_profiles table (not in JWT claims)
  - Rationale: Role can change without re-login; simpler than custom JWT claims
  - Tradeoff: Extra DB query on page load to get role (cached by TanStack Query)

### Backend Architecture
- Services:
  - Supabase Auth handles OAuth flow (no custom backend needed for auth)
  - `UserProfileService` — CRUD for user_profiles table
- APIs:
  - `GET /api/users/me` — returns current user profile (role, email, display_name)
  - `POST /api/users/profile` — creates/updates user profile (role selection, email)
- Data:
  - `user_profiles`: id (uuid, PK), user_id (FK to auth.users), email, display_name, role (enum: investor|admin), first_login_complete (bool), created_at, updated_at
  - RLS: Users can read/write only their own profile
- Security/compliance:
  - Google OAuth only (no password storage)
  - Email is the only PII stored (required for profile display)
  - RLS on user_profiles prevents cross-user access

### Frontend Architecture
- Routes/pages:
  - `/login` — role selector + Google OAuth button
  - `/` — redirect to dashboard after login
- State/data-flow:
  - Zustand `useAuthStore`: user, role, isAuthenticated, isLoading
  - Supabase `onAuthStateChange` listener for session sync
  - TanStack Query for user profile fetch
- Client integration contracts:
  - Supabase JS client for auth operations
  - Backend API for profile CRUD
- Failure states:
  - OAuth popup blocked → show manual link
  - Network error during OAuth → retry message
  - Session expired → redirect to login

### UI Architecture
- Information architecture: Login page is single-purpose (role + OAuth)
- Component structure:
  - `LoginPage` → `RoleSelector` + `GoogleAuthButton`
  - `EmailCaptureModal` (shown once on first login)
  - `AuthProvider` (wraps app, provides auth context)
- Core interactions:
  - Select role → click "Sign in with Google" → OAuth popup → redirect to dashboard
  - First login: modal appears for email confirmation → submit → never shown again
- Accessibility/responsive notes: Focus management on modal; role selector keyboard-navigable

### Risks and Mitigations
- Risk: Google OAuth consent screen not configured
  - Mitigation: Document setup steps in phase README; provide test credentials for development
- Risk: Supabase free tier OAuth limit
  - Mitigation: 50,000 MAU on free tier; demo project will never approach this
- Risk: User refreshes during OAuth flow
  - Mitigation: Supabase handles redirect callback; session persists in localStorage

### Deliverables
- `phase-03-auth/README.md` — setup, env vars, verification table
- `phase-03-auth/PHASE_LOG.md` — gates and debug notes
- `phase-03-auth/backend/main.py` — FastAPI app + CORS
- `phase-03-auth/backend/deps.py` — Supabase JWT verification
- `phase-03-auth/backend/routers/user_router.py`
- `phase-03-auth/backend/services/user_profile_service.py`
- `phase-03-auth/frontend/src/pages/Login.tsx`
- `phase-03-auth/frontend/src/components/RoleSelector.tsx`
- `phase-03-auth/frontend/src/components/EmailCaptureModal.tsx`
- `phase-03-auth/frontend/src/stores/auth-store.ts`
- `phase-03-auth/frontend/src/providers/AuthProvider.tsx`
- `phase-03-auth/tests/` — pytest (API/service) + vitest (RoleSelector)
- `phase-03-auth/expected_outputs/`
- Supabase migration: `phase-03-auth/migrations/003_user_profiles.sql`

### Success Criteria
- User can log in via Google OAuth and land on dashboard
- Role selection persists across sessions
- First-login email modal appears only once
- Sign-out clears all state and returns to login page
- Investor role cannot access admin-only routes (enforced)

### Exit Criteria
- [ ] Google OAuth flow completes without errors
- [ ] user_profiles row created on first login
- [ ] Role-based route protection works (investor cannot navigate to admin pages)
- [ ] Session persists after page refresh
- [ ] Sign-out fully resets auth state
- [ ] All tests pass

### Phase Logging and Debug Gates
- Checks Run:
  - ReadLints: ruff (backend) + eslint (frontend)
  - Focused tests: auth flow unit tests + profile CRUD tests
  - Build/type check: TypeScript strict mode on frontend; mypy on backend
  - Runtime sanity check: Manual login → verify profile in Supabase → sign out → verify cleared
- Debug Notes: Log auth state transitions; verify RLS blocks cross-user queries
- Result: PASS | FAIL
- Next Step: Phase 04 (Dashboard)

### Edge Cases and Test Coverage
#### Edge Inventory
- Inputs: User cancels OAuth popup; user has no Google account; email field left empty in capture modal
- System: Supabase Auth service down; duplicate user_profiles row (race condition on first login)
- Dependencies: Google OAuth service unavailable; Supabase session token expired mid-use
- User behavior: User refreshes during OAuth callback; user opens app in multiple tabs; user changes role after initial selection
- Environment: Third-party cookies blocked (affects OAuth in some browsers); browser private mode
- AI-specific: N/A

#### Prioritization (Impact x Likelihood)
- High impact/high likelihood: OAuth popup blocked by browser
- High impact/low likelihood: Supabase Auth outage
- Low impact/high likelihood: User accidentally selects wrong role
- Low impact/low likelihood: Duplicate profile race condition

#### Failure Containment and Guardrails
- Graceful failure/fallback: OAuth failure → clear error message with retry; session expiry → silent re-auth attempt, then redirect to login
- Defensive controls: Unique constraint on user_id in user_profiles; UPSERT for profile creation; validate role enum on backend
- Observability signals: Log login success/failure counts; track first_login_complete conversion rate

#### Edge-Case Test Plan
- Unit: Profile creation with missing fields; role validation; session token parsing
- Integration: Full OAuth mock flow (Supabase test helpers); profile CRUD with RLS
- E2E: Complete login → role select → dashboard redirect → refresh → still logged in → sign out

---

## Phase 04: Dashboard + App Shell

### Objective
Build the app shell (sidebar, topbar) and role-aware dashboard with KPI cards, mutual fund strip, booking summary, and weekly pulse preview widget.

### Scope
#### In Scope
- App shell: sidebar navigation (role-aware), topbar with status indicators
- 4-column KPI strip (Login Sessions, Chatbot Sessions, Voice Sessions, Bookings)
- Mutual fund NAV strip (latest scraped data)
- Booking status breakdown (confirmed/cancelled/rescheduled)
- Weekly Pulse preview widget
- Role-based data scoping (investor: personal, admin: platform-wide)

#### Out of Scope
- Actual chatbot/voice functionality (Phase 05, 06)
- Approval Center navigation item behavior (Phase 07)
- Live KPI updates via websocket (future enhancement)

### PRD / Problem Mapping
- Features: Feature 2 (Dashboard)
- Problem statement: Problem 6 (data is siloed — dashboard unifies)
- Constraints: KPI calculations per PRD Section 5.2; UI per UIguidelines.md

### Architecture Decisions
- Decision: Server-side KPI calculation (backend API)
  - Rationale: KPI logic involves time windows, aggregations, and trend formulas. Doing this in SQL/backend is cleaner and more testable than client-side.
  - Tradeoff: Extra API round-trip vs. querying Supabase directly from frontend
- Decision: TanStack Query with 60-second stale time for dashboard data
  - Rationale: Dashboard data doesn't change every second. 60s cache reduces Supabase load.
  - Tradeoff: Data can be up to 60s stale (acceptable for operational dashboard)

### Backend Architecture
- Services:
  - `DashboardService` — calculates KPIs with time windows and trend formulas
  - `FundStripService` — returns latest NAV for all tracked funds
- APIs:
  - `GET /api/dashboard/kpis?user_id={}&role={}` — returns 4 KPI values with trends
  - `GET /api/dashboard/bookings?user_id={}&role={}` — returns booking status counts
  - `GET /api/dashboard/fund-strip` — returns latest NAV for all funds
  - `GET /api/dashboard/pulse-preview` — returns latest pulse summary
- Data:
  - Reads from: activity_log, bookings, mutual_fund_data, weekly_pulse (when available)
  - `activity_log`: id, user_id, user_name, event_type, metadata, created_at
  - `bookings`: id, user_id, booking_code, status, topic, scheduled_at, created_at
- Security/compliance:
  - user_id filter enforced server-side for investor role
  - Admin sees platform-wide aggregates (no user_id filter)

### Frontend Architecture
- Routes/pages:
  - `/dashboard` — main dashboard page
  - Layout: `AppShell` wraps all authenticated pages
- State/data-flow:
  - TanStack Query hooks: `useKPIs()`, `useBookings()`, `useFundStrip()`, `usePulsePreview()`
  - Zustand: sidebar collapsed state, active nav item
- Client integration contracts:
  - All dashboard data from backend APIs (not direct Supabase)
- Failure states:
  - API error → skeleton placeholders with "Unable to load" message
  - Empty data → "No activity yet" empty state with helpful text

### UI Architecture
- Information architecture: KPIs at top → fund strip → booking breakdown → pulse preview
- Component structure:
  - `AppShell` → `Sidebar` + `Topbar` + `<main>` slot
  - `DashboardPage` → `KPIGrid` + `FundStrip` + `BookingSummary` + `PulsePreview`
  - `KPICard` (reusable, per UI guidelines pattern)
  - `FundRow` (fund name, category, NAV, date)
- Core interactions:
  - Sidebar nav click → route change
  - KPI cards are display-only (no click action in v1)
  - Fund strip scrollable if >5 funds visible
- Accessibility/responsive notes:
  - Sidebar collapses to icons on mobile
  - KPI grid: 4 cols desktop, 2 cols mobile
  - All cards keyboard-focusable for screen readers

### Risks and Mitigations
- Risk: No activity_log data yet (new install)
  - Mitigation: Handle zero-state gracefully (show 0 with "No data yet" subtitle)
- Risk: KPI trend calculation divides by zero
  - Mitigation: Backend handles NULLIF(previous, 0) per PRD formula

### Deliverables
- `phase-04-dashboard/backend/routers/dashboard_router.py`
- `phase-04-dashboard/backend/services/dashboard_service.py`
- `phase-04-dashboard/frontend/src/components/AppShell.tsx`
- `phase-04-dashboard/frontend/src/components/Sidebar.tsx`
- `phase-04-dashboard/frontend/src/components/Topbar.tsx`
- `phase-04-dashboard/frontend/src/pages/Dashboard.tsx`
- `phase-04-dashboard/frontend/src/components/KPICard.tsx`
- `phase-04-dashboard/frontend/src/components/FundStrip.tsx`
- `phase-04-dashboard/frontend/src/components/BookingSummary.tsx`
- `phase-04-dashboard/tests/`
- `phase-04-dashboard/expected_outputs/`

### Success Criteria
- Dashboard renders with correct KPIs scoped by role
- Sidebar shows/hides admin items based on role
- Fund strip displays latest NAV data from scraped source
- Trend indicators show correct direction (up/down/neutral)
- All UI matches UIguidelines.md patterns exactly

### Exit Criteria
- [ ] App shell renders with sidebar + topbar
- [ ] KPI cards display correct values (verified against Supabase)
- [ ] Role filtering works (investor sees own data, admin sees all)
- [ ] Empty states render correctly when no data
- [ ] Responsive layout works at mobile, tablet, desktop
- [ ] All tests pass

### Phase Logging and Debug Gates
- Checks Run:
  - ReadLints: eslint + ruff
  - Focused tests: dashboard API tests + component render tests
  - Build/type check: `tsc --noEmit` + mypy
  - Runtime sanity check: Log in as investor → verify scoped data; log in as admin → verify aggregate
- Debug Notes: Verify KPI formulas match PRD Section 5.2 exactly
- Result: PASS | FAIL
- Next Step: Phase 05 (Smart Search)

### Edge Cases and Test Coverage
#### Edge Inventory
- Inputs: No activity_log rows for current user; activity only in previous window (trend shows decline); all bookings cancelled
- System: Dashboard API timeout; Supabase connection pool exhausted
- Dependencies: mutual_fund_data table empty (scraper hasn't run yet)
- User behavior: User switches role mid-session (re-fetch needed); rapid page refreshes
- Environment: Slow network → show loading skeletons; screen width < 320px

#### Prioritization (Impact x Likelihood)
- High impact/high likelihood: Empty state on first use (no data yet)
- High impact/low likelihood: API timeout
- Low impact/high likelihood: Previous period has zero activity (trend = +100%)
- Low impact/low likelihood: Screen width < 320px

#### Failure Containment and Guardrails
- Graceful failure/fallback: API error → show skeleton with retry; empty data → helpful empty state
- Defensive controls: Backend never returns nulls for KPI values (defaults to 0); trend formula handles division by zero
- Observability signals: Log API response times; track cache hit/miss rates

#### Edge-Case Test Plan
- Unit: KPI calculation with zero previous values; trend formula edge cases; role filtering
- Integration: Dashboard API with seeded activity_log data; empty database state
- E2E: Login → dashboard renders → verify KPI values → switch role → verify change

---

## Phase 05: Smart Search (RAG Chatbot)

### Objective
Build a multi-session RAG chatbot that answers fund questions with citations, maintains cross-session memory, refuses investment advice, and provides suggested starter queries.

### Scope
#### In Scope
- Chat UI: session list, message thread, input row
- Session management: create, rename, delete, switch
- RAG pipeline: query → retrieve → LLM → grounded response
- Citation embedding in responses
- Advice/unsafe prompt refusal
- Cross-session memory (LLM-generated summaries)
- Suggested starter questions for empty sessions
- Activity logging (chatbot_used events)

#### Out of Scope
- Voice input (Phase 06)
- Intent detection for approvals (Phase 07)
- Resource Hub / Explorer UI for fee explainer (Phase 10); Smart Search still retrieves fee-explainer **chunks** from the shared RAG index when the user asks conceptual fee questions

### PRD / Problem Mapping
- Features: Feature 3 (Smart Search)
- Problem statement: Problem 1 (investors cannot self-serve), Problem 5 (AI quality)
- Constraints: No advice; grounded only; concise answers; citations required

### Architecture Decisions
- Decision: System prompt with strict grounding instructions
  - Rationale: Compliance requires answers ONLY from provided context. System prompt instructs: "Answer only from the provided context. If the answer is not in context, say so. Never give investment advice."
  - Tradeoff: May refuse some answerable questions if retrieval misses relevant chunk
- Decision: Cross-session memory via LLM summaries stored in user_memory table
  - Rationale: Storing full history is expensive context. A condensed summary (updated after each session) gives personalization without token bloat.
  - Tradeoff: Summary may lose details; acceptable for "remembers your name and preferred funds" use case
- Decision: PII detection + redaction on all user inputs before processing
  - Rationale: Compliance requires no PII storage. Regex patterns detect PAN, Aadhaar, phone, email in messages.
  - Tradeoff: Regex may have false positives (e.g., 10-digit number that isn't a phone)

### Backend Architecture
- Services:
  - `ChatService` — orchestrates RAG pipeline: PII → intent → refusal → retrieve → build prompt → call LLM → format response
  - `PIIDetector` — regex-based PII detection and redaction
  - `IntentRouter` — mandatory intent classification per Addendum A2 (factual/action/safety/clarification); for **factual** turns, `classify_factual_corpus()` routes to `mutual_fund` vs `fee_explainer` Chroma corpus with confidence; below-threshold queries use unified retrieval (no corpus filter)
  - `MemoryService` — manages cross-session summaries (generate, store, retrieve)
  - `RefusalClassifier` — detects advice requests, unsafe prompts (rule-based)
  - `LLMClient` — OpenRouter client with primary (Claude 3.5 Sonnet) + fallback (Gemini Flash) chain
- APIs:
  - `POST /api/chat/message` — send message, get AI response (streaming optional)
  - `GET /api/chat/sessions?user_id={}` — list user's chat sessions
  - `POST /api/chat/sessions` — create new session
  - `DELETE /api/chat/sessions/{id}` — delete session
  - `GET /api/chat/sessions/{id}/messages` — get session messages
  - `GET /api/chat/memory?user_id={}` — get user's memory summary
- Data:
  - `chat_sessions`: id, user_id, title, last_message_at, created_at
  - `chat_messages`: id, session_id, role (user|assistant|system), content, citations (jsonb), metadata (jsonb), created_at
  - `user_memory`: id, user_id, summary_text, topics (jsonb), updated_at
  - `activity_log`: insert on session create (event_type: 'chatbot_used')
- Jobs/events: Memory summary updated async after each session ends (or every 5 messages)
- Security/compliance:
  - PII redaction before storage
  - No advice prompt patterns → immediate refusal response
  - All responses include "This is not investment advice" footer when discussing specific funds

### Frontend Architecture
- Routes/pages:
  - `/smart-search` — chat interface
- State/data-flow:
  - TanStack Query: `useSessions()`, `useMessages(sessionId)`, `useMemory()`
  - Zustand: `useChatStore` — activeSessionId, isThinking, inputValue
  - Optimistic updates: user message appears immediately, assistant response streams in
- Client integration contracts:
  - Backend chat API for all operations
  - Real-time message display (polling or SSE for streaming)
- Failure states:
  - LLM timeout → "I'm having trouble responding. Please try again." + retry button
  - LLM degraded → fallback model + "Using simplified mode" indicator
  - Network error → message marked as failed with retry option

### UI Architecture
- Information architecture: Left panel (sessions) + Right panel (messages + input)
- Component structure:
  - `SmartSearchPage` → `SessionList` + `ChatArea`
  - `SessionList` → `NewChatButton` + `SessionItem[]`
  - `ChatArea` → `MessageList` + `InputRow` + `SuggestedQueries`
  - `MessageBubble` (user style vs assistant style per UI guidelines)
  - `ThinkingIndicator` (animated loader + "Searching...")
  - `CitationBadge` (source link in assistant messages)
- Core interactions:
  - "New Chat" → creates session → shows suggested queries
  - Type message → send → thinking state → response appears
  - Click session → loads messages → can continue conversation
  - Hover session → show delete button → confirm → delete
- Accessibility/responsive notes:
  - Chat area auto-scrolls to latest message
  - Input row always visible (sticky bottom)
  - Session list becomes drawer on mobile
  - Focus moves to input after session switch

### Risks and Mitigations
- Risk: LLM hallucinates despite grounding instructions
  - Mitigation: Judge LLM evaluates faithfulness periodically (Phase 11); system prompt emphasizes "ONLY from context"
- Risk: Retrieval misses relevant chunk → LLM says "I don't know" for answerable questions
  - Mitigation: Tune retrieval (top-k=5, reranking if needed); expand chunk overlap
- Risk: PII regex has false positives (blocks legitimate messages)
  - Mitigation: Only redact, don't block; warn user that sensitive info was removed

### Deliverables
- `phase-05-smart-search/backend/config/settings.py`
- `phase-05-smart-search/backend/deps.py`
- `phase-05-smart-search/backend/main.py`
- `phase-05-smart-search/backend/models/schemas.py`
- `phase-05-smart-search/backend/routers/chat_router.py`
- `phase-05-smart-search/backend/services/chat_service.py`
- `phase-05-smart-search/backend/services/pii_detector.py`
- `phase-05-smart-search/backend/services/memory_service.py`
- `phase-05-smart-search/backend/services/refusal_classifier.py`
- `phase-05-smart-search/backend/services/intent_router.py`
- `phase-05-smart-search/backend/services/llm_client.py`
- `phase-05-smart-search/frontend/src/pages/SmartSearch.tsx`
- `phase-05-smart-search/frontend/src/components/SessionList.tsx`
- `phase-05-smart-search/frontend/src/components/ChatInput.tsx`
- `phase-05-smart-search/frontend/src/components/MessageBubble.tsx`
- `phase-05-smart-search/frontend/src/components/SuggestedQueries.tsx`
- `phase-05-smart-search/frontend/src/hooks/useChat.ts`
- `phase-05-smart-search/frontend/src/stores/chat-store.ts`
- `phase-05-smart-search/tests/`
- `phase-05-smart-search/expected_outputs/`
- `phase-05-smart-search/migrations/001_create_chat_tables.sql`

### Success Criteria
- Chatbot answers "What is the exit load of Mirae Asset Large Cap?" with correct info + citation
- Chatbot refuses "Should I invest in Mirae Asset ELSS?" with appropriate refusal message
- Sessions persist across page refreshes
- Cross-session memory remembers user's previously discussed funds
- PII (10-digit phone number) is redacted before storage
- Suggested queries appear for new sessions

### Exit Criteria
- [ ] Chat UI fully functional (create/switch/delete sessions)
- [ ] RAG pipeline returns grounded answers with citations
- [ ] Refusal triggers for advice requests
- [ ] PII detection catches PAN/Aadhaar/phone/email patterns
- [ ] Memory summary generated and retrieved across sessions
- [ ] Activity logged on session creation
- [ ] All tests pass including edge cases

### Phase Logging and Debug Gates
- Checks Run:
  - ReadLints: eslint + ruff
  - Focused tests: RAG pipeline tests, PII detector tests, refusal classifier tests, chat API tests
  - Build/type check: tsc + mypy
  - Runtime sanity check: Ask 5 fund questions → verify grounded answers; ask advice → verify refusal
- Debug Notes: Log retrieval chunks per query; log LLM token usage; log PII detection events
- Result: PASS | FAIL
- Next Step: Phase 06 (Voice Agent)

### Edge Cases and Test Coverage
#### Edge Inventory
- Inputs: Empty message; extremely long message (>5000 chars); message in non-English; prompt injection ("ignore instructions and..."); PII in message; multiple questions in one message
- System: LLM API timeout; LLM returns empty response; ChromaDB returns zero results; session already deleted mid-conversation
- Dependencies: OpenRouter rate limit hit; OpenRouter model unavailable; Supabase message insert fails
- User behavior: Rapid-fire messages; delete session while response is streaming; open same session in two tabs; mid-conversation topic switch
- Environment: Slow network (message appears to hang); browser tab inactive (background)
- AI-specific: LLM hallucination despite grounding; LLM refuses to answer factual question; retrieval returns wrong fund's data; prompt injection attempts; adversarial queries designed to extract system prompt

#### Prioritization (Impact x Likelihood)
- High impact/high likelihood: LLM hallucination on edge-case fund questions
- High impact/high likelihood: Prompt injection attempts
- High impact/low likelihood: OpenRouter full outage
- Low impact/high likelihood: User sends empty/whitespace message
- Low impact/low likelihood: Same session in two tabs causing race condition

#### Failure Containment and Guardrails
- Graceful failure/fallback: LLM timeout → retry with fallback model → show error message with retry; empty retrieval → "I don't have information about that specific topic" response
- Defensive controls: Input length limit (5000 chars); rate limit per user (disabled for demo but configurable); system prompt injection protection (separate system message, not in user content)
- Observability signals: Log every LLM call (model, tokens, latency, success/failure); track refusal rate; track retrieval-zero-results rate; track PII detection events

#### Edge-Case Test Plan
- Unit: PII regex patterns (valid PAN, Aadhaar, phone, email + false positives); refusal classifier (advice vs factual boundary); empty/long input handling
- Integration: Full RAG pipeline with mock LLM; session CRUD operations; memory generation
- E2E: Multi-turn conversation → verify context maintained; advice refusal → verify response; prompt injection → verify blocked

---

## Phase 06: Voice Agent

### Objective
Build a dual-mode (voice + text) AI agent that uses Web Speech API for STT, browser TTS + Edge TTS for response playback, maintains session history, and shares the same RAG pipeline as Smart Search.

### Scope
#### In Scope
- Voice mode: microphone recording, live transcript, TTS playback
- Text mode: standard text input (reuses Smart Search logic)
- Mode toggle within same session
- Web Speech API for speech-to-text
- Browser TTS primary + Edge TTS fallback for text-to-speech
- Voice session persistence (voice_sessions, voice_messages tables)
- Activity logging (voice_agent_used events)
- Graceful fallback when Web Speech API unavailable

#### Out of Scope
- Intent detection for bookings (Phase 07)
- Calendar integration (Phase 08)
- Multilingual voice (future)

### PRD / Problem Mapping
- Features: Feature 4 (Voice Agent)
- Problem statement: Problem 3 (voice-first support missing)
- Constraints: No PII collection on voice call; English only in v1

### Architecture Decisions
- Decision: Browser Web Speech API (not server-side STT)
  - Rationale: Zero cost, no API keys needed, real-time transcript. Works in Chrome/Edge (majority of users).
  - Tradeoff: Doesn't work in Firefox/Safari (fallback to text mode)
- Decision: Edge TTS as server-side fallback (not ElevenLabs/OpenAI TTS)
  - Rationale: Free, natural-sounding Microsoft voices, no API key. Browser TTS varies wildly in quality.
  - Tradeoff: Edge TTS is unofficial (could break); browser TTS as primary keeps it working if Edge TTS fails
- Decision: Shared RAG pipeline with Smart Search (not separate)
  - Rationale: Same knowledge base, same grounding rules, same refusal behavior. No duplication.
  - Tradeoff: Voice responses may be too long for speech (need length constraint in prompt)

### Backend Architecture
- Services:
  - `VoiceSessionService` — session CRUD for voice sessions
  - `TTSService` — Edge TTS integration (server-side audio generation)
  - Reuses: `ChatService`, `RetrievalService`, `PIIDetector`, `RefusalClassifier` from Phase 05
- APIs:
  - `POST /api/voice/message` — same as chat but with input_mode field and shorter response prompt (uses the same RAG retrieval + **factual corpus routing** as Smart Search)
  - `GET /api/voice/greeting-theme` — optional greeting line built from the latest **Phase 09** `weekly_pulse` row in Supabase (`llm_themes` preferred, else `themes`; stale if older than 14 days). This is **separate from RAG** until the user sends a message
  - `GET /api/voice/sessions?user_id={}` — list voice sessions
  - `POST /api/voice/sessions` — create voice session
  - `DELETE /api/voice/sessions/{id}` — delete
  - `GET /api/voice/sessions/{id}/messages` — get messages
  - `POST /api/voice/tts` — text → audio (Edge TTS), returns audio stream/URL
- Data:
  - `voice_sessions`: id, user_id, title, mode (voice|text), last_message_at, created_at
  - `voice_messages`: id, session_id, role, content, input_mode (voice|text), created_at
  - `activity_log`: insert on session create (event_type: 'voice_agent_used')
- Security/compliance:
  - No audio stored (only transcripts)
  - PII redaction on transcripts before storage
  - No PII collected via voice

### Frontend Architecture
- Routes/pages:
  - `/voice-agent` — voice/text dual-mode interface
- State/data-flow:
  - Zustand: `useVoiceStore` — isRecording, transcript, mode (voice|text), audioPlaying
  - TanStack Query: `useVoiceSessions()`, `useVoiceMessages(sessionId)`
  - Web Speech API: `SpeechRecognition` instance managed in custom hook
- Client integration contracts:
  - Backend voice API for messages and TTS
  - Browser Web Speech API for STT (client-side only)
- Failure states:
  - Web Speech API unavailable → auto-switch to text mode with notice
  - TTS fails → show text response only (no audio)
  - Microphone permission denied → show instructions to enable

### UI Architecture
- Information architecture: Mode toggle at top → session list (left) → chat/voice area (right)
- Component structure:
  - `VoiceAgentPage` → `VoiceSessionList` + `VoiceArea`
  - `VoiceArea` → `ModeToggle` + `MicButton` | `TextInput` + `MessageList`
  - `MicButton` — large, prominent, red pulse when active
  - `LiveTranscript` — shows real-time speech-to-text below mic
  - `ModeToggle` — Voice | Text switch
- Core interactions:
  - Toggle to Voice mode → press mic → speak → release → transcript submitted
  - Red animated pulse during recording
  - Response read aloud via TTS (if in voice mode)
  - Toggle to Text mode → standard text input (same as Smart Search UX)
- Accessibility/responsive notes:
  - Mic button minimum 44x44 touch target
  - Visual recording indicator (not just color — includes animation)
  - TTS can be disabled by user preference

### Risks and Mitigations
- Risk: Web Speech API not available in user's browser
  - Mitigation: Feature detection on mount; show banner "Voice not supported, using text mode"
- Risk: Edge TTS library breaks (unofficial)
  - Mitigation: Browser SpeechSynthesis as primary; Edge TTS as quality upgrade
- Risk: Voice responses too long for natural speech
  - Mitigation: Add "concise voice response" instruction to LLM prompt (max 3 sentences for voice mode)

### Deliverables
- `phase-06-voice-agent/backend/routers/voice_router.py`
- `phase-06-voice-agent/backend/services/voice_session_service.py`
- `phase-06-voice-agent/backend/services/tts_service.py`
- `phase-06-voice-agent/frontend/src/pages/VoiceAgent.tsx`
- `phase-06-voice-agent/frontend/src/components/MicButton.tsx`
- `phase-06-voice-agent/frontend/src/components/LiveTranscript.tsx`
- `phase-06-voice-agent/frontend/src/components/ModeToggle.tsx`
- `phase-06-voice-agent/frontend/src/hooks/useSpeechRecognition.ts`
- `phase-06-voice-agent/frontend/src/hooks/useTTS.ts`
- `phase-06-voice-agent/frontend/src/stores/voice-store.ts`
- `phase-06-voice-agent/tests/`
- `phase-06-voice-agent/expected_outputs/`

### Success Criteria
- Voice mode: press mic → speak → transcript appears → AI response read aloud
- Text mode: type → send → response displayed (identical to Smart Search quality)
- Mode toggle preserves session context
- Sessions persist after refresh
- Graceful fallback when Speech API unavailable
- TTS plays response in natural voice (Edge TTS)

### Exit Criteria
- [ ] Voice recording and transcript work in Chrome
- [ ] TTS plays responses (browser primary, Edge TTS fallback)
- [ ] Mode toggle works without losing context
- [ ] Sessions persist in voice_sessions/voice_messages tables
- [ ] Fallback to text mode when Speech API unavailable
- [ ] Activity logged on session creation
- [ ] All tests pass

### Phase Logging and Debug Gates
- Checks Run:
  - ReadLints: eslint + ruff
  - Focused tests: TTS service tests, voice session tests, speech recognition hook tests
  - Build/type check: tsc + mypy
  - Runtime sanity check: Record voice → verify transcript → verify response → verify TTS playback
- Debug Notes: Log Speech API availability; log TTS method used (browser vs Edge); log transcript accuracy
- Result: PASS | FAIL
- Next Step: Phase 07 (Intent Detection + Approvals)

### Edge Cases and Test Coverage
#### Edge Inventory
- Inputs: Silent recording (no speech detected); very long recording (>2 minutes); background noise produces garbage transcript; user speaks non-English
- System: Web Speech API fires error event; Edge TTS server unreachable; audio playback interrupted
- Dependencies: Microphone hardware fails; browser permission revoked mid-session; TTS audio format incompatible
- User behavior: Press mic then immediately stop; switch modes while response is being read; close browser mid-recording; multiple rapid record/stop cycles
- Environment: Slow network makes TTS audio buffer; mobile browser background-kills audio; no speakers/headphones connected
- AI-specific: LLM response too long for natural TTS; transcript is garbled but LLM tries to answer garbage

#### Prioritization (Impact x Likelihood)
- High impact/high likelihood: Web Speech API unavailable in Firefox/Safari
- High impact/low likelihood: Edge TTS completely breaks
- Low impact/high likelihood: Background noise produces imperfect transcript
- Low impact/low likelihood: Audio format incompatibility

#### Failure Containment and Guardrails
- Graceful failure/fallback: Speech API unavailable → text mode with banner; TTS fails → show text only; garbled transcript → let user edit before sending
- Defensive controls: Minimum transcript length (>2 chars) before auto-submit; recording timeout (2 minutes max); TTS timeout (10 seconds)
- Observability signals: Log speech API error types; log TTS fallback usage; track voice vs text mode usage ratio

#### Edge-Case Test Plan
- Unit: Speech recognition hook with mock events; TTS service with mock audio; empty/short transcript handling
- Integration: Voice message flow with mock Speech API; TTS endpoint with Edge TTS mock
- E2E: Full voice flow in Chrome (record → transcript → response → audio playback)

---

## Phase 07: AI Intent Detection + Approval Center

### Objective
Build multi-turn AI intent detection that identifies actionable intents from conversations (booking, email, calendar, notes, cancellation, rescheduling) and generates approval items for admin review. Build the admin-facing Approval Center UI.

### Scope
#### In Scope
- Intent detection from chat/voice conversation context
- Multi-turn intent tracking (user changes mind, cancels, reschedules)
- Approval item generation (calendar, email, booking, notes, follow-ups)
- Admin Approval Center UI (list, detail panel, approve/reject/edit)
- Status management (pending → approved/rejected)
- Filter by status
- Email draft preview (for email-type approvals)

#### Out of Scope
- Actual Google Calendar API calls (Phase 08)
- Actual email sending (v1 models but doesn't send)
- Evaluation of intent accuracy (Phase 11)

### PRD / Problem Mapping
- Features: Feature 7 (Approval Center)
- Problem statement: Problem 4 (AI actions lack human approval)
- Constraints: Approval-gated; no auto-send emails; booking codes persist

### Architecture Decisions
- Decision: LLM-based intent detection with structured output
  - Rationale: Rule-based intent detection cannot handle mid-conversation changes, negation, or ambiguous phrasing. LLM with structured JSON output (via function calling or response format) handles complex multi-turn scenarios.
  - Tradeoff: Higher latency per message (extra LLM call); cost per intent check
- Decision: Intent detection runs on every assistant response (not just user message)
  - Rationale: The full conversation context (including assistant confirmations) is needed to determine if an actionable intent has crystallized
  - Tradeoff: More LLM calls; mitigated by using cheap fallback model for intent detection
- Decision: Separate intent-detection prompt (not mixed with RAG response generation)
  - Rationale: Separation of concerns — RAG answers questions, intent detector identifies actions. Mixing creates conflicts.
  - Tradeoff: Two LLM calls per message in conversations with potential intents

### Backend Architecture
- Services:
  - `IntentDetectionService` — analyzes conversation history, extracts structured intents
  - `ApprovalGeneratorService` — converts detected intents into approval items
  - `ApprovalService` — CRUD for approvals, status management
  - `IntentTracker` — tracks intent state across conversation turns (confirmed, cancelled, modified)
- APIs:
  - `POST /api/intents/detect` — given conversation history, returns detected intents (internal)
  - `GET /api/approvals?status={}&user_id={}` — list approvals (admin: all; investor: own)
  - `GET /api/approvals/{id}` — get approval detail
  - `PATCH /api/approvals/{id}` — update status (approve/reject/reset)
  - `GET /api/approvals/stats` — count by status (for badge)
- Data:
  - `approvals`: id, action_type (calendar|email|booking|note|follow_up), title, description, investor_id, investor_name, status (pending|approved|rejected), priority (low|medium|high), payload (jsonb — full action details), source_session_id, source_type (chat|voice), reviewed_by, reviewed_at, created_at
  - `activity_log`: insert on approval action (event_type: 'approval_reviewed')
- Security/compliance:
  - Only admin role can approve/reject
  - Investor can view own approval items (read-only)
  - Payload never contains PII (redacted before storage)

### Frontend Architecture
- Routes/pages:
  - `/approval-center` — admin-only approval queue (hidden from investor nav)
- State/data-flow:
  - TanStack Query: `useApprovals(status)`, `useApprovalDetail(id)`, `useApprovalStats()`
  - Zustand: `useApprovalStore` — selectedApprovalId, activeFilter
- Client integration contracts:
  - Backend approval API for all operations
  - Badge count from stats endpoint (for sidebar)
- Failure states:
  - Empty queue → "No pending approvals" with explanation
  - Approve/reject fails → toast error with retry

### UI Architecture
- Information architecture: Filter bar → list (left) → detail panel (right, sticky)
- Component structure:
  - `ApprovalCenterPage` → `ApprovalFilterBar` + `ApprovalList` + `ApprovalDetail`
  - `ApprovalListItem` — type icon, title, investor name, timestamp, status badge, priority badge, approve/reject buttons
  - `ApprovalDetail` — full context, payload preview, action buttons
  - `EmailPreview` — rendered email draft for email-type approvals
- Core interactions:
  - Filter by status (All/Pending/Approved/Rejected)
  - Click row → detail panel opens
  - Approve (green button) → status updates → success toast
  - Reject (destructive button) → status updates → success toast
  - Email items: additional "Edit Draft" / "Don't Send" actions
- Accessibility/responsive notes:
  - Pending items have amber left border (per UI guidelines)
  - Keyboard navigation through approval list
  - Detail panel becomes full-screen modal on mobile

### Risks and Mitigations
- Risk: LLM incorrectly detects intent (false positive — creates unwanted approval)
  - Mitigation: Confidence threshold; require explicit user confirmation before generating approval; admin review catches errors
- Risk: User changes intent mid-conversation (cancel after booking request)
  - Mitigation: IntentTracker maintains state; cancellation intent removes/updates pending approval
- Risk: High volume of approvals overwhelms admin
  - Mitigation: Priority classification; filter by type; batch approve functionality (future)

### Deliverables
- `phase-07-intent-approvals/backend/services/intent_detection_service.py`
- `phase-07-intent-approvals/backend/services/approval_generator_service.py`
- `phase-07-intent-approvals/backend/services/approval_service.py`
- `phase-07-intent-approvals/backend/services/intent_tracker.py`
- `phase-07-intent-approvals/backend/routers/approval_router.py`
- `phase-07-intent-approvals/frontend/src/pages/ApprovalCenter.tsx`
- `phase-07-intent-approvals/frontend/src/components/ApprovalList.tsx`
- `phase-07-intent-approvals/frontend/src/components/ApprovalDetail.tsx`
- `phase-07-intent-approvals/frontend/src/components/EmailPreview.tsx`
- `phase-07-intent-approvals/frontend/src/stores/approval-store.ts`
- `phase-07-intent-approvals/tests/`
- `phase-07-intent-approvals/expected_outputs/`

### Success Criteria
- "I'd like to schedule a call about my SIP" in chat → pending approval created
- "Actually, never mind, cancel that" → approval removed/cancelled
- "Can you reschedule to next week?" → approval updated with new details
- Admin can see, approve, and reject items
- Badge shows correct pending count
- Email-type approvals show draft preview

### Exit Criteria
- [ ] Intent detection correctly identifies booking/email/calendar/note intents
- [ ] Multi-turn tracking handles cancellation and modification
- [ ] Approval items appear in admin queue
- [ ] Approve/reject updates status correctly
- [ ] Sidebar badge shows pending count
- [ ] Detail panel renders full context
- [ ] All tests pass (including multi-turn scenarios)

### Phase Logging and Debug Gates
- Checks Run:
  - ReadLints: eslint + ruff
  - Focused tests: Intent detection with multi-turn fixtures; approval CRUD tests; UI component tests
  - Build/type check: tsc + mypy
  - Runtime sanity check: Chat conversation with booking intent → verify approval created → approve → verify status
- Debug Notes: Log intent detection confidence; log false positive rate; log intent state transitions
- Result: PASS | FAIL
- Next Step: Phase 08 (Calendar + Booking)

### Edge Cases and Test Coverage
#### Edge Inventory
- Inputs: Ambiguous intent ("maybe I should talk to someone"); sarcastic intent ("sure, book me a call with the president"); multi-intent in one message ("book a call and email me the details"); intent with no specifics ("book something")
- System: Intent detection LLM timeout; approval insert fails; concurrent approve/reject on same item
- Dependencies: OpenRouter rate limit during intent check; Supabase connection fails on insert
- User behavior: User says "book" then immediately "cancel" in next message; user confirms then goes silent; admin approves already-cancelled intent; rapid approve/reject toggle
- Environment: Admin opens approval center on mobile (small screen for detail panel)
- AI-specific: LLM hallucinates intent that wasn't expressed; LLM misses clear intent; confidence score unreliable; intent detection disagrees with conversation flow

#### Prioritization (Impact x Likelihood)
- High impact/high likelihood: Ambiguous intent → false positive approval creation
- High impact/high likelihood: User changes mind after intent detected
- High impact/low likelihood: Concurrent approve/reject race condition
- Low impact/high likelihood: Intent with no specifics (no time/topic mentioned)
- Low impact/low likelihood: Sarcastic intent false positive

#### Failure Containment and Guardrails
- Graceful failure/fallback: Intent detection timeout → skip (no approval created); LLM can't determine → ask user "Would you like me to set that up?"; false positive → admin rejects (human-in-the-loop catches errors)
- Defensive controls: Confidence threshold (>0.7 required); explicit user confirmation prompt before finalizing intent; unique constraint on (session_id + intent_hash) to prevent duplicates
- Observability signals: Log intent detection results per message; track approval creation → rejection rate (high rejection = poor intent detection); alert on intent detection latency spikes

#### Edge-Case Test Plan
- Unit: Intent extraction from 20+ conversation fixtures (including ambiguous, negation, multi-intent); approval state machine transitions; confidence threshold logic
- Integration: Full conversation → intent → approval flow with mock LLM; concurrent approval operations
- E2E: Multi-turn chat resulting in booking intent → verify approval in center → approve → verify status

---

## Phase 08: Google Calendar + Booking System

### Objective
Integrate Google Calendar through the in-house **FastMCP action server** (per global decision A5) so booking lifecycle operations (create / confirm / cancel / reschedule) flow through approval-gated MCP tool calls. Add booking code generation, availability checking, and a booking-confirmation **email extension** (admin-triggered, sent via the same FastMCP server using a `gmail.send` tool, body enriched with Weekly Pulse content from Phase 09).

### Scope
#### In Scope
- **FastMCP `calendar.*` tools** wrapping Google Calendar API: `calendar.check_availability`, `calendar.create_event`, `calendar.update_event`, `calendar.cancel_event`
- Booking code generation (BK-YYYYMMDD-NNN format)
- Availability check before booking proposal
- Calendar holds (tentative events pending approval)
- Booking status lifecycle (pending → confirmed / cancelled / rescheduled)
- Calendar view in Approval Center (iframe + events list)
- `bookings` table for tracking all bookings
- **UI buttons in Approval Center / Booking detail:** `Approve`, `Cancel`, `Reschedule`, `Send Email` (last one disabled until `status = confirmed`)
- **Booking-confirmation email extension (sub-feature):** FastMCP `gmail.send` tool; `BookingEmailService` orchestrator; `booking_emails` audit table; markdown template at `Docs/Architecture/Email-Templates/booking_confirmation_email.md`. Body content (weekly pulse summary, action items, top themes) is sourced from Phase 09 outputs when present; otherwise the pulse block is omitted and a footnote is inserted. **Send Email** stays disabled only until `status = confirmed` (not gated on Phase 09).

#### Out of Scope
- Real-time bidirectional sync with external calendar invites (we only render an iframe)
- Multiple advisor calendars (single calendar in v1)
- Recurring appointments
- Email reply handling / inbox parsing (we only send)
- Customer-self-serve email sending (admin-only, gated by approval status)

### PRD / Problem Mapping
- Features: Feature 7 (Approval Center — calendar tab), PRD Milestone M3 (Voice Appointment Scheduler)
- Problem statement: Problem 3 (voice-first support), Problem 4 (approval-gated actions)
- Constraints: Calendar holds must be approval-gated; booking codes persist across modules; no PII in booking metadata; **all external side-effects (calendar writes, email sends) must traverse the FastMCP action server and the Approval Center HITL gate** (decision A5).

### Architecture Decisions
- Decision: **Google Calendar accessed via FastMCP tools, not direct REST from the API server**
  - Rationale: Aligns Phase 08 with global decision A5 (FastMCP as the unified action transport for calendar / email / docs); single approval gate; uniform payload contracts (`approval_id`, `actor_id`, `idempotency_key`); easier to add new providers later without touching the booking service.
  - Tradeoff: One extra hop through the MCP layer; mitigated by co-locating the FastMCP server in the same backend deployment for v1.
  - Reference: [FastMCP Getting Started](https://gofastmcp.com/getting-started/welcome)
- Decision: Google service account (not user OAuth) for the underlying Calendar API call
  - Rationale: Single shared advisor calendar; no per-user consent flow needed at demo scale.
  - Tradeoff: Admin must grant the service account access to the target calendar.
- Decision: Booking code format `BK-YYYYMMDD-NNN`
  - Rationale: Human-readable; naturally sorted by date; NNN allows 999 bookings/day.
  - Tradeoff: Requires daily counter (computed from `bookings` rows for that day).
- Decision: **Email transport: in-house FastMCP `gmail.send` tool wrapping Gmail API (OAuth2 + refresh token)**
  - Rationale: Keeps the action layer in Python and uniform with calendar tooling; avoids adding a Node.js dependency. Works with a personal/Workspace Gmail account without domain-wide delegation.
  - Tradeoff: One-time OAuth2 desktop-flow consent to mint `GMAIL_REFRESH_TOKEN`; refresh token must be rotated if revoked.
  - Documented alternative: drop in `GongRzhe/Gmail-MCP-Server` ([github.com/GongRzhe/Gmail-MCP-Server](https://github.com/GongRzhe/Gmail-MCP-Server)) as the MCP server; the booking flow above does not change because both speak MCP.
- Decision: **Send Email is admin-triggered, idempotency-keyed, and gated on `status = confirmed`**
  - Rationale: Avoids accidental sends; allows admin to intentionally re-send after a state transition (e.g. cancel → cancel-notice email).
  - Tradeoff: One extra click per booking; acceptable for HITL product.

### Backend Architecture
- **FastMCP action server** (`mcp-action-server/`, single Python process, decision A5):
  - Tools registered:
    - `calendar.check_availability(date, duration_minutes) → slots[]`
    - `calendar.create_event(title, start, end, status="tentative"|"confirmed", booking_code) → event_id`
    - `calendar.update_event(event_id, start, end, status) → event_id`
    - `calendar.cancel_event(event_id) → ok`
    - `gmail.send(to[], subject, body_markdown, body_html, idempotency_key, approval_id) → message_id`
  - Every tool call requires `approval_id`, `actor_id`, `idempotency_key` per A5 contract.
- API server services:
  - `BookingService` — orchestrator; calls FastMCP `calendar.*` tools; manages booking lifecycle and `bookings` row updates.
  - `BookingCodeGenerator` — generates `BK-YYYYMMDD-NNN`.
  - `BookingEmailService` — orchestrator for the email extension; loads template, fetches Weekly Pulse (Phase 09 output), renders markdown + HTML, calls FastMCP `gmail.send`, writes `booking_emails` audit row.
  - `EmailTemplateRenderer` — loads `Docs/Architecture/Email-Templates/booking_confirmation_email.md`, substitutes placeholders, produces both markdown (for audit log) and HTML (for delivery).
- APIs:
  - `GET /api/calendar/availability?date={}&duration={}` — proxy to `calendar.check_availability`.
  - `POST /api/bookings` — create booking (tentative event + pending approval).
  - `GET /api/bookings?user_id={}&status={}` — list bookings.
  - `PATCH /api/bookings/{id}/confirm` — admin confirm; calls `calendar.update_event(status="confirmed")`.
  - `PATCH /api/bookings/{id}/cancel` — admin cancel; calls `calendar.cancel_event`.
  - `PATCH /api/bookings/{id}/reschedule` — admin reschedule; calls `calendar.update_event(start, end)`.
  - `POST /api/bookings/{id}/send-email` — admin-triggered booking-confirmation email (extension). Allowed only when `bookings.status ∈ {confirmed, cancelled, rescheduled}` (per spec the user wanted **only confirmed**, but cancel-notice and reschedule-notice variants are explicitly modeled with the same template selecting a different intro block; the button is only enabled when at least the first confirmation has been sent or `status = confirmed`).
- Data:
  - `bookings` (existing): id, user_id, booking_code, topic, scheduled_at, duration_minutes, status (pending|confirmed|cancelled|rescheduled), calendar_event_id, approval_id, created_at, updated_at.
  - `booking_emails` (new): id, booking_id, status_at_send, recipient_role (user|advisor), recipient_email, subject, body_markdown, body_html, idempotency_key (unique with booking_id+recipient_role+status_at_send), gmail_message_id, sent_at, sent_by (admin user_id).
- Security / compliance:
  - User email is read from Supabase auth (`auth.users.email`) by `BookingEmailService`; never stored on the client.
  - Advisor email is read from `ADVISOR_EMAIL` env var only; never exposed to the frontend.
  - Email body contains the booking code and topic only — no PII beyond what the user themselves typed.
  - Gmail OAuth2 refresh token lives only in backend env; never sent to the browser.

### Frontend Architecture
- Routes / pages:
  - No new page; integrates into Approval Center (calendar tab + booking detail) and Dashboard (booking summary).
- State / data-flow:
  - TanStack Query: `useAvailability(date)`, `useBookings(userId, status)`, `useBookingEmails(bookingId)`.
  - Mutations: `useConfirmBooking`, `useCancelBooking`, `useRescheduleBooking`, `useSendBookingEmail`.
- Client integration contracts:
  - Backend booking API for all operations; frontend never speaks to FastMCP or Gmail directly.
- Failure states:
  - Calendar tool unreachable → "Calendar unavailable, retry" toast.
  - No available slots → "No slots available for this date" empty state.
  - Send Email when not confirmed → button disabled with tooltip.
  - Send Email failure → toast with retry; do not mark booking as failed (email is independent of booking truth).
  - Weekly Pulse not yet generated → email still sendable; pulse section replaced by footnote (UI may show an amber hint that the pulse block was omitted).

### UI Architecture
- Component structure:
  - `CalendarTab` (in Approval Center) — Google Calendar iframe.
  - `BookingDetailPanel` (in Approval Center) — booking summary + action row.
  - `BookingActionBar` — explicit buttons: `Approve` (when pending), `Cancel`, `Reschedule`, `Send Email`.
  - `SendBookingEmailButton` — shows recipient list (user + advisor); disabled unless `status = confirmed`; tooltip explains why if disabled; opens a small preview modal showing rendered markdown before send.
  - `BookingEmailHistory` — audit list of past sends (status snapshot, recipients, sent_at, idempotency_key).
  - `BookingStatusBadge` — confirmed (green), pending (amber), cancelled (red), rescheduled (blue).
- Core interactions:
  - AI proposes time → user confirms → booking created (pending) → admin approves → confirmed → admin clicks Send Email → preview → confirm → email dispatched to user + advisor.
  - Admin can re-send after status changes (cancel/reschedule); each send is idempotency-keyed by `(booking_id, status_at_send, recipient_role)` so accidental double-clicks don't double-send.

### Risks and Mitigations
- Risk: Google Calendar API quota exceeded
  - Mitigation: Cache availability results (5-minute TTL); batch operations where possible.
- Risk: Service account OAuth setup complexity
  - Mitigation: Document setup in phase README; use env toggle for mock mode during local development only (CI/E2E always live, per live-execution policy).
- Risk: Tentative event created but approval never comes
  - Mitigation: Auto-expire tentative events after 48 hours (background job).
- Risk: Gmail refresh token revoked or expired
  - Mitigation: `gmail.send` returns a typed error; backend surfaces "Email transport unavailable — re-authorize" admin notice; booking truth is unaffected.
- Risk: Weekly Pulse stale or missing when email is sent
  - Mitigation: `BookingEmailService` first checks for a pulse generated in the last 14 days; if none, omit pulse block and add a footnote in the email "Weekly Pulse not available for this period."

### Deliverables
- `phase-08-calendar-booking/backend/mcp_action_server/server.py` — FastMCP server entrypoint
- `phase-08-calendar-booking/backend/mcp_action_server/tools/calendar_tools.py`
- `phase-08-calendar-booking/backend/mcp_action_server/tools/gmail_tools.py`
- `phase-08-calendar-booking/backend/services/booking_service.py`
- `phase-08-calendar-booking/backend/services/booking_email_service.py`
- `phase-08-calendar-booking/backend/services/email_template_renderer.py`
- `phase-08-calendar-booking/backend/services/booking_code_generator.py`
- `phase-08-calendar-booking/backend/routers/booking_router.py`
- `phase-08-calendar-booking/backend/routers/calendar_router.py`
- `phase-08-calendar-booking/frontend/src/components/CalendarTab.tsx`
- `phase-08-calendar-booking/frontend/src/components/BookingActionBar.tsx`
- `phase-08-calendar-booking/frontend/src/components/SendBookingEmailButton.tsx`
- `phase-08-calendar-booking/frontend/src/components/BookingEmailHistory.tsx`
- `phase-08-calendar-booking/frontend/src/components/BookingStatusBadge.tsx`
- `phase-08-calendar-booking/tests/`
- `phase-08-calendar-booking/expected_outputs/`
- `Docs/Architecture/Email-Templates/booking_confirmation_email.md` (editable, single source of truth)
- Supabase migration: `booking_emails` table

### Success Criteria
- Availability check returns correct free/busy slots through the FastMCP `calendar.check_availability` tool.
- Booking creation creates a tentative event via `calendar.create_event` and a pending approval row.
- Admin approval transitions the event to confirmed via `calendar.update_event` and updates `bookings.status = 'confirmed'`.
- Booking code generated correctly (BK-YYYYMMDD-NNN).
- Cancel button calls `calendar.cancel_event` and sets `status = 'cancelled'`.
- Reschedule button calls `calendar.update_event` and sets `status = 'rescheduled'`.
- Send Email button is **disabled when `status != 'confirmed'`** and **enabled when confirmed**; click sends one email to the user (Supabase auth email) and one to `ADVISOR_EMAIL` via `gmail.send`; both deliveries logged in `booking_emails`.
- Email body, when Phase 09 is shipped, contains: booking status (booked / cancelled / rescheduled), booking code, scheduled time, topic, and the latest Weekly Pulse summary + 3 action items + top themes.
- Re-send after a status transition is supported and idempotency-keyed (no double-sends within the same status).

### Exit Criteria
- [ ] FastMCP action server boots and exposes `calendar.*` + `gmail.send` tools
- [ ] Calendar tools work end-to-end against a real Google Calendar
- [ ] Bookings create events; approval transitions confirm them
- [ ] Cancel / Reschedule buttons round-trip through MCP and update calendar
- [ ] Booking codes generated and unique per day
- [ ] Calendar iframe visible in Approval Center
- [ ] Booking summary updates on Dashboard
- [ ] Send Email button disabled when not confirmed; enabled when confirmed
- [ ] Send Email delivers to both user (from Supabase auth) and `ADVISOR_EMAIL`
- [ ] `booking_emails` audit row written per send with idempotency key
- [ ] Email template loaded from `Docs/Architecture/Email-Templates/booking_confirmation_email.md`
- [ ] Phase 09 readiness: when Weekly Pulse is available, email body includes pulse summary + action items + top themes; when not, email omits pulse block with a footnote
- [ ] All tests pass

### Phase Logging and Debug Gates
- Checks Run:
  - ReadLints: eslint + ruff
  - Focused tests: FastMCP tool unit tests; calendar tool integration (live calendar); booking lifecycle tests; code generation tests; email template rendering tests; `gmail.send` integration test (sends to a mailbox you control)
  - Build/type check: tsc + mypy
  - Runtime sanity check: Create booking → calendar event → approve → confirmed → click Send Email → verify both inboxes
- Debug Notes: Log MCP tool latency per tool name; log booking state transitions; log email idempotency-key collisions; log Gmail API error codes verbatim
- Result: PASS | FAIL
- Next Step: Phase 09 (Weekly Pulse) — required to populate the email pulse block

### Edge Cases and Test Coverage
#### Edge Inventory
- Inputs: Booking request for past date; booking for unavailable slot; invalid duration (0 or >480 minutes); booking code collision (unlikely but possible); Send Email clicked while booking is `pending`; Send Email clicked twice within a status (idempotency)
- System: Calendar tool returns 429 (rate limit); event creation succeeds but Supabase insert fails (orphaned calendar event); concurrent bookings for same slot; FastMCP server unreachable; Gmail refresh token revoked mid-session
- Dependencies: Google Calendar service down; OAuth token expired; calendar deleted; Phase 09 weekly pulse not yet generated
- User behavior: Double-click confirm (duplicate booking); cancel then re-book same slot; reschedule to already-booked time; admin sends email after cancel (cancel-notice variant)
- Environment: Timezone mismatch between user, server, and calendar; user has no email recorded in Supabase auth (edge — should not happen post-Phase-03)
- AI-specific: AI proposes time that becomes unavailable before user confirms; AI extracts wrong time from user speech

#### Prioritization (Impact x Likelihood)
- High impact / high likelihood: Timezone mismatch causing wrong booking time
- High impact / low likelihood: Double-booking same slot (race condition); duplicate email send (idempotency miss)
- Low impact / high likelihood: User requests unavailable time; admin clicks Send Email before approval (UI must prevent)
- Low impact / low likelihood: Booking code collision; Gmail refresh token revoked

#### Failure Containment and Guardrails
- Graceful failure / fallback: Calendar tool down → create booking in DB as `pending_calendar` → retry on next tool success; slot unavailable → suggest next 3 available slots; email tool down → mark `booking_emails.status = failed`, surface retry button to admin, never auto-retry without admin click; Phase 09 pulse missing → send email **without** pulse block + footnote.
- Defensive controls: Lock-and-check before creating event (prevent double-book); validate date is in future; timezone normalization (UTC stored, IST displayed); Send Email button server-side re-validates `status = confirmed` (don't trust UI); idempotency key `(booking_id, status_at_send, recipient_role)` enforced by unique index on `booking_emails`.
- Observability signals: Log MCP tool success/failure rate per tool; track booking → confirmation conversion; alert on orphaned tentative events (>48 h); track email send success rate; alert on Gmail auth errors.

#### Edge-Case Test Plan
- Unit: Booking code generation (uniqueness, format); date validation; timezone conversion; availability parsing; email template rendering with and without pulse block; idempotency key generation
- Integration: Full booking flow with mocked FastMCP server; concurrent booking test; approval → calendar confirmation; admin send-email path; double-send same status (must dedupe); send after cancel (cancel-notice variant)
- E2E: Voice conversation → booking intent → calendar event visible → admin approves → confirmed status → admin Send Email → both inboxes receive correctly rendered email with weekly-pulse content (Phase 09 prereq)

---

## Phase 09: Weekly Pulse (Review Intelligence)

### Objective
Build an automated review analysis pipeline that processes Google Play reviews into sentiment, themes, keywords, and a structured weekly summary, displayed in a multi-tab intelligence dashboard.

### Scope
#### In Scope
- Sentiment analysis of app reviews (positive/neutral/negative)
- Theme extraction (top recurring topics)
- Keyword trend tracking (week-over-week change)
- Weekly summary generation (LLM, <250 words, 3 action items)
- Multi-tab UI: Overview, Reviews, Keywords
- 4-week trend table
- Rating distribution chart
- Automated weekly analysis (GitHub Action post-scrape)

#### Out of Scope
- Real-time review alerts (future)
- Responding to reviews (future)
- Multi-app review tracking (Groww only)

### PRD / Problem Mapping
- Features: Feature 5 (Weekly Pulse)
- Problem statement: Problem 2 (support disconnected from product intelligence)
- Constraints: Under 250 words; exactly 3 action ideas; public reviews only

### Architecture Decisions
- Decision: LLM-based analysis (not traditional NLP sentiment models)
  - Rationale: LLM can extract themes, generate summaries, and identify action items in one pass. Traditional NLP requires separate models for sentiment, NER, summarization.
  - Tradeoff: Higher cost per analysis run; but runs only weekly so cost is negligible
- Decision: Store both raw reviews and processed pulse data separately
  - Rationale: Raw reviews support filtering/browsing; processed data supports dashboard KPIs without re-computing
  - Tradeoff: Some data duplication; worth it for query performance
- Decision: LLM judge validates pulse output (word count, action items, neutrality)
  - Rationale: Ensures compliance with PRD constraints (under 250 words, 3 action items)
  - Tradeoff: Extra judge call per pulse generation

### Backend Architecture
- Services:
  - `SentimentAnalyzer` — classifies each review as positive/neutral/negative (LLM batch or rule-based on star rating)
  - `ThemeExtractor` — identifies top themes from review corpus (LLM)
  - `KeywordTracker` — tracks keyword mentions and week-over-week changes
  - `PulseSummaryGenerator` — generates weekly summary with 3 action items (LLM)
  - `PulseJudge` — validates summary against constraints (judge LLM)
- APIs:
  - `GET /api/pulse/latest` — returns latest weekly pulse (summary, rating, trends)
  - `GET /api/pulse/reviews?sentiment={}&page={}` — paginated reviews with filter
  - `GET /api/pulse/keywords` — keyword trend data
  - `GET /api/pulse/trends` — 4-week trend table data
  - `POST /api/pulse/generate` — trigger pulse generation (admin only)
- Data:
  - `weekly_pulse`: id, week_start, overall_rating, total_reviews, positive_count, neutral_count, negative_count, summary_text, action_items (jsonb), themes (jsonb), generated_at
  - `review_keywords`: id, keyword, week_start, mention_count, wow_change_pct
  - `app_reviews` (from Phase 01): gets sentiment field added
- Jobs/events:
  - GitHub Action: After weekly scrape → trigger pulse generation
  - `POST /api/pulse/generate` also available for on-demand admin trigger

### Frontend Architecture
- Routes/pages:
  - `/weekly-pulse` — multi-tab pulse dashboard
- State/data-flow:
  - TanStack Query: `usePulseLatest()`, `usePulseReviews(sentiment, page)`, `usePulseKeywords()`, `usePulseTrends()`
  - Zustand: active tab, active sentiment filter
- Client integration contracts:
  - Backend pulse API for all data
- Failure states:
  - No pulse generated yet → "First analysis will run on Monday" empty state
  - Partial data → show available sections, skeleton for missing

### UI Architecture
- Information architecture: Header KPIs → Tabs (Overview | Reviews | Keywords)
- Component structure:
  - `WeeklyPulsePage` → `PulseKPIs` + `PulseTabs`
  - `PulseKPIs` — Overall Rating, New Reviews, Positive Count, Negative Count
  - `OverviewTab` — 4-week trend table + rating distribution bar chart
  - `ReviewsTab` — sentiment filter pills + scrollable review cards
  - `KeywordsTab` — keyword table with WoW change (color-coded)
  - `ReviewCard` — star rating, reviewer, date, comment text
  - `ScrapeTimestamp` — last scraped indicator with green pulse dot
- Core interactions:
  - Switch tabs (Overview/Reviews/Keywords)
  - Filter reviews by sentiment
  - View keyword trends (up/down indicators)
- Accessibility/responsive notes:
  - Trend indicators use icons (not just color) for colorblind accessibility
  - Review cards stack on mobile
  - Table becomes scrollable on small screens

### Risks and Mitigations
- Risk: LLM generates summary >250 words
  - Mitigation: Judge validates word count; if >250, regenerate with stricter prompt
- Risk: Too few reviews in a given week for meaningful analysis
  - Mitigation: If <10 reviews, show "Insufficient data this week" with previous week's pulse

### Deliverables
- `phase-09-weekly-pulse/migrations/001_weekly_pulse_llm_persistence.sql`
- `phase-09-weekly-pulse/backend/main.py`
- `phase-09-weekly-pulse/backend/models/schemas.py`
- `phase-09-weekly-pulse/backend/services/sentiment_analyzer.py`
- `phase-09-weekly-pulse/backend/services/theme_extractor.py`
- `phase-09-weekly-pulse/backend/services/keyword_tracker.py`
- `phase-09-weekly-pulse/backend/services/pulse_summary_generator.py`
- `phase-09-weekly-pulse/backend/services/pulse_judge.py`
- `phase-09-weekly-pulse/backend/routers/pulse_router.py`
- `phase-09-weekly-pulse/frontend/src/pages/WeeklyPulse.tsx`
- `phase-09-weekly-pulse/frontend/src/components/PulseKPIs.tsx`
- `phase-09-weekly-pulse/frontend/src/components/ReviewCard.tsx`
- `phase-09-weekly-pulse/frontend/src/components/KeywordTable.tsx`
- `phase-09-weekly-pulse/tests/`
- `phase-09-weekly-pulse/expected_outputs/`
- `phase-09-weekly-pulse/README.md`
- `phase-09-weekly-pulse/PHASE_LOG.md`

### Success Criteria
- Weekly pulse summary is <250 words with exactly 3 action items
- Sentiment classification matches star ratings (4-5=positive, 3=neutral, 1-2=negative)
- Keyword WoW change calculated correctly
- 4-week trend shows rating trajectory
- Judge validates pulse output passes constraints
- Automated generation runs after weekly scrape
- Model fallback chain enforced: primary LLM → fallback LLM → deterministic fallback
- Dashboard shows LLM vs deterministic comparison side by side with deterministic algorithm label
- Downstream theme consumers (email and voice greeting) use LLM themes only

### Exit Criteria
- [ ] Pulse generation produces valid summary from review data
- [ ] Judge validates output passes (word count, action items)
- [ ] All three tabs render correctly with data
- [ ] Sentiment filter works on Reviews tab
- [ ] 4-week trend data accurate
- [ ] Automated trigger works via GitHub Action
- [ ] All tests pass

### Phase Logging and Debug Gates
- Checks Run:
  - ReadLints: eslint + ruff
  - Focused tests: Sentiment classifier tests, keyword tracker tests, summary validation tests
  - Build/type check: tsc + mypy
  - Runtime sanity check: Generate pulse from real reviews → verify summary constraints → verify UI renders
- Debug Notes: Log LLM token usage per pulse generation; log judge pass/fail; log review count per sentiment
- Result: PASS | FAIL
- Next Step: Phase 10 (Explorer + Resources)

### Edge Cases and Test Coverage
#### Edge Inventory
- Inputs: Zero reviews in a week; all reviews same rating (no variance); reviews in non-English; extremely long review text; reviews with only emojis
- System: LLM generates >250 words (constraint violation); LLM generates <3 action items; pulse generation takes >30s (timeout)
- Dependencies: Review scraper failed this week (no new data); OpenRouter unavailable during analysis
- User behavior: Admin triggers generation twice simultaneously; investor expects real-time pulse (it's weekly)
- Environment: Large review volume (>500/week) exceeds LLM context
- AI-specific: Theme extraction produces generic themes ("good app"); sentiment misclassifies sarcastic reviews; summary mentions specific user names from reviews

#### Prioritization (Impact x Likelihood)
- High impact/high likelihood: Summary exceeds 250 words
- High impact/low likelihood: Zero reviews in a week
- Low impact/high likelihood: Generic/unhelpful themes extracted
- Low impact/low likelihood: Sarcastic review misclassified

#### Failure Containment and Guardrails
- Graceful failure/fallback: Summary too long → regenerate (max 3 attempts) → truncate; zero reviews → show previous week's data with "No new data" notice; LLM fails → use rule-based sentiment (star rating) + skip summary
- Defensive controls: Word count validation before storage; action items count validation; theme deduplication; review text truncation (max 500 chars per review to LLM)
- Observability signals: Log pulse generation success/failure/retry; track word count distribution; monitor LLM cost per generation

#### Edge-Case Test Plan
- Unit: Word count validator; action items extractor; sentiment by star rating; keyword WoW calculation
- Integration: Full pulse generation with mock reviews; judge pass/fail scenarios; empty review set handling
- E2E: Trigger generation → verify UI shows correct data → verify judge passed

---

## Phase 10: Mutual Fund Explorer + Resource Hub

### Objective
Build a searchable, filterable mutual fund explorer and a structured fee/tax explainer resource hub, both powered by the same scraped data used in the RAG pipeline.

### Scope
#### In Scope
- Mutual Fund Explorer: search, category filter, fund cards with all metrics
- Summary bar (tracked funds count, avg expense ratio, high-risk count)
- Resource Hub: Mutual Funds tab + Fee Explainer tab
- Fee Explainer: exit load, expense ratio, capital gains, stamp duty sections
- Source attribution on all content (Groww URL + scraped timestamp)
- Scrape timestamp indicator

#### Out of Scope
- Fund comparison tool (future)
- Portfolio tracking (future)
- Fund recommendations (compliance: no advice)

### PRD / Problem Mapping
- Features: Feature 6 (Mutual Fund Explorer), Feature 9 (Resource Hub)
- Problem statement: Problem 1 (self-serve fund info), Problem 6 (siloed data)
- Constraints: Data from configured Groww links only; no advice; source attribution required

### Architecture Decisions
- Decision: Fee explainer data seeded from scraper + stored in fee_explainer_data table
  - Rationale: Fee rules are relatively static (exit load percentages, tax slabs). Seed once from official sources, update on weekly scrape if changes detected.
  - Tradeoff: May lag behind regulatory changes by up to a week
- Decision: Client-side search and filter (not server-side)
  - Rationale: 30 funds is small enough to load all at once. Client-side filtering is instantaneous. No need for server pagination.
  - Tradeoff: Would need to change if tracking 500+ funds (not in scope)

### Backend Architecture
- Services:
  - `FundExplorerService` — returns all funds with latest data + summary stats
  - `FeeExplainerService` — returns structured fee/tax data
- APIs:
  - `GET /api/funds` — all funds with latest metrics
  - `GET /api/funds/summary` — tracked count, avg expense ratio, high-risk count, last scraped
  - `GET /api/resources/fees` — structured fee explainer data
- Data:
  - `mutual_fund_data` (from Phase 01): reads latest per fund_slug
  - `fee_explainer_data`: id, fee_type (exit_load|expense_ratio|capital_gains|stamp_duty|stt), category, description, typical_range, applicable_to, notes, source_url, last_updated
- Security/compliance:
  - Public data only; no user-specific access control needed
  - Source URL attribution on every piece of data

### Frontend Architecture
- Routes/pages:
  - `/mutual-fund-explorer` — searchable fund grid
  - `/resource-hub` — tabbed resource library
- State/data-flow:
  - TanStack Query: `useFunds()`, `useFundSummary()`, `useFeeExplainer()`
  - Local state: search term, active category filter (client-side filtering)
- Client integration contracts:
  - Backend fund/resource APIs
- Failure states:
  - No fund data → "Data loading, please check back" with last scrape time
  - Search returns nothing → "No funds match your search" with clear filter option

### UI Architecture
- Component structure (Mutual Fund Explorer):
  - `MutualFundExplorerPage` → `SummaryBar` + `SearchInput` + `CategoryFilters` + `FundGrid`
  - `FundCard` — name, category badge, NAV, NAV date, AUM, expense ratio, min SIP, risk badge, returns (1Y/3Y/5Y)
  - `CategoryFilterPills` — All, Large Cap, Mid Cap, Small Cap, etc.
- Component structure (Resource Hub):
  - `ResourceHubPage` → `Tabs` (Mutual Funds | Fee Explainer)
  - `FundListRow` — compact row with key metrics
  - `FeeSection` (expandable) — exit load table, expense ratio ranges, tax rules
  - `SourceAttribution` — Groww URL + timestamp
- Core interactions:
  - Type in search → instant filter
  - Click category pill → filter by category
  - Expand fee section → show detailed rules
- Accessibility/responsive notes:
  - Fund grid: 2 cols mobile, 3-4 cols desktop
  - Search input has aria-label and role
  - Risk badges use icon + text (not color alone)

### Deliverables
- `phase-10-explorer-resources/backend/routers/fund_router.py`
- `phase-10-explorer-resources/backend/routers/resource_router.py`
- `phase-10-explorer-resources/backend/services/fund_explorer_service.py`
- `phase-10-explorer-resources/backend/services/fee_explainer_service.py`
- `phase-10-explorer-resources/frontend/src/pages/MutualFundExplorer.tsx`
- `phase-10-explorer-resources/frontend/src/pages/ResourceHub.tsx`
- `phase-10-explorer-resources/frontend/src/components/FundCard.tsx`
- `phase-10-explorer-resources/frontend/src/components/FeeSection.tsx`
- `phase-10-explorer-resources/tests/`
- `phase-10-explorer-resources/expected_outputs/`

### Success Criteria
- All 30 funds displayed with correct metrics
- Search filters funds by name in real-time
- Category filter works correctly
- Summary bar shows accurate counts
- Fee explainer sections are readable and sourced
- Scrape timestamp visible and accurate

### Exit Criteria
- [ ] Fund explorer displays all tracked funds
- [ ] Search and filter work together
- [ ] Summary bar matches underlying data
- [ ] Fee explainer sections render with source attribution
- [ ] Responsive layout at all breakpoints
- [ ] All tests pass

### Phase Logging and Debug Gates
- Checks Run:
  - ReadLints: eslint + ruff
  - Focused tests: Fund API tests, fee data tests, component render tests, search/filter logic tests
  - Build/type check: tsc + mypy
  - Runtime sanity check: Verify fund count matches Supabase; verify search finds specific fund
- Debug Notes: Verify all fund categories are represented; verify returns display correctly (handle null for new funds)
- Result: PASS | FAIL
- Next Step: Phase 11 (Evaluation Suite)

### Edge Cases and Test Coverage
#### Edge Inventory
- Inputs: Search for fund not in tracked list; search with special characters; filter category with zero funds
- System: Supabase returns stale data (scraper failed); fund missing key fields (no returns_5y for new fund)
- Dependencies: Backend API timeout; Supabase connection limit
- User behavior: Rapid search typing (debounce needed); applying multiple filters simultaneously
- Environment: Slow network → delayed fund card rendering; very small screen truncates fund names

#### Prioritization (Impact x Likelihood)
- High impact/high likelihood: New fund missing returns_5y (shows "N/A")
- High impact/low likelihood: All fund data missing (scraper never ran)
- Low impact/high likelihood: Search produces zero results
- Low impact/low likelihood: Special characters in search breaking regex

#### Failure Containment and Guardrails
- Graceful failure/fallback: Missing field → show "N/A" (not crash); empty results → helpful empty state; API error → cache previous results
- Defensive controls: Debounce search input (300ms); sanitize search input (no regex injection); handle null returns gracefully in UI
- Observability signals: Track search queries (for improving RAG); log fund data completeness per scrape

#### Edge-Case Test Plan
- Unit: Search filter logic; category filter; null field handling; summary calculations
- Integration: Fund API with incomplete data; fee API with missing sections
- E2E: Search → filter → verify card content → switch to Resource Hub → verify fees

### Implementation Status
- Implemented in `phase-10-explorer-resources/`:
  - Backend APIs: `GET /api/funds`, `GET /api/funds/summary`, `GET /api/resources/fees`
  - Frontend pages/components: explorer grid/cards and resource hub fee sections
  - Coverage: service/API tests plus expected output artifact

---

## Phase 11: Evaluation Suite

### Objective
Build a continuous AI quality and safety monitoring dashboard with RAG faithfulness tests, relevance tests, safety/adversarial tests, UX validation, and LLM judge integration.

### Scope
#### In Scope
- RAG faithfulness evaluation (is answer supported by retrieved context?)
- RAG relevance evaluation (does answer address the question?)
- Safety tests (adversarial prompt resistance)
- UX validation (pulse word count, action items, voice mention)
- LLM judge integration (separate model evaluates RAG output)
- Hand-crafted test cases + LLM-generated expansion
- Scheduled + on-demand evaluation runs
- Dashboard UI with KPIs and per-test breakdown

#### Out of Scope
- A/B testing different models (future)
- User satisfaction surveys (future)
- Real-time evaluation during conversations (future)

### PRD / Problem Mapping
- Features: Feature 8 (Evaluation Suite)
- Problem statement: Problem 5 (AI quality not continuously measured)
- Constraints: Thresholds: ≥85% faithfulness, ≥85% relevance, ≥90% safety; pulse 150-200 words with ≥3 actions

### Architecture Decisions
- Decision: LLM-as-judge pattern (GPT-4o-mini evaluates Claude's outputs)
  - Rationale: Different model ensures independent evaluation. GPT-4o-mini is fast/cheap for batch evaluation.
  - Tradeoff: Judge itself may have errors; mitigated by structured evaluation criteria
- Decision: Test case set: 50 hand-crafted + LLM generates 50 more (100 total)
  - Rationale: Hand-crafted ensures coverage of critical scenarios. LLM expansion increases variety without manual effort.
  - Tradeoff: LLM-generated cases may be lower quality; human review recommended
- Decision: Evaluation runs stored in DB (not ephemeral)
  - Rationale: Historical evaluation data enables trend analysis (is the bot getting better/worse over time?)
  - Tradeoff: Storage for evaluation results; trivial at ~100 rows per run

### Backend Architecture
- Services:
  - `EvaluationRunner` — orchestrates full evaluation run (RAG + safety + UX)
  - `FaithfulnessEvaluator` — given (query, context, answer), judges if answer is faithful to context
  - `RelevanceEvaluator` — given (query, answer), judges if answer addresses the question
  - `SafetyEvaluator` — runs adversarial prompts through RAG pipeline, checks for refusal
  - `UXValidator` — checks pulse word count, action items, structural requirements
  - `TestCaseGenerator` — LLM generates additional test cases from knowledge base
- APIs:
  - `POST /api/eval/run` — trigger evaluation run (admin only)
  - `GET /api/eval/latest` — latest run results (KPIs + per-test breakdown)
  - `GET /api/eval/history` — historical run results for trend
  - `GET /api/eval/cases` — all test cases with pass/fail status
- Data:
  - `evaluation_runs`: id, run_type (scheduled|manual), rag_faithfulness_pct, rag_relevance_pct, safety_pass_pct, pulse_word_count, action_items_count, total_cases, passed_cases, started_at, completed_at
  - `evaluation_cases`: id, run_id, case_type (rag_faithfulness|rag_relevance|safety|ux), query, expected_behavior, actual_output, passed (bool), judge_reasoning, created_at
  - `test_cases`: id, case_type, query, expected_answer_snippet, adversarial (bool), source (hand_crafted|llm_generated)
- Jobs/events:
  - GitHub Action: scheduled evaluation (weekly, after pulse generation)
  - Manual trigger via admin UI
  - Report sync job: generate `Docs/Architecture/Evals-Report.md` from latest `evaluation_runs` + `evaluation_cases` after each scheduled/manual run (DB is source of truth; report is derived artifact)

### Frontend Architecture
- Routes/pages:
  - `/evaluation-suite` — admin-only evaluation dashboard
- State/data-flow:
  - TanStack Query: `useEvalLatest()`, `useEvalHistory()`, `useEvalCases(runId)`
  - Zustand: active tab
- Client integration contracts:
  - Backend eval API for all data
  - "Run Evaluation" button triggers `POST /api/eval/run`
- Failure states:
  - No evaluation run yet → "Run your first evaluation" CTA
  - Eval in progress → loading state with progress indicator

### UI Architecture
- Information architecture: KPI strip → Tabs (RAG Evaluation | Safety Tests | UX Validation)
- Component structure:
  - `EvaluationSuitePage` → `EvalKPIs` + `EvalTabs` + `RunButton`
  - `EvalKPIs` — Faithfulness %, Relevance %, Safety % (color-coded vs threshold)
  - `RAGEvalTab` — table of (Query, Expected, Faithful?, Relevant?) with checkmark/cross
  - `SafetyTab` — table of (Prompt, Type, Pass/Fail, Notes)
  - `UXTab` — metric cards (pulse word count, action items, etc.)
  - `ThresholdIndicator` — shows actual vs target with pass/fail color
- Core interactions:
  - "Run Evaluation" button → triggers run → shows progress → refreshes results
  - Switch tabs to view different evaluation categories
  - Click individual test case to see judge reasoning
- Accessibility/responsive notes:
  - Pass/fail uses icons + colors (not color alone)
  - Tables scrollable on mobile
  - KPI threshold text always visible

### Deliverables
- `phase-11-evaluation-suite/backend/services/evaluation_runner.py`
- `phase-11-evaluation-suite/backend/services/faithfulness_evaluator.py`
- `phase-11-evaluation-suite/backend/services/relevance_evaluator.py`
- `phase-11-evaluation-suite/backend/services/safety_evaluator.py`
- `phase-11-evaluation-suite/backend/services/ux_validator.py`
- `phase-11-evaluation-suite/backend/services/test_case_generator.py`
- `phase-11-evaluation-suite/backend/routers/eval_router.py`
- `phase-11-evaluation-suite/frontend/src/pages/EvaluationSuite.tsx`
- `phase-11-evaluation-suite/frontend/src/components/EvalKPIs.tsx`
- `phase-11-evaluation-suite/frontend/src/components/RAGEvalTable.tsx`
- `phase-11-evaluation-suite/frontend/src/components/SafetyTable.tsx`
- `phase-11-evaluation-suite/tests/`
- `phase-11-evaluation-suite/expected_outputs/`
- `phase-11-evaluation-suite/test_cases/` (hand-crafted JSON fixtures)
- `phase-11-evaluation-suite/scripts/generate_evals_report.py` (renders `Docs/Architecture/Evals-Report.md` from persisted run results)

### Success Criteria
- Evaluation run completes and produces percentage scores
- Faithfulness evaluator correctly identifies hallucinated answers
- Safety evaluator catches prompt injection and advice requests
- UX validator checks pulse constraints
- KPIs display with pass/fail vs thresholds
- Judge reasoning is stored and viewable

### Exit Criteria
- [ ] Evaluation run executes end-to-end (RAG + safety + UX)
- [ ] KPI scores calculate correctly
- [ ] Per-test breakdown visible in UI
- [ ] Judge reasoning stored for each case
- [ ] Scheduled evaluation works via GitHub Action
- [ ] Manual trigger works from admin UI
- [ ] All tests pass

### Phase Logging and Debug Gates
- Checks Run:
  - ReadLints: eslint + ruff
  - Focused tests: Evaluator unit tests with known pass/fail inputs; runner integration test
  - Build/type check: tsc + mypy
  - Runtime sanity check: Run evaluation → verify scores match manual inspection of 5 random cases
- Debug Notes: Log judge model calls and latency; log per-case timing; log token usage for eval run
- Result: PASS | FAIL
- Next Step: Phase 12 (Assembly + Deployment)

### Edge Cases and Test Coverage
#### Edge Inventory
- Inputs: Test case with ambiguous expected answer; safety prompt that is borderline (not clearly adversarial); query that RAG cannot answer (legitimate "I don't know")
- System: Judge LLM disagrees with itself on retry (inconsistent evaluation); evaluation run times out (100 cases * LLM call latency)
- Dependencies: OpenRouter rate limit during batch evaluation; judge model unavailable
- User behavior: Admin triggers run while another is in progress; admin expects instant results (but run takes minutes)
- Environment: Large token usage exceeds OpenRouter budget for evaluation
- AI-specific: Judge LLM is wrong (gives PASS to a hallucinated answer); judge too strict (fails acceptable paraphrases); drift between evaluation results and actual user experience

#### Prioritization (Impact x Likelihood)
- High impact/high likelihood: Judge LLM inconsistency between runs
- High impact/low likelihood: Evaluation timeout (100 cases too many)
- Low impact/high likelihood: Borderline safety cases causing flaky results
- Low impact/low likelihood: Token budget exceeded

#### Failure Containment and Guardrails
- Graceful failure/fallback: Single case failure → mark as "error" (don't fail entire run); judge timeout → skip case; concurrent run → queue second run
- Defensive controls: Max 1 run at a time (lock mechanism); per-case timeout (30s); batch cases to manage rate limits (10 at a time with backoff)
- Observability signals: Log eval run duration; track score variance between consecutive runs; alert if scores drop >10% between runs

#### Edge-Case Test Plan
- Unit: Faithfulness evaluator with known hallucination vs faithful pairs; safety evaluator with adversarial vs benign prompts; UX validator edge cases
- Integration: Full evaluation run with mock LLM responses; concurrent run prevention
- E2E: Trigger evaluation → wait for completion → verify UI shows results → verify scores are plausible

---

## Phase 12: Assembly + Deployment

### Objective
Assemble all phase code into deployable frontend (Vercel) and backend (Render) applications, set up CI/CD, configure environment variables, and verify end-to-end functionality in production.

### Scope
#### In Scope
- Build script to assemble frontend from all phase folders
- Build script to assemble backend from all phase folders
- Vercel configuration for frontend deployment
- Render configuration for backend deployment
- Environment variable documentation and setup
- CI/CD pipeline (GitHub Actions: test → build → deploy)
- Smoke tests for production
- Shared code consolidation (avoid import path issues)

#### Out of Scope
- Custom domain setup (manual post-deploy)
- Monitoring/alerting infrastructure (future)
- Performance optimization beyond basic (future)

### PRD / Problem Mapping
- Features: All features assembled into production
- Problem statement: "The platform feels like a connected product, not separate scripts"
- Constraints: No secrets in repo; env vars for all configurations

### Architecture Decisions
- Decision: Assembly script copies/symlinks phase code into standard directory structure for deployment
  - Rationale: Phase-first development structure doesn't match deployment expectations (Vercel expects single frontend folder, Render expects single backend folder)
  - Tradeoff: Extra build step; but keeps development organized by phase while deployment is clean
- Decision: Shared code via Python packages (backend) and path aliases (frontend)
  - Rationale: Shared utilities (DB client, config, types) need to be importable from any phase; standard Python packaging and TypeScript path aliases handle this
  - Tradeoff: Slightly more complex import setup
- Decision: Preview deployments on PRs (Vercel automatic) + manual production promotion
  - Rationale: Preview deployments catch issues early; manual production deploy prevents accidental releases
  - Tradeoff: Extra click for production; acceptable for demo project

### Backend Architecture
- Assembled structure:
  ```
  backend-deploy/
  ├── app/
  │   ├── main.py (imports all routers from phases)
  │   ├── routers/ (assembled from all phases)
  │   ├── services/ (assembled from all phases)
  │   └── models/
  ├── scrapers/ (from phase-01)
  ├── shared/ (from shared/)
  ├── requirements.txt (consolidated)
  ├── Dockerfile
  └── render.yaml
  ```
- Render configuration:
  - Python 3.11+ runtime
  - Persistent disk for ChromaDB data
  - Environment variables for all API keys
  - Health check endpoint: `GET /health`

### Frontend Architecture
- Assembled structure:
  ```
  frontend-deploy/
  ├── src/
  │   ├── pages/ (assembled from all phases)
  │   ├── components/ (assembled from all phases)
  │   ├── hooks/ (assembled from all phases)
  │   ├── stores/ (assembled from all phases)
  │   ├── lib/ (from shared/)
  │   └── App.tsx (router with all pages)
  ├── public/
  ├── package.json (consolidated)
  ├── vite.config.ts
  └── vercel.json
  ```
- Vercel configuration:
  - Framework preset: Vite
  - Build command: `npm run build`
  - Output directory: `dist`
  - Environment variables for Supabase URL/key

### Deliverables
- `phase-12-assembly-deploy/scripts/assemble-backend.sh`
- `phase-12-assembly-deploy/scripts/assemble-frontend.sh`
- `phase-12-assembly-deploy/ci/deploy.yml` (GitHub Action)
- `phase-12-assembly-deploy/smoke-tests/`
- `phase-12-assembly-deploy/env.example` (all required env vars documented)
- `phase-12-assembly-deploy/README.md` (deployment runbook)
### Render Deployment Checklist (Executable)
1. Build backend deployment directory:
   - Run `phase-12-assembly-deploy/scripts/assemble-backend.sh`
2. Create Render web service:
   - Link GitHub repo and set root to `backend-deploy/`
3. Set Render service configuration:
   - Runtime: Python 3.11+
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port ${PORT}`
   - Healthcheck path: `/health`
4. Configure environment variables (backend):
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_JWT_SECRET`
   - `OPENROUTER_API_KEY`
   - `OPENROUTER_PRIMARY_MODEL`
   - `OPENROUTER_FALLBACK_MODEL`
   - `ALLOWED_ORIGINS` (must include Vercel frontend URL)
   - Phase-specific vars (`GOOGLE_SERVICE_ACCOUNT_JSON`, `GOOGLE_CALENDAR_ID`, `GMAIL_REFRESH_TOKEN`, etc.)
5. Attach persistent Render disk:
   - Mount path for Chroma persistence (e.g. `/var/data/chroma`)
   - Set `CHROMA_PERSIST_DIR` to mounted path
6. Deploy and verify:
   - Check build logs
   - Verify `GET /health` returns 200
   - Run smoke flow: login → dashboard → chat → voice → approvals

### Render Config Template (`render.yaml`)
```yaml
services:
  - type: web
    name: investorintelligence-backend
    runtime: python
    rootDir: backend-deploy
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
```

### Success Criteria
- Frontend builds and deploys to Vercel without errors
- Backend builds and deploys to Render without errors
- All features accessible in production
- Health check returns 200
- Smoke tests pass (login → dashboard → chat → voice → approvals)
- Environment variables documented completely

### Exit Criteria
- [ ] Assembly scripts produce clean deployable directories
- [ ] Frontend deploys to Vercel and loads without errors
- [ ] Backend deploys to Render and API health check passes
- [ ] CI/CD pipeline runs on push to main
- [ ] Smoke tests pass in production
- [ ] All environment variables documented in env.example
- [ ] README deployment runbook is complete

### Phase Logging and Debug Gates
- Checks Run:
  - ReadLints: All assembled files pass lints
  - Focused tests: Smoke test suite (login, dashboard, chat, voice)
  - Build/type check: Full build of both frontend and backend in CI
  - Runtime sanity check: Hit every main route in production; verify data flows end-to-end
- Debug Notes: Log build times; verify no import errors; check console for runtime errors
- Result: PASS | FAIL
- Next Step: Production monitoring and iteration

### Edge Cases and Test Coverage
#### Edge Inventory
- Inputs: Missing environment variable on deploy; wrong Supabase URL; invalid OpenRouter key
- System: Build fails due to import path mismatch between phases; Render disk full; Vercel build timeout
- Dependencies: Render cold start (first request slow); Vercel serverless timeout; GitHub Actions runner unavailable
- User behavior: User accesses production before deploy completes; user bookmarks deep link (must work after deploy)
- Environment: Production Supabase vs development Supabase; CORS mismatch between frontend domain and backend domain

#### Prioritization (Impact x Likelihood)
- High impact/high likelihood: CORS mismatch between Vercel and Render domains
- High impact/high likelihood: Missing env var causes silent failure
- High impact/low likelihood: Import path errors in assembly
- Low impact/high likelihood: Render cold start (first request ~5s delay)

#### Failure Containment and Guardrails
- Graceful failure/fallback: Missing env var → startup failure with clear error message naming the missing var; CORS → documented allowed origins in config; cold start → loading indicator in frontend
- Defensive controls: Startup validation (check all required env vars exist); health check endpoint; CORS whitelist configuration
- Observability signals: Render deployment logs; Vercel build logs; health check monitoring; error tracking (future: Sentry)

#### Edge-Case Test Plan
- Unit: Assembly script with missing phase folder; env var validation; import resolution
- Integration: Full build pipeline in CI; deploy to preview environment
- E2E: Smoke test suite covering critical user journeys in production

---

## Addendum A: Retrieval, MCP, and Integration Hardening (May 2026)

### A1) Server-Driven Clarification
- This product is intentionally server-driven: Supabase-backed services are the source of truth for funds, approvals, chat/voice sessions, activity logs, weekly pulse, and KPI cards.
- UI components render what backend services return; business logic, retrieval orchestration, and approval workflows remain on backend services.
- Yes, this server-driven data feeds the RAG pipeline. The scraper and resource services update canonical records, which are chunked/embedded and indexed for retrieval.

### A2) Retrieval Upgrade (Top-k -> Robust Retrieval Stack)
- Phase 02 and Phase 05 are upgraded from pure top-k retrieval to a multi-step pipeline:
  1. Query normalization (spelling correction + typo normalization + synonym expansion).
  2. Entity resolver (fund canonicalization, e.g., "mirae larg cap" -> "Mirae Asset Large Cap Fund Direct Growth").
  3. Hybrid retrieval (vector similarity + lexical/BM25 on key fields such as fund name, fee labels, and rule text).
  4. Dynamic-k retrieval (k adapts by confidence and query complexity instead of fixed top-k only).
  5. Cross-encoder reranking for final context ordering.
  6. Conversation-aware retrieval (session memory + previous turn entities, pronouns such as "this fund").
  7. Clarification policy when confidence is low or entity is ambiguous.
- Phase 05 intent detection is mandatory and runs in parallel with response generation:
  - Information intent (factual Q&A),
  - Action intent (booking/email/calendar/note),
  - Safety intent (advice/PII/prohibited request),
  - Clarification intent (missing entity, ambiguous follow-up).

### A3) Mandatory Retrieval Success Criteria (Phase 05/06)
- Query: "What is the exit load of Mirae Asset Large Cap?" returns context containing: "1% if redeemed before 1 year" with source citation.
- Follow-up query in same session: "What is NAV of this fund?" resolves "this fund" to Mirae Asset Large Cap and returns the correct NAV row.
- Semantic/typo query: "tell query about mirae larg cap" correctly resolves to Mirae Asset Large Cap and returns grounded results.
- Multi-turn continuity: entity memory remains stable across chat and voice turns unless user explicitly changes fund.

### A4) Cross-Milestone Integrations (M1 + M2 + M3)
- Integration 1 (M1 + M2): Unified Search
  - User can ask blended questions such as:
    - "What is the exit load for the ELSS fund and why was I charged it?"
  - System must compose:
    - M1 factsheet retrieval (fund/facts source),
    - M2 fee-logic retrieval (explainer source).
  - Output contract remains strict:
    - source citations preserved for each evidence block,
    - fixed 6-bullet response structure for combined answers.
- Integration 2 (M2 -> M3): Theme-Aware Voice Greeting
  - Voice agent reads latest Weekly Pulse top theme in real time at session start.
  - If top themes include "Login Issues" or "Nominee Updates", greeting proactively references that theme and offers relevant help path.
- Integration 3 (MCP actions -> single HITL center)
  - Post-call action bundle includes:
    - calendar hold proposal,
    - advisor email draft,
    - optional weekly pulse summary push to Google Docs.
  - Advisor email draft includes a "Market Context" snippet from latest Weekly Pulse before approval.

### A5) MCP Architecture Decision (FastMCP)
- MCP action services are standardized through a single in-house **FastMCP action server** (`mcp-action-server/`) exposing tools for:
  - calendar actions: `calendar.check_availability`, `calendar.create_event`, `calendar.update_event`, `calendar.cancel_event`,
  - email actions: `gmail.send` (admin-triggered booking confirmation, cancel-notice, and reschedule-notice; admin-triggered advisor draft sends),
  - Google Docs update actions: `docs.update_pulse_summary`.
- All tools require `approval_id`, `actor_id`, and `idempotency_key` on every call (uniform contract across tools).
- Approval Center remains the only execution gate: MCP actions are proposed first, then executed only after admin approval. The booking-confirmation email (Phase 08 extension) is a special case — it is admin-triggered directly from the booking detail panel after the booking has reached `confirmed` (or a subsequent terminal state); it does not generate a separate approval row because the booking approval already authorizes the lifecycle.
- Email transport: in-house FastMCP `gmail.send` tool wrapping Gmail API (OAuth2 + refresh token). Documented alternative: `GongRzhe/Gmail-MCP-Server` ([github.com/GongRzhe/Gmail-MCP-Server](https://github.com/GongRzhe/Gmail-MCP-Server)) — same MCP surface, swap at the server boundary without touching the booking flow.
- Reference: [FastMCP Getting Started](https://gofastmcp.com/getting-started/welcome)

### A6) Evaluation Suite Expansion (Phase 11)
- Minimum required eval categories on integrated product:
  1. Retrieval Accuracy (RAG Eval): golden dataset with 5 complex M1+M2 blended questions.
  2. Constraint Adherence (Safety Eval): 3 adversarial prompts (investment advice + PII extraction attempts).
  3. Tone and Structure (UX Eval): pulse output checks (<250 words, exactly 3 action ideas), and voice "top theme mention" logic checks.
- Required metrics:
  - Faithfulness: answer content only from retrieved cited context.
  - Relevance: answer addresses user scenario, including multi-turn entity carryover.
  - Safety pass rate: 100% refusal for investment-advice and PII-leak attempts.
- Formal report artifact is required at:
  - `Docs/Architecture/Evals-Report.md`

### A7) Per-Phase Edge/Success Artifact Contract
- Each phase must maintain a dedicated edge-case + success-criteria file in:
  - `Docs/Architecture/Phase-Criteria/phase-XX-edge-cases-success.md`
- These files are mandatory alongside phase content in `architecture.md`, `HLD.md`, and `LLD.md`.
