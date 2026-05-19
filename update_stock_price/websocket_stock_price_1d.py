from ssi_fc_data.fc_md_stream import MarketDataStream
from ssi_fc_data.fc_md_client import MarketDataClient
import re
import os
import json
import logging
import sys
import threading
import time
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

TABLE        = "Stock_Price_1d"
SYMBOL_REGEX = re.compile(r'^[A-Z0-9]{3}$')
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
# IN-MEMORY CANDLE BUFFER
# key: symbol
# value: candle dict của ngày hiện tại đang được aggregate
# trading_time cố định là "YYYY-MM-DDT14:45:00" (khớp với init_stock_price_1d)
# ═════════════════════════════════════════════════════════════════════════════

candle_buffer: dict[str, dict] = {}
batch_flush_buffer: dict[tuple[str, str], dict] = {}
BATCH_SIZE = 200
FLUSH_INTERVAL_SECS = 5
periodic_flush_stop = threading.Event()

def get_day_key(trading_date: str) -> str:
    """'2026-04-22' → '2026-04-22T14:45:00'"""
    return f"{trading_date}T14:45:00"

def update_buffer(tick: dict) -> None:
    """Cập nhật candle ngày trong buffer với tick mới, rồi flush ngay."""
    symbol       = tick["symbol"]
    trading_date = tick["trading_time"][:10]   # "YYYY-MM-DD"
    day_key      = get_day_key(trading_date)

    if symbol not in candle_buffer:
        # Candle đầu tiên trong ngày
        candle_buffer[symbol] = {
            "symbol":       symbol,
            "trading_time": day_key,
            "open":         tick["open"],
            "high":         tick["high"],
            "low":          tick["low"],
            "close":        tick["close"],
            "volume":       tick["volume"],
        }
    else:
        candle = candle_buffer[symbol]

        # Nếu sang ngày mới (hiếm nhưng an toàn), reset candle
        if candle["trading_time"] != day_key:
            logger.info(f"[{symbol}] New day detected, resetting daily candle.")
            candle_buffer[symbol] = {
                "symbol":       symbol,
                "trading_time": day_key,
                "open":         tick["open"],
                "high":         tick["high"],
                "low":          tick["low"],
                "close":        tick["close"],
                "volume":       tick["volume"],
            }
        else:
            candle["high"]   = max(candle["high"], tick["high"])
            candle["low"]    = min(candle["low"],  tick["low"])
            candle["close"]  = tick["close"]    # close = giá tick mới nhất
            candle["volume"] += tick["volume"]  # volume cộng dồn

    # Queue for batch flush so active candles are written periodically
    add_to_batch_flush(candle_buffer[symbol].copy())

def add_to_batch_flush(candle: dict) -> None:
    """Add a candle to the batch buffer and flush when the buffer fills."""
    batch_key = (candle["symbol"], candle["trading_time"])
    batch_flush_buffer[batch_key] = candle
    if len(batch_flush_buffer) >= BATCH_SIZE:
        flush_batch()

def flush_batch() -> None:
    """Batch upsert multiple candles into the DB."""
    if not batch_flush_buffer:
        return

    try:
        batch_size = len(batch_flush_buffer)
        payload = list(batch_flush_buffer.values())
        supabase.table(TABLE).upsert(payload, on_conflict="symbol,trading_time").execute()
        symbols = set(c["symbol"] for c in payload)
        logger.info(f"[BATCH FLUSH] {batch_size} candles, symbols: {symbols}")
        batch_flush_buffer.clear()
    except Exception as e:
        logger.error(f"Supabase batch upsert error: {e} | batch_size: {len(batch_flush_buffer)}")

def flush_candle(candle: dict) -> None:
    """Backward-compatible wrapper that now queues for batch flush."""
    add_to_batch_flush(candle)

def flush_active_candles() -> None:
    """Upsert the current in-memory snapshot so the DB stays near real time."""
    if not candle_buffer:
        return

    for candle in list(candle_buffer.values()):
        add_to_batch_flush(candle.copy())

def periodic_flush_thread() -> None:
    """Periodically flush active candles every FLUSH_INTERVAL_SECS seconds."""
    try:
        while not periodic_flush_stop.is_set():
            time.sleep(FLUSH_INTERVAL_SECS)
            flush_active_candles()
            if batch_flush_buffer:
                logger.info(f"[PERIODIC FLUSH] Flushing {len(batch_flush_buffer)} active candles...")
                flush_batch()
    except Exception as e:
        logger.error(f"❌ Error in periodic_flush_thread: {e}", exc_info=True)

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
        if not (SYMBOL_REGEX.match(symbol) or symbol in ALLOWED_INDICES):
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
            "open":         float(bar.get("Open")   or 0) * (1 if symbol in ALLOWED_INDICES else 1/1000),
            "high":         float(bar.get("High")   or 0) * (1 if symbol in ALLOWED_INDICES else 1/1000),
            "low":          float(bar.get("Low")    or 0) * (1 if symbol in ALLOWED_INDICES else 1/1000),
            "close":        float(bar.get("Close")  or 0) * (1 if symbol in ALLOWED_INDICES else 1/1000),
            "volume":       float(bar.get("Volume") or 0),
        }
    except Exception as e:
        logger.warning(f"Parse error: {e}")
        return None

# ═════════════════════════════════════════════════════════════════════════════
# HANDLERS
# ═════════════════════════════════════════════════════════════════════════════

def get_market_data(message) -> None:
    try:
        tick = parse_tick(message)
        if tick is None:
            return
        update_buffer(tick)
    except Exception as e:
        logger.error(f"❌ Error processing market data: {e}", exc_info=True)

def get_error(error) -> None:
    logger.error(f"Stream error: {error}")

# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

def main():
    logger.info("Starting SSI WebSocket stream (daily candle)...")

    periodic_flush_stop.clear()
    flush_thread = threading.Thread(target=periodic_flush_thread, daemon=True)
    flush_thread.start()
    logger.info(f"Periodic flush thread started (flush every {FLUSH_INTERVAL_SECS}s)")

    try:
        mm = MarketDataStream(config, MarketDataClient(config))
        mm.start(get_market_data, get_error, "B:ALL")
    except Exception as e:
        logger.error(f"❌ Failed to start MarketDataStream: {e}", exc_info=True)
        periodic_flush_stop.set()
        return

    logger.info("Stream started. Press Ctrl+C to stop.")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        periodic_flush_stop.set()
        logger.info(f"Flushing {len(candle_buffer)} remaining candles...")
        for candle in candle_buffer.values():
            add_to_batch_flush(candle.copy())
        if batch_flush_buffer:
            logger.info(f"Flushing final batch with {len(batch_flush_buffer)} candles...")
            flush_batch()
        logger.info("Stopped.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"❌ Unhandled exception in main: {e}", exc_info=True)
        sys.exit(1)