-- Adds bank-only (credit institution) CAMELS indicator columns to FA_Indicator.
-- These stay NULL for every non-bank symbol; SSI iBoard only emits them for
-- banks (see _INDICATOR_COLUMNS in utils/crawl_financial_downloads/ssi_financial_downloader.py).
-- Run once in the Supabase SQL editor, then re-run the downloader for bank symbols
-- to backfill (--symbol per bank ticker, or --reset-progress for a full re-crawl).

ALTER TABLE "FA_Indicator"
    ADD COLUMN IF NOT EXISTS casa_ratio                     NUMERIC,
    ADD COLUMN IF NOT EXISTS car                            NUMERIC,
    ADD COLUMN IF NOT EXISTS net_interest_income             NUMERIC,
    ADD COLUMN IF NOT EXISTS nii_growth                      NUMERIC,
    ADD COLUMN IF NOT EXISTS credit_growth                   NUMERIC,
    ADD COLUMN IF NOT EXISTS deposit_growth                  NUMERIC,
    ADD COLUMN IF NOT EXISTS nim                             NUMERIC,
    ADD COLUMN IF NOT EXISTS yield_on_earning_assets         NUMERIC,
    ADD COLUMN IF NOT EXISTS cost_of_funds                   NUMERIC,
    ADD COLUMN IF NOT EXISTS non_interest_to_interest_income NUMERIC,
    ADD COLUMN IF NOT EXISTS cir                             NUMERIC,
    ADD COLUMN IF NOT EXISTS equity_to_liabilities           NUMERIC,
    ADD COLUMN IF NOT EXISTS equity_to_loans                 NUMERIC,
    ADD COLUMN IF NOT EXISTS equity_to_assets                NUMERIC,
    ADD COLUMN IF NOT EXISTS ldr                             NUMERIC,
    ADD COLUMN IF NOT EXISTS npl_ratio                       NUMERIC,
    ADD COLUMN IF NOT EXISTS npl_coverage_ratio              NUMERIC,
    ADD COLUMN IF NOT EXISTS loan_loss_reserve_ratio         NUMERIC,
    ADD COLUMN IF NOT EXISTS provision_expense_to_loans      NUMERIC;
