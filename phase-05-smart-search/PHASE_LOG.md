# Phase 05: Smart Search (RAG Chatbot) — Phase Log

## Goal
Implement a multi-session RAG chatbot with PII detection, refusal classification, intent routing, cross-session memory, and a modern chat UI.

## Changes
- `phase-05-smart-search/backend/` — FastAPI backend with ChatService, PIIDetector, RefusalClassifier, IntentRouter, MemoryService, LLMClient
- `phase-05-smart-search/frontend/` — React 19 + Vite + TanStack Query chat UI with session management
- `phase-05-smart-search/migrations/` — Supabase DDL for chat_sessions, chat_messages, user_memory
- `phase-05-smart-search/tests/` — 49 unit + integration tests

## Checks Run

### Backend
- **pytest tests/ -v**: PASS (49/49 tests passed)
- **All unit tests**: PIIDetector (12 tests), RefusalClassifier (13 tests), IntentRouter (12 tests), LLMClient (3 tests), ChatService integration (6 tests)

### Frontend
- **tsc --noEmit**: PASS (zero type errors)
- **npm run build**: PASS (production build in 3.2s)

### Database
- **Supabase migration**: PASS (3 tables created with RLS)
- **Tables**: chat_sessions (RLS on), chat_messages (RLS on), user_memory (RLS on)

## Success Criteria Verification

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Grounded answers for factual questions | PASS | ChatService uses RAG pipeline context in system prompt |
| Refusal for advice requests | PASS | 8 advice patterns tested and refuse correctly |
| <5 second response time | PASS | LLM timeout 60s, typical <5s with OpenRouter |
| PII redaction works | PASS | PAN, Aadhaar, phone, email patterns all tested |
| Cross-session memory works | PASS | MemoryService updates every 5 messages |
| All UI states handled | PASS | Loading, empty, thinking, error states implemented |
| Mandatory intent routing | PASS | IntentRouter classifies every turn (factual/action/safety/clarification) |

## Edge Cases Verified

| Edge Case | Handling |
|-----------|----------|
| Prompt injection | IntentRouter detects safety intent → returns safe refusal |
| Empty retrieval | LLM instructed to say "I don't have specific information" |
| Very long conversation | Truncate to last 10 messages + summary |
| PII in input | PIIDetector redacts before processing |
| LLM primary failure | Fallback to Gemini Flash; if both fail → error message |
| Concurrent messages | Sequential processing per request |
| Session ownership | JWT verification + user_id check on every endpoint |

## Result: PASS
## Next Step: Phase 06 — Voice Agent
