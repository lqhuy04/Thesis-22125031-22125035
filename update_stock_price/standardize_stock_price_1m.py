import os
import re
import logging
import requests
from datetime import date, timedelta
from dotenv import load_dotenv
from supabase import create_client
from ssi_fc_data import fc_md_client, model

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

TABLE         = "Stock_Price_1m"
KEEP_DAYS     = 30
LOOKBACK_DAYS  = 2
SYMBOL_REGEX  = re.compile(r'^[A-Z0-9]{3}$')
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

        return access_token
    except Exception as e:
        logger.error(f"Failed to get SSI access token: {e}")
        return ""

def get_hose_symbols() -> set[str]:
    """Fetch HOSE symbols from SSI API and keep only symbols with 3 characters, plus allowed indices."""
    try:
        access_token = get_ssi_access_token()
        if not access_token:
            return ALLOWED_INDICES.copy()

        url = "https://fc-data.ssi.com.vn/api/v2/Market/Securities?Market=HOSE&PageSize=1000"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()
        symbols = {
            str(item.get("Symbol") or "").strip().upper()
            for item in (data.get("data") or [])
            if str(item.get("Symbol") or "").strip().upper()
        }
        filtered = {symbol for symbol in symbols if SYMBOL_REGEX.match(symbol)}
        # Add allowed indices
        filtered.update(ALLOWED_INDICES)
        return filtered
    except Exception as e:
        logger.error(f"Failed to fetch HOSE symbols from SSI API: {e}")
        return ALLOWED_INDICES.copy()

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
    supabase.table(TABLE).upsert(candles, on_conflict="symbol,trading_time").execute()

def delete_old_candles(symbol: str, cutoff_iso: str) -> None:
    supabase.table(TABLE) \
        .delete() \
        .eq("symbol", symbol) \
        .lt("trading_time", cutoff_iso) \
        .execute()
    logger.info(f"[{symbol}] Deleted candles older than {cutoff_iso}")

# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

def main():
    today      = date.today()
    today_str  = today.strftime("%d/%m/%Y")
    from_date  = (today - timedelta(days=LOOKBACK_DAYS)).strftime("%d/%m/%Y")
    cutoff_iso = (today - timedelta(days=KEEP_DAYS)).isoformat()

    logger.info(f"=== Starting intraday sync: {from_date} → {today_str} ===")

    symbols = get_hose_symbols()
    logger.info(f"Fetched {len(symbols)} HOSE symbols")

    if not symbols:
        logger.warning("No symbols to process")
        return

    all_candles = []
    for symbol in sorted(symbols):
        try:
            candles = fetch_intraday_ohlc(symbol, from_date, today_str)
            if candles:
                logger.info(f"[{symbol}] Fetched {len(candles)} candles")
                all_candles.extend(candles)
                upsert_candles(candles)
            delete_old_candles(symbol, cutoff_iso)
        except Exception as e:
            logger.error(f"[{symbol}] Error processing: {e}")

    reconcile_latest_day(sorted(symbols), today.isoformat(), from_date, today_str)

    logger.info(f"Total candles processed: {len(all_candles)}")
    logger.info("=== Done ===")

if __name__ == "__main__":
    main()