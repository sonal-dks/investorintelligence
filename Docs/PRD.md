# Product Requirements Document (PRD)
## Investor Ops Intelligence Suite

**Version:** 1.0  
**Status:** Shipped (v1.0)

---

## 1. Product Overview

### 1.1 Product Name
Investor Ops Intelligence Suite

### 1.2 One-Line Description
An AI-powered operations platform for mutual fund investors and fund managers — combining a RAG chatbot, voice agent, approvals workflow, AI evaluation suite, and market intelligence in a single dashboard.

### 1.3 Target Audience

| Role | Description |
|---|---|
| Investor | Retail mutual fund investor enrolled in SIPs or lumpsum schemes; seeks self-service fund information, portfolio visibility, and mutual-fund data |
| Admin / Fund Manager | Internal operations staff at a fund house or advisory firm; manages approvals, AI quality, investor activity, and platform health |

### 1.4 Core Value Proposition
- For investors: answer any fund or fee question in seconds, via chat or voice, without calling support.
- For fund managers: review and approve every AI-generated investor action before it executes, with full audit context.
- For both: one unified dashboard combining mutual-fund data, fund performance, operational metrics, and product sentiment.

---

## 2. Goals and Non-Goals

### 2.1 Goals (v1.0)
- Reduce investor support volume for fund/fee queries by enabling AI self-service.
- Give fund managers a single approval queue for all AI-generated investor actions.
- Provide continuous, measurable AI quality and safety monitoring.
- Unify mutual-fund data, activity logs, and review trends in one interface.
- Support both text and voice interaction modalities.

### 2.2 Non-Goals (v1.0)
- Real-time brokerage execution (buy/sell orders) — this is not a trading platform.
- Building proprietary data-provider contracts is out of scope; v1.0 consumes live data from configured public sources via compliant scraping pipelines.
- Multi-language (Hindi/regional) voice support — English only in v1.0.
- Mobile native app (iOS/Android) — web-first in v1.0.
- Full KYC workflow — KYC review scheduling is supported, not the KYC process itself.
- **Generic ESP / marketing email** — transactional booking-confirmation email for approved calendar bookings is delivered via **Phase 08** (FastMCP `gmail.send` + Gmail API). Broad marketing blasts, templated campaigns, and third-party ESP integrations remain out of scope for v1.0.

---

## 3. User Personas

### Persona A — Arjun (Retail Investor)
- Age: 34, software professional
- Manages 3 active SIPs (Large Cap, Mid Cap, ELSS)
- Uses the app on desktop during lunch or after market hours
- Wants to understand exit load before redeeming units
- Frustrated that he has to call the fund house for basic questions
- Comfortable with chat; open to voice queries when at home

### Persona B — Meera (Fund Ops Admin)
- Age: 41, senior operations manager at a mid-size fund house
- Oversees investor communications, KYC scheduling, and SIP service requests
- Receives dozens of AI-suggested actions daily across multiple channels
- Needs audit trails for regulatory reviews
- Wants to know if the chatbot is giving correct answers before it causes investor harm

---

## 4. Feature Specifications

---

### Feature 1: Authentication and Role Management

**Description:** Users log in via a Google SSO flow and are assigned one of two roles: Investor or Admin. Role determines navigation access and dashboard data scope.

**User Stories:**
- As a user, I can select my role (Investor / Admin) on the login screen so I see the relevant interface.
- As a first-time user, I am prompted to provide my email address for confirmation.
- As a returning user, my session is persisted and I land on the dashboard.

**Acceptance Criteria:**
- Login page shows role selector before SSO redirect.
- Email capture modal appears on first login only (`first_login_complete = false`).
- Investor role hides Approval Center and Evaluation Suite from navigation.
- Admin role shows all navigation items including a pending-count badge on Approvals.
- Sign-out clears session and returns to login.

**Evaluation Criteria:**
- Role-based navigation changes correctly after login.
- First-login email capture appears only once.
- Session persistence works after refresh/reload.
- Sign-out fully resets the UI state.

**Data Model:**
- `user_profiles`: id, user_id, email, display_name, role, first_login_complete

**Implementation (Phase 03):** Delivered in repo folder `phase-03-auth/` (OAuth, profile API, login UI, `/admin` guard). Role-aware sidebar/navigation items called out in acceptance criteria above ship with Phase 04 (Dashboard + app shell).

---

### Feature 2: Dashboard

**Description:** Role-aware operational dashboard showing KPIs, live mutual-fund snapshot data, booking summary, and platform health at a glance.

**User Stories:**
- As an investor, I can see my personal activity metrics (login count, chatbot sessions, voice usage, bookings).
- As an admin, I can see platform-wide metrics across all investors.
- As any user, I can see latest NAV snapshots for tracked mutual funds.
- As any user, I can see my booking status breakdown (confirmed, cancelled, rescheduled).

**Acceptance Criteria:**
- 4-column KPI strip at top of page: Login Sessions, Chatbot Sessions, Voice Sessions, Bookings.
- KPI cards show value, label, trend indicator, and contextual icon.
- Investor view: metrics scoped to `user_id`; Admin view: platform-wide aggregates.
- Mutual fund strip shows: fund name, category, latest NAV, and NAV date.
- Booking breakdown shows 3 counts and a 3-column mini-grid.
- Weekly Pulse preview widget (rating, new reviews, sentiment summary) visible on dashboard.

**Evaluation Criteria:**
- KPI values update correctly when activity data changes.
- Investor and admin scopes return different values correctly.
- Mutual fund strip renders all tracked funds and their latest NAV snapshots.
- Weekly Pulse preview is visible and reflects the latest pulse summary.

**Data Model:**
- `activity_log`: event counts grouped by event_type and user_id
- `bookings`: status counts grouped by user_id (investor) or all (admin)
- `mutual_fund_data`: latest scraped rows for tracked fund slugs, ordered by fund_name

---

### Feature 3: Smart Search (RAG Chatbot)

**Description:** A multi-session RAG chatbot for fund-related Q&A. Answers are grounded in a curated knowledge base covering mutual fund mechanics, fee structures, tax rules, and SIP comparisons.

**User Stories:**
- As an investor, I can ask natural language questions about mutual funds and get accurate, grounded answers.
- As a user, I can maintain multiple chat sessions and switch between them.
- As a user, I can delete a session I no longer need.
- As a new user, I see suggested starter questions so I know what to ask.

**Acceptance Criteria:**
- Left panel: session list with "New Chat" button, session titles, delete-on-hover.
- Right panel: message thread + input row.
- User messages: right-aligned, primary background.
- Assistant messages: left-aligned, muted background.
- Thinking state shown while awaiting response (animated loader + "Searching…" text).
- Suggested queries shown when session has no messages yet.
- Sessions persisted to Supabase; messages fetched on session selection.
- New session created on "New Chat" with placeholder title, updated after first message.

**Evaluation Criteria:**
- A new session can be created, renamed, and deleted.
- Messages persist when switching sessions.
- Answers remain grounded to the knowledge base and include citations.
- Advice/refusal behavior triggers correctly for non-factual prompts.

**Knowledge Base Coverage (v1.0):**
- Exit load rules (1% if redeemed before 1 year, fund-specific)
- Expense ratio ranges by fund category (Direct: 0.1–0.5%, Regular: 1–2.5%)
- Capital gains tax (STCG 15% under 1 year equity; LTCG 10% over ₹1L above 1 year)
- NAV calculation, SIP vs lumpsum comparison, fund ranking queries
- **Fee explainer corpus:** conceptual explanations sourced from Supabase `fee_explainer_data`, chunked and embedded alongside `mutual_fund_data` in Phase 02; Smart Search / Voice use **intent-first corpus routing** (scoped retrieval when confidence is high, otherwise unified retrieval across both corpora)

**Data Model:**
- `chat_sessions`: id, user_id, title, last_message_at, created_at
- `chat_messages`: id, session_id, role, content, citations (jsonb), metadata (jsonb), created_at
- `user_memory`: id, user_id, summary_text, topics (jsonb), updated_at
- `activity_log`: insert row on each session start (event_type: 'chatbot_used')

---

### Feature 4: Voice Agent

**Description:** A dual-mode (voice + text) AI agent for investment queries. In voice mode, it uses Web Speech API for speech-to-text input and TTS for spoken responses. It maintains session history identical to the chatbot.

**User Stories:**
- As an investor, I can ask investment questions using my microphone.
- As a user, I can toggle between voice mode and text mode within the same session.
- As a user, I can see a live transcript of what I'm saying while speaking.
- As a user, my voice sessions are saved and accessible in the session list.

**Acceptance Criteria:**
- Mode toggle (Voice / Text) in top of right panel.
- In voice mode: large microphone button shown; press to start recording, press again to stop.
- Live transcript appears below mic button while recording.
- Red animated pulse indicator shown during active recording.
- On recording stop, transcript is submitted as user message.
- TTS reads assistant response aloud in voice mode (if browser supports).
- Graceful fallback to text input if Web Speech API not available.
- Sessions stored in `voice_sessions`; messages in `voice_messages` with `input_mode` field.

**Evaluation Criteria:**
- Voice mode and text mode can be switched without losing context.
- Transcript appears live and is saved with the session.
- TTS triggers when supported and fails gracefully when unsupported.
- Voice session history remains accessible after refresh.

**Data Model:**
- `voice_sessions`: id, user_id, title, mode, last_message_at
- `voice_messages`: id, session_id, role, content, input_mode, created_at
- `activity_log`: insert on session start (event_type: 'voice_agent_used')

---

### Feature 5: Weekly Pulse (Product Intelligence)

**Description:** Scraped and analyzed app-review data surfaced as an operational intelligence view. Shows overall rating, sentiment breakdown, keyword trends, and individual review samples.

**User Stories:**
- As an admin, I can see the current app rating and how it has trended over the past 4 weeks.
- As an admin, I can view individual reviews filtered by sentiment (positive / negative / neutral).
- As an admin, I can see which keywords are trending in reviews and whether they are rising or falling.
- As an investor, I can view the pulse summary as a contextual product health signal.

**Acceptance Criteria:**
- Header KPIs: Overall Rating (star display + number), New Reviews This Week, Positive Count, Negative Count.
- Tabs: Overview | Reviews | Keywords.
- Overview tab: 4-week trend table (week, rating, reviews, sentiment breakdown), rating distribution bar chart.
- Reviews tab: filter bar (All / Positive / Neutral / Negative) + scrollable review cards with star rating, user name, date, comment.
- Keywords tab: table of keyword, mention count, week-over-week change (color-coded), trend indicator.
- Scrape timestamp shown below page title with green pulse dot.

**Evaluation Criteria:**
- Weekly summary is visible and traceable to source reviews.
- Top themes and sentiment shifts are reflected accurately.
- Filters update review cards correctly.
- Timestamp changes when new data is loaded.
- Weekly Pulse dashboard shows LLM output and deterministic fallback comparison side by side.
- Deterministic algorithm label is visible for transparency.
- Voice greeting theme mention and booking email pulse themes consume LLM themes only.

**Implementation (Phase 09):** Delivered in repo folder `phase-09-weekly-pulse/` (backend pulse APIs/services, frontend pulse page/components, tests, and expected outputs).

---

### Feature 6: Mutual Fund Explorer

**Description:** A searchable, filterable mutual-fund explorer showing live-scraped data from a configured list of Groww mutual-fund pages. The same dataset is used to ground the mutual-fund RAG bot.

**User Stories:**
- As a user, I can search for a fund by fund name.
- As a user, I can filter funds by category (Large Cap, Mid Cap, Small Cap, Hybrid, Debt, ETF/FOF, Sectoral/Thematic).
- As a user, I can see key metrics for each fund: NAV, NAV date, AUM, expense ratio, min SIP, risk level, and returns.

**Acceptance Criteria:**
- Search input filters results in real-time by fund name.
- Category filter pills: All, Large Cap, Mid Cap, Small Cap, Flexi Cap, Multicap, Debt, Hybrid, ETF/FOF, Sectoral/Thematic.
- Fund cards in a responsive grid (2 columns mobile, 3–4 desktop).
- Each card: fund name, category badge, latest NAV, NAV date, AUM, expense ratio, min SIP, risk badge, and key returns (1Y/3Y/5Y where available).
- Summary bar above grid: Tracked Funds count, Average Expense Ratio, High-Risk Funds count.
- Scrape timestamp shown below page title.

**Evaluation Criteria:**
- Search and filter work together without breaking layout.
- Fund cards show the required metrics.
- Summary counters match the underlying mutual-fund data.
- Timestamp reflects the latest refresh.

**Data Model:**
- `mutual_fund_data`: fund_slug, fund_name, category, nav, nav_date, aum_cr, expense_ratio, min_sip, risk_level, returns_1m, returns_6m, returns_1y, returns_3y, returns_5y, exit_load_text, tax_text, source_url, scraped_at

---

### Feature 7: Approval Center (Admin-only)

**Description:** A human-in-the-loop approval queue for all AI-generated investor actions. Actions include calendar events, outgoing emails, booking changes, and notes. Admins can approve, reject, edit, or reset each item.

**User Stories:**
- As an admin, I can see all pending AI-generated actions in a list.
- As an admin, I can approve or reject an item with a single click.
- As an admin, I can view the full context of an action in a side panel before deciding.
- As an admin, I can filter the list by status (Pending / Approved / Rejected / All).
- As an admin, I can view the connected calendar to validate scheduling context.

**Acceptance Criteria:**
- List view (left panel): each item shows type icon, title, investor name, timestamp, status badge, priority badge.
- Pending items have amber left border accent (`border-l-4 border-l-amber-400`).
- Inline Approve (emerald) and Reject (destructive outline) buttons on each list row.
- Clicking a row opens the detail side panel (right panel, sticky).
- Detail panel: full title, investor details, notes/description, email body preview (for email types), approve/reject buttons.
- Email items show additional actions: "Send Email", "Edit Draft", "Don't Send".
- Filter bar: All | Pending | Approved | Rejected — with item counts per status.
- Calendar tab: embedded Google Calendar iframe for scheduling context (`GET /api/calendar/iframe-url` when `GOOGLE_CALENDAR_ID` is configured).
- **Phase 08 — Bookings:** After a booking approval, admins manage the live booking via the Phase 08 API / UI module (`phase-08-calendar-booking/`): confirm (tentative → confirmed in Google Calendar via FastMCP tools), cancel, reschedule, and **Send Email** (admin-triggered confirmation to investor + advisor, idempotent per booking status; Weekly Pulse block included when Phase 09 data exists in Supabase).
- MCP: all calendar writes and booking emails go through the FastMCP action layer (`calendar.*`, `gmail.send`) per Architecture decision A5.
- Approved items: Approve button disabled, "Approved" badge; Reject button still active (for undo).
- Activity logged on approval/rejection (event_type: 'approval_reviewed').

**Evaluation Criteria:**
- Pending, approved, and rejected items are visually distinct.
- Approve/reject actions update state and badge status.
- Detail panel shows the full context before action.
- Calendar context is visible for booking-related items.
- Email-related items expose edit/send/don’t send actions.

**Data Model:**
- `approvals`: id, action_type, title, description, investor_id, investor_name, status, priority, payload, source_session_id, source_type, intent_hash, reviewed_by, reviewed_at, created_at
- `bookings`, `booking_emails`: see Phase 08 migration `phase-08-calendar-booking/migrations/001_bookings_and_booking_emails.sql` (booking lifecycle + email audit).
- Approval Center reads and writes live rows from `approvals`; production wiring replaces any in-memory demo queues from early phases.

---

### Feature 8: Evaluation Suite (Admin-only)

**Description:** A continuous AI quality and safety monitoring dashboard. Measures RAG faithfulness, response relevance, and safety guardrail pass rates with per-test breakdowns.

**User Stories:**
- As an admin, I can see at a glance whether the chatbot is meeting quality thresholds.
- As an admin, I can drill into individual RAG test cases to see which queries failed faithfulness or relevance checks.
- As an admin, I can review safety test results to know whether the AI resisted adversarial prompts.
- As an admin, I can see UX validation metrics (pulse word count, action item presence, etc.).

**Acceptance Criteria:**
- Top KPI strip: RAG Faithfulness %, RAG Relevance %, Safety Pass % — each with pass/fail color coding vs threshold.
- Three tabs: RAG Evaluation | Safety Tests | UX Validation.
- RAG Evaluation tab: table of (Query, Expected Answer snippet, Faithful?, Relevant?) with checkmark/cross icons.
- Safety Tests tab: table of (Prompt, Type, Pass/Fail, Notes).
- UX Validation tab: metric cards for (Pulse word count vs target, Action items present, Voice agent mention, Faithfulness rate, Safety rate).
- All thresholds visible alongside actuals (e.g., "83.3% vs 85% target").
- Metrics calculated from live `evaluation_cases` and `evaluation_runs` datasets produced by scheduled and on-demand eval jobs.

**Evaluation Criteria:**
- All three evaluation types are visible and individually interpretable.
- Threshold pass/fail states are clearly shown.
- Adversarial prompts produce refusal/pass outcomes.
- Weekly pulse structure checks can be verified quickly.

**Thresholds (v1.0):**
- RAG Faithfulness target: ≥ 85%
- RAG Relevance target: ≥ 85%
- Safety Pass target: ≥ 90%
- Pulse word count target: 150–200 words
- Action items: ≥ 3 per pulse

---

## 5. Live Data Sources and KPI Logic

### 5.1 Source Registry (No Mock Data)
- **Feature 1 — Authentication and Role Management:** Google Identity (OAuth) for login identity; user profile/session state from Supabase Auth + `user_profiles`.
- **Feature 2 — Dashboard:** KPI cards from `activity_log` and `bookings`; mutual-fund strip from live `mutual_fund_data` ingestion.
- **Feature 3 — Smart Search (RAG Chatbot):** Uses the same scraped mutual-fund dataset as Feature 6, from the configured Groww mutual-fund URL list. Refresh cadence is weekly.
- **Feature 4 — Voice Agent:** Same RAG corpus as Smart Search; voice input/output via browser Web Speech APIs; transcripts and turns stored in `voice_sessions`/`voice_messages`.
- **Feature 5 — Weekly Pulse:** Public app reviews ingested from Google Play for Groww app listing (`https://play.google.com/store/apps/details?id=com.nextbillion.groww&hl=en_IN`); processed into sentiment, themes, and keyword trends.
- **Feature 6 — Mutual Fund Explorer:** Live mutual-fund data scraped from configured Groww mutual-fund pages and persisted in `mutual_fund_data`.
- **Feature 7 — Approval Center:** Queue items generated from live chat/voice/booking workflows and persisted to `approvals`.
- **Feature 8 — Evaluation Suite:** Quality/safety metrics computed from live evaluation runs stored in `evaluation_cases` and `evaluation_runs`.

### 5.1.1 Configured Mutual Fund Scrape URLs (Initial Set)
- `https://groww.in/mutual-funds/mirae-asset-elss-tax-saver-fund-direct-growth`
- `https://groww.in/mutual-funds/mirae-asset-large-midcap-fund-direct-growth`
- `https://groww.in/mutual-funds/mirae-asset-small-cap-fund-direct-growth`
- `https://groww.in/mutual-funds/mirae-asset-midcap-fund-direct-growth`
- `https://groww.in/mutual-funds/mirae-asset-bse-india-defence-etf-fof-direct-growth`
- `https://groww.in/mutual-funds/mirae-asset-gold-silver-passive-fof-direct-growth`
- `https://groww.in/mutual-funds/mirae-asset-large-cap-fund-direct-growth`
- `https://groww.in/mutual-funds/mirae-asset-nifty-metal-etf-fof-direct-growth`
- `https://groww.in/mutual-funds/mirae-asset-nifty-smallcap-250-momentum-quality-100-etf-fof-direct-growth`
- `https://groww.in/mutual-funds/mirae-asset-multicap-fund-direct-growth`
- `https://groww.in/mutual-funds/mirae-asset-healthcare-fund-direct-growth`
- `https://groww.in/mutual-funds/mirae-asset-liquid-fund-direct-growth`
- `https://groww.in/mutual-funds/mirae-asset-flexi-cap-fund-direct-growth`
- `https://groww.in/mutual-funds/mirae-asset-great-consumer-fund-direct-growth`
- `https://groww.in/mutual-funds/mirae-asset-nifty-midsmallcap400-momentum-quality-100-etf-fof-direct-growth`
- `https://groww.in/mutual-funds/mirae-asset-banking-and-financial-services-fund-direct-growth`
- `https://groww.in/mutual-funds/mirae-asset-gold-etf-fof-direct-growth`
- `https://groww.in/mutual-funds/mirae-asset-multi-asset-allocation-fund-direct-growth`
- `https://groww.in/mutual-funds/mirae-asset-aggressive-hybrid-fund-direct-growth`
- `https://groww.in/mutual-funds/mirae-asset-infrastructure-fund-direct-growth`
- `https://groww.in/mutual-funds/mirae-asset-nifty-india-new-age-consumption-etf-fof-direct-growth`
- `https://groww.in/mutual-funds/mirae-asset-ultra-short-duration-fund-direct-growth`
- `https://groww.in/mutual-funds/mirae-asset-silver-etf-fof-direct-growth`
- `https://groww.in/mutual-funds/mirae-asset-equity-savings-fund-direct-growth`
- `https://groww.in/mutual-funds/mirae-asset-focused-fund-direct-growth`
- `https://groww.in/mutual-funds/mirae-asset-diversified-equity-allocator-passive-fof-direct-growth`
- `https://groww.in/mutual-funds/mirae-asset-arbitrage-fund-direct-growth`
- `https://groww.in/mutual-funds/mirae-asset-dynamic-bond-fund-direct-growth`
- `https://groww.in/mutual-funds/mirae-asset-nifty-100-esg-sector-leaders-fof-direct-growth`
- `https://groww.in/mutual-funds/mirae-asset-balanced-advantage-fund-direct-growth`

### 5.2 KPI Calculation Logic (Backend)
- **Scope filter:** For investor role, every KPI query applies `WHERE user_id = :current_user_id`; admin role uses platform-wide aggregates.
- **Time windows:** `current_window = now() - interval '7 days' to now()`; `previous_window = now() - interval '14 days' to now() - interval '7 days'`.
- **Trend formula:** `trend_pct = ((current_value - previous_value) / NULLIF(previous_value, 0)) * 100`; if `previous_value = 0` and `current_value > 0`, set trend to `+100%`.
- **Dashboard KPIs:**
  - `login_sessions = COUNT(activity_log WHERE event_type = 'login' AND created_at IN current_window)`.
  - `chatbot_sessions = COUNT(activity_log WHERE event_type = 'chatbot_used' AND created_at IN current_window)`.
  - `voice_sessions = COUNT(activity_log WHERE event_type = 'voice_agent_used' AND created_at IN current_window)`.
  - `bookings = COUNT(bookings WHERE created_at IN current_window)`.
- **Booking status mini-grid:** `confirmed_count`, `cancelled_count`, `rescheduled_count` from `bookings GROUP BY status`.
- **Weekly Pulse KPIs:**
  - `overall_rating = ROUND(AVG(rating), 2)` over trailing 28 days of `app_reviews`.
  - `new_reviews_this_week = COUNT(app_reviews WHERE review_date >= date_trunc('week', now()))`.
  - `positive_count = COUNT(rating >= 4)`, `neutral_count = COUNT(rating = 3)`, `negative_count = COUNT(rating <= 2)`.
  - `keyword_wow_change = ((mentions_this_week - mentions_prev_week) / NULLIF(mentions_prev_week, 0)) * 100`.
- **Mutual Fund Explorer KPIs:**
  - `tracked_funds = COUNT(DISTINCT fund_slug)` from latest `mutual_fund_data`.
  - `high_risk_funds = COUNT(mutual_fund_data WHERE risk_level IN ('High', 'Very High'))`.
  - `avg_expense_ratio = ROUND(AVG(expense_ratio), 2)`.
  - `last_scraped_at = MAX(mutual_fund_data.scraped_at)`.
- **Evaluation Suite KPIs:**
  - `rag_faithfulness_pct = 100 * SUM(CASE WHEN faithful = true THEN 1 ELSE 0 END) / COUNT(rag_cases)`.
  - `rag_relevance_pct = 100 * SUM(CASE WHEN relevant = true THEN 1 ELSE 0 END) / COUNT(rag_cases)`.
  - `safety_pass_pct = 100 * SUM(CASE WHEN passed = true THEN 1 ELSE 0 END) / COUNT(safety_cases)`.
  - `pulse_word_count = array_length(regexp_split_to_array(trim(pulse_text), '\s+'), 1)`.
  - `action_items_present = CASE WHEN action_item_count >= 3 THEN true ELSE false END`.
- **Threshold classification:**
  - Faithfulness pass if `rag_faithfulness_pct >= 85`.
  - Relevance pass if `rag_relevance_pct >= 85`.
  - Safety pass if `safety_pass_pct >= 90`.
  - Pulse structure pass if `150 <= pulse_word_count <= 200` and `action_item_count >= 3`.

---

## 6. Navigation and Information Architecture

```text
App Shell
├── Sidebar (always visible, role-aware)
│   ├── Dashboard            [investor + admin]
│   ├── Smart Search         [investor + admin]
│   ├── Weekly Pulse         [investor + admin]
│   ├── Mutual Fund Explorer [investor + admin]
│   ├── Voice Agent          [investor + admin]
│   ├── Approval Center      [admin only, badge: pending count]
│   └── Evaluation Suite     [admin only]
└── Topbar (always visible)
    ├── App name + active page
    ├── Live status badge
    ├── Last-updated chip
    └── Notifications + avatar
```

---

## Addendum A (May 2026): Retrieval and Product Integration Requirements

### A1) Smart Search Retrieval Requirements (Mandatory)
- Top-k similarity search alone is not sufficient.
- Feature 3 must implement:
  - hybrid retrieval (vector + lexical),
  - query rewriting and typo tolerance,
  - semantic entity resolution for fund names,
  - reranking,
  - dynamic-k retrieval,
  - multi-turn memory-aware retrieval.
- Mandatory behavior examples:
  - "What is the exit load of Mirae Asset Large Cap?" -> response includes "1% if redeemed before 1 year" with citation.
  - Follow-up "What is NAV of this fund?" -> system resolves "this fund" to Mirae Asset Large Cap.
  - "mirae larg cap" typo query -> still resolves to correct fund via semantics.

### A2) Intent Detection Scope Update
- Intent detection is mandatory from Phase 5 onward (not optional/deferred).
- Feature 3 and Feature 4 must classify each turn into:
  - factual intent,
  - action intent,
  - safety intent,
  - clarification intent.
- Feature 7 continues as primary HITL execution layer for action intents.

### A3) Unified Search (M1 + M2) Requirement
- Feature 3 and Feature 9 together must support blended responses combining:
  - M1 mutual fund factsheet evidence,
  - M2 fee explainer logic.
- Output constraints for blended answers:
  - preserve source citations,
  - enforce fixed 6-bullet answer structure.

### A4) Weekly Pulse -> Voice Agent Briefing
- Feature 4 must consume latest Feature 5 pulse in real time at greeting time.
- Voice greeting must be theme-aware when top issue themes are available.

### A5) MCP Standardization Requirement
- MCP action services for email, calendar, and Google Docs updates must be implemented through FastMCP-compatible tooling.
- Approval Center remains mandatory gate before action execution.
- Reference: [FastMCP Getting Started](https://gofastmcp.com/getting-started/welcome)

### A6) Evaluation Suite Requirement Expansion
- Feature 8 must include and report:
  - Retrieval Accuracy Eval: 5 blended golden questions (M1 + M2),
  - Safety Eval: 3 adversarial prompts (advice + PII),
  - UX Eval: pulse structure checks and voice top-theme mention logic.
- Required report artifact:
  - `Docs/Architecture/Evals-Report.md`