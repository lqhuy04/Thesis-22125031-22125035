import os
import logging
import re
import requests
import time
from datetime import date, datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client

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

TABLE         = "Stock_Price_1m"
SLEEP_SECONDS = 1.1
SYMBOL_SKIP_SUFFIX_RE = re.compile(r"\d{4}$")
SYMBOL_3CHAR_RE = re.compile(r'^[A-Z0-9]{3}$')

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
# SSI DATA
# ═════════════════════════════════════════════════════════════════════════════

def get_ssi_access_token() -> str:
    """Get access token from SSI API using consumer credentials."""
    try:
        url = "https://fc-data.ssi.com.vn/api/v2/Market/AccessToken"
        payload = {
            "consumerID": config.consumerID,
            "consumerSecret": config.consumerSecret
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

def fetch_intraday_rows(symbol: str, from_date: str, to_date: str, access_token: str) -> list[dict]:
    """Fetch raw intraday rows for one symbol from SSI's IntradayOhlc endpoint."""
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

def get_all_symbols(access_token: str) -> list[str]:
    """Fetch all HOSE symbols from SSI API."""
    try:
        if not access_token:
            return []
        
        url = "https://fc-data.ssi.com.vn/api/v2/Market/Securities?Market=HOSE&PageSize=1000"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        symbols = [item.get("Symbol") for item in (data.get("data") or []) if item.get("Symbol")]
        logger.info(f"Fetched {len(symbols)} HOSE symbols from SSI API")
        return sorted(symbols)
    except Exception as e:
        logger.error(f"Failed to fetch symbols from SSI API: {e}")
        return []

def filter_symbols(symbols: list[str]) -> list[str]:
    """Return only 3-character HOSE symbols (skip ones ending with 4-digit suffix)."""
    return [s for s in symbols if SYMBOL_3CHAR_RE.match(s) and not SYMBOL_SKIP_SUFFIX_RE.search(s)]

def _aggregate_intraday_minutes(rows: list[dict]) -> list[dict]:
    """Aggregate raw SSI trade rows into 1m candles without synthetic gap fill."""
    if not rows:
        return []

    rows = sorted(rows, key=lambda row: row["trading_time"])
    symbol = rows[0]["symbol"]

    aggregated: dict[datetime, dict] = {}
    for row in rows:
        minute_dt = datetime.fromisoformat(row["trading_time"]).replace(second=0, microsecond=0)
        candle = aggregated.get(minute_dt)
        if candle is None:
            aggregated[minute_dt] = {
                "symbol": symbol,
                "trading_time": minute_dt.isoformat(timespec="seconds"),
                "open": row["open"],
                "high": row["high"],
                "low": row["low"],
                "close": row["close"],
                "volume": row["volume"],
            }
            continue

        candle["high"] = max(candle["high"], row["high"])
        candle["low"] = min(candle["low"], row["low"])
        candle["close"] = row["close"]
        candle["volume"] += row["volume"]

    return [aggregated[minute_dt] for minute_dt in sorted(aggregated)]

def fetch_intraday_ohlc(symbol: str, from_date: str, to_date: str, access_token: str) -> list[dict]:
    """Fetch intraday OHLC data for a specific symbol."""
    try:
        rows = fetch_intraday_rows(symbol, from_date, to_date, access_token)

        result = []
        for r in rows:
            trading_date = r.get("TradingDate") or r.get("tradingdate") or ""
            raw_time     = r.get("Time")        or r.get("time")        or ""
            if not trading_date or not raw_time:
                continue

            dd, mm, yyyy    = trading_date.split("/")

            result.append({
                "symbol":       symbol,
                "trading_time": f"{yyyy}-{mm}-{dd}T{raw_time[:5]}:00",
                "open":         float(r.get("Open")   or 0) / 1000,
                "high":         float(r.get("High")   or 0) / 1000,
                "low":          float(r.get("Low")    or 0) / 1000,
                "close":        float(r.get("Close")  or 0) / 1000,
                "volume":       float(r.get("Volume") or 0),
            })

        time.sleep(SLEEP_SECONDS)  # Rate limiting
        return _aggregate_intraday_minutes(result)
    except Exception as e:
        logger.error(f"Failed to fetch intraday data for {symbol}: {e}")
        return []

# ═════════════════════════════════════════════════════════════════════════════
# SUPABASE
# ═════════════════════════════════════════════════════════════════════════════

def upsert_candles(candles: list[dict]) -> None:
    """Deduplicate and upsert candles to database."""
    if not candles:
        return
    
    try:
        supabase.table(TABLE).upsert(candles, on_conflict="symbol,trading_time").execute()
    except Exception as e:
        logger.error(f"Error upserting candles: {e}")

# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

def main():
    access_token = get_ssi_access_token()
    if not access_token:
        logger.error("No SSI access token found. Exiting.")
        return

    symbols = get_all_symbols(access_token)
    if not symbols:
        logger.error("No symbols found. Exiting.")
        return

    symbols = filter_symbols(symbols)
    if not symbols:
        logger.error("No symbols left after filtering. Exiting.")
        return

    today     = date.today()
    to_date   = today.strftime("%d/%m/%Y")
    from_date = (today - timedelta(days=30)).strftime("%d/%m/%Y")

    logger.info(f"Processing {len(symbols)} HOSE symbols (without 4-digit suffix)...")
    logger.info(f"Date range: {from_date} → {to_date}")
    
    total_candles_fetched = 0
    total_candles_upserted = 0
    
    for idx, symbol in enumerate(symbols, 1):
        logger.info(f"[{idx}/{len(symbols)}] Fetching 1m data for {symbol}...")
        
        candles = fetch_intraday_ohlc(symbol, from_date, to_date, access_token)
        if candles:
            total_candles_fetched += len(candles)
            upsert_candles(candles)
            total_candles_upserted += len(candles)
            logger.info(f"  → Upserted {len(candles)} candles")
        else:
            logger.info(f"  → No data fetched")
    
    logger.info(f"\n✅ Completed!")
    logger.info(f"Total candles fetched: {total_candles_fetched}")
    logger.info(f"Total candles upserted: {total_candles_upserted}")

if __name__ == "__main__":
    main()