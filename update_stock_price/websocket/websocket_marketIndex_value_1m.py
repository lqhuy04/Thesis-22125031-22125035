import logging
import os
import sys
import time
from datetime import datetime, timedelta, timezone
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

VN_TZ = timezone(timedelta(hours=7))

TABLE = "MarketIndex_Value_1m"
INDEX_SYMBOLS = ("VN100", "VN30")
ACCESS_TOKEN_URL = "https://fc-data.ssi.com.vn/api/v2/Market/AccessToken"
INTRADAY_OHLC_URL = "https://fc-data.ssi.com.vn/api/v2/Market/IntradayOhlc"
PAGE_SIZE = 1000
POLL_INTERVAL_SECONDS = 1
SLEEP_BETWEEN_SYMBOLS = 1.1
TOKEN_REFRESH_SECONDS = 50 * 60
OVERLAP_MINUTES = 2

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
# SSI CLIENT
# ═════════════════════════════════════════════════════════════════════════════


class SSIIntradayClient:
    def __init__(self):
        self.access_token = ""
        self.token_refreshed_at = 0.0

    def refresh_access_token(self) -> bool:
        """Refresh the SSI access token."""
        try:
            payload = {
                "consumerID": config.consumerID,
                "consumerSecret": config.consumerSecret,
            }
            response = requests.post(
                ACCESS_TOKEN_URL,
                json=payload,
                timeout=10,
            )
            response.raise_for_status()

            data = response.json()
            access_token = data.get("data", {}).get("accessToken", "")
            if not access_token:
                raise ValueError("No access token in response")

            self.access_token = access_token
            self.token_refreshed_at = time.monotonic()
            logger.info("Successfully refreshed SSI access token")
            return True
        except Exception as e:
            logger.error(f"Failed to refresh SSI access token: {e}")
            return False

    def ensure_access_token(self) -> bool:
        token_age = time.monotonic() - self.token_refreshed_at
        if not self.access_token or token_age >= TOKEN_REFRESH_SECONDS:
            return self.refresh_access_token()
        return True

    def fetch_intraday_rows(
        self,
        symbol: str,
        trading_date: str,
    ) -> list[dict]:
        """Fetch page 1 of today's SSI IntradayOhlc data."""
        if not self.ensure_access_token():
            return []

        params = {
            "pageIndex": 1,
            "pageSize": PAGE_SIZE,
            "symbol": symbol,
            "fromDate": trading_date,
            "toDate": trading_date,
        }

        for attempt in range(2):
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(
                INTRADAY_OHLC_URL,
                params=params,
                headers=headers,
                timeout=30,
            )

            if response.status_code == 401 and attempt == 0:
                logger.warning(
                    f"[{symbol}] SSI token expired; refreshing and retrying"
                )
                if not self.refresh_access_token():
                    return []
                continue

            response.raise_for_status()
            payload = response.json()
            rows = payload.get("data") or payload.get("dataList") or []
            if not isinstance(rows, list):
                raise ValueError(
                    f"Unexpected IntradayOhlc data type: {type(rows).__name__}"
                )
            return rows

        return []


# ═════════════════════════════════════════════════════════════════════════════
# DATA NORMALIZATION
# ═════════════════════════════════════════════════════════════════════════════


def parse_ssi_datetime(row: dict) -> datetime | None:
    """Parse SSI TradingDate + Time into a naive Vietnam-market datetime."""
    trading_date = (
        row.get("TradingDate")
        or row.get("tradingDate")
        or row.get("tradingdate")
        or ""
    )
    raw_time = row.get("Time") or row.get("time") or ""
    if not trading_date or not raw_time:
        return None

    raw_time = str(raw_time).strip()
    time_format = "%H:%M:%S" if raw_time.count(":") == 2 else "%H:%M"

    try:
        return datetime.strptime(
            f"{trading_date} {raw_time}",
            f"%d/%m/%Y {time_format}",
        )
    except (TypeError, ValueError):
        return None


def normalize_intraday_values(
    rows: list[dict],
    market_index_id: str,
) -> list[dict]:
    """
    Normalize SSI rows to one value per minute.

    If SSI returns multiple points in the same minute, retain the point with
    the latest second so the minute value converges to its final value.
    """
    latest_by_minute: dict[datetime, tuple[datetime, dict]] = {}

    for row in rows:
        trading_dt = parse_ssi_datetime(row)
        raw_value = row.get("Value")
        if raw_value is None:
            raw_value = row.get("value")

        if trading_dt is None or raw_value in (None, ""):
            continue

        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            continue

        minute_dt = trading_dt.replace(second=0, microsecond=0)
        current = latest_by_minute.get(minute_dt)
        if current is None or trading_dt >= current[0]:
            latest_by_minute[minute_dt] = (
                trading_dt,
                {
                    "market_index_id": market_index_id,
                    "trading_time": minute_dt.isoformat(timespec="seconds"),
                    "value": value,
                },
            )

    return [
        latest_by_minute[minute_dt][1]
        for minute_dt in sorted(latest_by_minute)
    ]


def select_values_to_upsert(
    values: list[dict],
    last_upserted_minute: datetime | None,
) -> list[dict]:
    """Select new values plus a small overlap that finalizes recent minutes."""
    if last_upserted_minute is None:
        return values

    threshold = last_upserted_minute - timedelta(minutes=OVERLAP_MINUTES)
    return [
        item
        for item in values
        if datetime.fromisoformat(item["trading_time"]) >= threshold
    ]


# ═════════════════════════════════════════════════════════════════════════════
# SUPABASE
# ═════════════════════════════════════════════════════════════════════════════


def get_market_indexes() -> dict[str, str]:
    """Resolve VN100 and VN30 to their MarketIndex ids."""
    result: dict[str, str] = {}

    for symbol in INDEX_SYMBOLS:
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
                continue
            result[symbol] = str(rows[0]["id"])
        except Exception as e:
            logger.error(f"Failed to resolve MarketIndex '{symbol}': {e}")

    return result


def upsert_values(values: list[dict]) -> int:
    """Upsert normalized values and return the number of submitted rows."""
    if not values:
        return 0

    deduped = {
        (item["market_index_id"], item["trading_time"]): item
        for item in values
    }
    payload = list(deduped.values())
    supabase.table(TABLE).upsert(
        payload,
        on_conflict="market_index_id,trading_time",
    ).execute()
    return len(payload)


# ═════════════════════════════════════════════════════════════════════════════
# POLLING
# ═════════════════════════════════════════════════════════════════════════════


def poll_index(
    client: SSIIntradayClient,
    symbol: str,
    market_index_id: str,
    trading_date: str,
    last_upserted_minute: datetime | None,
) -> datetime | None:
    """Fetch one index, upsert its new values, and advance its cursor."""
    try:
        rows = client.fetch_intraday_rows(symbol, trading_date)
        values = normalize_intraday_values(rows, market_index_id)
        selected_values = select_values_to_upsert(
            values,
            last_upserted_minute,
        )

        if not selected_values:
            logger.info(f"[{symbol}] No new intraday index values")
            return last_upserted_minute

        upserted = upsert_values(selected_values)
        latest_minute = max(
            datetime.fromisoformat(item["trading_time"])
            for item in selected_values
        )
        logger.info(
            f"[{symbol}] Upserted {upserted} values; "
            f"latest={latest_minute.isoformat(timespec='minutes')}"
        )
        return latest_minute
    except Exception as e:
        logger.error(f"[{symbol}] Poll failed: {e}", exc_info=True)
        return last_upserted_minute


def main():
    logger.info(
        "Starting SSI intraday index poller for VN100 and VN30 "
        "(once per minute)..."
    )

    market_indexes = get_market_indexes()
    if not market_indexes:
        logger.error("No VN100 or VN30 MarketIndex records found. Exiting.")
        return

    missing_symbols = set(INDEX_SYMBOLS) - set(market_indexes)
    if missing_symbols:
        logger.warning(
            f"Skipping missing MarketIndex records: {sorted(missing_symbols)}"
        )

    client = SSIIntradayClient()
    if not client.ensure_access_token():
        logger.error("No SSI access token found. Exiting.")
        return

    last_poll_minute: datetime | None = None
    cursor_date = ""
    last_upserted_by_symbol: dict[str, datetime | None] = {
        symbol: None for symbol in market_indexes
    }

    try:
        while True:
            now = datetime.now(VN_TZ)
            current_poll_minute = now.replace(
                second=0,
                microsecond=0,
                tzinfo=None,
            )
            trading_date = now.strftime("%d/%m/%Y")

            if trading_date != cursor_date:
                cursor_date = trading_date
                last_upserted_by_symbol = {
                    symbol: None for symbol in market_indexes
                }
                logger.info(f"New trading date: {trading_date}")

            if current_poll_minute != last_poll_minute:
                for position, (symbol, market_index_id) in enumerate(
                    market_indexes.items(),
                    start=1,
                ):
                    last_upserted_by_symbol[symbol] = poll_index(
                        client,
                        symbol,
                        market_index_id,
                        trading_date,
                        last_upserted_by_symbol[symbol],
                    )
                    if position < len(market_indexes):
                        time.sleep(SLEEP_BETWEEN_SYMBOLS)

                last_poll_minute = current_poll_minute

            time.sleep(POLL_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        logger.info("Stopped intraday index poller.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Unhandled exception in main: {e}", exc_info=True)
        sys.exit(1)
