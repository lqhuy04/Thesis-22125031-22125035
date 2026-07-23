import logging
import os
import sys
import time
from datetime import date, datetime, timedelta
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

TABLE = "MarketIndex_Value_1m"
INDEX_SYMBOLS = ("VN100", "VN30")
SLEEP_SECONDS = 1.1
LOOKBACK_MONTHS = 3
DAYS_PER_MONTH = 30

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


def fetch_intraday_rows(
    symbol: str,
    from_date: str,
    to_date: str,
    access_token: str,
) -> list[dict]:
    """Fetch raw intraday rows for one index from SSI's IntradayOhlc endpoint."""
    try:
        if not access_token:
            return []

        url = "https://fc-data.ssi.com.vn/api/v2/Market/IntradayOhlc"
        params = {
            "PageSize": 9999,
            "FromDate": from_date,
            "ToDate": to_date,
            "Symbol": symbol,
        }
        headers = {"Authorization": f"Bearer {access_token}"}

        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        return data.get("data") or []
    except Exception as e:
        logger.error(f"Failed to fetch intraday rows for {symbol}: {e}")
        return []


def _aggregate_intraday_minutes(rows: list[dict]) -> list[dict]:
    """Keep the latest index value in each minute without synthetic gap fill."""
    if not rows:
        return []

    rows = sorted(rows, key=lambda row: row["trading_time"])
    aggregated: dict[datetime, dict] = {}

    for row in rows:
        trading_dt = datetime.fromisoformat(row["trading_time"])
        minute_dt = trading_dt.replace(second=0, microsecond=0)
        aggregated[minute_dt] = {
            "market_index_id": row["market_index_id"],
            "trading_time": minute_dt.isoformat(timespec="seconds"),
            "value": row["value"],
        }

    return [aggregated[minute_dt] for minute_dt in sorted(aggregated)]


def fetch_intraday_values(
    symbol: str,
    market_index_id: str,
    from_date: str,
    to_date: str,
    access_token: str,
) -> list[dict]:
    """Fetch and convert SSI intraday values for a market index."""
    try:
        rows = fetch_intraday_rows(symbol, from_date, to_date, access_token)

        result = []
        for row in rows:
            trading_date = row.get("TradingDate") or row.get("tradingdate") or ""
            raw_time = row.get("Time") or row.get("time") or ""
            raw_value = row.get("Value")
            if raw_value is None:
                raw_value = row.get("value")

            if not trading_date or not raw_time or raw_value in (None, ""):
                continue

            dd, mm, yyyy = trading_date.split("/")
            result.append(
                {
                    "market_index_id": market_index_id,
                    "trading_time": f"{yyyy}-{mm}-{dd}T{raw_time}",
                    "value": float(raw_value),
                }
            )

        return _aggregate_intraday_minutes(result)
    except Exception as e:
        logger.error(f"Failed to fetch intraday data for {symbol}: {e}")
        return []


def build_monthly_date_ranges(reference_date: date) -> list[tuple[str, str]]:
    """Build three consecutive 30-day SSI query windows, newest first."""
    date_ranges = []
    for month_offset in range(LOOKBACK_MONTHS):
        range_end = reference_date - timedelta(days=DAYS_PER_MONTH * month_offset)
        range_start = range_end - timedelta(days=DAYS_PER_MONTH)
        date_ranges.append(
            (
                range_start.strftime("%d/%m/%Y"),
                range_end.strftime("%d/%m/%Y"),
            )
        )
    return date_ranges


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


def upsert_values(values: list[dict]) -> None:
    """Deduplicate and upsert index values to database."""
    if not values:
        return

    try:
        supabase.table(TABLE).upsert(
            values,
            on_conflict="market_index_id,trading_time",
        ).execute()
    except Exception as e:
        logger.error(f"Error upserting market index values: {e}")
        raise


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

    date_ranges = build_monthly_date_ranges(date.today())
    logger.info(
        f"Date range: {date_ranges[-1][0]} → {date_ranges[0][1]} "
        f"({LOOKBACK_MONTHS} requests per index)"
    )

    total_values_fetched = 0
    total_values_upserted = 0

    for idx, (symbol, market_index_id) in enumerate(market_indexes.items(), 1):
        logger.info(
            f"[{idx}/{len(market_indexes)}] Fetching 1m index data for {symbol}..."
        )

        for month_idx, (from_date, to_date) in enumerate(date_ranges, 1):
            logger.info(
                f"  [{month_idx}/{LOOKBACK_MONTHS}] "
                f"Fetching {from_date} → {to_date}"
            )
            try:
                values = fetch_intraday_values(
                    symbol,
                    market_index_id,
                    from_date,
                    to_date,
                    access_token,
                )
                if values:
                    total_values_fetched += len(values)
                    upsert_values(values)
                    total_values_upserted += len(values)
                    logger.info(f"    → Upserted {len(values)} index values")
                else:
                    logger.info("    → No data fetched")
            finally:
                time.sleep(SLEEP_SECONDS)

    logger.info("\n✅ Completed!")
    logger.info(f"Total index values fetched: {total_values_fetched}")
    logger.info(f"Total index values upserted: {total_values_upserted}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        input("Press Enter to exit...")  # giữ cửa sổ lại để đọc lỗi
