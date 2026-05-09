# High Level Design (HLD)

## System Context (Global)

### Actors
| Actor | Description | Access Level |
|-------|-------------|-------------|
| Investor | Retail mutual fund investor, uses chat/voice/dashboard | Read own data, write messages/bookings |
| Admin | Fund operations staff, manages approvals and quality | Full platform access, approve/reject actions |
| Scraper Bot | Automated GitHub Action, ingests data weekly | Write to mutual_fund_data and app_reviews |
| LLM (Primary) | Claude 3.5 Sonnet via OpenRouter, generates RAG responses | Read retrieved context, generate responses |
| LLM (Judge) | GPT-4o-mini via OpenRouter, evaluates quality | Read outputs + criteria, return verdicts |
| LLM (Fallback) | Gemini Flash via OpenRouter, degraded mode | Same as primary with simpler prompts |

### External Systems
| System | Purpose | Protocol | Auth |
|--------|---------|----------|------|
| Supabase | PostgreSQL database + Auth + RLS | HTTPS (REST + JS SDK) | API key + JWT |
| OpenRouter | LLM API gateway (Claude, GPT, Gemini) | HTTPS REST | API key |
| Google OAuth | User authentication | OAuth 2.0 | Client ID/Secret |
| Google Calendar API | Availability + event management | HTTPS REST | Service Account JWT |
| Groww (web) | Mutual fund data source (scraped) | HTTPS (browser automation) | None (public) |
| Google Play Store | App review data source (scraped) | HTTPS (library) | None (public) |
| Edge TTS | Server-side text-to-speech | Websocket | None (unofficial) |
| GitHub Actions | Scheduled job execution | GitHub API | GITHUB_TOKEN |

## Global Component Map

```
┌────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Vercel)                                │
│  React 19 + Vite + TanStack Query + Zustand                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │  Login   │ │Dashboard │ │  Smart   │ │  Voice   │ │ Approval │   │
│  │  Page    │ │  Page    │ │  Search  │ │  Agent   │ │  Center  │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                              │
│  │  Weekly  │ │  Fund    │ │  Eval    │                              │
│  │  Pulse   │ │Explorer/ │ │  Suite   │                              │
│  │          │ │Resources │ │          │                              │
│  └──────────┘ └──────────┘ └──────────┘                              │
└───────────────────────────────┬────────────────────────────────────────┘
                                │ HTTPS (REST API)
┌───────────────────────────────┼────────────────────────────────────────┐
│                         BACKEND (Render)                                 │
│  Python FastAPI                                                          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                   │
│  │  Auth Router  │ │  Chat Router │ │ Voice Router │                   │
│  └──────────────┘ └──────────────┘ └──────────────┘                   │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                   │
│  │Dashboard Rtr │ │Approval Rtr  │ │  Eval Router │                   │
│  └──────────────┘ └──────────────┘ └──────────────┘                   │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                   │
│  │Booking Rtr   │ │  Pulse Rtr   │ │  Fund Router │                   │
│  └──────────────┘ └──────────────┘ └──────────────┘                   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │                      SERVICE LAYER                           │       │
│  │  ChatService │ RAGRetrieval │ IntentDetection │ TTS         │       │
│  │  MemoryService │ PIIDetector │ CalendarService │ Booking    │       │
│  │  PulseGenerator │ EvalRunner │ FundExplorer                 │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                       │
│  │  ChromaDB   │  │  Embedding │  │  Scrapers  │                       │
│  │ (embedded)  │  │  Service   │  │            │                       │
│  └────────────┘  └────────────┘  └────────────┘                       │
└───────────────────────────────┬────────────────────────────────────────┘
                                │
┌───────────────────────────────┼────────────────────────────────────────┐
│                    EXTERNAL SERVICES                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                 │
│  │ Supabase │ │OpenRouter│ │  Google  │ │  GitHub  │                 │
│  │(Postgres)│ │  (LLMs)  │ │Calendar  │ │  Actions │                 │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘                 │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 01: Data Ingestion (Scraping Pipeline)

### High-Level Components
- Component: MutualFundScraper
  - Responsibility: Navigate Groww fund pages via Playwright, extract structured data
  - Dependencies: Playwright, Groww website availability
- Component: MutualFundSchemaMigration
  - Responsibility: Keep `mutual_fund_data` schema aligned with newly scraped fields before batch writes
  - Dependencies: Supabase SQL migration execution
- Component: ReviewScraper
  - Responsibility: Fetch Google Play reviews for Groww app using paginated pull within a 60-day lookback window
  - Dependencies: google-play-scraper library, Google Play availability
- Component: ReviewCleaner
  - Responsibility: Filter out non-English, harmful/profane, and <5-word reviews before persistence
  - Dependencies: Text heuristics/profanity list
- Component: DataValidator
  - Responsibility: Validate scraped data against schema before insert
  - Dependencies: None (pure logic)
- Component: SupabaseWriter
  - Responsibility: Batch insert validated data to Supabase
  - Dependencies: Supabase client, network
- Component: GitHubAction (weekly-scrape)
  - Responsibility: Orchestrate weekly scraping job
  - Dependencies: GitHub Actions runner, all scraper components

### Integration View
- MutualFundScraper → DataValidator:
  - Protocol: In-process function call
  - Contract: Returns list of validated FundData objects or validation errors
- DataValidator → SupabaseWriter:
  - Protocol: In-process function call
  - Contract: Accepts list of valid FundData, returns insert count + failures
- SupabaseWriter → Supabase:
  - Protocol: HTTPS REST (supabase-py client)
  - Contract: Batch INSERT into mutual_fund_data; idempotent UPSERT into app_reviews on `review_id` to tolerate rolling-window reruns
- GitHub Action → Scraper:
  - Protocol: Python subprocess execution
  - Contract: Exit code 0 = success; non-zero = failure (partial results logged)

### Data Flow (Narrative)
1. GitHub Action triggers on schedule (Monday 6 AM IST) or manual dispatch
2. Installs Playwright + Chromium in runner
3. MutualFundScraper launches headless browser, visits each of 30 URLs (5 concurrent)
4. For each URL: wait for page render → extract data using CSS selectors → build FundData dict
5. DataValidator checks each FundData: required fields present, types correct, values in bounds
6. Valid records passed to SupabaseWriter for batch INSERT (with scraped_at = now())
7. ReviewScraper paginates Google Play newest reviews until 60-day cutoff
8. ReviewCleaner drops non-English/profane/<5-word rows
9. Reviews validated and batch-inserted to app_reviews table
10. Action summary reports: X/30 funds scraped, Y raw reviews fetched, Y' cleaned reviews inserted, Z validation errors

### Security and Compliance
- AuthN/AuthZ model: GitHub Action authenticates to Supabase via service-role key (bypasses RLS for batch insert)
- Data classification: All scraped data is public. No PII in fund data or reviews (reviewer names are public Google Play names)
- Audit/approval controls: None needed (batch data ingestion, no user-facing actions)

### Scalability and Reliability
- Scaling expectations: Fixed at 30 URLs + variable review volume over 60 days. Pagination is required for reviews; if review volume increases significantly, cap max pages with alerting.
- Failure domains: Individual URL failure is isolated (partial success); Supabase outage blocks all writes
- Recovery strategy: On failure, GitHub Action can be manually re-triggered. Previous data remains valid. New scrape appends (never deletes old data).

### Open Questions
- None (all resolved in Q&A)

### Success Criteria
- 30/30 fund URLs scraped with all required fields
- Reviews are collected for the last 60 days and cleaned with policy filters before insert
- Data validated and inserted to Supabase
- GitHub Action completes within 10 minutes

### Exit Criteria
- [ ] Tables populated with valid data
- [ ] Action runs successfully on schedule
- [ ] Partial failure handling verified

### Logging and Debug Requirements
- Required checks: Scraper output log (per-URL timing, success/failure); Supabase insert count; validation error details
- Escalation: If >5 URLs fail consecutively, investigate Groww page structure change

### Edge-Case Design
- 5-category inventory: URL 404 (handled, skip); page structure changed (detection via empty required fields); rate limiting by Groww (2s delay between pages); Supabase batch insert partial failure (retry failed rows); Google Play scraper blocked (fallback to cached data); review cleaning over-filters data
- Containment: Each URL scraped independently; failure of one does not stop others
- Observability: GitHub Action summary annotation shows success/failure counts; Supabase data has scraped_at for freshness tracking

---

## Phase 02: RAG Pipeline (Embeddings + Vector Store)

### Principle: structured source of truth + retrieval text layer

Data may be **unstructured on the source website**, but Phase 01 stores **validated, structured records** in Supabase. That is by design: schemas, RLS, and downstream features depend on typed columns. **RAG is not blocked by structured storage:** Phase 02 reads those rows and **materializes natural-language chunks** (facts + descriptions + long-text fields as needed), then embeds and searches them in the vector store. So: **Postgres = canonical structured data; vector index = derived retrieval layer**—complementary layers, not “unstructured DB vs structured DB.”

### High-Level Components
- Component: ChunkingService
  - Responsibility: Transform fund data rows into hybrid chunks (facts + a combined description); regex-extract canonical exit-load and tax rule lines from Groww's run-together copy; build **fee explainer narrative chunks** (one per `fee_type`) from `fee_explainer_data`
  - Dependencies: Supabase (reads `mutual_fund_data`, `fee_explainer_data`)
- Component: EmbeddingService
  - Responsibility: Generate dense vectors with primary `BAAI/bge-large-en-v1.5` (1024-dim); fall back to `all-MiniLM-L6-v2` (384-dim) if primary fails to load
  - Dependencies: sentence-transformers, model weights on disk
- Component: ChromaService
  - Responsibility: Manage the persistent ChromaDB collection (`mutual_fund_knowledge`, cosine distance) — create, delete-and-recreate on refresh, upsert, query, full-document export
  - Dependencies: ChromaDB embedded instance, persistent disk (`CHROMA_PERSIST_DIR`)
- Component: LexicalIndex (BM25)
  - Responsibility: In-memory BM25 sidecar built from the Chroma documents; covers exact-phrase / fee-rule retrieval
  - Dependencies: `rank-bm25`
- Component: EntityResolver
  - Responsibility: Map fuzzy/shorthand fund mentions (e.g., "mirae larg cap") to a canonical `fund_slug` (Addendum A2 step 2)
  - Dependencies: `rapidfuzz`
- Component: RetrievalService
  - Responsibility: Hybrid retrieval — query normalization, entity resolution, vector + BM25 retrieval fused via Reciprocal Rank Fusion, dynamic-k confidence widening; optional **corpus filter** (`mutual_fund` | `fee_explainer`) for intent-scoped queries (Phase 05 / 06)
  - Dependencies: EmbeddingService, ChromaService, LexicalIndex, EntityResolver
- Component: RAGPipeline (orchestrator)
  - Responsibility: Compose the modules above into the two end-to-end flows (`refresh()`, `get_retrieval()`); rebuild BM25 + EntityResolver after each refresh and after process restart
  - Dependencies: ChunkingService, EmbeddingService, ChromaService, LexicalIndex, EntityResolver

### Integration View
- ChunkingService → Supabase:
  - Protocol: HTTPS REST (supabase-py)
  - Contract: SELECT latest mutual_fund_data grouped by fund_slug; SELECT `fee_explainer_data` for narrative chunking on refresh
- ChunkingService → EmbeddingService:
  - Protocol: In-process call
  - Contract: List of text chunks → list of 1024-dim float vectors
- EmbeddingService → ChromaService:
  - Protocol: In-process call
  - Contract: Vectors + metadata → stored in collection
- RetrievalService → EmbeddingService:
  - Protocol: In-process call
  - Contract: Query string → 1024-dim vector
- RetrievalService → ChromaService:
  - Protocol: In-process call
  - Contract: Query vector + top_k → list of (chunk_text, metadata, distance)

### Data Flow (Narrative)
1. Refresh triggered (post-scrape, manual CLI, or `POST /api/rag/refresh`)
2. RAGPipeline calls SupabaseReader → returns the latest row per `fund_slug` (max `scraped_at`) **and** fee explainer rows
3. ChunkingService produces ~8–9 chunks per fund (≈262 chunks for the 30-fund Mirae corpus) **plus** ~5 fee-explainer narrative chunks (one per canonical `fee_type` when data exists):
   - Fact chunks per populated field: `category`, `nav`, `aum_cr`, `expense_ratio`, `min_sip`, `risk_level`, `returns`, `exit_load`, `tax`
   - Regex extracts the active rule line out of long Groww copy (e.g., "Exit load of 1% if redeemed within 1 year") so the chunk isn't dominated by glossary noise
   - One combined `description` chunk concatenates the populated facts + the extracted exit-load rule
4. EmbeddingService encodes all chunks in a single batch (BGE-large primary; falls back to MiniLM if BGE fails to load) with `normalize_embeddings=True`
5. ChromaService deletes any existing collection then creates a fresh one (cosine distance) and `add()`s the documents+embeddings+metadata
6. RAGPipeline rebuilds the in-memory BM25 LexicalIndex and EntityResolver from the new corpus
7. **On query**:
   - Resolve fuzzy fund mention to a canonical `fund_slug` (or `None`; skipped when retrieving the fee-explainer corpus)
   - Vector arm — embed the query (BGE query-instruction prefix), `chroma.query()` with optional `where` (`fund_slug` and/or `corpus` as implemented)
   - Lexical arm — BM25 search; same fund filter and corpus filter applied post-hoc
   - Fuse with Reciprocal Rank Fusion (`k_const=60`)
   - Dynamic-k — widen the result set when best vector confidence is low
   - Return diagnostics: `resolved_fund_slug`, `used_dynamic_k`, `embedding_model_used`, `query_time_ms`

### Security and Compliance
- AuthN/AuthZ model: RAG pipeline is internal (not exposed directly to users). Access via authenticated backend APIs only.
- Data classification: Vector store contains only public fund information (no user data, no PII)
- Audit/approval controls: N/A

### Scalability and Reliability
- Scaling expectations: ~450 chunks, ~450 vectors. ChromaDB handles millions; this is trivial.
- Failure domains: Embedding model load failure (blocks refresh); ChromaDB disk corruption (rebuilt from Supabase)
- Recovery strategy: ChromaDB is rebuildable from Supabase (source of truth). Model can be redownloaded.

### Success Criteria
- Collection contains ~260 chunks from 30 funds (live: 262)
- Query returns relevant results in <500ms steady-state (cold first call ~10s due to lazy model load)
- Precision >80% on the 20-query benchmark (live: **95% top-3 precision**)
- Mandatory query — "What is the exit load of Mirae Asset Large Cap?" — returns the active rule chunk ("Exit load of 1% if redeemed within 1 year") as top-1 (verified)

### Exit Criteria
- [ ] Collection populated and queryable
- [ ] Retrieval benchmark passes
- [ ] Refresh endpoint works end-to-end

### Logging and Debug Requirements
- Required checks: Chunk count per fund; embedding batch timing; collection size; query latency distribution
- Escalation: If retrieval precision drops below 70%, investigate chunking strategy or model

### Edge-Case Design
- Missing fund data → skip fund during chunking (log warning)
- Very short text (<10 chars) → skip chunk (bad embedding quality)
- Embedding model OOM → fall back to all-MiniLM-L6-v2 (smaller)
- ChromaDB corruption → trigger full rebuild from Supabase
- Observability: Log chunk count delta between refreshes; track query latency P50/P95/P99

---

## Phase 03: Authentication + User Management

### High-Level Components
- Component: Supabase Auth
  - Responsibility: Handle Google OAuth flow, session management, JWT issuance
  - Dependencies: Google OAuth consent screen, Supabase project config
- Component: UserProfileService (backend)
  - Responsibility: CRUD for user_profiles, role management
  - Dependencies: Supabase (user_profiles table)
- Component: AuthProvider (frontend)
  - Responsibility: Wrap app with auth context, manage session state
  - Dependencies: Supabase JS client, Zustand store
- Component: LoginPage (frontend)
  - Responsibility: Role selector + OAuth trigger
  - Dependencies: AuthProvider, Supabase Auth

### Integration View
- Frontend → Supabase Auth:
  - Protocol: HTTPS (supabase-js SDK)
  - Contract: signInWithOAuth({provider:'google'}) → session with JWT
- Frontend → Backend (UserProfileService):
  - Protocol: HTTPS REST
  - Contract: `GET /api/users/me` and `POST /api/users/profile` → user profile JSON
- Backend → Supabase (user_profiles):
  - Protocol: HTTPS REST (supabase-py)
  - Contract: SELECT/INSERT/UPDATE with RLS using service-role key

### Data Flow (Narrative)
1. User visits /login → selects role (Investor/Admin)
2. Clicks "Sign in with Google" → Supabase Auth redirects to Google consent
3. User authenticates with Google → redirect back with code
4. Supabase exchanges code for tokens → creates auth.users row → issues JWT
5. Frontend receives session → stores in Zustand
6. Frontend calls GET /api/users/me with JWT (404 if no row yet)
7. On 404, frontend POST /api/users/profile with pending role + OAuth email/metadata (idempotent UPSERT)
8. If first_login_complete = false → frontend shows email capture modal
9. User submits email → POST /api/users/profile updates first_login_complete = true
10. Redirect to /dashboard with role-appropriate navigation

### Security and Compliance
- AuthN/AuthZ model: Google OAuth (no passwords stored); JWT in httpOnly cookie or localStorage; role checked on every protected API call
- Data classification: Email (PII but necessary for profile display); role (not sensitive)
- Audit/approval controls: Login events logged to activity_log

### Scalability and Reliability
- Scaling expectations: 1-5 concurrent users (demo). Supabase Auth handles 50K MAU free.
- Failure domains: Google OAuth outage (no login possible); Supabase Auth outage (same)
- Recovery strategy: Session persists in localStorage; refresh token handles silent re-auth

### Success Criteria
- OAuth flow completes < 5 seconds
- Session persists across refresh
- Role correctly determines navigation access

### Exit Criteria
- [ ] Login → dashboard flow complete
- [ ] Role-based access enforced
- [ ] First-login modal works once

### Logging and Debug Requirements
- Log auth state transitions (anonymous → authenticated → expired)
- Log profile CRUD operations
- Track login success/failure rate

### Edge-Case Design
- OAuth popup blocked → show manual redirect link
- Duplicate profile creation (race condition) → UPSERT with ON CONFLICT
- Session expired mid-use → silent refresh attempt → if fails, redirect to login
- User in two tabs → shared session via localStorage events
- Observability: Log login events in activity_log; track role distribution

---

## Phase 04: Dashboard + App Shell

### High-Level Components
- Component: AppShell (frontend)
  - Responsibility: Sidebar + topbar + main content area
  - Dependencies: AuthProvider (for role), React Router (for navigation)
- Component: DashboardPage (frontend)
  - Responsibility: Renders KPIs, fund strip, bookings, pulse preview
  - Dependencies: Dashboard API, TanStack Query
- Component: DashboardService (backend)
  - Responsibility: Calculates KPIs with time windows and trends
  - Dependencies: Supabase (activity_log, bookings, mutual_fund_data)

### Integration View
- Frontend (DashboardPage) → Backend (DashboardService):
  - Protocol: HTTPS REST
  - Contract: GET /api/dashboard/kpis → {login_sessions, chatbot_sessions, voice_sessions, bookings, trends}
- Backend → Supabase:
  - Protocol: HTTPS REST
  - Contract: Aggregate queries on activity_log, bookings, mutual_fund_data

### Data Flow (Narrative)
1. User lands on /dashboard after login
2. TanStack Query fires: useKPIs(), useFundStrip(), useBookings(), usePulsePreview()
3. Backend receives requests with user_id and role from JWT
4. DashboardService: queries activity_log with time windows (7-day current, 7-day previous)
5. Calculates trend_pct per KPI: ((current - previous) / previous) * 100
6. Returns KPI values + trend values + fund strip data
7. Frontend renders KPI cards with values, trends, and icons per UI guidelines
8. Fund strip maps mutual_fund_data to fund rows (name, category, NAV, date)
9. Booking summary counts from bookings table grouped by status

### Security and Compliance
- AuthN/AuthZ model: JWT required; role determines data scope (investor: own user_id; admin: all)
- Data classification: KPIs are aggregate (no PII); fund data is public
- Audit/approval controls: N/A (read-only dashboard)

### Scalability and Reliability
- Scaling expectations: Dashboard queries are simple aggregates on indexed tables. Fast at any demo scale.
- Failure domains: Supabase slow query (KPI calculation with large activity_log)
- Recovery strategy: TanStack Query shows cached data while refetching; skeleton on initial load

### Success Criteria
- Dashboard loads in <2 seconds
- KPIs scoped correctly by role
- Responsive layout at all breakpoints

### Exit Criteria
- [ ] All KPI cards render with data
- [ ] Role scoping verified
- [ ] Fund strip shows latest data
- [ ] Empty states handled

### Logging and Debug Requirements
- Log API response times for dashboard endpoints
- Verify KPI formulas match PRD Section 5.2
- Track cache hit rates in TanStack Query

### Edge-Case Design
- Zero activity → show 0 with "No data yet" subtitle (not error state)
- Division by zero in trend → show "New" badge instead of percentage
- Fund data empty (scraper never ran) → show "Awaiting first data refresh" in fund strip
- Observability: Log dashboard load times; track which KPIs are always zero (indicates unused features)

---

## Phase 05: Smart Search (RAG Chatbot)

### High-Level Components
- Component: ChatService (backend)
  - Responsibility: Orchestrate RAG pipeline end-to-end (PII → intent → refusal → retrieval → LLM → response)
  - Dependencies: RetrievalService, LLMClient, PIIDetector, RefusalClassifier, IntentRouter, MemoryService
- Component: PIIDetector (backend)
  - Responsibility: Detect and redact PII patterns from user input
  - Dependencies: Regex patterns (PAN, Aadhaar, phone, email)
- Component: IntentRouter (backend)
  - Responsibility: Classify every user turn into factual/action/safety/clarification intent (mandatory per Addendum A2)
  - Dependencies: Rule-based pattern matching
- Component: RefusalClassifier (backend)
  - Responsibility: Identify advice/unsafe requests that should be refused
  - Dependencies: Rule-based patterns
- Component: LLMClient (backend)
  - Responsibility: OpenRouter API client with primary model + fallback chain
  - Dependencies: OpenRouter API (Claude 3.5 Sonnet primary, Gemini Flash fallback)
- Component: MemoryService (backend)
  - Responsibility: Generate and retrieve cross-session conversation summaries
  - Dependencies: OpenRouter (for summary generation), Supabase (user_memory table)
- Component: SmartSearchPage (frontend)
  - Responsibility: Chat UI with sessions, messages, input, optimistic updates
  - Dependencies: Chat API, TanStack Query, Zustand

### Integration View
- Frontend → Backend (ChatService):
  - Protocol: HTTPS REST (POST /api/chat/message)
  - Contract: {session_id, content} → {role: "assistant", content, citations}
- ChatService → PIIDetector:
  - Protocol: In-process
  - Contract: raw_text → {clean_text, redacted_items[]}
- ChatService → RefusalClassifier:
  - Protocol: In-process
  - Contract: clean_text → {should_refuse: bool, reason?: string}
- ChatService → RetrievalService:
  - Protocol: In-process
  - Contract: query → top-k chunks with metadata
- ChatService → OpenRouter:
  - Protocol: HTTPS REST
  - Contract: system_prompt + context + conversation → assistant response
- ChatService → MemoryService:
  - Protocol: In-process (async)
  - Contract: session_messages → updated summary (stored)

### Data Flow (Narrative)
1. User types message in chat input → frontend sends POST /api/chat/message
2. PIIDetector scans input → redacts if PII found → warns user via response metadata
3. RefusalClassifier checks if message is advice request → if yes, return refusal response immediately
4. RetrievalService embeds cleaned query → searches ChromaDB → returns top-5 chunks
5. ChatService builds prompt: system instruction + user memory summary + retrieved context + conversation history + current question
6. OpenRouter call (Claude 3.5 Sonnet) → generates grounded response with citations
7. If LLM call fails → retry with fallback model (Gemini Flash) → if still fails → error response
8. Response stored in chat_messages → returned to frontend
9. Frontend displays assistant message with citations
10. Async: MemoryService checks if summary needs update (every 5 messages) → generates new summary

### Security and Compliance
- AuthN/AuthZ model: JWT required; user can only access own sessions
- Data classification: Chat messages may contain sensitive questions (but PII is redacted); stored in Supabase with RLS
- Audit/approval controls: All messages logged; refusal events logged separately

### Scalability and Reliability
- Scaling expectations: 1-5 concurrent users. LLM calls are the bottleneck (~2-5s per response).
- Failure domains: OpenRouter outage (no responses); ChromaDB query failure (no retrieval)
- Recovery strategy: Fallback model chain (Claude → Gemini → error message); ChromaDB rebuild if corrupted

### Success Criteria
- Grounded answers for factual questions
- Refusal for advice requests
- <5 second response time (including LLM call)
- Cross-session memory works

### Exit Criteria
- [ ] RAG pipeline produces grounded answers
- [ ] Refusal behavior correct
- [ ] PII redaction works
- [ ] Memory persists across sessions
- [ ] All UI states handled

### Logging and Debug Requirements
- Log per-message: retrieval time, LLM model used, token count, latency, refusal triggered (y/n), PII detected (y/n)
- Track: average response time, refusal rate, retrieval-empty rate, fallback model usage
- Escalation: If response time >10s consistently, investigate LLM provider latency

### Edge-Case Design
- Prompt injection → system prompt is separate (not in user-controllable context); output filtered for system prompt leakage
- Empty retrieval → LLM instructed to say "I don't have specific information about that"
- Very long conversation → truncate older messages from context (keep last 10 + summary)
- Concurrent messages from same user → queue and process sequentially per session
- Observability: Log all LLM interactions for evaluation suite; track hallucination indicators

---

## Phase 06: Voice Agent

### High-Level Components
- Component: VoiceAgentPage (frontend)
  - Responsibility: Dual-mode UI (voice + text), recording controls, TTS playback
  - Dependencies: Web Speech API, useSpeechRecognition hook, TTS hook
- Component: useSpeechRecognition (frontend hook)
  - Responsibility: Manage browser SpeechRecognition API lifecycle
  - Dependencies: Browser Web Speech API
- Component: useTTS (frontend hook)
  - Responsibility: Play TTS audio (browser primary, Edge TTS fallback)
  - Dependencies: Browser SpeechSynthesis, backend TTS endpoint
- Component: TTSService (backend)
  - Responsibility: Generate audio from text via Edge TTS
  - Dependencies: edge-tts Python library
- Component: VoiceSessionService (backend)
  - Responsibility: Session CRUD, message storage with input_mode
  - Dependencies: Supabase (voice_sessions, voice_messages)

### Integration View
- Frontend (useSpeechRecognition) → Browser Web Speech API:
  - Protocol: Browser API
  - Contract: start() → onresult(transcript) / onerror(error)
- Frontend → Backend (Voice message):
  - Protocol: HTTPS REST
  - Contract: POST /api/voice/message {session_id, content, input_mode} → {response, audio_url?}
- Frontend → Backend (TTS):
  - Protocol: HTTPS REST
  - Contract: POST /api/voice/tts {text} → audio/mpeg stream
- Backend (VoiceSessionService) → ChatService:
  - Protocol: In-process
  - Contract: Reuses RAG pipeline from Phase 05 (same retrieval, same LLM, same refusal)

### Data Flow (Narrative)
1. User toggles to Voice mode → mic button becomes prominent
2. User presses mic → useSpeechRecognition.start() → browser requests mic permission
3. User speaks → onresult fires with interim transcripts → displayed live below mic
4. User presses mic again (or silence timeout) → final transcript captured
5. Transcript sent to POST /api/voice/message with input_mode: "voice"
6. Backend: same pipeline as Smart Search (PII check → refusal check → RAG → LLM response)
7. Response prompt includes "Keep response under 3 sentences (voice mode)"
8. Response returned + frontend triggers TTS
9. useTTS: try browser SpeechSynthesis → if quality poor or unavailable → request Edge TTS from backend
10. Audio plays to user; response also displayed as text in message list

### Security and Compliance
- AuthN/AuthZ model: Same as Smart Search (JWT + session ownership)
- Data classification: No audio stored (only text transcripts); PII redacted from transcripts
- Audit/approval controls: Voice sessions logged to activity_log

### Scalability and Reliability
- Scaling expectations: 1-2 concurrent voice users (demo). Edge TTS is lightweight.
- Failure domains: Web Speech API unavailable (Firefox/Safari); Edge TTS server unreachable
- Recovery strategy: Speech API fail → text mode; Edge TTS fail → browser TTS; both fail → text only

### Success Criteria
- Voice recording produces accurate transcript
- TTS reads response naturally
- Mode toggle preserves context
- Fallbacks work when APIs unavailable

### Exit Criteria
- [ ] Voice recording works in Chrome
- [ ] TTS playback works
- [ ] Mode toggle works
- [ ] Fallbacks verified

### Logging and Debug Requirements
- Log: Speech API availability per session; TTS method used; transcript length; voice session count
- Track: voice vs text usage ratio; TTS fallback frequency
- Escalation: If Edge TTS fails >50% of attempts, investigate library status

### Edge-Case Design
- No microphone → show "Please connect a microphone" message
- Speech not detected (silence) → after 10s, stop recording with "No speech detected"
- Background noise → let user review/edit transcript before sending
- Browser permission denied → show manual permission instructions
- Observability: Track transcript word error rate (if verifiable); log TTS generation time

---

## Phase 07: AI Intent Detection + Approval Center

### High-Level Components
- Component: IntentDetectionService (backend)
  - Responsibility: Analyze conversation context, extract structured action intents
  - Dependencies: OpenRouter (Gemini Flash for cost-effective intent detection), conversation history
- Component: IntentTracker (backend)
  - Responsibility: Track intent state across turns (detected → confirmed → cancelled → modified)
  - Dependencies: Session state, IntentDetectionService output
- Component: ApprovalGeneratorService (backend)
  - Responsibility: Convert confirmed intents into approval items
  - Dependencies: IntentTracker, Supabase (approvals table)
- Component: ApprovalService (backend)
  - Responsibility: CRUD for approvals, status management, stats
  - Dependencies: Supabase (approvals table)
- Component: ApprovalCenterPage (frontend)
  - Responsibility: Admin queue UI with list, detail, actions
  - Dependencies: Approval API, Zustand, TanStack Query

### Integration View
- ChatService/VoiceService → IntentDetectionService:
  - Protocol: In-process (async, runs after each assistant response)
  - Contract: conversation_history → {intents: [{type, confidence, details, status}]}
- IntentDetectionService → OpenRouter:
  - Protocol: HTTPS REST
  - Contract: Structured prompt requesting JSON output → parsed intent objects
- IntentDetectionService → IntentTracker:
  - Protocol: In-process
  - Contract: new_intents + previous_state → updated_state (handles cancellation/modification)
- IntentTracker → ApprovalGeneratorService:
  - Protocol: In-process (triggered when intent is confirmed)
  - Contract: confirmed_intent → approval item inserted into Supabase
- Frontend → Backend (ApprovalService):
  - Protocol: HTTPS REST
  - Contract: GET/PATCH /api/approvals → approval list/status update

### Data Flow (Narrative)
1. User says "Can you book a call with an advisor about my ELSS fund?" in chat/voice
2. After assistant responds, IntentDetectionService runs on full conversation context
3. LLM extracts: {type: "booking", confidence: 0.85, details: {topic: "ELSS fund discussion"}}
4. IntentTracker: new intent detected, status = "detected"
5. Assistant response includes: "Would you like me to set up a call with an advisor about your ELSS fund?"
6. User: "Yes, sometime next week"
7. IntentTracker: confidence increased, details enriched {time_preference: "next week"}, status = "confirmed"
8. ApprovalGeneratorService creates approval item: {action_type: "booking", title: "Advisor call - ELSS fund", status: "pending", priority: "medium", payload: {topic, time_preference}}
9. If user later says "Actually, cancel that" → IntentTracker updates status to "cancelled" → approval removed/cancelled
10. Admin sees pending approval in Approval Center → reviews → approves (triggers Phase 08 calendar flow)

### Security and Compliance
- AuthN/AuthZ model: Only admin can approve/reject; investor can view own approvals (read-only)
- Data classification: Approval payloads contain action details (no PII — redacted upstream)
- Audit/approval controls: This IS the approval layer — all AI actions gated here

### Scalability and Reliability
- Scaling expectations: Few approvals per day (demo). No scaling concern.
- Failure domains: Intent detection LLM failure (no approvals created); approval insert failure
- Recovery strategy: Intent detection failure → skip (no false positives created); admin can manually create approvals

### Success Criteria
- Intent correctly detected from natural conversation
- Multi-turn tracking handles cancellation/modification
- Admin queue functional with approve/reject
- Badge count accurate

### Exit Criteria
- [ ] Intent detection works for booking/email/calendar/note/follow-up types
- [ ] Cancellation and modification handled
- [ ] Approval Center UI fully functional
- [ ] Admin can approve/reject

### Logging and Debug Requirements
- Log: intent detection per message (type, confidence, decision); approval state transitions; admin actions
- Track: intent false positive rate (approvals rejected immediately); intent detection latency
- Escalation: If >30% approvals rejected, intent detection threshold needs tuning

### Edge-Case Design
- Ambiguous intent → lower confidence → ask user for confirmation before creating approval
- Contradictory intents in same message → take most recent/explicit one
- Admin approves while user cancels → check approval status before executing
- Concurrent intent detection calls → idempotency via (session_id + intent_hash)
- Observability: Log intent confidence distribution; track user confirmation rate

---

## Phase 08: Google Calendar + Booking System

**Implementation folder:** `phase-08-calendar-booking/` (FastAPI + in-process `McpBridge` + optional `python -m backend.mcp_action_server.server`).

### High-Level Components
- Component: **MCPActionServer (FastMCP, in-process or sidecar)**
  - Responsibility: Single point of egress for calendar and email side-effects; exposes `calendar.*` and `gmail.send` MCP tools.
  - Dependencies: Google Calendar API (service account); Gmail API (OAuth2 + refresh token); FastMCP runtime.
  - Decision reference: [A4 — MCP Consolidation via FastMCP](#a4-mcp-consolidation-via-fastmcp).
- Component: BookingService (backend)
  - Responsibility: Booking lifecycle (create, confirm, cancel, reschedule); orchestrates MCP `calendar.*` calls; never speaks to Google Calendar directly.
  - Dependencies: MCPActionServer, ApprovalService, BookingCodeGenerator.
- Component: BookingCodeGenerator (backend)
  - Responsibility: Generate unique BK-YYYYMMDD-NNN codes
  - Dependencies: Supabase (count existing bookings for today)
- Component: **BookingEmailService (backend, Phase 08 email extension)**
  - Responsibility: Admin-triggered booking-confirmation email; loads markdown template, fetches Weekly Pulse (Phase 09), renders user + advisor variants, calls MCP `gmail.send`, writes audit row.
  - Dependencies: MCPActionServer (`gmail.send`), Supabase (auth user email lookup), Phase 09 pulse store, EmailTemplateRenderer.
- Component: **EmailTemplateRenderer (backend)**
  - Responsibility: Loads the editable template at `Docs/Architecture/Email-Templates/booking_confirmation_email.md`, substitutes placeholders, returns markdown + HTML.
  - Dependencies: Filesystem, simple Mustache-style placeholder engine.
- Component: **BookingActionBar (frontend)**
  - Responsibility: Renders the four explicit buttons — `Approve`, `Cancel`, `Reschedule`, `Send Email`. Send Email is disabled unless `bookings.status = 'confirmed'` (also re-checked server-side).
  - Dependencies: Booking API; user role from auth (admin only).

### Integration View
- ApprovalService (approve action) → BookingService:
  - Protocol: In-process (webhook-style trigger on approval).
  - Contract: approved_booking_intent → booking confirmed via MCP, calendar event updated.
- BookingService → MCPActionServer (FastMCP):
  - Protocol: MCP (stdio or HTTP/SSE depending on deployment shape).
  - Contract: `{tool: "calendar.create_event"|"calendar.update_event"|"calendar.cancel_event", arguments: {...}, approval_id, actor_id, idempotency_key}` → MCP tool result.
- MCPActionServer → Google Calendar API:
  - Protocol: HTTPS REST (google-api-python-client).
  - Contract: Service account OAuth2 → event CRUD.
- BookingEmailService → MCPActionServer (FastMCP):
  - Protocol: MCP.
  - Contract: `{tool: "gmail.send", arguments: {to, subject, body_markdown, body_html, idempotency_key}, approval_id, actor_id}` → message_id.
- MCPActionServer → Gmail API:
  - Protocol: HTTPS REST.
  - Contract: OAuth2 refresh-token → `users.messages.send`.
- BookingEmailService → Supabase Auth:
  - Protocol: Supabase admin SDK.
  - Contract: `auth.admin.getUserById(user_id) → email`.
- BookingEmailService → Phase 09 Weekly Pulse store:
  - Protocol: In-process Supabase read.
  - Contract: `weekly_pulse latest where generated_at > now()-14d → {summary, action_items, themes}` (nullable; if null, email omits the pulse block).
- Frontend → Backend (BookingService / BookingEmailService):
  - Protocol: HTTPS REST.
  - Contract: GET /api/bookings, GET /api/calendar/availability, PATCH /api/bookings/{id}/{confirm|cancel|reschedule}, POST /api/bookings/{id}/send-email.

### Data Flow (Narrative)
1. Intent confirmed (from Phase 07) → ApprovalGenerator creates booking approval.
2. Admin approves → BookingService.confirm(approval_id).
3. BookingService: generate booking code (BK-YYYYMMDD-NNN).
4. BookingService → MCP `calendar.check_availability` for preferred time → if available, MCP `calendar.create_event` (confirmed).
5. If unavailable → suggest alternatives → create with closest available slot.
6. Booking record created/updated in Supabase: `{booking_code, scheduled_at, status: "confirmed", calendar_event_id}`.
7. On cancel: BookingService → MCP `calendar.cancel_event` → booking status = "cancelled".
8. On reschedule: BookingService → MCP `calendar.update_event` → booking status = "rescheduled" → new time stored.
9. **Email extension (admin-triggered):** Admin clicks `Send Email` (only enabled when `status = confirmed`). Backend re-validates status, then BookingEmailService:
   - Looks up user email from Supabase auth and reads `ADVISOR_EMAIL` from env.
   - Reads latest Weekly Pulse (if available, last 14 d).
   - Renders the markdown template twice (user variant, advisor variant) with placeholders `{user_name}`, `{booking_code}`, `{status}`, `{scheduled_at}`, `{topic}`, `{pulse_summary}`, `{pulse_action_items}`, `{top_themes}`.
   - Calls MCP `gmail.send` once per recipient with idempotency key `(booking_id, status_at_send, recipient_role)`.
   - Writes one row to `booking_emails` per recipient.
10. Subsequent state transitions (cancel, reschedule) re-enable the button so admin can send updated notices; idempotency key prevents accidental re-send within the same status.

### Security and Compliance
- AuthN/AuthZ: Service account for Calendar; OAuth2 refresh token for Gmail (server-side only, never on client). Admin-only for all mutating endpoints (enforced at API + RLS).
- Data classification: Calendar events contain booking code + topic only (no PII). Email bodies contain user-typed topic + booking code + (optional) public pulse summary. No sensitive PII.
- Secrets: All Gmail/Calendar credentials in backend env, never in frontend code or Supabase rows.
- Audit: `booking_emails` row per send is the source of truth; idempotency key enforced by DB unique index.
- Approval: Calendar lifecycle is approval-gated (Phase 07). The send-email action does **not** create a new approval row because the underlying booking approval already authorizes the lifecycle; admin click is the explicit human-in-the-loop step.

### Scalability and Reliability
- Scaling expectations: 1–5 bookings per day; ≤10 emails per day (demo).
- Failure domains: Google Calendar API outage; service account token expiry; Gmail OAuth refresh token revoked; FastMCP server crash.
- Recovery strategy:
  - Calendar tool fail → booking persisted as `pending_calendar` → retry button + background retry on next success.
  - Gmail tool fail → `booking_emails.status = failed`; admin retry button; never auto-retry without click.
  - FastMCP server crash → BookingService surfaces "Action server unavailable"; no calendar/email writes succeed silently.

### Success Criteria
- Availability check returns correct free/busy slots via MCP `calendar.check_availability`.
- Booking creates calendar event via MCP `calendar.create_event`.
- Booking code generated and unique.
- Cancel/Reschedule round-trip through MCP and update calendar.
- Send Email button disabled when status ≠ confirmed.
- Send Email delivers to user (Supabase auth email) + `ADVISOR_EMAIL` and writes one audit row each.
- When Phase 09 has produced a recent pulse, email body includes summary + 3 action items + top themes; otherwise email omits the pulse block with a footnote.
- Re-send after status transition works; same-status re-send is deduped by idempotency key.

### Exit Criteria
- [ ] FastMCP action server boots; `calendar.*` and `gmail.send` tools registered
- [ ] Calendar tools work end-to-end against a real calendar
- [ ] Bookings create events; approvals confirm them
- [ ] Cancel / Reschedule buttons work via MCP
- [ ] Codes are unique per day
- [ ] Send Email button disabled on non-confirmed bookings
- [ ] Send Email delivers to user + advisor
- [ ] `booking_emails` audit row written with idempotency key
- [ ] Email template loaded from `Docs/Architecture/Email-Templates/booking_confirmation_email.md` and editable
- [ ] Phase 09 readiness: pulse block included when available, gracefully omitted when not

### Logging and Debug Requirements
- Log: MCP tool calls (tool name, latency, success/failure, idempotency_key); booking state transitions; code generation; email send result with Gmail message_id.
- Track: booking conversion rate (intent → approval → confirmed); MCP tool error rate per tool; email send success rate.
- Escalation: Calendar tool consistently failing → check service account credentials/quota; Gmail tool consistently failing → re-mint refresh token (OAuth2 desktop flow).

### Edge-Case Design
- Concurrent booking for same slot → lock-then-check pattern (optimistic with retry).
- Timezone mismatch → all times stored/compared in UTC, displayed in IST.
- Calendar API quota exceeded → queue and retry with backoff.
- Orphaned tentative events → background job cleans up events >48 h old without matching confirmed booking.
- Send Email when booking is `pending` → UI button disabled + server returns 409 if called directly.
- Double-click Send Email → idempotency key collision returns existing `booking_emails` row, does not re-send.
- Weekly Pulse missing or >14 days old → email rendered without pulse block + explicit footnote.
- User has no email in Supabase auth (edge — should never happen post-Phase-03) → server returns 422 with actionable message; advisor email still sent.
- Gmail refresh token revoked → typed error surfaced to admin with "Re-authorize email transport" CTA; booking truth unaffected.
- Observability: Track tentative → confirmed conversion time; track booking → email-sent latency; alert on orphaned events; alert on Gmail auth errors.

---

## Phase 09: Weekly Pulse (Review Intelligence)

### High-Level Components
- Component: SentimentAnalyzer (backend)
  - Responsibility: Classify reviews as positive/neutral/negative
  - Dependencies: Star rating (rule-based primary) + LLM for ambiguous cases
- Component: ThemeExtractor (backend)
  - Responsibility: Identify top recurring themes from reviews
  - Dependencies: OpenRouter (LLM batch analysis)
- Component: KeywordTracker (backend)
  - Responsibility: Track keyword frequency and week-over-week change
  - Dependencies: Supabase (review_keywords table)
- Component: PulseSummaryGenerator (backend)
  - Responsibility: Generate weekly summary (<250 words, 3 action items)
  - Dependencies: OpenRouter (Primary LLM + fallback LLM), PulseJudge, deterministic fallback
- Component: PulseJudge (backend)
  - Responsibility: Validate summary against constraints
  - Dependencies: OpenRouter (GPT-4o-mini)

### Integration View
- GitHub Action (post-scrape) → PulseSummaryGenerator:
  - Protocol: HTTPS REST (triggers POST /api/pulse/generate)
  - Contract: Trigger → generates pulse from latest reviews → stores in weekly_pulse
- PulseSummaryGenerator → SentimentAnalyzer:
  - Protocol: In-process
  - Contract: reviews[] → reviews_with_sentiment[]
- PulseSummaryGenerator → ThemeExtractor:
  - Protocol: In-process
  - Contract: reviews_with_sentiment[] → themes[]
- PulseSummaryGenerator → PulseJudge:
  - Protocol: In-process
  - Contract: summary_text → {pass: bool, issues: []}
- Phase 06 Voice Router → weekly_pulse:
  - Protocol: Supabase data API (service role via backend)
  - Contract: reads latest `llm_themes` for greeting theme mention.

### Data Flow (Narrative)
1. Weekly scrape completes → GitHub Action triggers POST /api/pulse/generate
2. PulseSummaryGenerator fetches reviews from current week (app_reviews with review_date in last 7 days)
3. SentimentAnalyzer: classify each review (4-5 stars = positive, 3 = neutral, 1-2 = negative)
4. ThemeExtractor: batch reviews to LLM → extract top 5 themes with example quotes
5. KeywordTracker: extract keywords, compare to previous week → calculate WoW change
6. PulseSummaryGenerator: sends themes + sentiment stats to primary LLM → on failure retry strict prompt then fallback LLM → if both fail use deterministic fallback
7. PulseJudge validates: word count ≤250? action items = 3? neutral tone?
8. If judge fails → regenerate (max 3 attempts) → store best attempt
9. Store in weekly_pulse table with all metrics
10. Frontend displays on next load via /api/pulse/latest

### Security and Compliance
- AuthN/AuthZ model: Generation endpoint admin-only; read endpoints available to all authenticated users
- Data classification: Reviews are public data; summaries are derived insights (no PII)
- Audit/approval controls: Judge validates every summary before storage
- Integration rule: downstream consumers (Phase 08 email pulse block, Phase 06 voice greeting theme mention) must use LLM themes only.

### Scalability and Reliability
- Scaling expectations: ~100-200 reviews per week. Single LLM call for summary.
- Failure domains: LLM generates non-compliant summary; too few reviews for analysis
- Recovery strategy: Judge → regenerate loop (max 3); <10 reviews → show previous week's data

### Success Criteria
- Summary under 250 words with 3 action items
- Sentiment classification matches star ratings
- Keyword trends calculated correctly
- Judge passes summary before storage

### Exit Criteria
- [ ] Pulse generation works end-to-end
- [ ] Judge validates output
- [ ] UI renders all three tabs
- [ ] Automated trigger works

### Implementation Status
- Implemented in `phase-09-weekly-pulse/` with API router, backend services, frontend page/components, and tests.

### Logging and Debug Requirements
- Log: Pulse generation time, LLM token usage, judge pass/fail, retry count
- Track: Word count distribution, action items consistency, theme quality
- Escalation: If judge fails 3x consecutively, alert for manual review
- Track fallback path usage: `primary_llm`, `fallback_llm`, `deterministic_fallback`.

### Edge-Case Design
- Zero reviews in a week → show "Insufficient data" with previous pulse preserved
- All reviews same sentiment → note "unanimously positive/negative" in summary
- LLM generates generic summary → judge rejects → retry with stricter prompt
- Observability: Log pulse generation success/failure/retry per week; track word count over time

---

## Phase 10: Mutual Fund Explorer

### High-Level Components
- Component: FundExplorerService (backend)
  - Responsibility: Return all funds with latest metrics + summary stats
  - Dependencies: Supabase (mutual_fund_data)
- Component: MutualFundExplorerPage (frontend)
  - Responsibility: Searchable/filterable fund grid
  - Dependencies: Fund API, client-side filtering

### Integration View
- Frontend → Backend:
  - Protocol: HTTPS REST
  - Contract: GET /api/funds → all funds
- Backend → Supabase:
  - Protocol: HTTPS REST
  - Contract: SELECT with GROUP BY fund_slug, MAX(scraped_at)

### Data Flow (Narrative)
1. User navigates to /mutual-fund-explorer
2. TanStack Query fetches all funds (GET /api/funds)
3. Backend queries Supabase: latest row per fund_slug (DISTINCT ON fund_slug ORDER BY scraped_at DESC)
4. Returns 30 fund objects with all metrics
5. Frontend renders grid; search/filter is client-side (instant, no API calls)
8. Each section shows: rules, ranges, source URL, last_updated timestamp

### Security and Compliance
- AuthN/AuthZ model: Authenticated users only (JWT); no role restriction (both investor and admin can view)
- Data classification: All public fund data; no user-specific information
- Audit/approval controls: N/A (read-only)

### Scalability and Reliability
- Scaling expectations: 30 funds loaded once, filtered client-side. Trivial.
- Failure domains: Supabase query failure; stale data (scraper didn't run)
- Recovery strategy: TanStack Query cache; show last-known data with "Data may be outdated" notice

### Success Criteria
- All 30 funds displayed with correct data
- Search and filter work instantly
- Responsive on all devices

### Exit Criteria
- [ ] Fund explorer renders all funds
- [ ] Search/filter work together
- [ ] Source attribution visible

### Logging and Debug Requirements
- Log: Fund query time; number of funds returned; stale data detection
- Track: Most searched funds; most used category filters
- Escalation: If fund count drops below 25, investigate scraper issues

### Edge-Case Design
- New fund with missing returns_5y → show "N/A" in card
- Category with zero funds → hide from filter pills or show "No funds"
- Stale data (>14 days old) → show warning badge on timestamp
- Observability: Track data freshness; log search queries for RAG improvement

### Implementation Status
- Implemented in `phase-10-explorer-resources/` with:
  - Backend: `fund_router.py`, `fund_explorer_service.py`
  - Frontend: `MutualFundExplorer.tsx`, `FundCard.tsx`
  - Tests and expected outputs under `tests/` and `expected_outputs/`

---

## Phase 11: Evaluation Suite

### High-Level Components
- Component: EvaluationRunner (backend)
  - Responsibility: Orchestrate full evaluation run across all test types
  - Dependencies: All evaluator services, test case data
- Component: FaithfulnessEvaluator (backend)
  - Responsibility: Judge if answer is supported by retrieved context
  - Dependencies: OpenRouter (judge model)
- Component: RelevanceEvaluator (backend)
  - Responsibility: Judge if answer addresses the question
  - Dependencies: OpenRouter (judge model)
- Component: SafetyEvaluator (backend)
  - Responsibility: Run adversarial prompts, verify refusal/safe behavior
  - Dependencies: ChatService (runs prompts through actual pipeline)
- Component: UXValidator (backend)
  - Responsibility: Check structural requirements (pulse word count, action items)
  - Dependencies: weekly_pulse data
- Component: TestCaseGenerator (backend)
  - Responsibility: LLM generates additional test cases from knowledge base
  - Dependencies: OpenRouter, ChromaDB chunks

### Integration View
- Admin/GitHub Action → EvaluationRunner:
  - Protocol: HTTPS REST (POST /api/eval/run)
  - Contract: Trigger → runs all evaluators → stores results → returns summary
- EvaluationRunner → FaithfulnessEvaluator:
  - Protocol: In-process
  - Contract: (query, context, answer) → {faithful: bool, reasoning: string}
- EvaluationRunner → SafetyEvaluator:
  - Protocol: In-process
  - Contract: adversarial_prompt → {passed: bool, actual_response: string}
- SafetyEvaluator → ChatService:
  - Protocol: In-process
  - Contract: Runs prompt through full RAG pipeline as if real user
- EvaluationRunner → EvalsReportGenerator:
  - Protocol: In-process script/job
  - Contract: Read latest `evaluation_runs` + `evaluation_cases` → render `Docs/Architecture/Evals-Report.md`

### Data Flow (Narrative)
1. Evaluation triggered (admin button or GitHub Action schedule)
2. EvaluationRunner loads test cases from test_cases table (hand-crafted + LLM-generated)
3. For RAG faithfulness/relevance tests:
   - Run each query through RAG pipeline → capture (retrieved_context, answer)
   - Send to judge LLM: "Is this answer faithful to the context? Is it relevant to the question?"
   - Judge returns structured verdict with reasoning
4. For safety tests:
   - Run each adversarial prompt through ChatService
   - Check if response is refusal/safe or if it violated safety rules
5. For UX validation:
   - Check latest pulse: word count, action items count, structure
6. Aggregate: calculate percentages, compare to thresholds
7. Store in evaluation_runs (summary) and evaluation_cases (per-test detail)
8. Generate/update `Docs/Architecture/Evals-Report.md` from persisted run data (derived, human-readable artifact)
9. Return to frontend for display

### Security and Compliance
- AuthN/AuthZ model: Admin-only access; evaluation results not visible to investors
- Data classification: Test cases and results are internal quality data
- Audit/approval controls: Evaluation results inform AI governance; logged for audit trail

### Scalability and Reliability
- Scaling expectations: 100 test cases * LLM call = ~100 API calls per run. Takes 3-5 minutes.
- Failure domains: OpenRouter rate limit during batch; individual test case timeout
- Recovery strategy: Per-case error → mark as "error" → don't fail run; rate limit → batch with backoff

### Success Criteria
- Evaluation produces valid percentage scores
- Judge correctly identifies hallucinated answers
- Safety tests catch prompt injections
- Results visible in dashboard with per-test drill-down

### Exit Criteria
- [ ] Full evaluation run completes
- [ ] Scores calculate correctly
- [ ] Per-test breakdown available
- [ ] Scheduled + manual triggers work
- [ ] `Docs/Architecture/Evals-Report.md` refreshes from latest run outputs

### Logging and Debug Requirements
- Log: Per-case evaluation (query, verdict, reasoning, time); run summary; judge disagreements
- Track: Score trends across runs; flaky test cases; judge consistency
- Escalation: Scores drop >10% between runs → investigate RAG pipeline changes

### Edge-Case Design
- Judge LLM gives PASS to hallucinated answer → track judge accuracy; add "gold standard" test cases where correct answer is known
- Run takes >10 minutes → implement per-case timeout (30s) and skip
- Concurrent evaluation runs → mutex/lock (only one run at a time)
- Observability: Compare judge verdicts across multiple runs for same test case (detect drift)

---

## Phase 12: Assembly + Deployment

### High-Level Components
- Component: AssemblyScripts
  - Responsibility: Collect code from phase folders into deployable structure
  - Dependencies: All phase code, shared/ folder
- Component: CI/CD Pipeline
  - Responsibility: Test → build → deploy on push to main
  - Dependencies: GitHub Actions, Vercel CLI, Render API
- Component: SmokeTests
  - Responsibility: Verify critical paths in production
  - Dependencies: Deployed frontend + backend

### Integration View
- GitHub (push to main) → CI/CD Pipeline:
  - Protocol: GitHub Actions webhook
  - Contract: Run tests → assemble → deploy → smoke test
- CI/CD → Vercel:
  - Protocol: Vercel CLI / GitHub integration
  - Contract: Frontend build → production deployment
- CI/CD → Render:
  - Protocol: Render deploy hook
  - Contract: Backend build → production deployment

### Data Flow (Narrative)
1. Developer pushes to main branch
2. GitHub Action triggers: run tests (backend + frontend)
3. If tests pass: run assemble-backend.sh → creates backend-deploy/ directory
4. Run assemble-frontend.sh → creates frontend-deploy/ directory
5. Deploy frontend-deploy/ to Vercel (via GitHub integration or CLI)
6. Deploy backend-deploy/ to Render (via deploy hook or CLI)
7. Wait for both deployments to be live
8. Run smoke tests against production URLs
9. If smoke tests pass → deployment complete; if fail → alert + rollback guidance

### Security and Compliance
- AuthN/AuthZ model: Deploy credentials stored as GitHub Secrets (never in code)
- Data classification: No secrets in repository; env.example documents required vars without values
- Audit/approval controls: Main branch protection; PR review required (future); deploy logs preserved

### Scalability and Reliability
- Scaling expectations: Single instance each (Vercel + Render). Sufficient for demo.
- Failure domains: Build failure; deployment timeout; smoke test failure
- Recovery strategy: Vercel instant rollback to previous deployment; Render manual rollback

### Success Criteria
- Both apps deploy without errors
- Smoke tests pass all critical paths
- Zero secrets in repository

### Exit Criteria
- [ ] Assembly scripts work
- [ ] Deployment succeeds
- [ ] Smoke tests pass
- [ ] Env documentation complete

### Logging and Debug Requirements
- Log: Build times, deploy times, smoke test results
- Track: Deployment frequency, failure rate, rollback count
- Escalation: Deploy fails → check build logs → fix → re-deploy

### Edge-Case Design
- Import path errors after assembly → integration test in CI before deploy
- CORS mismatch → configured via env vars (ALLOWED_ORIGINS)
- Render cold start → health check fails initially → retry with backoff in smoke tests
- Missing env var → startup validation lists all missing vars clearly
- Observability: Health check endpoint returns version + uptime; Vercel/Render deployment logs

---

## Addendum A: HLD Integration Updates (May 2026)

### A1) Retrieval Architecture Upgrade (Phase 02 + 05 + 06)
- Replace "single top-k similarity search" as the only strategy with a retrieval graph:
  - QueryNormalizer -> EntityResolver -> HybridRetriever (vector + lexical) -> DynamicKSelector -> CrossEncoderReranker -> ContextAssembler.
- ConversationContextResolver is introduced as a shared high-level component for chat and voice:
  - carries forward active entity (fund), time window, and user intent state across turns.
- IntentRouter becomes mandatory in Phase 05 (not deferred):
  - factual intent -> retrieval answer flow,
  - action intent -> approval flow seed,
  - safety intent -> refusal guardrails,
  - clarification intent -> follow-up question branch.

### A2) Unified Search (M1 + M2) High-Level Flow
- New high-level component: UnifiedAnswerComposer.
- Integration path:
  - FundFactsRetriever (M1 factsheet source) + FeeLogicRetriever (M2 explainer source) -> UnifiedAnswerComposer -> 6-bullet formatted response with dual-source citations.
- Example supported combined query class:
  - "Exit load for ELSS fund and why I was charged it."

### A3) Theme-Aware Voice Flow (M2 -> M3)
- New high-level component: VoiceGreetingContextService.
- On voice session start:
  - fetch latest Weekly Pulse themes,
  - inject top theme into greeting template in real time,
  - continue normal conversational flow after greeting.

### A4) MCP Consolidation via FastMCP
- Introduce MCPActionServer (FastMCP-based) as a unified action transport for:
  - calendar lifecycle actions (`calendar.check_availability`, `calendar.create_event`, `calendar.update_event`, `calendar.cancel_event`),
  - email actions (`gmail.send`) — covers advisor-draft sends **and** the Phase 08 booking-confirmation email (admin-triggered, gated on `bookings.status = confirmed`),
  - weekly-pulse-to-Google-Docs actions (`docs.update_pulse_summary`).
- Every MCP tool call carries `approval_id`, `actor_id`, and `idempotency_key`.
- Approval Center remains the centralized HITL gate for proposing actions. Booking-confirmation email is a Phase 08 sub-feature that does **not** create a separate approval row — the underlying booking approval already authorizes the lifecycle; the admin click is the explicit HITL step.
- Email transport under `gmail.send`: in-house FastMCP wrapper around Gmail API (OAuth2 + refresh token). Drop-in alternative: `GongRzhe/Gmail-MCP-Server` ([github.com/GongRzhe/Gmail-MCP-Server](https://github.com/GongRzhe/Gmail-MCP-Server)).
- Reference: [FastMCP Getting Started](https://gofastmcp.com/getting-started/welcome)

### A5) Evaluation Coverage Upgrade (Phase 11)
- HLD evaluation scope must explicitly include:
  - 5-item blended golden dataset (M1 facts + M2 fee logic),
  - 3 adversarial safety prompts (advice + PII attempts),
  - voice theme-mention logic checks against latest pulse theme.
- Quality thresholds:
  - Faithfulness and relevance tracked per case,
  - safety refusals required at 100% for prohibited requests.

### A6) Phase Artifacts
- Every phase must have a dedicated edge/success artifact:
  - `Docs/Architecture/Phase-Criteria/phase-XX-edge-cases-success.md`
- HLD phase sections remain canonical, while phase artifacts hold expanded testable edge coverage and concrete acceptance checks.
