"""
Crawl SSI iBoard financial-indicator data for bank symbols that are still
missing bank-only (CAMELS) indicators in Supabase.

Scope
─────
  Symbols  : only stocks in the "Ngân hàng" category
             ({"idx":14,"id":"8300","category_name":"Ngân hàng"} in Category)
  Page     : only the "Chỉ số tài chính" tab — Cân đối kế toán / Kết quả
             kinh doanh / Lưu chuyển tiền tệ are skipped entirely, since
             bank-only indicators (car, nim, ldr, npl_ratio, ...) only ever
             appear on that tab (see _INDICATOR_COLUMNS in
             ssi_financial_downloader.py).
  Filter   : a bank symbol is only crawled if FA_Indicator has no row for
             its stock_id, or at least one row has a NULL bank-only column.

This only downloads + cleans the CSVs into --output; it does not write to
Supabase (no existing script upserts into FA_Indicator yet, and the
(stock_id, year) upsert conflict target hasn't been confirmed).

Usage
─────
  python crawl_bank_missing_indicators.py
  python crawl_bank_missing_indicators.py --output ./bank_output --headless
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv
from supabase import Client, create_client

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ssi_financial_downloader as sfd

# {"idx":14,"id":"8300","category_name":"Ngân hàng"}
BANK_CATEGORY_ID = "8300"

# Bank-only (credit institution) columns added to FA_Indicator — see
# add_bank_indicator_columns.sql. Kept in sync with _INDICATOR_COLUMNS'
# bank-only entries in ssi_financial_downloader.py.
BANK_INDICATOR_COLUMNS = [
    "casa_ratio", "car", "net_interest_income", "nii_growth", "credit_growth",
    "deposit_growth", "nim", "yield_on_earning_assets", "cost_of_funds",
    "non_interest_to_interest_income", "cir", "equity_to_liabilities",
    "equity_to_loans", "equity_to_assets", "ldr", "npl_ratio",
    "npl_coverage_ratio", "loan_loss_reserve_ratio", "provision_expense_to_loans",
]

QUERY_CHUNK_SIZE = 200

PROGRESS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "bank_indicator_progress.txt"
)


def _get_supabase_client() -> Client:
    backend_env = Path(__file__).resolve().parents[2] / "backend" / ".env"
    load_dotenv(backend_env)

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in backend/.env")

    return create_client(url, key)


def _fetch_bank_symbols(client: Client) -> Dict[str, str]:
    """Return {stock_id: symbol} for every stock in the Ngân hàng category."""
    links = (
        client.table("Category_Stock")
        .select("stock_id")
        .eq("category_id", BANK_CATEGORY_ID)
        .execute()
        .data
        or []
    )
    stock_ids = [row["stock_id"] for row in links]
    if not stock_ids:
        return {}

    stock_id_to_symbol: Dict[str, str] = {}
    for i in range(0, len(stock_ids), QUERY_CHUNK_SIZE):
        chunk = stock_ids[i : i + QUERY_CHUNK_SIZE]
        rows = (
            client.table("Stock")
            .select("id, stock_symbol")
            .in_("id", chunk)
            .execute()
            .data
            or []
        )
        for row in rows:
            stock_id_to_symbol[row["id"]] = row["stock_symbol"]

    return stock_id_to_symbol


def _fetch_symbols_missing_bank_indicators(
    client: Client, stock_id_to_symbol: Dict[str, str]
) -> List[str]:
    """
    Return the symbols that either have no FA_Indicator row at all, or have
    at least one row with a NULL bank-only column.
    """
    stock_ids = list(stock_id_to_symbol.keys())
    if not stock_ids:
        return []

    columns = "stock_id,year," + ",".join(BANK_INDICATOR_COLUMNS)
    seen_ids = set()
    missing_ids = set()

    for i in range(0, len(stock_ids), QUERY_CHUNK_SIZE):
        chunk = stock_ids[i : i + QUERY_CHUNK_SIZE]
        rows = (
            client.table("FA_Indicator")
            .select(columns)
            .in_("stock_id", chunk)
            .execute()
            .data
            or []
        )
        for row in rows:
            seen_ids.add(row["stock_id"])
            if any(row.get(col) is None for col in BANK_INDICATOR_COLUMNS):
                missing_ids.add(row["stock_id"])

    # Banks with zero FA_Indicator rows also need a full crawl.
    missing_ids |= (set(stock_ids) - seen_ids)

    return sorted(stock_id_to_symbol[sid] for sid in missing_ids)


def _load_progress() -> set:
    if not os.path.exists(PROGRESS_FILE):
        return set()
    with open(PROGRESS_FILE, encoding="utf-8") as f:
        return {line.strip().upper() for line in f if line.strip()}


def _mark_done(symbol: str) -> None:
    with open(PROGRESS_FILE, "a", encoding="utf-8") as f:
        f.write(symbol.upper() + "\n")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Crawl the 'Chỉ số tài chính' tab for bank symbols missing "
            "bank-only indicators in FA_Indicator."
        )
    )
    parser.add_argument(
        "--output", "-o",
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "bank_output"),
        help="Directory where downloaded/processed CSVs are saved (default: ./bank_output)",
    )
    parser.add_argument("--headless", action="store_true", help="Run Chrome in headless mode")
    parser.add_argument(
        "--reset-progress", action="store_true",
        help="Clear the bank progress file and start from scratch.",
    )
    args = parser.parse_args()

    if args.reset_progress and os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)
        print("Progress file cleared.")

    client = _get_supabase_client()

    stock_id_to_symbol = _fetch_bank_symbols(client)
    print(f"Bank symbols in category {BANK_CATEGORY_ID} (Ngân hàng): {len(stock_id_to_symbol)}")
    if not stock_id_to_symbol:
        print("No bank symbols found in Category_Stock — nothing to do.")
        return

    missing_symbols = _fetch_symbols_missing_bank_indicators(client, stock_id_to_symbol)
    print(f"Missing at least one bank indicator: {len(missing_symbols)}")
    if not missing_symbols:
        print("All bank symbols already have complete bank indicators.")
        return

    done = _load_progress()
    remaining = [s for s in missing_symbols if s.upper() not in done]
    print(f"Already crawled this run : {len(done)}")
    print(f"Remaining to crawl       : {len(remaining)}")

    if not remaining:
        print("All missing bank symbols have already been crawled.")
        return

    downloader = sfd.SSIFinancialDownloader(download_dir=args.output, headless=args.headless)
    try:
        downloader.start()
        if not downloader.login():
            print("Login failed. Exiting.")
            sys.exit(1)

        for idx, symbol in enumerate(remaining, start=1):
            print(f"\n{'=' * 60}")
            print(f"[{idx}/{len(remaining)}] {symbol}")
            print("=" * 60)

            try:
                csv_path = downloader.download_financial_indicators_for_symbol(symbol)
                if not csv_path or not os.path.exists(csv_path):
                    print(f"[WARN] No file downloaded for {symbol} — skipping.")
                    continue

                df = sfd.process_financial_indicators_csv(csv_path, symbol=symbol)
                df.to_csv(csv_path, index=False, encoding="utf-8-sig")
                print(f"[OK] {os.path.basename(csv_path)}  ({len(df)} rows, {len(df.columns)} cols)")

                _mark_done(symbol)

            except Exception as exc:
                print(f"[ERROR] {symbol}: {exc}")
                import traceback
                traceback.print_exc()

                if sfd.is_browser_dead(exc):
                    try:
                        downloader.restart()
                    except Exception as restart_exc:
                        print(f"[FATAL] Could not restart browser: {restart_exc}")
                        break

                print(f"Skipping {symbol} and continuing …")
                continue

        print(f"\n{'=' * 60}")
        print("ALL DONE")
        print("=" * 60)
        print(f"Completed: {len(_load_progress())} / {len(missing_symbols)} bank symbols")

    except Exception as exc:
        print(f"Fatal error: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        downloader.close()


if __name__ == "__main__":
    main()
