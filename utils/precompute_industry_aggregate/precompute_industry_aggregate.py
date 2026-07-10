"""
precompute_industry_aggregate.py
================================
Tính chỉ tiêu TRUNG VỊ theo ngành ICB cấp 2 (theo từng năm) rồi ghi vào
bảng Supabase `FA_Industry_Aggregate` (schema: fa_industry_aggregate_schema.sql).

Gộp ngành theo 2 chữ số đầu của mã ICB chi tiết (BI_Profile.icb_code), vd
'83xx' → '8300' (Ngân hàng) — khớp cách bảng `Category` lưu mã ngành cấp 2
(đã xác minh: mọi icb_code hợp lệ trong BI_Profile đều khớp đúng 1 category
theo 2 số đầu).

Luồng:
  1. BI_Profile: stock_id → icb_code → industry_code.
  2. FA_Indicator: stock_id, year, các chỉ số.
  3. Gộp theo (industry_code, year), lấy trung vị mỗi chỉ số (bỏ giá trị thiếu).
  4. peer_count = số mã có dữ liệu trong (industry_code, year).
  5. Upsert vào FA_Industry_Aggregate (on_conflict = category_id,year).

Chạy:  python utils/precompute_industry_aggregate/precompute_industry_aggregate.py
"""
import os
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv
from supabase import Client, create_client

PAGE_SIZE = 1000
UPSERT_CHUNK = 500

# Chỉ giữ/tổng hợp các năm trong khoảng này (bao gồm 2 đầu mút).
MIN_YEAR = 2021
MAX_YEAR = 2025

# Chỉ tiêu được gộp trung vị — phải trùng tên cột trong FA_Indicator và FA_Industry_Aggregate.
INDICATOR_KEYS = [
    "roe", "roa", "roic", "gross_margin", "ebit_margin", "net_margin",
    "asset_turnover", "fixed_asset_turnover", "debt_to_equity", "financial_leverage",
    "loans_to_equity", "interest_coverage", "current_ratio", "quick_ratio", "cash_ratio",
    "days_inventory", "days_receivable", "pe_ratio", "pb_ratio", "ps_ratio",
    "ev_ebitda", "eps", "bvps",
    # Bank-only (CAMELS) — chỉ ngành 8300 (Ngân hàng) có dữ liệu, các ngành khác NULL.
    "car", "nim", "ldr", "npl_ratio",
]

_ICB_CATEGORY_CODE = {
    "05": "0500", "13": "1300", "17": "1700", "23": "2300", "27": "2700",
    "33": "3300", "35": "3500", "37": "3700", "45": "4500", "53": "5300",
    "55": "5500", "57": "5700", "65": "6500", "75": "7500", "83": "8300",
    "85": "8500", "86": "8600", "87": "8700", "89": "8900", "95": "9500",
}


def icb_to_industry_code(icb_code) -> Optional[str]:
    """Mã ICB chi tiết (vd '8355') → mã ngành ICB cấp 2 ('8300')."""
    return _ICB_CATEGORY_CODE.get(str(icb_code or "").strip()[:2])


def get_supabase_client() -> Client:
    backend_env = Path(__file__).resolve().parents[2] / "backend" / ".env"
    load_dotenv(backend_env)
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in backend/.env")
    return create_client(url, key)


def fetch_all(client: Client, table: str, columns: str) -> List[dict]:
    """Đọc toàn bộ bảng theo trang (PostgREST giới hạn ~1000 dòng/lần)."""
    rows: List[dict] = []
    offset = 0
    while True:
        batch = (
            client.table(table)
            .select(columns)
            .range(offset, offset + PAGE_SIZE - 1)
            .execute()
            .data
            or []
        )
        rows.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return rows


def _to_float(value) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def build_aggregate_rows(profiles: List[dict], indicators: List[dict]) -> List[dict]:
    # stock_id → industry_code
    industry_by_stock: Dict[object, str] = {}
    for p in profiles:
        sid = p.get("stock_id")
        code = icb_to_industry_code(p.get("icb_code"))
        if sid is not None and code:
            industry_by_stock[sid] = code

    # (industry_code, year) → {indicator: [values]}, và tập stock_id (peer_count).
    values: Dict[tuple, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
    peers: Dict[tuple, set] = defaultdict(set)

    for row in indicators:
        sid = row.get("stock_id")
        industry_code = industry_by_stock.get(sid)
        year = row.get("year")
        if not industry_code or year is None:
            continue
        try:
            year = int(year)
        except (TypeError, ValueError):
            continue
        if year < MIN_YEAR or year > MAX_YEAR:
            continue

        gkey = (industry_code, year)
        peers[gkey].add(sid)
        for key in INDICATOR_KEYS:
            v = _to_float(row.get(key))
            if v is not None:
                values[gkey][key].append(v)

    out: List[dict] = []
    for (industry_code, year), per_key in values.items():
        record = {
            "category_id": industry_code,
            "year": year,
            "peer_count": len(peers[(industry_code, year)]),
        }
        for key in INDICATOR_KEYS:
            vals = per_key.get(key)
            record[key] = statistics.median(vals) if vals else None
        out.append(record)

    out.sort(key=lambda r: (r["category_id"], r["year"]))
    return out


def main() -> None:
    client = get_supabase_client()

    print("Đọc BI_Profile (stock_id, icb_code)...")
    profiles = fetch_all(client, "BI_Profile", "stock_id, icb_code")
    print(f"  {len(profiles)} profiles")

    print("Đọc FA_Indicator...")
    indicators = fetch_all(client, "FA_Indicator", "stock_id, year," + ",".join(INDICATOR_KEYS))
    print(f"  {len(indicators)} indicator rows")

    rows = build_aggregate_rows(profiles, indicators)
    print(f"Tính được {len(rows)} dòng (industry_code, year).")
    if not rows:
        print("Không có dòng nào để ghi — kiểm tra dữ liệu icb_code / FA_Indicator.")
        return

    for i in range(0, len(rows), UPSERT_CHUNK):
        chunk = rows[i : i + UPSERT_CHUNK]
        client.table("FA_Industry_Aggregate").upsert(chunk, on_conflict="category_id,year").execute()
    print(f"Đã upsert {len(rows)} dòng vào FA_Industry_Aggregate.")

    # Dọn các năm ngoài khoảng giữ lại (phòng dữ liệu cũ từ lần chạy trước).
    client.table("FA_Industry_Aggregate").delete().lt("year", MIN_YEAR).execute()
    client.table("FA_Industry_Aggregate").delete().gt("year", MAX_YEAR).execute()
    print(f"Đã xóa các năm ngoài {MIN_YEAR}–{MAX_YEAR}.")

    # Dọn category_id không còn hợp lệ (vd đổi bảng phân ngành → mã cũ còn sót lại).
    existing_ids = {r["category_id"] for r in fetch_all(client, "FA_Industry_Aggregate", "category_id")}
    stale_ids = sorted(existing_ids - set(_ICB_CATEGORY_CODE.values()))
    if stale_ids:
        client.table("FA_Industry_Aggregate").delete().in_("category_id", stale_ids).execute()
        print(f"Đã xóa category_id không còn hợp lệ: {', '.join(stale_ids)}.")

    industries = sorted({r["category_id"] for r in rows})
    print(f"Ngành đã tổng hợp ({len(industries)}): {', '.join(industries)}")


if __name__ == "__main__":
    main()
