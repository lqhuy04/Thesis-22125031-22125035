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

SYMBOL        = "VNINDEX"
TABLE         = "Stock_Price_1d"
CHUNK_DAYS    = 30          # SSI giới hạn tối đa 30 ngày mỗi request
SLEEP_SECONDS = 1.1         # Delay giữa các request để tránh rate-limit SSI
YEARS_BACK    = 5           # Số năm lấy dữ liệu lịch sử

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
# DATE RANGE GENERATOR
# ═════════════════════════════════════════════════════════════════════════════

def generate_chunks(start: date, end: date, chunk_days: int):
    """Yield (from_date, to_date) tuples in DD/MM/YYYY, each <= chunk_days apart."""
    cursor = start
    while cursor <= end:
        chunk_end = min(cursor + timedelta(days=chunk_days - 1), end)
        yield cursor.strftime("%d/%m/%Y"), chunk_end.strftime("%d/%m/%Y")
        cursor = chunk_end + timedelta(days=1)

# ═════════════════════════════════════════════════════════════════════════════
# SSI DATA
# ═════════════════════════════════════════════════════════════════════════════

def fetch_daily_ohlc(from_date: str, to_date: str) -> list[dict]:
    """
    Gọi client.daily_ohlc và chuẩn hoá kết quả về dict phù hợp với bảng DB.
    Giá trả về từ SSI là VNĐ (integer), không cần chia 1000.
    """
    req  = model.daily_ohlc(SYMBOL, from_date, to_date, 1, 100, "HOSE")
    data = client.daily_ohlc(config, req)

    if isinstance(data, dict):
        rows = data.get("data") or data.get("dataList") or []
    elif isinstance(data, list):
        rows = data
    else:
        logger.error(f"Unexpected response type: {type(data)}")
        return []

    # DEBUG: in raw row đầu tiên để kiểm tra field names thực tế
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

        # Chuẩn hoá ngày DD/MM/YYYY → YYYY-MM-DD
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

# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

def main():
    today      = date.today()
    start_date = today.replace(year=today.year - YEARS_BACK)

    chunks     = list(generate_chunks(start_date, today, CHUNK_DAYS))
    total      = len(chunks)

    logger.info(
        f"[{SYMBOL}] Init daily OHLC: {start_date} → {today} "
        f"({total} chunks × {CHUNK_DAYS}d, delay={SLEEP_SECONDS}s)"
    )

    all_candles = []

    for idx, (from_date, to_date) in enumerate(chunks, start=1):
        logger.info(f"[{SYMBOL}] Chunk {idx}/{total}: {from_date} → {to_date}")

        try:
            candles = fetch_daily_ohlc(from_date, to_date)
            logger.info(f"[{SYMBOL}]   Fetched {len(candles)} candles")
            all_candles.extend(candles)

        except Exception as exc:
            logger.error(f"[{SYMBOL}]   Error on chunk {from_date}→{to_date}: {exc}")

        # Delay giữa các lần gọi SSI, bỏ qua lần cuối
        if idx < total:
            time.sleep(SLEEP_SECONDS)

    logger.info(f"[{SYMBOL}] Fetch done. Total candles: {len(all_candles)}. Upserting...")
    upsert_candles(all_candles)
    logger.info(f"[{SYMBOL}] Done. Upserted {len(all_candles)} daily candles.")

if __name__ == "__main__":
    main()