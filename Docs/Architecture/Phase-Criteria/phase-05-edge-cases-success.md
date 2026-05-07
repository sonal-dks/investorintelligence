# Phase 05: Smart Search (RAG Chatbot) - Edge Cases and Success Criteria

## Detailed Edge Cases
- Retrieval edge: top-k misses the correct fund rule, lexical-only hit conflicts with vector hit.
- Entity edge: user types "mirae larg cap", "that large cap fund", or "this fund" in follow-up turn.
- Intent edge (mandatory): factual and action intents appear in same message; ambiguous intent requires clarification.
- Safety edge: user asks for return prediction, PII, or prompt leakage.
- Conversation edge: multi-turn context drift after topic change, stale memory causes wrong fund carryover.

## Success Criteria
- Mandatory intent routing is active for every message (factual/action/safety/clarification).
- Query "What is the exit load of Mirae Asset Large Cap?" returns evidence containing "1% if redeemed before 1 year" with citation.
- Follow-up "What is NAV of this fund?" resolves fund context from previous turn and returns correct NAV.
- Semantic typo query "tell query about mirae larg cap" resolves to canonical fund via entity resolver.
- Unified Search responses combining fund facts + fee logic use strict 6-bullet format with source citations.
- Advice and PII extraction prompts are refused with compliant safe response.
