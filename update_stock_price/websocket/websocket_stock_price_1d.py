from ssi_fc_data.fc_md_stream import MarketDataStream
from ssi_fc_data.fc_md_client import MarketDataClient
import re
import os
import json
import logging
import sys
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Optional
from pathlib import Path

UPDATE_STOCK_PRICE_DIR = Path(__file__).resolve().parents[1]
if str(UPDATE_STOCK_PRICE_DIR) not in sys.path:
    sys.path.insert(0, str(UPDATE_STOCK_PRICE_DIR))

from dotenv import load_dotenv
from supabase import create_client

from utils.stock_price_validation import normalize_ohlcv
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

VN_TZ = timezone(timedelta(hours=7))

TABLE        = "Stock_Price_1d"
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

stock_ids_by_symbol: dict[str, str] = {}


def get_target_stocks() -> dict[str, str]:
    """Return the VN100 stock_symbol -> Stock.id mapping."""
    return get_vn100_stock_ids(supabase)


def _get_field(payload: dict, *keys: str, default=None):
    for key in keys:
        if key in payload and payload[key] not in (None, ""):
            return payload[key]
    return default


def _normalize_timestamp(bar: dict) -> str | None:
    raw_timestamp = str(
        _get_field(bar, "TradingTime", "Time", "trading_time", "time", default="")
    ).strip()
    if not raw_timestamp:
        return None

    if "T" in raw_timestamp or (" " in raw_timestamp and len(raw_timestamp) >= 19):
        normalized = raw_timestamp.replace(" ", "T")
        return normalized[:19]

    raw_date = str(
        _get_field(bar, "TradingDate", "tradingdate", "Date", "date", default="")
    ).strip()
    if raw_date:
        if "/" in raw_date:
            parts = raw_date.split("/")
            if len(parts) != 3:
                return None
            dd, mm, yyyy = parts
        elif "-" in raw_date:
            parts = raw_date.split("-")
            if len(parts) != 3:
                return None
            yyyy, mm, dd = parts
        else:
            return None
    else:
        today = datetime.now(VN_TZ).date()
        yyyy = today.strftime("%Y")
        mm = today.strftime("%m")
        dd = today.strftime("%d")

    return f"{yyyy}-{mm}-{dd}T{raw_timestamp[:8]}"

# ═════════════════════════════════════════════════════════════════════════════
# IN-MEMORY CANDLE BUFFER
# key: symbol
# value: candle dict của ngày hiện tại đang được aggregate
# trading_time cố định là "YYYY-MM-DDT14:45:00" (khớp với init_stock_price_1d)
# ═════════════════════════════════════════════════════════════════════════════

candle_buffer: dict[str, dict] = {}
batch_flush_buffer: dict[tuple[str, str], dict] = {}
FLUSH_INTERVAL_SECS = 5
periodic_flush_stop = threading.Event()
# Bảo vệ candle_buffer/batch_flush_buffer vì cả luồng callback SSI và
# periodic_flush_thread đều đọc/ghi 2 dict này đồng thời.
buffer_lock = threading.Lock()

def get_day_key(trading_date: str) -> str:
    """'2026-04-22' → '2026-04-22T14:45:00'"""
    return f"{trading_date}T14:45:00"

def update_buffer(tick: dict) -> None:
    """Cập nhật candle ngày trong buffer với tick mới, rồi flush ngay."""
    symbol       = tick["symbol"]
    stock_id     = tick["stock_id"]
    trading_date = tick["trading_time"][:10]   # "YYYY-MM-DD"
    day_key      = get_day_key(trading_date)

    with buffer_lock:
        if symbol not in candle_buffer:
            # Candle đầu tiên trong ngày
            candle_buffer[symbol] = {
                "stock_id":     stock_id,
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
                    "stock_id":     stock_id,
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

        snapshot = candle_buffer[symbol].copy()

    # Queue for batch flush so active candles are written periodically
    add_to_batch_flush(snapshot)

def add_to_batch_flush(candle: dict) -> None:
    """Add a candle to the batch buffer.

    Không tự flush ở đây: hàm này được gọi từ update_buffer trên luồng
    callback nhận tick SSI, nên chỉ làm thao tác dict (nhanh, không I/O).
    periodic_flush_thread (luồng riêng, mỗi FLUSH_INTERVAL_SECS giây) là nơi
    duy nhất gọi Supabase, để luồng nhận tick không bao giờ bị block bởi
    network I/O — quan trọng khi rổ mã mở rộng (vd VN100 ~100 mã).
    """
    batch_key = (candle["stock_id"], candle["trading_time"])
    with buffer_lock:
        batch_flush_buffer[batch_key] = candle

def flush_batch() -> None:
    """Batch upsert multiple candles into the DB."""
    with buffer_lock:
        if not batch_flush_buffer:
            return
        payload = list(batch_flush_buffer.values())

    try:
        supabase.table(TABLE).upsert(
            payload,
            on_conflict="stock_id,trading_time",
        ).execute()
        # Chỉ xoá đúng những entry đã flush thành công; nếu trong lúc upsert
        # có bản cập nhật mới hơn cho cùng key thì giữ lại bản mới đó.
        with buffer_lock:
            for candle in payload:
                batch_key = (candle["stock_id"], candle["trading_time"])
                if batch_flush_buffer.get(batch_key) is candle:
                    del batch_flush_buffer[batch_key]
    except Exception as e:
        logger.error(f"Supabase batch upsert error: {e} | batch_size: {len(payload)}")

def flush_candle(candle: dict) -> None:
    """Backward-compatible wrapper that now queues for batch flush."""
    add_to_batch_flush(candle)

def flush_active_candles() -> None:
    """Upsert the current in-memory snapshot so the DB stays near real time."""
    with buffer_lock:
        candles = list(candle_buffer.values())

    for candle in candles:
        add_to_batch_flush(candle.copy())

def periodic_flush_thread() -> None:
    """Periodically flush active candles every FLUSH_INTERVAL_SECS seconds."""
    try:
        while not periodic_flush_stop.is_set():
            time.sleep(FLUSH_INTERVAL_SECS)
            flush_active_candles()
            flush_batch()
    except Exception as e:
        logger.error(f"❌ Error in periodic_flush_thread: {e}", exc_info=True)

# ═════════════════════════════════════════════════════════════════════════════
# PARSE
# ═════════════════════════════════════════════════════════════════════════════

def parse_tick(message) -> Optional[dict]:
    try:
        msg = json.loads(message) if isinstance(message, str) else message

        data_type = str(msg.get("DataType") or msg.get("datatype") or "").upper()
        if data_type != "B":
            return None

        content = msg.get("Content") or msg.get("content")
        bar     = json.loads(content) if isinstance(content, str) else content
        if not isinstance(bar, dict):
            return None

        symbol = str(bar.get("Symbol") or "").strip().upper()
        if not SYMBOL_REGEX.match(symbol):
            return None
        stock_id = stock_ids_by_symbol.get(symbol)
        if stock_id is None:
            return None

        trading_time = _normalize_timestamp(bar)
        if not trading_time:
            return None

        ohlcv, rejection_reason = normalize_ohlcv(
            _get_field(bar, "Open", "open"),
            _get_field(bar, "High", "high"),
            _get_field(bar, "Low", "low"),
            _get_field(bar, "Close", "close"),
            _get_field(bar, "Volume", "volume"),
            price_multiplier=1 / 1000,
            allow_zero_volume=False,
        )
        if ohlcv is None:
            logger.debug(
                "[%s] Dropping invalid realtime OHLCV at %s: %s",
                symbol,
                trading_time,
                rejection_reason,
            )
            return None

        return {
            "symbol":       symbol,
            "stock_id":     stock_id,
            "trading_time": trading_time,
            **ohlcv,
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

    global stock_ids_by_symbol
    stock_ids_by_symbol = get_target_stocks()
    if not stock_ids_by_symbol:
        logger.warning("No VN100 stock symbols loaded from DB; all incoming symbols will be rejected.")
    else:
        logger.info(
            f"Loaded {len(stock_ids_by_symbol)} VN100 stock ids for websocket filtering."
        )

    periodic_flush_stop.clear()
    flush_thread = threading.Thread(target=periodic_flush_thread, daemon=True)
    flush_thread.start()

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
            time.sleep(1)
    except KeyboardInterrupt:
        periodic_flush_stop.set()
        flush_active_candles()
        flush_batch()
        logger.info("Stopped.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"❌ Unhandled exception in main: {e}", exc_info=True)
        sys.exit(1)
