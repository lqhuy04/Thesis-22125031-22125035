import re
import os
import json
import logging
from datetime import date
from typing import Optional
from dotenv import load_dotenv
from supabase import create_client
from ssi_fc_data.fc_md_stream import MarketDataStream
from ssi_fc_data.fc_md_client import MarketDataClient

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
# PARSE
# ═════════════════════════════════════════════════════════════════════════════

def parse_bar(message) -> Optional[dict]:
    try:
        msg = json.loads(message) if isinstance(message, str) else message

        if msg.get("Datatype") != "B" and msg.get("datatype") != "B":
            return None

        content = msg.get("Content") or msg.get("content")
        bar     = json.loads(content) if isinstance(content, str) else content

        symbol = str(bar.get("Symbol") or "").strip().upper()
        if not SYMBOL_REGEX.match(symbol):
            return None

        trading_time_str = bar.get("TradingTime") or bar.get("tradingtime") or ""
        if not trading_time_str:
            return None

        trading_time = f"{date.today().isoformat()}T{trading_time_str}"

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
        return None

# ═════════════════════════════════════════════════════════════════════════════
# HANDLERS
# ═════════════════════════════════════════════════════════════════════════════

def on_message(message) -> None:
    logger.debug(f"Received message: {message}")
    candle = parse_bar(message)
    if candle is None:
        return

    try:
        supabase.table(TABLE).upsert(candle, on_conflict="symbol,trading_time").execute()
        logger.debug(f"[{candle['symbol']}] {candle['trading_time']} close={candle['close']}")
    except Exception as e:
        logger.error(f"Supabase upsert error: {e}")

def on_error(error) -> None:
    logger.error(f"Stream error: {error}")

# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

def main():
    logger.info("Starting SSI WebSocket stream...")

    stream = MarketDataStream(config, MarketDataClient(config))
    stream.start(on_message, on_error, "B:ALL")

    logger.info("Stream started. Press Ctrl+C to stop.")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        logger.info("Stopped.")

if __name__ == "__main__":
    main()