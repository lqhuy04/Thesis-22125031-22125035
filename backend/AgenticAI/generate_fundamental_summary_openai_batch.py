import time

from agents.service.openai_fundamental import (
    get_candidate_symbols,
    get_existing_summary_symbols,
    summarize_fundamental,
)


# Batch configuration
MAX_SYMBOLS = 100
SOURCE_TABLE = "financial_indicators"
LIMIT_YEARS = 5
FORCE_REGENERATE = False
FETCH_SYMBOL_RETRIES = 10
FETCH_SYMBOL_RETRY_DELAY_SECONDS = 20


def main() -> None:
    candidate_symbols = []
    for attempt in range(1, FETCH_SYMBOL_RETRIES + 1):
        try:
            candidate_symbols = get_candidate_symbols(limit=MAX_SYMBOLS, source_table=SOURCE_TABLE)
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

    for idx, symbol in enumerate(symbols_to_run, start=1):
        try:
            result = summarize_fundamental(symbol=symbol, limit=LIMIT_YEARS)
            success_count += 1
            print(
                f"[{idx}/{len(symbols_to_run)}] OK {symbol} | years={result['source_years']}"
            )
        except Exception as exc:
            fail_count += 1
            print(f"[{idx}/{len(symbols_to_run)}] FAIL {symbol} | error={exc}")

    print("\nBatch completed")
    print(f"Success: {success_count}")
    print(f"Failed: {fail_count}")


if __name__ == "__main__":
    main()
