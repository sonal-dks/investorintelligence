# Phase 04: Dashboard and App Shell - Edge Cases and Success Criteria

## Detailed Edge Cases
- Data edge: all KPI sources return zero, one KPI source delayed while others are fresh.
- UI edge: empty fund strip, missing trend baseline causing divide-by-zero.
- Auth edge: role switch between investor/admin with cached stale dashboard data.
- Dependency edge: one dashboard endpoint timeout while others succeed.
- Observability edge: KPI mismatch hidden due to stale cache.

## Success Criteria
- KPI cards render safely for zero, null, and missing baseline values.
- Dashboard shows latest available data with explicit freshness timestamp.
- Role-aware dashboard views return correct scoped data.
- Partial API failures degrade gracefully without blanking full page.
- KPI formulas match PRD logic and are test-verified.
