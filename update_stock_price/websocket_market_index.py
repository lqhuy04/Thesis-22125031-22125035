from ssi_fc_data.fc_md_stream import MarketDataStream
from ssi_fc_data.fc_md_client import MarketDataClient
import json
import logging
import os
import sys
from typing import Any, Optional

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# ═════════════════════════════════════════════════════════════════════════════
# CONFIG
# ═════════════════════════════════════════════════════════════════════════════


class Config:
    auth_type = os.getenv("SSI_AUTH_TYPE", "Bearer")
    consumerID = os.getenv("SSI_CONSUMER_ID", "")
    consumerSecret = os.getenv("SSI_CONSUMER_SECRET", "")
    url = os.getenv("SSI_API_URL", "https://fc-data.ssi.com.vn/")
    stream_url = os.getenv("SSI_STREAM_URL", "https://fc-datahub.ssi.com.vn/")


config = Config()

TABLE = "Current_Market_Index"
ALLOWED_INDEX_IDS = {"VNINDEX", "VN30", "VN100", "HNXINDEX", "HNXUpcomIndex"}
ALLOWED_INDEX_LOOKUP = {index_id.upper(): index_id for index_id in ALLOWED_INDEX_IDS}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

supabase = create_client(
    os.getenv("SUPABASE_URL", ""),
    os.getenv("SUPABASE_KEY", ""),
)


def _to_float(value: Any) -> float:
    try:
        if value in (None, ""):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _get_field(payload: dict, *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in payload and payload[key] not in (None, ""):
            return payload[key]
    return default


def parse_index_tick(message) -> Optional[dict]:
    try:
        msg = json.loads(message) if isinstance(message, str) else message

        data_type = str(msg.get("DataType") or msg.get("datatype") or "").upper()
        if data_type != "MI":
            return None

        content = msg.get("Content") or msg.get("content")
        index_data = json.loads(content) if isinstance(content, str) else content
        if not isinstance(index_data, dict):
            return None

        index_id = str(
            _get_field(index_data, "IndexId", "IndexID", "index_id", default="")
        ).strip()
        if not index_id:
            return None

        index_id = ALLOWED_INDEX_LOOKUP.get(index_id.upper())
        if not index_id:
            return None

        trading_date = str(_get_field(index_data, "TradingDate", "tradingdate", default="")).strip()
        trading_time = str(_get_field(index_data, "Time", "time", default="")).strip()
        if not trading_date or not trading_time:
            return None

        return {
            "index_id": index_id,
            "index_name": _get_field(index_data, "IndexName", "index_name", default=index_id),
            "type_index": _get_field(index_data, "IndexType", "TypeIndex", "type_index", default=None),
            "index_value": _to_float(_get_field(index_data, "IndexValue", "index_value", default=0)),
            "change": _to_float(_get_field(index_data, "Change", "change", default=0)),
            "ratio_change": _to_float(_get_field(index_data, "RatioChange", "ratio_change", default=0)),
            "advances": int(_to_float(_get_field(index_data, "Advances", "advances", default=0))),
            "no_changes": int(_to_float(_get_field(index_data, "NoChanges", "Nochanges", "no_changes", default=0))),
            "declines": int(_to_float(_get_field(index_data, "Declines", "declines", default=0))),
            "ceilings": int(_to_float(_get_field(index_data, "Ceilings", "Ceiling", "ceilings", default=0))),
            "floors": int(_to_float(_get_field(index_data, "Floors", "Floor", "floors", default=0))),
            "total_trade": _to_float(_get_field(index_data, "TotalTrade", "total_trade", default=0)),
            "total_match_vol": _to_float(_get_field(index_data, "TotalQtty", "TotalMatchVol", "total_match_vol", default=0)),
            "total_match_val": _to_float(_get_field(index_data, "TotalValue", "TotalMatchVal", "total_match_val", default=0)),
            "total_deal_vol": _to_float(_get_field(index_data, "TotalQttyPt", "TotalQttyPT", "total_deal_vol", default=0)),
            "total_deal_val": _to_float(_get_field(index_data, "TotalValuePt", "TotalValuePT", "total_deal_val", default=0)),
            "total_vol": _to_float(_get_field(index_data, "AllQty", "total_vol", default=0)),
            "total_val": _to_float(_get_field(index_data, "AllValue", "total_val", default=0)),
            "trading_date": trading_date,
            "trading_time": trading_time,
            "trading_session": _get_field(index_data, "TradingSession", "trading_session", default=None),
        }
    except Exception as e:
        logger.warning(f"Parse error: {e}")
        return None


def upsert_index_snapshot(snapshot: dict) -> None:
    supabase.table(TABLE).upsert([snapshot], on_conflict="index_id").execute()


def get_market_data(message) -> None:
    try:
        snapshot = parse_index_tick(message)
        if snapshot is None:
            return

        upsert_index_snapshot(snapshot)
        logger.info(
            "[INDEX ROW] %s",
            snapshot,
        )
        logger.debug(
            "[INDEX] %s %s value=%s change=%s ratio=%s",
            snapshot["index_id"],
            snapshot["trading_time"],
            snapshot["index_value"],
            snapshot["change"],
            snapshot["ratio_change"],
        )
    except Exception as e:
        logger.error(f"❌ Error processing index data: {e}", exc_info=True)


def get_error(error) -> None:
    logger.error(f"Stream error: {error}")


def main():
    logger.info("Starting SSI market index websocket stream...")

    try:
        mm = MarketDataStream(config, MarketDataClient(config))
        mm.start(get_market_data, get_error, "MI:ALL")
    except Exception as e:
        logger.error(f"❌ Failed to start MarketDataStream: {e}", exc_info=True)
        return

    logger.info("Index stream started. Press Ctrl+C to stop.")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        logger.info("Stopped.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"❌ Unhandled exception in main: {e}", exc_info=True)
        sys.exit(1)