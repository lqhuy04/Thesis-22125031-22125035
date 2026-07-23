import logging
import os
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import requests

UPDATE_STOCK_PRICE_DIR = Path(__file__).resolve().parents[1]
if str(UPDATE_STOCK_PRICE_DIR) not in sys.path:
    sys.path.insert(0, str(UPDATE_STOCK_PRICE_DIR))

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# ═════════════════════════════════════════════════════════════════════════════
# CONFIG
# ═════════════════════════════════════════════════════════════════════════════


class Config:
    auth_type = os.getenv("SSI_AUTH_TYPE", "Bearer")
    consumerID = os.getenv("SSI_CONSUMER_ID", "")
    consumerSecret = os.getenv("SSI_CONSUMER_SECRET", "")
    url = os.getenv("SSI_API_URL", "https://fc-data.ssi.com.vn/")
    stream_url = os.getenv("SSI_STREAM_URL", "https://fc-datahub.ssi.com.vn/")


config = Config()

TABLE = "MarketIndex_Value_1d"
INDEX_SYMBOLS = ("VN100", "VN30")
DAILY_INDEX_URL = "https://fc-data.ssi.com.vn/api/v2/Market/DailyIndex"
CHUNK_DAYS = 30
PAGE_SIZE = 100
SLEEP_SECONDS = 1.1
YEARS_BACK = 5

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

supabase = create_client(
    os.getenv("SUPABASE_URL", ""),
    os.getenv("SUPABASE_KEY", ""),
)

# ═════════════════════════════════════════════════════════════════════════════
# DATE RANGE GENERATOR
# ═════════════════════════════════════════════════════════════════════════════


def generate_chunks(start: date, end: date, chunk_days: int):
    """Yield DD/MM/YYYY date ranges, each containing at most chunk_days days."""
    cursor = start
    while cursor <= end:
        chunk_end = min(cursor + timedelta(days=chunk_days - 1), end)
        yield cursor.strftime("%d/%m/%Y"), chunk_end.strftime("%d/%m/%Y")
        cursor = chunk_end + timedelta(days=1)


# ═════════════════════════════════════════════════════════════════════════════
# SSI DATA
# ═════════════════════════════════════════════════════════════════════════════


def get_ssi_access_token() -> str:
    """Get access token from SSI API using consumer credentials."""
    try:
        url = "https://fc-data.ssi.com.vn/api/v2/Market/AccessToken"
        payload = {
            "consumerID": config.consumerID,
            "consumerSecret": config.consumerSecret,
        }
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()

        data = response.json()
        access_token = data.get("data", {}).get("accessToken", "")
        if not access_token:
            raise ValueError("No access token in response")

        logger.info("Successfully obtained SSI access token")
        return access_token
    except Exception as e:
        logger.error(f"Failed to get SSI access token: {e}")
        return ""


def fetch_daily_index_rows(
    symbol: str,
    from_date: str,
    to_date: str,
    access_token: str,
) -> list[dict]:
    """Fetch all DailyIndex pages for one index and date range."""
    if not access_token:
        return []

    rows: list[dict] = []
    page_index = 1

    while True:
        params = {
            "indexId": symbol,
            "fromDate": from_date,
            "toDate": to_date,
            "pageIndex": page_index,
            "pageSize": PAGE_SIZE,
        }
        headers = {"Authorization": f"Bearer {access_token}"}

        response = requests.get(
            DAILY_INDEX_URL,
            params=params,
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()

        payload = response.json()
        page_rows = payload.get("data") or payload.get("dataList") or []
        if not isinstance(page_rows, list):
            raise ValueError(
                f"Unexpected DailyIndex data type: {type(page_rows).__name__}"
            )

        rows.extend(page_rows)

        try:
            total_record = int(payload.get("totalRecord") or len(rows))
        except (TypeError, ValueError):
            total_record = len(rows)

        if not page_rows or len(page_rows) < PAGE_SIZE or len(rows) >= total_record:
            break

        page_index += 1
        time.sleep(SLEEP_SECONDS)

    return rows


def fetch_daily_index_values(
    symbol: str,
    market_index_id: str,
    from_date: str,
    to_date: str,
    access_token: str,
) -> list[dict]:
    """Fetch DailyIndex data and convert IndexValue to database rows."""
    try:
        rows = fetch_daily_index_rows(
            symbol,
            from_date,
            to_date,
            access_token,
        )

        result = []
        for row in rows:
            trading_date = (
                row.get("TradingDate")
                or row.get("tradingDate")
                or row.get("tradingdate")
                or ""
            )
            raw_value = row.get("IndexValue")
            if raw_value is None:
                raw_value = row.get("indexValue")

            if not trading_date or raw_value in (None, ""):
                continue

            parts = trading_date.split("/")
            if len(parts) != 3:
                logger.warning(
                    f"[{symbol}] Cannot parse date {trading_date!r}, skipping"
                )
                continue

            try:
                dd, mm, yyyy = parts
                value = float(raw_value)
            except (TypeError, ValueError):
                logger.warning(
                    f"[{symbol}] Cannot parse IndexValue {raw_value!r} "
                    f"on {trading_date}, skipping"
                )
                continue

            result.append(
                {
                    "market_index_id": market_index_id,
                    "trading_time": f"{yyyy}-{mm}-{dd}T14:45:00",
                    "value": value,
                }
            )

        return result
    except Exception as e:
        logger.error(
            f"Failed to fetch DailyIndex data for {symbol} "
            f"({from_date} → {to_date}): {e}"
        )
        return []


# ═════════════════════════════════════════════════════════════════════════════
# SUPABASE
# ═════════════════════════════════════════════════════════════════════════════


def get_market_index_id(symbol: str) -> str:
    """Resolve a MarketIndex id by its name."""
    try:
        response = (
            supabase.table("MarketIndex")
            .select("id")
            .eq("name", symbol)
            .limit(1)
            .execute()
        )
        rows = getattr(response, "data", None) or []
        if not rows:
            logger.error(f"MarketIndex '{symbol}' not found")
            return ""
        return str(rows[0]["id"])
    except Exception as e:
        logger.error(f"Failed to resolve MarketIndex '{symbol}': {e}")
        return ""


def upsert_values(values: list[dict]) -> int:
    """Deduplicate and upsert daily market index values."""
    if not values:
        return 0

    deduped = {
        (item["market_index_id"], item["trading_time"]): item
        for item in values
    }
    rows = list(deduped.values())
    supabase.table(TABLE).upsert(
        rows,
        on_conflict="market_index_id,trading_time",
    ).execute()
    return len(rows)


# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════


def main():
    access_token = get_ssi_access_token()
    if not access_token:
        logger.error("No SSI access token found. Exiting.")
        return

    market_indexes = {
        symbol: market_index_id
        for symbol in INDEX_SYMBOLS
        if (market_index_id := get_market_index_id(symbol))
    }
    if not market_indexes:
        logger.error("No VN100 or VN30 MarketIndex records found. Exiting.")
        return

    missing_symbols = set(INDEX_SYMBOLS) - set(market_indexes)
    if missing_symbols:
        logger.warning(
            f"Skipping missing MarketIndex records: {sorted(missing_symbols)}"
        )

    today = date.today()
    start_date = today - timedelta(days=365 * YEARS_BACK)
    chunks = list(generate_chunks(start_date, today, CHUNK_DAYS))
    total_chunks = len(chunks)

    logger.info(
        f"Date range: {start_date} → {today} "
        f"({total_chunks} chunks × {CHUNK_DAYS}d, delay={SLEEP_SECONDS}s)"
    )

    total_indexes = len(market_indexes)
    total_fetched = 0
    total_upserted = 0

    for index_position, (symbol, market_index_id) in enumerate(
        market_indexes.items(),
        start=1,
    ):
        logger.info(f"[{index_position}/{total_indexes}] Processing {symbol}...")
        index_values = []

        for chunk_position, (from_date, to_date) in enumerate(chunks, start=1):
            logger.info(
                f"  [{symbol}] Chunk {chunk_position}/{total_chunks}: "
                f"{from_date} → {to_date}"
            )

            values = fetch_daily_index_values(
                symbol,
                market_index_id,
                from_date,
                to_date,
                access_token,
            )
            index_values.extend(values)
            total_fetched += len(values)
            logger.info(f"  [{symbol}]   Fetched {len(values)} daily values")

            if chunk_position < total_chunks or index_position < total_indexes:
                time.sleep(SLEEP_SECONDS)

        try:
            upserted = upsert_values(index_values)
            total_upserted += upserted
            logger.info(
                f"[{index_position}/{total_indexes}] {symbol} done. "
                f"Upserted {upserted} daily values."
            )
        except Exception as e:
            logger.error(f"[{symbol}] Failed to upsert daily values: {e}")

    logger.info("All done.")
    logger.info(f"Total daily values fetched: {total_fetched}")
    logger.info(f"Total daily values upserted: {total_upserted}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        input("Press Enter to exit...")  # giữ cửa sổ lại để đọc lỗi
