import os
import logging
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

SYMBOL    = "VNM"
TABLE     = "Stock_Price_1m"
KEEP_DAYS = 30

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

supabase = create_client(
    os.getenv("SUPABASE_URL", ""),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
)

# ═════════════════════════════════════════════════════════════════════════════
# SSI DATA
# ═════════════════════════════════════════════════════════════════════════════

def fetch_intraday_ohlc(from_date: str, to_date: str) -> list[dict]:
    req  = model.intraday_ohlc(SYMBOL, from_date, to_date, 1, 9999, "true", 1)
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
            "symbol":       SYMBOL,
            "trading_time": trading_time,
            "open":         float(r.get("Open")   or 0) / 1000,
            "high":         float(r.get("High")   or 0) / 1000,
            "low":          float(r.get("Low")    or 0) / 1000,
            "close":        float(r.get("Close")  or 0) / 1000,
            "volume":       float(r.get("Volume") or 0),
        })

    return result

# ═════════════════════════════════════════════════════════════════════════════
# SUPABASE
# ═════════════════════════════════════════════════════════════════════════════

def upsert_candles(candles: list[dict]) -> None:
    if not candles:
        return
    supabase.table(TABLE).upsert(candles, on_conflict="symbol,trading_time").execute()

def delete_old_candles(cutoff_iso: str) -> None:
    supabase.table(TABLE) \
        .delete() \
        .eq("symbol", SYMBOL) \
        .lt("trading_time", cutoff_iso) \
        .execute()
    logger.info(f"[{SYMBOL}] Deleted candles older than {cutoff_iso}")

# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

def main():
    today      = date.today()
    today_str  = today.strftime("%d/%m/%Y")
    cutoff_iso = (today - timedelta(days=KEEP_DAYS)).isoformat()

    logger.info(f"=== End-of-day sync [{SYMBOL}]: {today_str} ===")

    candles = fetch_intraday_ohlc(today_str, today_str)
    logger.info(f"[{SYMBOL}] Fetched {len(candles)} candles")

    upsert_candles(candles)
    logger.info(f"[{SYMBOL}] Upserted {len(candles)} candles")

    delete_old_candles(cutoff_iso)

    logger.info("=== Done ===")

if __name__ == "__main__":
    main()