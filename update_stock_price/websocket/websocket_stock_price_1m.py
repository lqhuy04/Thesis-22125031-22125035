from ssi_fc_data.fc_md_stream import MarketDataStream
from ssi_fc_data.fc_md_client import MarketDataClient
import contextlib
import io
import re
import os
import json
import logging
import sys
import threading
from typing import Optional
from datetime import datetime, timedelta, timezone
import time
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

TABLE        = "Stock_Price_1m"
SYMBOL_REGEX = re.compile(r'^[A-Z0-9]{3}$')

RECONNECT_INITIAL_SECONDS = 5
RECONNECT_MAX_SECONDS = 60
STREAM_STALE_SECONDS = 120

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

def get_target_stocks() -> dict[str, str]:
    """Return the VN100 stock_symbol -> Stock.id mapping."""
    return get_vn100_stock_ids(supabase)


def build_subscription_channel(stocks: dict[str, str]) -> str:
    """Build an SSI OHLCV channel containing only VN100 stock symbols."""
    symbols = sorted(
        symbol
        for symbol in stocks
        if SYMBOL_REGEX.fullmatch(symbol)
    )
    if not symbols:
        raise ValueError("Cannot subscribe: VN100 stock symbol list is empty")

    skipped = sorted(set(stocks) - set(symbols))
    if skipped:
        logger.warning("Skipped invalid SSI symbols from subscription: %s", skipped)

    return "B:" + "-".join(symbols)


def is_market_session(now: datetime) -> bool:
    """Return True while the VN100 cash market should be producing ticks."""
    if now.weekday() > 4:
        return False

    current = (now.hour, now.minute)
    morning_session = (9, 0) <= current < (11, 30)
    afternoon_session = (13, 0) <= current < (15, 0)
    return morning_session or afternoon_session


def close_stream(stream: MarketDataStream | None) -> None:
    """Best-effort shutdown for the transport bundled in ssi-fc-data."""
    if stream is None:
        return

    connection = getattr(stream, "connection", None)
    # ssi-fc-data 2.2.2 exposes no working public stop method: Connection.close()
    # calls a missing transport.close(). Use the transport's supported stop().
    transport = getattr(connection, "_Connection__transport", None)
    stop = getattr(transport, "stop", None)
    if callable(stop):
        try:
            stop()
        except Exception as e:
            logger.warning("Failed to close old SSI stream cleanly: %s", e)


def start_stream(
    channel: str,
) -> tuple[MarketDataStream, threading.Event, dict[str, float | bool]]:
    """Start one SSI stream attempt and expose its disconnect/heartbeat state."""
    disconnected = threading.Event()
    heartbeat: dict[str, float | bool] = {
        "last_message_at": time.monotonic(),
        "received_message": False,
    }

    def on_message(message) -> None:
        heartbeat["last_message_at"] = time.monotonic()
        heartbeat["received_message"] = True
        get_market_data(message)

    def on_error(error) -> None:
        get_error(error)
        disconnected.set()

    def on_close() -> None:
        logger.warning("SSI stream connection closed")
        disconnected.set()

    stream = MarketDataStream(
        config,
        MarketDataClient(config),
        on_close=on_close,
    )
    # ssi-fc-data 2.2.2 prints its request headers (including the Bearer token)
    # during negotiation. Suppress that SDK print so reconnects do not leak it.
    with contextlib.redirect_stdout(io.StringIO()):
        stream.start(on_message, on_error, channel)
    return stream, disconnected, heartbeat

# ═════════════════════════════════════════════════════════════════════════════
# IN-MEMORY CANDLE BUFFER
# key: (symbol, "YYYY-MM-DDTHH:MM:00")
# value: candle dict đang được aggregate
# ═════════════════════════════════════════════════════════════════════════════

candle_buffer: dict[tuple, dict] = {}
candle_buffer_lock = threading.Lock()
stock_ids_by_symbol: dict[str, str] = {}

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
        supabase.table(TABLE).upsert(
            payload,
            on_conflict="stock_id,trading_time",
        ).execute()
    except Exception as e:
        logger.error(f"Supabase minute flush error: {e} | batch_size: {len(payload)}")

def update_buffer(tick: dict) -> None:
    """Cập nhật candle trong buffer với tick mới.

    Không gọi flush_stale_candles() ở đây: hàm này chạy trên luồng callback
    nhận tick từ SSI, nếu upsert Supabase (network I/O) chặn luôn ở đây thì
    khi rổ mã mở rộng (vd VN100 ~100 mã, payload flush lớn hơn) luồng nhận
    tick sẽ bị block theo, dễ tụt hậu/rớt tick trong phiên cao điểm. Việc
    flush candle của phút đã đóng do main loop (luồng riêng) đảm nhiệm mỗi giây.
    """
    symbol       = tick["symbol"]
    stock_id     = tick["stock_id"]
    minute_key   = get_minute_key(tick["trading_time"])
    key          = (symbol, minute_key)

    with candle_buffer_lock:
        if key not in candle_buffer:
            candle_buffer[key] = {
                "stock_id":     stock_id,
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
    supabase.table(TABLE).upsert(
        [candle],
        on_conflict="stock_id,trading_time",
    ).execute()

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

    global stock_ids_by_symbol
    stock_ids_by_symbol = get_target_stocks()
    if not stock_ids_by_symbol:
        raise RuntimeError("No VN100 stocks loaded from DB; refusing to subscribe to B:ALL")

    reconnect_delay = RECONNECT_INITIAL_SECONDS
    shutdown = threading.Event()
    stream: MarketDataStream | None = None

    try:
        last_minute = None
        while not shutdown.is_set():
            try:
                refreshed_stocks = get_target_stocks()
                if refreshed_stocks:
                    stock_ids_by_symbol = refreshed_stocks
                else:
                    logger.warning(
                        "Failed to refresh VN100 stocks; reusing %d cached symbols",
                        len(stock_ids_by_symbol),
                    )

                channel = build_subscription_channel(stock_ids_by_symbol)
                logger.info(
                    "Connecting SSI stream for %d VN100 symbols (channel_length=%d)",
                    len(stock_ids_by_symbol),
                    len(channel),
                )
                stream, disconnected, heartbeat = start_stream(channel)

                active_session = False
                session_started_at = time.monotonic()
                connection_confirmed = False

                while not shutdown.is_set() and not disconnected.wait(1):
                    now = datetime.now(VN_TZ)
                    monotonic_now = time.monotonic()
                    current_minute = (
                        now.replace(second=0, microsecond=0).isoformat()[:16]
                    )

                    # Flush closed minutes once per minute (even if no ticks arrive).
                    if current_minute != last_minute:
                        try:
                            flush_stale_candles(current_minute)
                        except Exception as e:
                            logger.error(
                                "❌ Error in flush_stale_candles: %s",
                                e,
                                exc_info=True,
                            )
                        last_minute = current_minute

                    if heartbeat["received_message"] and not connection_confirmed:
                        logger.info("SSI stream is receiving VN100 data")
                        connection_confirmed = True
                        reconnect_delay = RECONNECT_INITIAL_SECONDS

                    session_now = is_market_session(now)
                    if session_now and not active_session:
                        # Give the feed a fresh grace period at 09:00 and 13:00;
                        # the lunch break legitimately contains no market ticks.
                        session_started_at = monotonic_now

                    if session_now:
                        last_message_at = float(heartbeat["last_message_at"])
                        watched_since = max(last_message_at, session_started_at)
                        if monotonic_now - watched_since >= STREAM_STALE_SECONDS:
                            logger.error(
                                "No SSI stream messages for %ds during market "
                                "session; forcing reconnect",
                                STREAM_STALE_SECONDS,
                            )
                            disconnected.set()
                            break

                    active_session = session_now
            except Exception as e:
                logger.error("❌ SSI stream attempt failed: %s", e, exc_info=True)
            finally:
                close_stream(stream)
                stream = None

            if shutdown.is_set():
                break

            logger.warning("Reconnecting SSI stream in %d seconds", reconnect_delay)
            if shutdown.wait(reconnect_delay):
                break
            reconnect_delay = min(
                reconnect_delay * 2,
                RECONNECT_MAX_SECONDS,
            )
    except KeyboardInterrupt:
        shutdown.set()
        close_stream(stream)
        if candle_buffer:
            # Only flush completed minutes (do not write the current open minute)
            now = datetime.now(VN_TZ).replace(second=0, microsecond=0).isoformat()[:16]
            with candle_buffer_lock:
                completed = [c for k, c in candle_buffer.items() if k[1][:16] < now]
            if completed:
                try:
                    supabase.table(TABLE).upsert(
                        completed,
                        on_conflict="stock_id,trading_time",
                    ).execute()
                except Exception as e:
                    logger.error(f"Supabase shutdown flush error: {e} | batch_size: {len(completed)}")
        logger.info("Stopped.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"❌ Unhandled exception in main: {e}", exc_info=True)
        sys.exit(1)
