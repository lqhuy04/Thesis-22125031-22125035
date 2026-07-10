-- FA_Indicator was documented as "one row per stock per year" but had no
-- constraint enforcing it (only a surrogate `id` primary key) — so a real
-- upsert on (stock_id, year) wasn't possible; re-importing would create
-- duplicate rows instead of updating existing ones.
--
-- Verified before applying: no existing (stock_id, year) duplicates among
-- rows with a non-null stock_id (only unrelated orphan rows with
-- stock_id IS NULL, which UNIQUE allows since NULLs don't conflict).
--
-- Already applied directly against the Supabase DB on 2026-07-10; kept here
-- for reference / re-applying on another environment.

ALTER TABLE "FA_Indicator"
    ADD CONSTRAINT fa_indicator_stock_year_unique UNIQUE (stock_id, year);
