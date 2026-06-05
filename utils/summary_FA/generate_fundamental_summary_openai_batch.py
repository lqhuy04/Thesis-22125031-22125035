import time

from backend.AgenticAI.service.openai_fundamental import (
    get_candidate_symbols_from_tables,
    get_existing_summary_symbols,
    summarize_fundamental,
)


# Batch configuration
# Set to None to process all available symbols from SOURCE_TABLES.
MAX_SYMBOLS = None
SOURCE_TABLES = [
    "financial_balance_sheets",
    "financial_income_statements",
    "financial_cash_flows",
    "financial_indicators",
]
LIMIT_YEARS = 5
FORCE_REGENERATE = False
FETCH_SYMBOL_RETRIES = 10
FETCH_SYMBOL_RETRY_DELAY_SECONDS = 20
SYMBOL_DELAY_SECONDS = 1.5
BATCH_COOLDOWN_EVERY = 25
BATCH_COOLDOWN_SECONDS = 3
MAX_CONSECUTIVE_FAILURES = 5


def main() -> None:
    candidate_symbols = []
    for attempt in range(1, FETCH_SYMBOL_RETRIES + 1):
        try:
            candidate_symbols = get_candidate_symbols_from_tables(
                limit=MAX_SYMBOLS,
                source_tables=SOURCE_TABLES,
            )
            break
        except Exception as exc:
            if attempt == FETCH_SYMBOL_RETRIES:
                print(f"Failed to load symbols after {FETCH_SYMBOL_RETRIES} attempts: {exc}")
                return
            print(
                f"Load symbols failed (attempt {attempt}/{FETCH_SYMBOL_RETRIES}): {exc}. "
                f"Retrying in {FETCH_SYMBOL_RETRY_DELAY_SECONDS}s..."
            )
            time.sleep(FETCH_SYMBOL_RETRY_DELAY_SECONDS)

    existing_symbols = get_existing_summary_symbols()

    if FORCE_REGENERATE:
        symbols_to_run = candidate_symbols
    else:
        symbols_to_run = [s for s in candidate_symbols if s not in existing_symbols]

    print(f"Candidate symbols: {len(candidate_symbols)}")
    print(f"Existing summaries: {len(existing_symbols)}")
    print(f"Symbols to process: {len(symbols_to_run)}")

    if not symbols_to_run:
        print("Nothing to process. All candidate symbols already have summaries.")
        return

    success_count = 0
    fail_count = 0
    consecutive_failures = 0

    for idx, symbol in enumerate(symbols_to_run, start=1):
        try:
            result = summarize_fundamental(symbol=symbol, limit=LIMIT_YEARS)
            success_count += 1
            consecutive_failures = 0
            print(
                f"[{idx}/{len(symbols_to_run)}] OK {symbol} | years={result['source_years']}"
            )
        except Exception as exc:
            fail_count += 1
            consecutive_failures += 1
            print(f"[{idx}/{len(symbols_to_run)}] FAIL {symbol} | error={exc}")

            # Stop early when the DB/API is likely degraded to avoid making it worse.
            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                print(
                    f"Reached {MAX_CONSECUTIVE_FAILURES} consecutive failures. "
                    "Stopping early to protect upstream services."
                )
                break

        # Add pacing so we do not hammer Supabase with back-to-back queries.
        if idx < len(symbols_to_run):
            time.sleep(SYMBOL_DELAY_SECONDS)
            if idx % BATCH_COOLDOWN_EVERY == 0:
                print(
                    f"Cooling down for {BATCH_COOLDOWN_SECONDS}s after {idx} symbols..."
                )
                time.sleep(BATCH_COOLDOWN_SECONDS)

    print("\nBatch completed")
    print(f"Success: {success_count}")
    print(f"Failed: {fail_count}")


if __name__ == "__main__":
    main()
