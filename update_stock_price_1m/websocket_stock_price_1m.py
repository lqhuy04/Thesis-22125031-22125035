from ssi_fc_data.fc_md_stream import MarketDataStream
from ssi_fc_data.fc_md_client import MarketDataClient
import re
import os
import json
import logging
from typing import Optional
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

TABLE        = "Stock_Price_1m"
SYMBOL_REGEX = re.compile(r'^[A-Z0-9]{3}$')

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
# IN-MEMORY CANDLE BUFFER
# key: (symbol, "YYYY-MM-DDTHH:MM:00")
# value: candle dict đang được aggregate
# ═════════════════════════════════════════════════════════════════════════════

candle_buffer: dict[tuple, dict] = {}

def get_minute_key(trading_time: str) -> str:
    """'2026-04-22T10:20:13' → '2026-04-22T10:20:00'"""
    return trading_time[:16] + ":00"

def update_buffer(tick: dict) -> None:
    """Cập nhật candle trong buffer với tick mới."""
    symbol       = tick["symbol"]
    minute_key   = get_minute_key(tick["trading_time"])
    key          = (symbol, minute_key)
    current_minute = minute_key[:16]  # "2026-04-22T10:20"

    # Flush các candle của symbol này nếu đã sang phút mới
    keys_to_flush = [
        k for k in candle_buffer
        if k[0] == symbol and k[1][:16] < current_minute
    ]
    for k in keys_to_flush:
        flush_candle(candle_buffer.pop(k))

    # Aggregate vào buffer
    if key not in candle_buffer:
        candle_buffer[key] = {
            "symbol":       symbol,
            "trading_time": minute_key,
            "open":         tick["open"],
            "high":         tick["high"],
            "low":          tick["low"],
            "close":        tick["close"],
            "volume":       tick["volume"],
        }
    else:
        candle = candle_buffer[key]
        candle["high"]   = max(candle["high"], tick["high"])
        candle["low"]    = min(candle["low"],  tick["low"])
        candle["close"]  = tick["close"]           # close = giá tick mới nhất
        candle["volume"] += tick["volume"]          # volume cộng dồn

def flush_candle(candle: dict) -> None:
    """Upsert 1 candle hoàn chỉnh vào DB."""
    try:
        supabase.table(TABLE).upsert(candle, on_conflict="symbol,trading_time").execute()
        logger.info(f"[{candle['symbol']}] {candle['trading_time']} close={candle['close']} vol={candle['volume']}")
    except Exception as e:
        logger.error(f"Supabase upsert error: {e} | candle: {candle}")

# ═════════════════════════════════════════════════════════════════════════════
# PARSE
# ═════════════════════════════════════════════════════════════════════════════

def parse_tick(message) -> Optional[dict]:
    try:
        msg = json.loads(message) if isinstance(message, str) else message

        if msg.get("DataType") != "B" and msg.get("datatype") != "B":
            return None

        content = msg.get("Content") or msg.get("content")
        bar     = json.loads(content) if isinstance(content, str) else content

        symbol = str(bar.get("Symbol") or "").strip().upper()
        if not SYMBOL_REGEX.match(symbol):
            return None

        trading_time_str = bar.get("Time")        or bar.get("time")        or ""
        trading_date_str = bar.get("TradingDate") or bar.get("tradingdate") or ""
        if not trading_time_str or not trading_date_str:
            return None

        dd, mm, yyyy = trading_date_str.split("/")
        trading_time = f"{yyyy}-{mm}-{dd}T{trading_time_str}"

        return {
            "symbol":       symbol,
            "trading_time": trading_time,
            "open":         float(bar.get("Open")   or 0),
            "high":         float(bar.get("High")   or 0),
            "low":          float(bar.get("Low")    or 0),
            "close":        float(bar.get("Close")  or 0),
            "volume":       float(bar.get("Volume") or 0),
        }
    except Exception as e:
        logger.warning(f"Parse error: {e}")
        return None

# ═════════════════════════════════════════════════════════════════════════════
# HANDLERS
# ═════════════════════════════════════════════════════════════════════════════

def get_market_data(message) -> None:
    tick = parse_tick(message)
    if tick is None:
        return
    update_buffer(tick)

def get_error(error) -> None:
    logger.error(f"Stream error: {error}")

# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

def main():
    logger.info("Starting SSI WebSocket stream...")

    mm = MarketDataStream(config, MarketDataClient(config))
    mm.start(get_market_data, get_error, "B:VNM")

    logger.info("Stream started. Press Ctrl+C to stop.")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        # Flush toàn bộ candle còn trong buffer trước khi tắt
        logger.info(f"Flushing {len(candle_buffer)} remaining candles...")
        for candle in candle_buffer.values():
            flush_candle(candle)
        logger.info("Stopped.")

if __name__ == "__main__":
    main()