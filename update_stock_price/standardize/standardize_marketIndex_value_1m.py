import logging
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

UPDATE_STOCK_PRICE_DIR = Path(__file__).resolve().parents[1]
if str(UPDATE_STOCK_PRICE_DIR) not in sys.path:
    sys.path.insert(0, str(UPDATE_STOCK_PRICE_DIR))

from dotenv import load_dotenv
from ssi_fc_data import fc_md_client, model
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
client = None

VN_TZ = timezone(timedelta(hours=7))

TABLE = "MarketIndex_Value_1m"
INDEX_SYMBOLS = ("VN100", "VN30")
KEEP_DAYS = 90
LOOKBACK_DAYS = 2
PAGE_SIZE = 9999
SLEEP_SECONDS = 1.1

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
# MARKET INDEX MANAGEMENT
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


# ═════════════════════════════════════════════════════════════════════════════
# SSI DATA
# ═════════════════════════════════════════════════════════════════════════════


def get_ssi_client():
    """Create the SSI client lazily so import does not perform network I/O."""
    global client
    if client is None:
        client = fc_md_client.MarketDataClient(config)
    return client


def parse_ssi_datetime(row: dict) -> datetime | None:
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


def fetch_intraday_values(
    symbol: str,
    market_index_id: str,
    from_date: str,
    to_date: str,
) -> list[dict]:
    """Fetch IntradayOhlc and retain the latest Value within each minute."""
    request = model.intraday_ohlc(
        symbol,
        from_date,
        to_date,
        1,
        PAGE_SIZE,
        "true",
        1,
    )
    response = get_ssi_client().intraday_ohlc(config, request)

    if isinstance(response, dict):
        rows = response.get("data") or response.get("dataList") or []
    elif isinstance(response, list):
        rows = response
    else:
        logger.error(
            f"[{symbol}] Unexpected response type: {type(response).__name__}"
        )
        return []

    latest_by_minute: dict[datetime, tuple[datetime, dict]] = {}
    rejected = 0

    for row in rows:
        trading_dt = parse_ssi_datetime(row)
        raw_value = row.get("Value")
        if raw_value is None:
            raw_value = row.get("value")

        if trading_dt is None or raw_value in (None, ""):
            rejected += 1
            continue

        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            rejected += 1
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

    if rejected:
        logger.warning(
            f"[{symbol}] Skipped {rejected}/{len(rows)} invalid intraday rows"
        )

    return [
        latest_by_minute[minute_dt][1]
        for minute_dt in sorted(latest_by_minute)
    ]


# ═════════════════════════════════════════════════════════════════════════════
# SUPABASE
# ═════════════════════════════════════════════════════════════════════════════


def upsert_values(values: list[dict]) -> int:
    """Deduplicate and upsert standardized 1m index values."""
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


def delete_old_values(market_index_id: str, cutoff_iso: str) -> None:
    """Remove 1m values outside the configured 90-day retention."""
    (
        supabase.table(TABLE)
        .delete()
        .eq("market_index_id", market_index_id)
        .lt("trading_time", cutoff_iso)
        .execute()
    )


def get_latest_trading_date(market_index_id: str) -> str | None:
    try:
        response = (
            supabase.table(TABLE)
            .select("trading_time")
            .eq("market_index_id", market_index_id)
            .order("trading_time", desc=True)
            .limit(1)
            .execute()
        )
        rows = getattr(response, "data", None) or []
        if not rows:
            return None
        latest = rows[0].get("trading_time") or ""
        return latest[:10] if latest else None
    except Exception as e:
        logger.warning(f"Failed to read latest trading_time: {e}")
        return None


# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════


def main():
    today = datetime.now(VN_TZ).date()
    today_str = today.strftime("%d/%m/%Y")
    from_date = (today - timedelta(days=LOOKBACK_DAYS)).strftime("%d/%m/%Y")
    cutoff_iso = (today - timedelta(days=KEEP_DAYS)).isoformat()

    logger.info(
        f"=== Starting MarketIndex 1m standardization: "
        f"{from_date} → {today_str} ==="
    )

    market_indexes = get_market_indexes()
    if not market_indexes:
        logger.error("No VN100 or VN30 MarketIndex records found. Exiting.")
        return

    total_upserted = 0

    for position, (symbol, market_index_id) in enumerate(
        market_indexes.items(),
        start=1,
    ):
        try:
            values = fetch_intraday_values(
                symbol,
                market_index_id,
                from_date,
                today_str,
            )
            upserted = upsert_values(values)
            total_upserted += upserted
            delete_old_values(market_index_id, cutoff_iso)

            latest_date = get_latest_trading_date(market_index_id)
            if latest_date != today.isoformat():
                logger.warning(
                    f"[{symbol}] Latest stored date is {latest_date!r}; "
                    f"expected {today.isoformat()}"
                )

            logger.info(f"[{symbol}] Upserted {upserted} standardized 1m values")
        except Exception as e:
            logger.error(f"[{symbol}] Standardization failed: {e}", exc_info=True)

        if position < len(market_indexes):
            time.sleep(SLEEP_SECONDS)

    logger.info(f"Total standardized 1m values upserted: {total_upserted}")
    logger.info("=== MarketIndex 1m standardization done ===")


if __name__ == "__main__":
    main()
