import logging
import sys
import time
from datetime import datetime
from pathlib import Path

WEBSOCKET_DIR = Path(__file__).resolve().parent
if str(WEBSOCKET_DIR) not in sys.path:
    sys.path.insert(0, str(WEBSOCKET_DIR))

from websocket_marketIndex_value_1m import (
    INDEX_SYMBOLS,
    POLL_INTERVAL_SECONDS,
    SLEEP_BETWEEN_SYMBOLS,
    SSIIntradayClient,
    VN_TZ,
    get_market_indexes,
    normalize_intraday_values,
    supabase,
)

TABLE = "MarketIndex_Value_1d"
DAILY_CLOSE_TIME = "14:45:00"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def build_daily_value(
    rows: list[dict],
    market_index_id: str,
) -> dict | None:
    """
    Build today's 1d value from the latest point returned by IntradayOhlc.

    normalize_intraday_values sorts the values chronologically and keeps the
    latest SSI point within each minute, so the final element is the newest
    available index value.
    """
    values = normalize_intraday_values(rows, market_index_id)
    if not values:
        return None

    latest_value = values[-1]
    trading_date = latest_value["trading_time"][:10]
    return {
        "market_index_id": market_index_id,
        "trading_time": f"{trading_date}T{DAILY_CLOSE_TIME}",
        "value": latest_value["value"],
    }


def upsert_daily_value(value: dict) -> None:
    """Upsert the current daily index value."""
    supabase.table(TABLE).upsert(
        [value],
        on_conflict="market_index_id,trading_time",
    ).execute()


def poll_index(
    client: SSIIntradayClient,
    symbol: str,
    market_index_id: str,
    trading_date: str,
) -> None:
    """Fetch today's intraday data and update the index's current daily value."""
    try:
        rows = client.fetch_intraday_rows(symbol, trading_date)
        daily_value = build_daily_value(rows, market_index_id)
        if daily_value is None:
            logger.info(f"[{symbol}] No intraday data available for daily value")
            return

        upsert_daily_value(daily_value)
        logger.info(
            f"[{symbol}] Updated daily value={daily_value['value']} "
            f"at {daily_value['trading_time']}"
        )
    except Exception as e:
        logger.error(f"[{symbol}] Daily poll failed: {e}", exc_info=True)


def main():
    logger.info(
        "Starting SSI daily index poller for VN100 and VN30 "
        "(IntradayOhlc once per minute)..."
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

    try:
        while True:
            now = datetime.now(VN_TZ)
            current_poll_minute = now.replace(
                second=0,
                microsecond=0,
                tzinfo=None,
            )
            trading_date = now.strftime("%d/%m/%Y")

            if current_poll_minute != last_poll_minute:
                for position, (symbol, market_index_id) in enumerate(
                    market_indexes.items(),
                    start=1,
                ):
                    poll_index(
                        client,
                        symbol,
                        market_index_id,
                        trading_date,
                    )
                    if position < len(market_indexes):
                        time.sleep(SLEEP_BETWEEN_SYMBOLS)

                last_poll_minute = current_poll_minute

            time.sleep(POLL_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        logger.info("Stopped daily index poller.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Unhandled exception in main: {e}", exc_info=True)
        sys.exit(1)
