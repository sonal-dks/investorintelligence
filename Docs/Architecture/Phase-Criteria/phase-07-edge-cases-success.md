# Phase 07: Intent Detection and Approval Center - Edge Cases and Success Criteria

## Detailed Edge Cases
- Intent edge: user changes intent mid-conversation (book -> cancel -> reschedule).
- Ambiguity edge: "maybe schedule something" without time/topic.
- Conflict edge: duplicate intent detection from concurrent chat and voice updates.
- Approval edge: admin approves outdated intent while user already cancelled.
- MCP prep edge: approval payload missing required fields for downstream email/calendar/docs tools.

## Success Criteria
- Multi-turn intent state transitions are tracked deterministically (detected/confirmed/cancelled/modified).
- Only confirmed intents create approval items; ambiguous intents trigger clarification.
- Approval queue remains idempotent (no duplicate pending action for same intent hash).
- Approval payload includes fields required for MCP action execution.
- Admin actions are auditable with reviewer identity and timestamps.
