# Phase 01: Data Ingestion - Edge Cases and Success Criteria

## Detailed Edge Cases
- Input edge: source page layout changes, missing NAV/expense fields, duplicate fund rows in same scrape.
- System edge: partial scrape failure after 10/30 funds, validator rejects required columns, write conflict on upsert.
- Dependency edge: Groww page timeout, Google Play rate-limit, Supabase transient write failure.
- User/ops edge: manual rerun while cron run is active, wrong URL configured in scrape registry.
- Data quality edge: stale scrape timestamp accepted as fresh, changed fund name breaks slug mapping.

## Success Criteria
- 100% configured URLs are attempted and logged with pass/fail state.
- Ingestion writes only validated rows and marks rejected rows with explicit reason.
- Duplicate protection ensures one canonical latest row per `fund_slug`.
- Failed scrape run can resume without duplicating already-written records.
- Dashboard source tables (`mutual_fund_data`, `app_reviews`) are query-ready for downstream phases.
