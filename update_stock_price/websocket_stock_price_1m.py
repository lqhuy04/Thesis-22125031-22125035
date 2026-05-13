from ssi_fc_data.fc_md_stream import MarketDataStream
from ssi_fc_data.fc_md_client import MarketDataClient
import re
import os
import json
import logging
import threading
import time
from datetime import datetime, timezone
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
batch_flush_buffer: dict[tuple[str, str], dict] = {}  # Buffer for batch inserts
BATCH_SIZE = 200  # Flush every 200 candles or when time changes
FLUSH_INTERVAL_SECS = 5  # Periodic flush every 5 seconds
periodic_flush_stop = threading.Event()  # Signal to stop periodic flush

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
        add_to_batch_flush(candle_buffer.pop(k))

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

def add_to_batch_flush(candle: dict) -> None:
    """Add candle to batch buffer and flush if threshold reached."""
    batch_key = (candle["symbol"], candle["trading_time"])
    batch_flush_buffer[batch_key] = candle
    if len(batch_flush_buffer) >= BATCH_SIZE:
        flush_batch()

def flush_batch() -> None:
    """Batch upsert multiple candles vào DB."""
    if not batch_flush_buffer:
        return
    
    try:
        batch_size = len(batch_flush_buffer)
        payload = list(batch_flush_buffer.values())
        supabase.table(TABLE).upsert(payload, on_conflict="symbol,trading_time").execute()
        
        # Log batch info
        symbols = set(c["symbol"] for c in payload)
        logger.info(f"[BATCH FLUSH] {batch_size} candles, symbols: {symbols}")
        
        batch_flush_buffer.clear()
    except Exception as e:
        logger.error(f"Supabase batch upsert error: {e} | batch_size: {len(batch_flush_buffer)}")

def flush_candle(candle: dict) -> None:
    """(Deprecated) Upsert 1 candle hoàn chỉnh vào DB - now uses batch."""
    add_to_batch_flush(candle)

def flush_active_candles() -> None:
    """Upsert all active in-memory candles so the DB tracks the latest minute in near real time."""
    if not candle_buffer:
        return

    # Copy the current snapshot so we can upsert it without mutating the buffer.
    for candle in list(candle_buffer.values()):
        add_to_batch_flush(candle.copy())

def periodic_flush_thread() -> None:
    """Periodically flush batch buffer every FLUSH_INTERVAL_SECS seconds."""
    while not periodic_flush_stop.is_set():
        time.sleep(FLUSH_INTERVAL_SECS)
        flush_active_candles()
        if batch_flush_buffer:
            logger.info(f"[PERIODIC FLUSH] Flushing {len(batch_flush_buffer)} active candles...")
            flush_batch()

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
            "open":         float(bar.get("Open")   or 0) / 1000,
            "high":         float(bar.get("High")   or 0) / 1000,
            "low":          float(bar.get("Low")    or 0) / 1000,
            "close":        float(bar.get("Close")  or 0) / 1000,
            "volume":       float(bar.get("Volume") or 0),
        }
    except Exception as e:
        logger.warning(f"Parse error: {e}")

# ═════════════════════════════════════════════════════════════════════════════
# HANDLERS
# ═════════════════════════════════════════════════════════════════════════════

def get_market_data(message) -> None:
    tick = parse_tick(message)
    if tick is None:
        return
    
    # Log individual tick for debugging
    logger.debug(f"[TICK] {tick['symbol']} at {tick['trading_time']} close={tick['close']}")
    update_buffer(tick)

def get_error(error) -> None:
    logger.error(f"Stream error: {error}")

# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

def main():
    logger.info("Starting SSI WebSocket stream...")
    
    # Start periodic flush thread
    periodic_flush_stop.clear()
    flush_thread = threading.Thread(target=periodic_flush_thread, daemon=True)
    flush_thread.start()
    logger.info(f"Periodic flush thread started (flush every {FLUSH_INTERVAL_SECS}s)")

    mm = MarketDataStream(config, MarketDataClient(config))
    mm.start(get_market_data, get_error, "B:ALL")

    logger.info("Stream started. Press Ctrl+C to stop.")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        # Signal periodic flush to stop
        periodic_flush_stop.set()
        
        # Flush toàn bộ candle còn trong buffer trước khi tắt
        logger.info(f"Shutting down... Flushing {len(candle_buffer)} remaining candles from candle_buffer...")
        for candle in candle_buffer.values():
            add_to_batch_flush(candle)
        
        # Flush remaining batch
        if batch_flush_buffer:
            logger.info(f"Flushing final batch with {len(batch_flush_buffer)} candles...")
            flush_batch()
        
        logger.info("Stopped.")

if __name__ == "__main__":
    main()