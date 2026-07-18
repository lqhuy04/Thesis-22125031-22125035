from ssi_fc_data.fc_md_stream import MarketDataStream
from ssi_fc_data.fc_md_client import MarketDataClient
import re
import os
import json
import logging
import sys
import threading
from typing import Optional
from datetime import datetime, timedelta, timezone
import time
from dotenv import load_dotenv
from supabase import create_client

from stock_price_validation import normalize_ohlcv
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

VN_TZ = timezone(timedelta(hours=7))

TABLE        = "Stock_Price_1m"
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

    # SSI may send either a full timestamp or just a time-of-day field.
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
        # Live bars sometimes omit the date, so fall back to the current trading day.
        today = datetime.now(VN_TZ).date()
        yyyy = today.strftime("%Y")
        mm = today.strftime("%m")
        dd = today.strftime("%d")

    return f"{yyyy}-{mm}-{dd}T{raw_timestamp[:8]}"

def get_target_symbols() -> set[str]:
    """Toàn bộ mã cổ phiếu thuộc VNINDEX (từ DB) ∪ các chỉ số cần giữ. Lỗi DB → chỉ còn các chỉ số."""
    vnindex_stocks = get_vnindex_symbols(supabase)
    return vnindex_stocks | ALLOWED_INDICES

# ═════════════════════════════════════════════════════════════════════════════
# IN-MEMORY CANDLE BUFFER
# key: (symbol, "YYYY-MM-DDTHH:MM:00")
# value: candle dict đang được aggregate
# ═════════════════════════════════════════════════════════════════════════════

candle_buffer: dict[tuple, dict] = {}
candle_buffer_lock = threading.Lock()
allowed_symbols: set[str] = set()

def get_minute_key(trading_time: str) -> str:
    """'2026-04-22T10:20:13' → '2026-04-22T10:20:00'"""
    return trading_time[:16] + ":00"

def flush_stale_candles(current_minute: str) -> None:
    """Flush every candle whose minute is older than the current minute.

    Có thể được gọi đồng thời từ luồng callback SSI (qua update_buffer) và
    luồng main loop, nên phần đọc/pop candle_buffer phải nằm trong lock để
    tránh 2 luồng cùng pop một key (KeyError) hoặc làm mất candle.
    """
    with candle_buffer_lock:
        stale_keys = [
            key for key in candle_buffer
            if key[1][:16] < current_minute
        ]
        payload = [candle_buffer.pop(key) for key in stale_keys]

    if not payload:
        return

    try:
        supabase.table(TABLE).upsert(payload, on_conflict="symbol,trading_time").execute()
    except Exception as e:
        logger.error(f"Supabase minute flush error: {e} | batch_size: {len(payload)}")

def update_buffer(tick: dict) -> None:
    """Cập nhật candle trong buffer với tick mới.

    Không gọi flush_stale_candles() ở đây: hàm này chạy trên luồng callback
    nhận tick từ SSI, nếu upsert Supabase (network I/O) chặn luôn ở đây thì
    khi rổ mã mở rộng (vd VNINDEX ~400 mã, payload flush lớn hơn) luồng nhận
    tick sẽ bị block theo, dễ tụt hậu/rớt tick trong phiên cao điểm. Việc
    flush candle của phút đã đóng do main loop (luồng riêng) đảm nhiệm mỗi giây.
    """
    symbol       = tick["symbol"]
    minute_key   = get_minute_key(tick["trading_time"])
    key          = (symbol, minute_key)

    with candle_buffer_lock:
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
    """Backward-compatible helper that flushes immediately."""
    supabase.table(TABLE).upsert([candle], on_conflict="symbol,trading_time").execute()

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
        if not (SYMBOL_REGEX.match(symbol) or symbol in ALLOWED_INDICES):
            return None
        if allowed_symbols and symbol not in allowed_symbols:
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
            price_multiplier=1 if symbol in ALLOWED_INDICES else 1 / 1000,
            allow_zero_volume=symbol in ALLOWED_INDICES,
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
            "trading_time": trading_time,
            **ohlcv,
        }
    except Exception as e:
        logger.warning(f"Parse error: {e}")

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
    logger.info("Starting SSI WebSocket stream...")

    global allowed_symbols
    allowed_symbols = get_target_symbols()
    if not (allowed_symbols - ALLOWED_INDICES):
        logger.warning("No VNINDEX symbols loaded from DB; stream will accept indices only until next refresh.")
    else:
        logger.info(f"Loaded {len(allowed_symbols)} target symbols (VNINDEX + indices) for websocket filtering.")

    try:
        mm = MarketDataStream(config, MarketDataClient(config))
        mm.start(get_market_data, get_error, "B:ALL")
    except Exception as e:
        logger.error(f"❌ Failed to start MarketDataStream: {e}", exc_info=True)
        return

    logger.info("Stream started. Press Ctrl+C to stop.")
    try:
        # Run a light loop: flush closed minutes periodically
        last_minute = None
        while True:
            try:
                now = datetime.now(VN_TZ)
                current_minute = now.replace(second=0, microsecond=0).isoformat()[:16]

                # Flush closed minutes once per minute (even if no incoming ticks)
                if current_minute != last_minute:
                    try:
                        flush_stale_candles(current_minute)
                    except Exception as e:
                        logger.error(f"❌ Error in flush_stale_candles: {e}", exc_info=True)
                    last_minute = current_minute

                time.sleep(1)
            except Exception as e:
                logger.error(f"❌ Error in main loop: {e}", exc_info=True)
                time.sleep(5)  # Wait before retrying
    except KeyboardInterrupt:
        if candle_buffer:
            # Only flush completed minutes (do not write the current open minute)
            now = datetime.now(VN_TZ).replace(second=0, microsecond=0).isoformat()[:16]
            with candle_buffer_lock:
                completed = [c for k, c in candle_buffer.items() if k[1][:16] < now]
            if completed:
                try:
                    supabase.table(TABLE).upsert(completed, on_conflict="symbol,trading_time").execute()
                except Exception as e:
                    logger.error(f"Supabase shutdown flush error: {e} | batch_size: {len(completed)}")
        logger.info("Stopped.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"❌ Unhandled exception in main: {e}", exc_info=True)
        sys.exit(1)
