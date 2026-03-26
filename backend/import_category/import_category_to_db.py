import csv
import os
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple

from dotenv import load_dotenv
from supabase import Client, create_client


CSV_FILE = Path(__file__).resolve().parent / "FiinProX_DNNY_Phannganh_09.2024.csv"
CATEGORY_COLUMNS = [
    "Phân ngành - L1",
    "Phân ngành - L2",
    "Phân ngành - L3",
    "Phân ngành - L4",
    "Phân ngành - L5",
]
SYMBOL_COLUMN = "Mã"
PAGE_SIZE = 1000


def get_supabase_client() -> Client:
    backend_env = Path(__file__).resolve().parents[1] / ".env"
    load_dotenv(backend_env)

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in backend/.env")

    return create_client(url, key)


def normalize_text(value: str) -> str:
    if value is None:
        return ""
    return str(value).strip()


def fetch_all_rows(client: Client, table_name: str, columns: str) -> List[dict]:
    rows: List[dict] = []
    offset = 0

    while True:
        response = (
            client.table(table_name)
            .select(columns)
            .range(offset, offset + PAGE_SIZE - 1)
            .execute()
        )
        batch = response.data or []
        rows.extend(batch)

        if len(batch) < PAGE_SIZE:
            break

        offset += PAGE_SIZE

    return rows


def chunked(records: List[dict], chunk_size: int = 500) -> Iterable[List[dict]]:
    for i in range(0, len(records), chunk_size):
        yield records[i : i + chunk_size]


def fetch_key_id_map_by_values(
    client: Client,
    table_name: str,
    key_column: str,
    values: Set[str],
    id_column: str = "id",
    query_chunk_size: int = 200,
) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    value_list = sorted([v for v in values if normalize_text(v)])

    for i in range(0, len(value_list), query_chunk_size):
        batch = value_list[i : i + query_chunk_size]
        rows = (
            client.table(table_name)
            .select(f"{id_column},{key_column}")
            .in_(key_column, batch)
            .execute()
            .data
            or []
        )

        for row in rows:
            key_value = normalize_text(row.get(key_column))
            id_value = normalize_text(row.get(id_column))
            if key_value and id_value:
                mapping[key_value] = id_value

    return mapping


def parse_csv_pairs(csv_path: Path) -> Tuple[Set[str], Dict[str, Set[str]]]:
    all_categories: Set[str] = set()
    symbol_to_categories: Dict[str, Set[str]] = {}

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            symbol = normalize_text(row.get(SYMBOL_COLUMN, ""))
            if not symbol:
                continue

            categories_for_symbol: List[str] = []
            seen_for_symbol: Set[str] = set()

            for col in CATEGORY_COLUMNS:
                category_name = normalize_text(row.get(col, ""))
                if not category_name or category_name in seen_for_symbol:
                    continue
                categories_for_symbol.append(category_name)
                seen_for_symbol.add(category_name)

            for category_name in categories_for_symbol:
                all_categories.add(category_name)
                symbol_to_categories.setdefault(symbol, set()).add(category_name)

    return all_categories, symbol_to_categories


def ensure_categories(client: Client, categories: Set[str]) -> Dict[str, str]:
    category_map = fetch_key_id_map_by_values(
        client, "category", "category_name", categories
    )

    missing = sorted([name for name in categories if name not in category_map])
    if missing:
        payload = [{"category_name": name} for name in missing]
        for batch in chunked(payload):
            client.table("category").upsert(batch, on_conflict="category_name").execute()

        category_map = fetch_key_id_map_by_values(
            client, "category", "category_name", categories
        )

    return category_map


def ensure_stocks(client: Client, symbols: Set[str]) -> Dict[str, str]:
    stock_map = fetch_key_id_map_by_values(
        client, "stock", "stock_symbol", symbols
    )

    missing_symbols = sorted([symbol for symbol in symbols if symbol not in stock_map])
    if missing_symbols:
        payload = [{"stock_symbol": symbol} for symbol in missing_symbols]
        for batch in chunked(payload):
            client.table("stock").upsert(batch, on_conflict="stock_symbol").execute()

        stock_map = fetch_key_id_map_by_values(
            client, "stock", "stock_symbol", symbols
        )

    return stock_map


def build_stock_category_payload_from_maps(
    symbol_to_categories: Dict[str, Set[str]],
    stock_map: Dict[str, str],
    category_map: Dict[str, str],
) -> List[dict]:
    payload: List[dict] = []

    for symbol in sorted(symbol_to_categories.keys()):
        stock_id = stock_map.get(symbol)
        if not stock_id:
            continue

        for category_name in sorted(symbol_to_categories[symbol]):
            cate_id = category_map.get(category_name)
            if not cate_id:
                continue

            payload.append(
                {
                    "stock_id": stock_id,
                    "cate_id": cate_id,
                }
            )

    return payload


def main() -> None:
    if not CSV_FILE.exists():
        raise FileNotFoundError(f"CSV file not found: {CSV_FILE}")

    client = get_supabase_client()

    categories, symbol_to_categories = parse_csv_pairs(CSV_FILE)
    print(f"Parsed {len(categories)} unique categories")
    print(f"Parsed {len(symbol_to_categories)} unique symbols from CSV")

    category_map = ensure_categories(client, categories)
    print(f"Category table now has at least {len(category_map)} mapped category names")

    stock_map = ensure_stocks(client, set(symbol_to_categories.keys()))
    print(f"Stock table now has at least {len(stock_map)} symbols")

    stock_category_payload = build_stock_category_payload_from_maps(
        symbol_to_categories, stock_map, category_map
    )
    if not stock_category_payload:
        print("No new stock-category mappings to insert.")
        return

    for batch in chunked(stock_category_payload):
        client.table("stock_category").upsert(batch, on_conflict="stock_id,cate_id").execute()

    print(f"Upserted {len(stock_category_payload)} rows into stock_category")


if __name__ == "__main__":
    main()
