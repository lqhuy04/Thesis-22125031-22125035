import os
import logging
import re
import requests
import time
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
SLEEP_SECONDS = 1.1
SYMBOL_SKIP_SUFFIX_RE = re.compile(r"\d{4}$")

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

def get_all_symbols() -> list[str]:
    """Fetch all HOSE symbols from SSI API."""
    try:
        access_token = get_ssi_access_token()
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
    """Skip symbols that end with four digits."""
    return [symbol for symbol in symbols if not SYMBOL_SKIP_SUFFIX_RE.search(symbol)]

def fetch_intraday_ohlc(symbol: str, from_date: str, to_date: str) -> list[dict]:
    """Fetch intraday OHLC data for a specific symbol."""
    try:
        req  = model.intraday_ohlc(symbol, from_date, to_date, 1, 9999, "true", 1)
        data = client.intraday_ohlc(config, req)

        # SDK trả về dict với key 'data' chứa list
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
                "open":         float(r.get("Open")   or 0) / 1000,
                "high":         float(r.get("High")   or 0) / 1000,
                "low":          float(r.get("Low")    or 0) / 1000,
                "close":        float(r.get("Close")  or 0) / 1000,
                "volume":       float(r.get("Volume") or 0),
            })

        time.sleep(SLEEP_SECONDS)  # Rate limiting
        return result
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
    
    # Deduplicate by symbol,trading_time to avoid conflict errors
    seen = {}
    for candle in candles:
        key = (candle["symbol"], candle["trading_time"])
        seen[key] = candle
    
    deduped = list(seen.values())
    if len(deduped) < len(candles):
        logger.info(f"  → Deduplicated {len(candles)} → {len(deduped)} candles")
    
    try:
        supabase.table(TABLE).upsert(deduped, on_conflict="symbol,trading_time").execute()
    except Exception as e:
        logger.error(f"Error upserting candles: {e}")

# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

def main():
    symbols = get_all_symbols()
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
        
        candles = fetch_intraday_ohlc(symbol, from_date, to_date)
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