"""
Upload crawled company profile CSVs to Supabase.

Tables populated:
  company_profiles      ← *_company_profile.csv  (upsert on symbol)
  company_leaders       ← *_leaders.csv           (delete-then-insert per symbol)
  company_subsidiaries  ← *_subsidiaries.csv      (delete-then-insert per symbol)

Usage:
    python upload_to_db.py
"""

import os
import glob
import math
import pandas as pd
from dotenv import load_dotenv

# Load credentials from backend/.env (one level up from this script)
_env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(_env_path)

from supabase import create_client, Client

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in backend/.env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')
BATCH_SIZE = 200   # rows per Supabase request


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _clean(row: dict) -> dict:
    """Replace NaN / inf with None so rows serialise to valid JSON."""
    out = {}
    for k, v in row.items():
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            out[k] = None
        else:
            out[k] = v
    return out


def _read_all(pattern: str) -> list[dict]:
    """Glob pattern → list of cleaned row dicts from all matching CSVs."""
    rows = []
    for f in sorted(glob.glob(pattern)):
        try:
            df = pd.read_csv(f)
            rows.extend(df.to_dict(orient='records'))
        except Exception as exc:
            print(f"  [WARN] skipping {os.path.basename(f)}: {exc}")
    return [_clean(r) for r in rows]


def _batched_insert(table: str, rows: list[dict], upsert_col: str | None = None):
    ok = err = 0
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]
        try:
            if upsert_col:
                supabase.table(table).upsert(batch, on_conflict=upsert_col).execute()
            else:
                supabase.table(table).insert(batch).execute()
            ok += len(batch)
        except Exception as exc:
            print(f"  [ERROR] {table} batch {i}–{i+len(batch)}: {exc}")
            err += len(batch)
    return ok, err


def _delete_by_symbols(table: str, symbols: list[str]):
    """Delete all rows for the given symbols in batches."""
    for i in range(0, len(symbols), BATCH_SIZE):
        chunk = symbols[i : i + BATCH_SIZE]
        try:
            supabase.table(table).delete().in_('symbol', chunk).execute()
        except Exception as exc:
            print(f"  [ERROR] delete {table} for symbols batch {i}: {exc}")


# ─────────────────────────────────────────────
# Upload functions
# ─────────────────────────────────────────────

def upload_profiles():
    print("=== company_profiles ===")
    rows = _read_all(os.path.join(OUTPUT_DIR, '*_company_profile.csv'))
    print(f"  Loaded {len(rows)} rows from {len(glob.glob(os.path.join(OUTPUT_DIR, '*_company_profile.csv')))} files")
    ok, err = _batched_insert('company_profiles', rows, upsert_col='symbol')
    print(f"  Upserted: {ok}  Errors: {err}")


def upload_leaders():
    print("=== company_leaders ===")
    rows = _read_all(os.path.join(OUTPUT_DIR, '*_leaders.csv'))
    print(f"  Loaded {len(rows)} rows from {len(glob.glob(os.path.join(OUTPUT_DIR, '*_leaders.csv')))} files")

    symbols = list({r['symbol'] for r in rows})
    print(f"  Deleting existing leaders for {len(symbols)} symbols …")
    _delete_by_symbols('company_leaders', symbols)

    ok, err = _batched_insert('company_leaders', rows)
    print(f"  Inserted: {ok}  Errors: {err}")


def upload_subsidiaries():
    print("=== company_subsidiaries ===")
    rows = _read_all(os.path.join(OUTPUT_DIR, '*_subsidiaries.csv'))
    print(f"  Loaded {len(rows)} rows from {len(glob.glob(os.path.join(OUTPUT_DIR, '*_subsidiaries.csv')))} files")

    symbols = list({r['symbol'] for r in rows})
    print(f"  Deleting existing subsidiaries for {len(symbols)} symbols …")
    _delete_by_symbols('company_subsidiaries', symbols)

    ok, err = _batched_insert('company_subsidiaries', rows)
    print(f"  Inserted: {ok}  Errors: {err}")


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────

if __name__ == '__main__':
    upload_profiles()
    print()
    upload_leaders()
    print()
    upload_subsidiaries()
    print("\nAll done.")
