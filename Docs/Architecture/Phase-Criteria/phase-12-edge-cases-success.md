# Phase 12: Assembly and Deployment - Edge Cases and Success Criteria

## Detailed Edge Cases
- Packaging edge: phase module collisions during assembly.
- Config edge: missing env vars for MCP, OpenRouter, Supabase, or calendar integrations.
- Integration edge: deployed app points to stale evaluation or pulse endpoints.
- Security edge: unintended secret exposure in deployment logs.
- Runtime edge: healthy build but broken chat/voice/approval critical path.

## Success Criteria
- Deployment includes all integrated modules (retrieval v2, intent router, MCP gateway, eval suite).
- Environment validation blocks release when required secrets/configs are missing.
- Post-deploy smoke tests validate chat, voice, approvals, calendar flow, and eval dashboard.
- Rollback strategy is documented and tested for failed release.
- Production build preserves compliance constraints and audit logging.
