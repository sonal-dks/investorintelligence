-- Widen returns_* columns: scraped UI can yield outlier values that overflow numeric(6,2).
-- Safe to re-run after 001_create_tables.sql (older installs).

ALTER TABLE mutual_fund_data
  ALTER COLUMN returns_1m TYPE numeric(12,4),
  ALTER COLUMN returns_6m TYPE numeric(12,4),
  ALTER COLUMN returns_1y TYPE numeric(12,4),
  ALTER COLUMN returns_3y TYPE numeric(12,4),
  ALTER COLUMN returns_5y TYPE numeric(12,4);
