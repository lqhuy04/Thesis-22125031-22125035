"""
Upload processed *_financial_indicators.csv files into Supabase FA_Indicator.

Resolves each file's symbol to Stock.id, then upserts on (stock_id, year) —
see add_fa_indicator_unique_constraint.sql for the constraint this relies on.

Usage
─────
  python import_financial_indicators_to_db.py                  # imports ./bank_output
  python import_financial_indicators_to_db.py --dir ./output   # imports another folder
"""

import argparse
import glob
import math
import os
from pathlib import Path
from typing import Dict, List

import pandas as pd
from dotenv import load_dotenv
from supabase import Client, create_client

BATCH_SIZE = 200
QUERY_CHUNK_SIZE = 200

# Columns FA_Indicator actually has (see db.get_pool()-based introspection);
# anything else in the CSV (e.g. "symbol") is dropped before upserting.
_FA_INDICATOR_COLUMNS = {
    "year", "stock_id",
    "cash_cycle_days", "net_income", "profit_yoy", "revenue", "revenue_yoy",
    "market_cap", "eps", "pe_ratio", "pb_ratio", "ps_ratio", "p_cash_flow",
    "shares_outstanding", "ev_ebitda", "bvps", "cash_ratio", "debt_to_equity",
    "roe", "roa", "days_receivable", "days_inventory", "quick_ratio",
    "days_payable", "gross_margin", "ebit_margin", "net_margin",
    "current_ratio", "asset_turnover", "loans_to_equity", "financial_leverage",
    "roic", "interest_coverage", "fixed_asset_turnover",
    "casa_ratio", "car", "net_interest_income", "nii_growth", "credit_growth",
    "deposit_growth", "nim", "yield_on_earning_assets", "cost_of_funds",
    "non_interest_to_interest_income", "cir", "equity_to_liabilities",
    "equity_to_loans", "equity_to_assets", "ldr", "npl_ratio",
    "npl_coverage_ratio", "loan_loss_reserve_ratio", "provision_expense_to_loans",
}


def _get_supabase_client() -> Client:
    backend_env = Path(__file__).resolve().parents[2] / "backend" / ".env"
    load_dotenv(backend_env)

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in backend/.env")

    return create_client(url, key)


def _resolve_stock_ids(client: Client, symbols: List[str]) -> Dict[str, str]:
    """Return {symbol: stock_id} for the given symbols."""
    symbol_to_id: Dict[str, str] = {}
    for i in range(0, len(symbols), QUERY_CHUNK_SIZE):
        chunk = symbols[i : i + QUERY_CHUNK_SIZE]
        rows = (
            client.table("Stock")
            .select("id, stock_symbol")
            .in_("stock_symbol", chunk)
            .execute()
            .data
            or []
        )
        for row in rows:
            symbol_to_id[row["stock_symbol"]] = row["id"]
    return symbol_to_id


def _clean_value(v):
    if isinstance(v, float) and math.isnan(v):
        return None
    if pd.isna(v):
        return None
    return v


def _load_rows(csv_path: str, stock_id: str) -> List[dict]:
    df = pd.read_csv(csv_path)
    records = []
    for row in df.to_dict(orient="records"):
        record = {k: _clean_value(v) for k, v in row.items() if k in _FA_INDICATOR_COLUMNS}
        record["stock_id"] = stock_id
        record["year"] = int(float(row["year"]))
        records.append(record)
    return records


def import_all(client: Client, input_dir: str) -> None:
    files = sorted(glob.glob(os.path.join(input_dir, "*_financial_indicators.csv")))
    if not files:
        print(f"No *_financial_indicators.csv files found in {input_dir}")
        return

    symbols = [os.path.basename(f).split("_")[0].upper() for f in files]
    symbol_to_id = _resolve_stock_ids(client, symbols)

    all_rows: List[dict] = []
    skipped: List[str] = []
    for f, symbol in zip(files, symbols):
        stock_id = symbol_to_id.get(symbol)
        if not stock_id:
            skipped.append(symbol)
            continue
        rows = _load_rows(f, stock_id)
        all_rows.extend(rows)
        print(f"  {symbol}: {len(rows)} year-rows queued")

    if skipped:
        print(f"[WARN] Skipped (no matching Stock row): {', '.join(skipped)}")

    if not all_rows:
        print("Nothing to upsert.")
        return

    ok = err = 0
    for i in range(0, len(all_rows), BATCH_SIZE):
        batch = all_rows[i : i + BATCH_SIZE]
        try:
            client.table("FA_Indicator").upsert(batch, on_conflict="stock_id,year").execute()
            ok += len(batch)
        except Exception as exc:
            print(f"  [ERROR] batch {i}-{i + len(batch)}: {exc}")
            err += len(batch)

    print(f"\nUpserted: {ok}  Errors: {err}  (out of {len(all_rows)} rows across {len(files) - len(skipped)} symbols)")


def main():
    parser = argparse.ArgumentParser(
        description="Upsert processed *_financial_indicators.csv files into Supabase FA_Indicator."
    )
    parser.add_argument(
        "--dir", "-d",
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "bank_output"),
        help="Directory containing *_financial_indicators.csv files (default: ./bank_output)",
    )
    args = parser.parse_args()

    client = _get_supabase_client()
    import_all(client, args.dir)


if __name__ == "__main__":
    main()
