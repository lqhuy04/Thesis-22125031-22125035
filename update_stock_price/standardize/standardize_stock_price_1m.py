import os
import sys
import time
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

UPDATE_STOCK_PRICE_DIR = Path(__file__).resolve().parents[1]
if str(UPDATE_STOCK_PRICE_DIR) not in sys.path:
    sys.path.insert(0, str(UPDATE_STOCK_PRICE_DIR))

from dotenv import load_dotenv
from supabase import create_client
from ssi_fc_data import fc_md_client, model

from utils.stock_price_validation import normalize_ohlcv
from utils.vn100_symbols import get_vn100_stock_ids

load_dotenv()

# ═════════════════════════════════════════════════════════════════════════════
# CONFIG
# ═════════════════════════════════════════════════════════════════════════════

class Config:
    auth_type      = os.getenv("SSI_AUTH_TYPE", "Bearer")
    consumerID     = os.getenv("SSI_CONSUMER_ID", "")
    consumerSecret = os.getenv("SSI_CONSUMER_SECRET", "")
    url            = os.getenv("SSI_API_URL", "https://fc-data.ssi.com.vn/")
    stream_url     = os.getenv("SSI_STREAM_URL", "https://fc-datahub.ssi.com.vn/")

config = Config()
client = fc_md_client.MarketDataClient(config)

VN_TZ = timezone(timedelta(hours=7))

TABLE         = "Stock_Price_1m"
KEEP_DAYS     = 90
LOOKBACK_DAYS  = 2
SLEEP_SECONDS  = 1.1        # Delay giữa các symbol để tránh rate-limit SSI

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

supabase = create_client(
    os.getenv("SUPABASE_URL", ""),
    os.getenv("SUPABASE_KEY", "")
)

# ═════════════════════════════════════════════════════════════════════════════
# SYMBOL MANAGEMENT
# ═════════════════════════════════════════════════════════════════════════════

def get_target_stocks() -> dict[str, str]:
    """Return the VN100 stock_symbol -> Stock.id mapping."""
    vn100_stocks = get_vn100_stock_ids(supabase)
    if not vn100_stocks:
        logger.warning("VN100 stock id mapping is empty (DB issue?)")
    return vn100_stocks

# ═════════════════════════════════════════════════════════════════════════════
# SSI DATA
# ═════════════════════════════════════════════════════════════════════════════

def fetch_intraday_ohlc(
    symbol: str,
    stock_id: str,
    from_date: str,
    to_date: str,
) -> list[dict]:
    req  = model.intraday_ohlc(symbol, from_date, to_date, 1, 9999, "true", 1)
    data = client.intraday_ohlc(config, req)

    if isinstance(data, dict):
        rows = data.get("data") or []
    elif isinstance(data, list):
        rows = data
    else:
        logger.error(f"Unexpected response type: {type(data)}")
        return []

    result = []
    rejected = 0
    for r in rows:
        trading_date = r.get("TradingDate") or r.get("tradingdate") or ""
        raw_time     = r.get("Time")        or r.get("time")        or ""
        if not trading_date or not raw_time:
            rejected += 1
            continue

        parts = raw_time.split(":")
        date_parts = trading_date.split("/")
        if len(parts) < 2 or len(date_parts) != 3:
            rejected += 1
            logger.debug("[%s] Skipping malformed timestamp: %r %r", symbol, trading_date, raw_time)
            continue

        normalized_time = f"{parts[0]}:{parts[1]}:00"
        dd, mm, yyyy    = date_parts
        trading_time    = f"{yyyy}-{mm}-{dd}T{normalized_time}"

        ohlcv, rejection_reason = normalize_ohlcv(
            r.get("Open"),
            r.get("High"),
            r.get("Low"),
            r.get("Close"),
            r.get("Volume"),
            price_multiplier=1 / 1000,
            allow_zero_volume=False,
        )
        if ohlcv is None:
            rejected += 1
            logger.debug(
                "[%s] Skipping invalid standardized OHLCV at %s: %s",
                symbol,
                trading_time,
                rejection_reason,
            )
            continue

        result.append({
            "stock_id":     stock_id,
            "trading_time": trading_time,
            **ohlcv,
        })

    if rejected:
        logger.warning("[%s] Skipped %d/%d invalid intraday rows", symbol, rejected, len(rows))

    return result

def get_latest_trading_date(stock_id: str, symbol: str) -> str | None:
    try:
        response = (
            supabase.table(TABLE)
            .select("trading_time")
            .eq("stock_id", stock_id)
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
        logger.warning(f"[{symbol}] Failed to read latest trading_time: {e}")
        return None

def reconcile_latest_day(
    stocks: dict[str, str],
    expected_date: str,
    from_date: str,
    to_date: str,
) -> None:
    stale_stocks: list[tuple[str, str]] = []

    for symbol, stock_id in stocks.items():
        latest_date = get_latest_trading_date(stock_id, symbol)
        if latest_date != expected_date:
            stale_stocks.append((symbol, stock_id))

    if not stale_stocks:
        logger.info(f"All symbols are up to date for {expected_date}")
        return

    logger.warning(
        f"[RECONCILE] {len(stale_stocks)} symbols are missing latest day {expected_date}; retrying SSI lookback {from_date} → {to_date}"
    )

    repaired = 0
    still_missing: list[str] = []
    for symbol, stock_id in stale_stocks:
        candles = fetch_intraday_ohlc(symbol, stock_id, from_date, to_date)
        if candles:
            upsert_candles(candles)
            repaired += 1
        else:
            still_missing.append(symbol)

    logger.info(
        f"[RECONCILE] repaired={repaired}, still_missing={len(still_missing)}"
    )
    if still_missing:
        logger.warning(f"[RECONCILE] still missing symbols: {still_missing[:20]}{' ...' if len(still_missing) > 20 else ''}")

# ═════════════════════════════════════════════════════════════════════════════
# SUPABASE
# ═════════════════════════════════════════════════════════════════════════════

def upsert_candles(candles: list[dict]) -> None:
    if not candles:
        return
    # Khử trùng lặp theo (stock_id, trading_time) để tránh lỗi
    # "ON CONFLICT DO UPDATE cannot affect row a second time" (giữ dòng sau cùng).
    deduped = {(c["stock_id"], c["trading_time"]): c for c in candles}
    supabase.table(TABLE).upsert(
        list(deduped.values()),
        on_conflict="stock_id,trading_time",
    ).execute()

def delete_old_candles(stock_id: str, cutoff_iso: str) -> None:
    supabase.table(TABLE) \
        .delete() \
        .eq("stock_id", stock_id) \
        .lt("trading_time", cutoff_iso) \
        .execute()

# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

def main():
    today      = datetime.now(VN_TZ).date()
    today_str  = today.strftime("%d/%m/%Y")
    from_date  = (today - timedelta(days=LOOKBACK_DAYS)).strftime("%d/%m/%Y")
    cutoff_iso = (today - timedelta(days=KEEP_DAYS)).isoformat()

    logger.info(f"=== Starting intraday sync: {from_date} → {today_str} ===")

    stocks = get_target_stocks()
    logger.info(f"Processing {len(stocks)} VN100 stocks")

    if not stocks:
        logger.warning("No stocks to process")
        return

    all_candles = []
    for symbol, stock_id in sorted(stocks.items()):
        try:
            candles = fetch_intraday_ohlc(
                symbol,
                stock_id,
                from_date,
                today_str,
            )
            if candles:
                all_candles.extend(candles)
                upsert_candles(candles)
            delete_old_candles(stock_id, cutoff_iso)
            time.sleep(SLEEP_SECONDS)  # Rate limiting
        except Exception as e:
            logger.error(f"[{symbol}] Error processing: {e}")

    reconcile_latest_day(stocks, today.isoformat(), from_date, today_str)

    logger.info(f"Total candles processed: {len(all_candles)}")
    logger.info("=== Done ===")

if __name__ == "__main__":
    main()
