import os
import sys
import logging
import requests
import time
from datetime import date, datetime, timedelta
from pathlib import Path

UPDATE_STOCK_PRICE_DIR = Path(__file__).resolve().parents[1]
if str(UPDATE_STOCK_PRICE_DIR) not in sys.path:
    sys.path.insert(0, str(UPDATE_STOCK_PRICE_DIR))

from dotenv import load_dotenv
from supabase import create_client

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

TABLE         = "Stock_Price_1m"
SLEEP_SECONDS = 1.1
LOOKBACK_MONTHS = 3
DAYS_PER_MONTH = 30

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

def _aggregate_intraday_minutes(rows: list[dict]) -> list[dict]:
    """Aggregate raw SSI trade rows into 1m candles without synthetic gap fill."""
    if not rows:
        return []

    rows = sorted(rows, key=lambda row: row["trading_time"])
    stock_id = rows[0]["stock_id"]

    aggregated: dict[datetime, dict] = {}
    for row in rows:
        minute_dt = datetime.fromisoformat(row["trading_time"]).replace(second=0, microsecond=0)
        candle = aggregated.get(minute_dt)
        if candle is None:
            aggregated[minute_dt] = {
                "stock_id": stock_id,
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

def fetch_intraday_ohlc(
    symbol: str,
    stock_id: str,
    from_date: str,
    to_date: str,
    access_token: str,
) -> list[dict]:
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
                "stock_id":     stock_id,
                "trading_time": f"{yyyy}-{mm}-{dd}T{raw_time[:5]}:00",
                "open":         float(r.get("Open")   or 0) *  1/1000,
                "high":         float(r.get("High")   or 0) *  1/1000,
                "low":          float(r.get("Low")    or 0) *  1/1000,
                "close":        float(r.get("Close")  or 0) *  1/1000,
                "volume":       float(r.get("Volume") or 0),
            })

        return _aggregate_intraday_minutes(result)
    except Exception as e:
        logger.error(f"Failed to fetch intraday data for {symbol}: {e}")
        return []

def build_monthly_date_ranges(reference_date: date) -> list[tuple[str, str]]:
    """Build three consecutive 30-day SSI query windows, newest first."""
    date_ranges = []
    for month_offset in range(LOOKBACK_MONTHS):
        range_end = reference_date - timedelta(days=DAYS_PER_MONTH * month_offset)
        range_start = range_end - timedelta(days=DAYS_PER_MONTH)
        date_ranges.append((
            range_start.strftime("%d/%m/%Y"),
            range_end.strftime("%d/%m/%Y"),
        ))
    return date_ranges

# ═════════════════════════════════════════════════════════════════════════════
# SUPABASE
# ═════════════════════════════════════════════════════════════════════════════

def upsert_candles(candles: list[dict]) -> None:
    """Deduplicate and upsert candles to database."""
    if not candles:
        return
    
    try:
        deduped = {
            (candle["stock_id"], candle["trading_time"]): candle
            for candle in candles
        }
        supabase.table(TABLE).upsert(
            list(deduped.values()),
            on_conflict="stock_id,trading_time",
        ).execute()
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

    stocks = get_vn100_stock_ids(supabase)
    if not stocks:
        logger.error("No VN100 stocks with Stock.id found. Exiting.")
        return
    logger.info(
        f"Processing {len(stocks)} VN100 symbols: {sorted(stocks)[:5]}..."
    )

    date_ranges = build_monthly_date_ranges(date.today())
    logger.info(
        f"Date range: {date_ranges[-1][0]} → {date_ranges[0][1]} "
        f"({LOOKBACK_MONTHS} requests per symbol)"
    )
    
    total_candles_fetched = 0
    total_candles_upserted = 0
    
    for idx, (symbol, stock_id) in enumerate(sorted(stocks.items()), 1):
        logger.info(f"[{idx}/{len(stocks)}] Fetching 1m data for {symbol}...")

        for month_idx, (from_date, to_date) in enumerate(date_ranges, 1):
            logger.info(
                f"  [{month_idx}/{LOOKBACK_MONTHS}] Fetching {from_date} → {to_date}"
            )
            try:
                candles = fetch_intraday_ohlc(
                    symbol,
                    stock_id,
                    from_date,
                    to_date,
                    access_token,
                )
                if candles:
                    total_candles_fetched += len(candles)
                    upsert_candles(candles)
                    total_candles_upserted += len(candles)
                    logger.info(f"    → Upserted {len(candles)} candles")
                else:
                    logger.info("    → No data fetched")
            finally:
                time.sleep(SLEEP_SECONDS)
    
    logger.info(f"\n✅ Completed!")
    logger.info(f"Total candles fetched: {total_candles_fetched}")
    logger.info(f"Total candles upserted: {total_candles_upserted}")
    
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        input("Press Enter to exit...")  # giữ cửa sổ lại để đọc lỗi
