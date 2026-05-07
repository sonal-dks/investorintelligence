# Investor Ops Intelligence Suite — Problem Statement

## 1. Overview

The mutual fund and investment-app ecosystem is fragmented across knowledge sources, customer support, product feedback, booking workflows, and compliance approvals. Retail investors struggle to get clear answers about fund facts and fees. Internal teams struggle to turn customer feedback into operational action. AI assistants can help, but without human oversight, grounded sources, and safety guardrails, they can create compliance and trust risks.

This project solves that by building a single AI-powered operations platform that unifies factual self-service, review intelligence, voice-based appointment booking, and approval-gated workflows inside one dashboard.

---

## 2. Who Is Affected

### Retail Investors
- Need quick, factual answers about mutual fund schemes, fees, taxes, and statements
- Often depend on support for common questions that should be self-serve
- Prefer text in some cases and voice in others
- Need visibility into their chats, bookings, and past interactions

### Admins / Fund Operations Teams
- Need to manage investor communications, approvals, and follow-ups
- Need visibility into bookings, support patterns, and product sentiment
- Need an oversight layer before AI-generated emails, notes, or calendar items are sent
- Need evidence that AI outputs are accurate, relevant, and safe

---

## 3. Core Problems

### Problem 1: Investors cannot self-serve on fund and fee questions
Common questions such as exit load, expense ratio, minimum SIP, lock-in, riskometer, benchmark, and statement download are often answered manually by support teams, even though the information exists in public official sources.

### Problem 2: Support workflows are disconnected from product intelligence
Customer reviews and app-store feedback contain valuable signals about pain points, but that data is not systematically converted into weekly insights or action items.

### Problem 3: Voice-first support is missing
Users who are more comfortable speaking than typing have limited access to digital self-service tools. A compliant voice assistant can reduce friction and improve accessibility.

### Problem 4: AI-generated actions lack a human approval layer
Emails, calendar holds, notes, and booking-related actions need review before execution. Without a centralized approval layer, errors can create compliance risk.

### Problem 5: AI quality and safety are not continuously measured
RAG answers, voice responses, and summary outputs need evaluation for faithfulness, relevance, and resistance to unsafe prompts.

### Problem 6: Product, mutual-fund, and operational data are siloed
Fund facts, fee rules, product reviews, bookings, and usage history live in different places. Teams need one connected dashboard to see the whole picture.

---

## 4. Opportunity

Build a single platform that connects:
- factual mutual-fund knowledge,
- weekly customer sentiment and review intelligence,
- fee explanations,
- voice-based booking,
- approval-gated operations,
- and evaluation tools for safety and quality.

The product should work for both customers and admins, and it should keep all workflows grounded, structured, and compliant.

---

## 5. Unified Product Vision

The final product, Investor Ops Intelligence Suite, brings together three milestone capabilities:

### M1: RAG-Based Mutual Fund FAQ Assistant
A facts-only assistant that answers mutual fund questions using the same live scraped mutual-fund dataset as the Mutual Fund Explorer (configured Groww mutual-fund links), with weekly refresh, citations, and refusal behavior for advice requests.

### M2: Weekly Product Pulse + Fee Explainer
A review-analysis workflow that ingests live public app-store reviews into themes, quotes, summaries, and actions, plus a structured fee explainer for one scenario with official sources.

### M3: AI Voice Appointment Scheduler
A compliant voice assistant that books tentative advisor slots, generates booking codes, creates calendar holds, notes, and approval-gated email drafts, and never collects PII on the call.

---

## 6. User Journeys

### Customer Journey
1. Log in to the platform.
2. Land on a dashboard with KPIs and last-updated timestamps.
3. Ask a question through chat or voice.
4. Receive a grounded, citation-backed answer or a safe refusal.
5. View chat history and saved memory.
6. Switch to voice to book an advisor slot.
7. Confirm topic and time, receive a booking code, and see booking status.
8. Open Resources to view mutual fund FAQs, fee explanations, and weekly pulse insights.
9. View all bookings, activity history, and last-updated content.

### Admin Journey
1. Log in to the admin dashboard.
2. See platform-wide KPIs, pending approvals, and weekly trends.
3. Review bookings in a calendar/table view.
4. Approve, reject, or edit calendar holds, notes, and email drafts.
5. View Weekly Pulse analytics and recurring issue themes.
6. Inspect mutual fund resources, fee explanations, and evaluation results.
7. Monitor AI quality, safety, and UX structure.

---

## 7. Product Constraints and Guidelines

### Compliance
- No PII collection or storage: no PAN, Aadhaar, account number, phone, email, or OTP.
- No investment advice, recommendations, or “should I buy/sell” guidance.
- No unsupported performance claims or return predictions.

### Data Sources
- Mutual-fund data must come from live scraping of configured Groww mutual-fund links (the tracked 15-30 fund URL set).
- No third-party blogs for factual answers.
- Review analysis must use public review data only from Google Play listing for Groww app (`https://play.google.com/store/apps/details?id=com.nextbillion.groww&hl=en_IN`).
- RAG refresh cadence is weekly, using the same mutual-fund scrape source as Mutual Fund Explorer.
- Production workflows must not use mock/dummy datasets.

### Workflow Rules
- Calendar holds, notes, and email drafts must be approval-gated.
- No auto-send emails.
- Booking codes must persist across modules.
- All content should be structured and explainable.

### Output Rules
- FAQ answers should remain concise.
- Weekly pulse must stay under 250 words and include exactly 3 action ideas.
- Fee explanations should remain neutral and capped at a short bullet structure.
- Every resource should show a last-updated timestamp.

### Product Boundaries
- No live brokerage execution.
- No mobile-native app in the first version.
- No multilingual voice support in the first version.
- No full KYC flow; only KYC-related booking support.

---

## 8. Success Criteria

The product is successful if:
- Customers can self-serve factual fund questions.
- Customers can move from chat to voice to booking smoothly.
- Admins can review and approve AI-generated actions safely.
- Weekly review trends are visible and actionable.
- AI outputs remain grounded, structured, and compliant.
- AI ragbots, voice chats should have persistent memory, should be able to have context of the conversation
- AI ragbots,agents should tackle all the edge cases that can arise when having a conversation with a customer. It should go beyong intent classification and understand what the user is actually trying to ask
- The platform feels like a connected product, not separate scripts.

### Expanded Success Checks (Integrated Product)
- Retrieval must handle semantic and typo-heavy fund mentions, not exact-match only.
- Follow-up turns ("this fund", "its NAV") must resolve correctly using conversation context.
- Unified Search responses must combine fund facts + fee logic with citations and fixed 6-bullet structure.
- Voice greeting must reflect latest weekly pulse theme when available in real time.
- Approval center must include MCP-backed email/calendar/doc actions with advisor email market-context snippets.
- Safety behavior must refuse investment-advice and PII extraction prompts consistently.

---

## 9. Summary

Investor Ops Intelligence Suite is a unified AI operations platform for a fintech context. It solves the problem of fragmented self-service, disconnected insights, and ungoverned AI actions by combining factual RAG answers, weekly product intelligence, fee explainers, voice-based booking, and human-in-the-loop approvals in one dashboard.