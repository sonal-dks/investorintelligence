-- Phase 01: Create mutual_fund_data and app_reviews tables
-- Run this in your Supabase SQL editor or via migration tool.

-- =============================================================
-- Table: mutual_fund_data
-- =============================================================
CREATE TABLE IF NOT EXISTS mutual_fund_data (
    id              uuid            PRIMARY KEY DEFAULT gen_random_uuid(),
    fund_slug       text            NOT NULL,
    fund_name       text            NOT NULL,
    category        text            NOT NULL,
    nav             numeric(10,4)   NOT NULL,
    nav_date        date,
    aum_cr          numeric(10,2),
    expense_ratio   numeric(5,3),
    min_sip         integer,
    risk_level      text,
    returns_1m      numeric(12,4),
    returns_6m      numeric(12,4),
    returns_1y      numeric(12,4),
    returns_3y      numeric(12,4),
    returns_5y      numeric(12,4),
    exit_load_text  text,
    tax_text        text,
    source_url      text            NOT NULL,
    scraped_at      timestamptz     NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_fund_slug_scraped
    ON mutual_fund_data (fund_slug, scraped_at DESC);

-- =============================================================
-- Table: app_reviews
-- =============================================================
CREATE TABLE IF NOT EXISTS app_reviews (
    id              uuid            PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id       text            UNIQUE,
    reviewer_name   text,
    rating          integer         NOT NULL CHECK (rating >= 1 AND rating <= 5),
    review_text     text,
    review_date     date,
    thumbs_up       integer         DEFAULT 0,
    app_version     text,
    sentiment       text,
    scraped_at      timestamptz     NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_review_date
    ON app_reviews (review_date DESC);

CREATE INDEX IF NOT EXISTS idx_review_sentiment
    ON app_reviews (sentiment);

-- =============================================================
-- RLS: Disable for service-role batch inserts (Phase 01 only).
-- Later phases will enable RLS with user-scoped policies.
-- =============================================================
ALTER TABLE mutual_fund_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_reviews ENABLE ROW LEVEL SECURITY;

-- Service role bypasses RLS automatically.
-- For anon/authenticated reads in later phases:
CREATE POLICY "Public read mutual_fund_data"
    ON mutual_fund_data FOR SELECT
    USING (true);

CREATE POLICY "Public read app_reviews"
    ON app_reviews FOR SELECT
    USING (true);
