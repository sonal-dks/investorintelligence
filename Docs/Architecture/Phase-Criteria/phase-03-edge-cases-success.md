# Phase 03: Authentication and User Management - Edge Cases and Success Criteria

## Detailed Edge Cases
- Input edge: OAuth callback missing state, role not selected, profile save with invalid email format.
- Session edge: expired token with active tab, concurrent login in two tabs with conflicting profile data.
- Authorization edge: investor attempts admin route by URL manipulation.
- Dependency edge: Supabase auth outage, delayed profile write after successful login.
- Compliance edge: accidental storage of disallowed PII beyond profile contract.

## Success Criteria
- Login flow consistently creates or loads profile with valid role.
- Role-based route protection blocks unauthorized page access.
- First-login profile capture runs once and does not reappear unnecessarily.
- Session persistence works across refresh with secure token handling.
- Only approved profile fields are stored and audited.
