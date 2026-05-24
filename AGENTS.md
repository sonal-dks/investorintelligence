# Agent instructions (Investor Ops / Next Leap project)

## Documentation (automatic)

Whenever you **implement, fix, or refactor** code that affects APIs, database schema, environment variables, auth, or cross-phase behavior, you **must** update the canonical docs in the same change set:

- `Docs/Architecture/architecture.md`
- `Docs/Architecture/HLD.md`
- `Docs/Architecture/LLD.md`
- `Docs/PRD.md` (if user-visible or acceptance-criteria behavior changes)
- Relevant phase `README.md` when the change is phase-local

Follow the project skill **architecture-docs-sync** (`.cursor/skills/architecture-docs-sync/SKILL.md`). The user should not need to ask for doc updates on every task.

## Testing expectations

For non-trivial behavior, prefer **real end-to-end** verification where appropriate; see **real-end-to-end-testing** (`.cursor/skills/real-end-to-end-testing/SKILL.md`). Unit tests stay fast; live Supabase/OpenRouter paths are env-gated.
