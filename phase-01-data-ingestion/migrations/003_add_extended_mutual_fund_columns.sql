-- Phase 01: add extended scraped fields to mutual_fund_data
-- Safe to run multiple times (IF NOT EXISTS guards).

ALTER TABLE mutual_fund_data
    ADD COLUMN IF NOT EXISTS min_lumpsum_first integer,
    ADD COLUMN IF NOT EXISTS min_lumpsum_second integer,
    ADD COLUMN IF NOT EXISTS rating smallint,
    ADD COLUMN IF NOT EXISTS asset_class text,
    ADD COLUMN IF NOT EXISTS lock_in_period text,
    ADD COLUMN IF NOT EXISTS one_day_return_pct numeric(12,4),
    ADD COLUMN IF NOT EXISTS returns_10y numeric(12,4),
    ADD COLUMN IF NOT EXISTS returns_since_inception numeric(12,4),
    ADD COLUMN IF NOT EXISTS stamp_duty_text text,
    ADD COLUMN IF NOT EXISTS benchmark text,
    ADD COLUMN IF NOT EXISTS investment_objective text,
    ADD COLUMN IF NOT EXISTS fund_manager_name text,
    ADD COLUMN IF NOT EXISTS fund_manager_tenure text,
    ADD COLUMN IF NOT EXISTS return_calculator_sip jsonb,
    ADD COLUMN IF NOT EXISTS return_calculator_one_time jsonb,
    ADD COLUMN IF NOT EXISTS returns_and_rankings_annualised jsonb,
    ADD COLUMN IF NOT EXISTS returns_and_rankings_absolute jsonb,
    ADD COLUMN IF NOT EXISTS holding_analysis jsonb,
    ADD COLUMN IF NOT EXISTS sector_allocation jsonb,
    ADD COLUMN IF NOT EXISTS advanced_ratios jsonb,
    ADD COLUMN IF NOT EXISTS faq_items jsonb;
