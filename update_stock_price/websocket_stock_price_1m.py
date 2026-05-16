from ssi_fc_data.fc_md_stream import MarketDataStream
from ssi_fc_data.fc_md_client import MarketDataClient
import re
import os
import json
import logging
import requests
import sys
from typing import Optional
from datetime import datetime
import time
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

def get_ssi_access_token() -> str:
    """Get access token from SSI API using consumer credentials."""
    try:
        url = "https://fc-data.ssi.com.vn/api/v2/Market/AccessToken"
        payload = {
            "consumerID": config.consumerID,
            "consumerSecret": config.consumerSecret,
        }
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()

        data = response.json()
        access_token = data.get("data", {}).get("accessToken", "")
        if not access_token:
            raise ValueError("No access token in response")

        return access_token
    except Exception as e:
        logger.error(f"Failed to get SSI access token: {e}")
        return ""

def get_hose_symbols() -> set[str]:
    """Fetch HOSE symbols from SSI API and keep only symbols with 3 characters."""
    try:
        access_token = get_ssi_access_token()
        if not access_token:
            return set()

        url = "https://fc-data.ssi.com.vn/api/v2/Market/Securities?Market=HOSE&PageSize=1000"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()
        symbols = {
            str(item.get("Symbol") or "").strip().upper()
            for item in (data.get("data") or [])
            if str(item.get("Symbol") or "").strip().upper()
        }
        return {symbol for symbol in symbols if SYMBOL_REGEX.match(symbol)}
    except Exception as e:
        logger.error(f"Failed to fetch HOSE symbols from SSI API: {e}")
        return set()

# ═════════════════════════════════════════════════════════════════════════════
# IN-MEMORY CANDLE BUFFER
# key: (symbol, "YYYY-MM-DDTHH:MM:00")
# value: candle dict đang được aggregate
# ═════════════════════════════════════════════════════════════════════════════

candle_buffer: dict[tuple, dict] = {}
allowed_symbols: set[str] = set()

def get_minute_key(trading_time: str) -> str:
    """'2026-04-22T10:20:13' → '2026-04-22T10:20:00'"""
    return trading_time[:16] + ":00"

def flush_stale_candles(current_minute: str) -> None:
    """Flush every candle whose minute is older than the current minute."""
    stale_keys = [
        key for key in candle_buffer
        if key[1][:16] < current_minute
    ]

    if stale_keys:
        logger.info(
            f"[MINUTE ROLLOVER] Flushing {len(stale_keys)} stale candles before {current_minute}:00"
        )

    if not stale_keys:
        return

    payload = [candle_buffer.pop(key) for key in stale_keys]

    try:
        supabase.table(TABLE).upsert(payload, on_conflict="symbol,trading_time").execute()
        symbols = {c["symbol"] for c in payload}
        logger.info(
            f"[MINUTE FLUSH] {len(payload)} candles flushed for completed minute(s), symbols: {symbols}"
        )
    except Exception as e:
        logger.error(f"Supabase minute flush error: {e} | batch_size: {len(payload)}")

def update_buffer(tick: dict) -> None:
    """Cập nhật candle trong buffer với tick mới."""
    symbol       = tick["symbol"]
    minute_key   = get_minute_key(tick["trading_time"])
    key          = (symbol, minute_key)
    current_minute = minute_key[:16]  # "2026-04-22T10:20"

    # Flush mọi candle của các phút cũ khi minute mới xuất hiện.
    flush_stale_candles(current_minute)

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
    """Backward-compatible helper that flushes immediately."""
    supabase.table(TABLE).upsert([candle], on_conflict="symbol,trading_time").execute()

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
        if allowed_symbols and symbol not in allowed_symbols:
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
    try:
        tick = parse_tick(message)
        if tick is None:
            return
        
        # Log individual tick for debugging
        logger.debug(f"[TICK] {tick['symbol']} at {tick['trading_time']} close={tick['close']}")
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
    allowed_symbols = get_hose_symbols()
    if not allowed_symbols:
        logger.warning("HOSE symbol list is empty; stream will rely only on the 3-character symbol filter.")
    else:
        logger.info(f"Loaded {len(allowed_symbols)} HOSE symbols for websocket filtering.")

    try:
        mm = MarketDataStream(config, MarketDataClient(config))
        mm.start(get_market_data, get_error, "B:ALL")
    except Exception as e:
        logger.error(f"❌ Failed to start MarketDataStream: {e}", exc_info=True)
        return

    logger.info("Stream started. Press Ctrl+C to stop.")
    try:
        # Run a light loop: flush closed minutes periodically and refresh allowed symbols hourly
        last_refresh = 0
        REFRESH_INTERVAL = 60 * 60  # seconds
        last_minute = None
        while True:
            try:
                now = datetime.now()
                current_minute = now.replace(second=0, microsecond=0).isoformat()[:16]

                # Flush closed minutes once per minute (even if no incoming ticks)
                if current_minute != last_minute:
                    try:
                        flush_stale_candles(current_minute)
                    except Exception as e:
                        logger.error(f"❌ Error in flush_stale_candles: {e}", exc_info=True)
                    last_minute = current_minute

                # Refresh HOSE allowlist periodically
                if time.time() - last_refresh > REFRESH_INTERVAL:
                    try:
                        allowed = get_hose_symbols()
                        if allowed:
                            allowed_symbols.clear()
                            allowed_symbols.update(allowed)
                            logger.info(f"Refreshed HOSE symbol list: {len(allowed_symbols)} symbols")
                        last_refresh = time.time()
                    except Exception as e:
                        logger.warning(f"Failed to refresh HOSE symbols: {e}")

                time.sleep(1)
            except Exception as e:
                logger.error(f"❌ Error in main loop: {e}", exc_info=True)
                time.sleep(5)  # Wait before retrying
    except KeyboardInterrupt:
        logger.info(f"Shutting down... Flushing {len(candle_buffer)} remaining candles from candle_buffer...")
        if candle_buffer:
            # Only flush completed minutes (do not write the current open minute)
            now = datetime.now().replace(second=0, microsecond=0).isoformat()[:16]
            completed = [c for k, c in candle_buffer.items() if k[1][:16] < now]
            if completed:
                try:
                    supabase.table(TABLE).upsert(completed, on_conflict="symbol,trading_time").execute()
                    logger.info(f"Flushed {len(completed)} completed candle(s) on shutdown.")
                except Exception as e:
                    logger.error(f"Supabase shutdown flush error: {e} | batch_size: {len(completed)}")
            else:
                logger.info("No completed candles to flush on shutdown; skipping open minute(s).")
        
        logger.info("Stopped.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"❌ Unhandled exception in main: {e}", exc_info=True)
        sys.exit(1)