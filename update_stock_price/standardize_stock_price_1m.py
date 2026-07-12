import os
import time
import logging
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from supabase import create_client
from ssi_fc_data import fc_md_client, model

from vnindex_symbols import get_vnindex_symbols

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
KEEP_DAYS     = 30
LOOKBACK_DAYS  = 2
SLEEP_SECONDS  = 1.1        # Delay giữa các symbol để tránh rate-limit SSI
ALLOWED_INDICES = {"VNINDEX", "VN30", "VN100", "HNXINDEX", "HNXUpcomIndex"}

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

def get_target_symbols() -> set[str]:
    """Toàn bộ mã cổ phiếu thuộc VNINDEX (từ DB) ∪ các chỉ số cần giữ."""
    vnindex_stocks = get_vnindex_symbols(supabase)
    if not vnindex_stocks:
        logger.warning("VNINDEX symbol list is empty (DB issue?); processing indices only")
    return vnindex_stocks | ALLOWED_INDICES

# ═════════════════════════════════════════════════════════════════════════════
# SSI DATA
# ═════════════════════════════════════════════════════════════════════════════

def fetch_intraday_ohlc(symbol: str, from_date: str, to_date: str) -> list[dict]:
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
    for r in rows:
        trading_date = r.get("TradingDate") or r.get("tradingdate") or ""
        raw_time     = r.get("Time")        or r.get("time")        or ""
        if not trading_date or not raw_time:
            continue

        parts           = raw_time.split(":")
        normalized_time = f"{parts[0]}:{parts[1]}:00"
        dd, mm, yyyy    = trading_date.split("/")
        trading_time    = f"{yyyy}-{mm}-{dd}T{normalized_time}"

        result.append({
            "symbol":       symbol,
            "trading_time": trading_time,
            "open":         float(r.get("Open")   or 0) * (1 if symbol in ALLOWED_INDICES else 1/1000),
            "high":         float(r.get("High")   or 0) * (1 if symbol in ALLOWED_INDICES else 1/1000),
            "low":          float(r.get("Low")    or 0) * (1 if symbol in ALLOWED_INDICES else 1/1000),
            "close":        float(r.get("Close")  or 0) * (1 if symbol in ALLOWED_INDICES else 1/1000),
            "volume":       float(r.get("Volume") or 0),
        })

    return result

def get_latest_trading_date(symbol: str) -> str | None:
    try:
        response = (
            supabase.table(TABLE)
            .select("trading_time")
            .eq("symbol", symbol)
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

def reconcile_latest_day(symbols: list[str], expected_date: str, from_date: str, to_date: str) -> None:
    stale_symbols: list[str] = []

    for symbol in symbols:
        latest_date = get_latest_trading_date(symbol)
        if latest_date != expected_date:
            stale_symbols.append(symbol)

    if not stale_symbols:
        logger.info(f"All symbols are up to date for {expected_date}")
        return

    logger.warning(
        f"[RECONCILE] {len(stale_symbols)} symbols are missing latest day {expected_date}; retrying SSI lookback {from_date} → {to_date}"
    )

    repaired = 0
    still_missing: list[str] = []
    for symbol in stale_symbols:
        candles = fetch_intraday_ohlc(symbol, from_date, to_date)
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
    # Khử trùng lặp theo (symbol, trading_time) để tránh lỗi
    # "ON CONFLICT DO UPDATE cannot affect row a second time" (giữ dòng sau cùng).
    deduped = {(c["symbol"], c["trading_time"]): c for c in candles}
    supabase.table(TABLE).upsert(list(deduped.values()), on_conflict="symbol,trading_time").execute()

def delete_old_candles(symbol: str, cutoff_iso: str) -> None:
    supabase.table(TABLE) \
        .delete() \
        .eq("symbol", symbol) \
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

    symbols = get_target_symbols()
    logger.info(f"Processing {len(symbols)} symbols (VNINDEX + indices)")

    if not symbols:
        logger.warning("No symbols to process")
        return

    all_candles = []
    for symbol in sorted(symbols):
        try:
            candles = fetch_intraday_ohlc(symbol, from_date, today_str)
            if candles:
                all_candles.extend(candles)
                upsert_candles(candles)
            delete_old_candles(symbol, cutoff_iso)
            time.sleep(SLEEP_SECONDS)  # Rate limiting
        except Exception as e:
            logger.error(f"[{symbol}] Error processing: {e}")

    reconcile_latest_day(sorted(symbols), today.isoformat(), from_date, today_str)

    logger.info(f"Total candles processed: {len(all_candles)}")
    logger.info("=== Done ===")

if __name__ == "__main__":
    main()