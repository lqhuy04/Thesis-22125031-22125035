"""
standardize_market_index.py
Chạy sau giờ đóng cửa để đồng bộ lại bảng Current_Market_Index bằng snapshot mới nhất từ SSI.

Bảng này chỉ giữ latest price cho mỗi index_id, nên script này chỉ upsert lại 5 chỉ số chuẩn.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import requests
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
VN_TZ = timezone(timedelta(hours=7))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

supabase = create_client(
    os.getenv("SUPABASE_URL", ""),
    os.getenv("SUPABASE_KEY", ""),
)


# ═════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═════════════════════════════════════════════════════════════════════════════

def now_vn() -> datetime:
    return datetime.now(VN_TZ)


def today_vn_ddmmyyyy() -> str:
    return now_vn().strftime("%d/%m/%Y")


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


def _normalize_time(value: Any) -> str:
    time_text = str(value or "").strip()
    if not time_text:
        return "14:45:00"
    if len(time_text) == 5:
        return f"{time_text}:00"
    return time_text[:8]


# ═════════════════════════════════════════════════════════════════════════════
# SSI API
# ═════════════════════════════════════════════════════════════════════════════

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


def fetch_daily_index(index_id: str, access_token: str, trading_date: str) -> list[dict]:
    """Fetch daily index rows for one index from SSI."""
    try:
        if not access_token:
            return []

        url = "https://fc-data.ssi.com.vn/api/v2/Market/DailyIndex"
        params = {
            "requestId": str(uuid.uuid4()),
            "indexId": index_id,
            "fromDate": trading_date,
            "toDate": trading_date,
            "pageIndex": 1,
            "pageSize": 100,
            "orderBy": "",
            "order": "",
        }
        headers = {
            "Authorization": f"{config.auth_type} {access_token}",
            "Accept": "application/json",
        }

        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()

        payload = response.json()
        if not isinstance(payload, dict):
            return []

        data = payload.get("data") or []
        if isinstance(data, dict):
            data = data.get("data") or data.get("items") or []
        if not isinstance(data, list):
            return []

        return data
    except Exception as e:
        logger.error(f"Failed to fetch daily index for {index_id}: {e}")
        return []


# ═════════════════════════════════════════════════════════════════════════════
# NORMALIZE
# ═════════════════════════════════════════════════════════════════════════════

def parse_index_row(row: dict) -> Optional[dict]:
    try:
        raw_index_id = str(
            _get_field(row, "IndexId", "IndexID", "IndexCode", "index_id", "indexCode", default="")
        ).strip()
        if not raw_index_id:
            return None

        index_id = ALLOWED_INDEX_LOOKUP.get(raw_index_id.upper())
        if not index_id:
            return None

        trading_date_str = str(
            _get_field(row, "TradingDate", "Tradingdate", "tradingdate", "Date", "date", default="")
        ).strip()
        if not trading_date_str:
            return None

        if "/" in trading_date_str:
            parts = trading_date_str.split("/")
            if len(parts) != 3:
                return None
            dd, mm, yyyy = parts
            iso_date = f"{yyyy}-{mm}-{dd}"
        elif "-" in trading_date_str:
            iso_date = trading_date_str[:10]
        else:
            return None

        trading_time = _normalize_time(
            _get_field(row, "TradingTime", "Time", "time", "trading_time", default="14:45:00")
        )

        return {
            "index_id": index_id,
            "index_name": _get_field(row, "IndexName", "index_name", default=index_id),
            "type_index": _get_field(row, "IndexType", "TypeIndex", "type_index", default=None),
            "index_value": _to_float(_get_field(row, "IndexValue", "index_value", "Close", "close", default=0)),
            "change": _to_float(_get_field(row, "Change", "change", default=0)),
            "ratio_change": _to_float(_get_field(row, "RatioChange", "ratio_change", default=0)),
            "advances": int(_to_float(_get_field(row, "Advances", "advances", default=0))),
            "no_changes": int(_to_float(_get_field(row, "NoChanges", "Nochanges", "no_changes", default=0))),
            "declines": int(_to_float(_get_field(row, "Declines", "declines", default=0))),
            "ceilings": int(_to_float(_get_field(row, "Ceilings", "Ceiling", "ceilings", default=0))),
            "floors": int(_to_float(_get_field(row, "Floors", "Floor", "floors", default=0))),
            "total_trade": _to_float(_get_field(row, "TotalTrade", "total_trade", default=0)),
            "total_match_vol": _to_float(_get_field(row, "TotalQtty", "TotalMatchVol", "total_match_vol", default=0)),
            "total_match_val": _to_float(_get_field(row, "TotalValue", "TotalMatchVal", "total_match_val", default=0)),
            "total_deal_vol": _to_float(_get_field(row, "TotalQttyPt", "TotalQttyPT", "total_deal_vol", default=0)),
            "total_deal_val": _to_float(_get_field(row, "TotalValuePt", "TotalValuePT", "total_deal_val", default=0)),
            "total_vol": _to_float(_get_field(row, "AllQty", "total_vol", default=0)),
            "total_val": _to_float(_get_field(row, "AllValue", "total_val", default=0)),
            "trading_date": trading_date_str,
            "trading_time": f"{iso_date}T{trading_time}",
            "trading_session": _get_field(row, "TradingSession", "trading_session", default=None),
        }
    except Exception as e:
        logger.warning(f"Parse error: {e}")
        return None


def pick_latest_snapshot(rows: list[dict]) -> Optional[dict]:
    parsed_rows = []
    for row in rows:
        parsed = parse_index_row(row)
        if parsed:
            parsed_rows.append(parsed)

    if not parsed_rows:
        return None

    parsed_rows.sort(key=lambda row: row.get("trading_time") or "")
    return parsed_rows[-1]


def upsert_index_snapshot(snapshot: dict) -> None:
    supabase.table(TABLE).upsert([snapshot], on_conflict="index_id").execute()


# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

def main():
    trading_date = today_vn_ddmmyyyy()
    logger.info(f"=== Starting market index standardize: {trading_date} ===")

    access_token = get_ssi_access_token()
    if not access_token:
        logger.error("No SSI access token found. Exiting.")
        return

    total_upserted = 0
    for index_id in sorted(ALLOWED_INDEX_IDS):
        try:
            rows = fetch_daily_index(index_id, access_token, trading_date)
            snapshot = pick_latest_snapshot(rows)
            if not snapshot:
                logger.info(f"[{index_id}] No daily index rows found")
                continue

            upsert_index_snapshot(snapshot)
            total_upserted += 1
            logger.info(
                f"[{index_id}] Upserted snapshot: value={snapshot['index_value']} time={snapshot['trading_time']}"
            )
        except Exception as e:
            logger.error(f"[{index_id}] Error processing: {e}")

    logger.info(f"Total index snapshots upserted: {total_upserted}")
    logger.info("=== Done ===")


if __name__ == "__main__":
    main()
