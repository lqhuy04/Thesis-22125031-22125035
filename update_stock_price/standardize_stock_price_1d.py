import os
import time
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

SYMBOL        = "VNM"
TABLE         = "Stock_Price_1d"
KEEP_DAYS     = 365 * 5     # Giữ lại 5 năm dữ liệu daily
CHUNK_DAYS    = 30
SLEEP_SECONDS = 1.1

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

def fetch_daily_ohlc(from_date: str, to_date: str) -> list[dict]:
    req  = model.daily_ohlc(SYMBOL, from_date, to_date, 1, 100, "HOSE")
    data = client.daily_ohlc(config, req)

    if isinstance(data, dict):
        rows = data.get("data") or data.get("dataList") or []
    elif isinstance(data, list):
        rows = data
    else:
        logger.error(f"Unexpected response type: {type(data)}")
        return []

    if rows:
        logger.info(f"[DEBUG] First raw row: {rows[0]}")

    result = []
    for r in rows:
        trading_date = (
            r.get("TradingDate") or r.get("tradingdate") or
            r.get("Tradingdate") or ""
        )
        if not trading_date:
            continue

        parts = trading_date.split("/")
        if len(parts) == 3:
            dd, mm, yyyy = parts
            iso_date = f"{yyyy}-{mm}-{dd}"
        else:
            logger.warning(f"Cannot parse date: {trading_date!r}, skipping")
            continue

        def _float(key_variants: list[str]) -> float:
            for k in key_variants:
                v = r.get(k)
                if v is not None and v != "":
                    try:
                        return float(v)
                    except (ValueError, TypeError):
                        pass
            return 0.0

        result.append({
            "symbol":       SYMBOL,
            "trading_time": f"{iso_date}T14:45:00",
            "open":         _float(["Open"])   / 1000,
            "high":         _float(["High"])   / 1000,
            "low":          _float(["Low"])    / 1000,
            "close":        _float(["Close"])  / 1000,
            "volume":       _float(["Volume"]),
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

    # Daily chỉ cần fetch ngày hôm nay (1 chunk, không cần loop)
    candles = fetch_daily_ohlc(today_str, today_str)
    logger.info(f"[{SYMBOL}] Fetched {len(candles)} candles")

    upsert_candles(candles)
    logger.info(f"[{SYMBOL}] Upserted {len(candles)} candles")

    delete_old_candles(cutoff_iso)

    logger.info("=== Done ===")

if __name__ == "__main__":
    main()