import os
import sys
import time
import logging
from datetime import date, timedelta
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

def fetch_daily_ohlc(symbol: str, from_date: str, to_date: str) -> list[dict]:
    """
    Gọi client.daily_ohlc và chuẩn hoá kết quả về dict phù hợp với bảng DB.
    Giá SSI trả về theo đơn vị VNĐ → chia 1000 cho cổ phiếu HOSE (đơn vị nghìn đồng);
    các chỉ số (indices) giữ nguyên giá trị.
    """
    req  = model.daily_ohlc(symbol, from_date, to_date, 1, 100, "HOSE")
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

        # Indices remain the same, divide by 1000 for HOSE stocks
        multiplier = 1/1000

        result.append({
            "symbol":       symbol,
            "trading_time": f"{iso_date}T14:45:00",
            "open":         _float(["Open"])   * multiplier,
            "high":         _float(["High"])   * multiplier,
            "low":          _float(["Low"])    * multiplier,
            "close":        _float(["Close"])  * multiplier,
            "volume":       _float(["Volume"]),
        })

    return result

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


def resolve_symbols(cli_symbols: list[str] | None = None) -> list[str]:
    if cli_symbols:
        return [symbol.strip().upper() for symbol in cli_symbols if symbol.strip()]
    return sorted(get_vnindex_symbols(supabase))

# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

def main(symbols: list[str] | None = None):
    symbols = resolve_symbols(symbols)
    logger.info(f"Init daily OHLC for {len(symbols)} symbols: {symbols}")

    today      = date.today()
    start_date = today - timedelta(days=365 * YEARS_BACK)
    chunks     = list(generate_chunks(start_date, today, CHUNK_DAYS))
    total_chunks = len(chunks)

    logger.info(
        f"Date range: {start_date} → {today} "
        f"({total_chunks} chunks × {CHUNK_DAYS}d, delay={SLEEP_SECONDS}s)"
    )

    total_symbols = len(symbols)
    total_upserted = 0

    for sym_idx, symbol in enumerate(symbols, start=1):
        logger.info(f"[{sym_idx}/{total_symbols}] Processing {symbol}...")
        symbol_candles = []

        for chunk_idx, (from_date, to_date) in enumerate(chunks, start=1):
            logger.info(f"  [{symbol}] Chunk {chunk_idx}/{total_chunks}: {from_date} → {to_date}")

            try:
                candles = fetch_daily_ohlc(symbol, from_date, to_date)
                logger.info(f"  [{symbol}]   Fetched {len(candles)} candles")
                symbol_candles.extend(candles)

            except Exception as exc:
                logger.error(f"  [{symbol}]   Error on chunk {from_date}→{to_date}: {exc}")

            # Delay giữa các lần gọi SSI, bỏ qua lần cuối
            if chunk_idx < total_chunks or sym_idx < total_symbols:
                time.sleep(SLEEP_SECONDS)

        # Upsert candles for this symbol immediately
        upsert_candles(symbol_candles)
        total_upserted += len(symbol_candles)
        logger.info(f"[{sym_idx}/{total_symbols}] {symbol} done. Upserted {len(symbol_candles)} candles.")

    logger.info(f"All done. Total upserted: {total_upserted} candles.")

if __name__ == "__main__":
    main(sys.argv[1:])