"""
Market Data Routes
FastAPI routes for SSI FC Data API integration
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, Any
import uuid
import asyncio
from datetime import datetime, timedelta

from app.services.market_service import MarketService
from app.models.market_data_schemas import (
    SecuritiesListRequest,
    SecuritiesDetailsRequest,
    DailyOHLCRequest,
    IntradayOHLCRequest,
    DailyStockPriceRequest,
    StockPriceByTimeFrameRequest,
    MarketDataResponse,
    SSIApiStatus,
    MarketEnum,
    ResolutionEnum,
    TimeFrameEnum,
    SecurityItem,
    SecuritySearchResponse
)
from app.config import settings

router = APIRouter(prefix="/api", tags=["Market Data"])

# Short-lived cache to avoid repeated slow SSI index calls.
_index_overview_cache = {
    "cached_at": None,
    "date": "",
    "rows": [],
}
_index_overview_cache_ttl_seconds = 60

_today_highlights_cache: dict = {}
_today_highlights_cache_ttl_seconds = 45


def _to_number(value: Any) -> Any:
    """Convert numeric-like strings to int/float while preserving non-numeric values."""
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        raw = value.strip()
        if raw == "":
            return value
        try:
            num = float(raw)
            return int(num) if num.is_integer() else num
        except ValueError:
            return value
    return value


def _coerce_ohlcv_payload_numbers(result: dict) -> dict:
    """Ensure Open/High/Low/Close/Volume are numeric in successful payload rows."""
    if not result.get("success"):
        return result

    data_wrapper = result.get("data")
    if not isinstance(data_wrapper, dict):
        return result

    rows = data_wrapper.get("data")
    if not isinstance(rows, list):
        return result

    numeric_keys = ("Open", "High", "Low", "Close", "Volume")
    for row in rows:
        if not isinstance(row, dict):
            continue
        for key in numeric_keys:
            if key in row:
                row[key] = _to_number(row.get(key))

    return result


def create_response(result: dict, request_id: str) -> MarketDataResponse:
    """Helper function to create standardized response"""
    if result.get("success"):
        return MarketDataResponse(
            data=result.get("data", {}),
            errorCode=0,
            errorDesc="",
            requestId=request_id,
            result=True
        )
    else:
        return MarketDataResponse(
            data={},
            errorCode=500001,
            errorDesc=result.get("error", "Unknown error"),
            requestId=request_id,
            result=False
        )


@router.get("/search/{symbol}", response_model=Any)
async def search_stock_by_symbol(
    symbol: str,
):
    request_id = str(uuid.uuid4())
    result =  MarketService.search_stock_by_symbol(symbol)
    return result


# @router.get("/price/{symbol}", response_model=MarketDataResponse)
# async def get_stock_price(symbol: str):
#     """
#     💰 Get ceiling/floor/reference price for a stock
    
#     Calculates prices based on Vietnamese stock market rules:
#     - **reference_price**: Previous day's closing price (giá tham chiếu)
#     - **ceiling_price**: giá trần = RefPrice * (1 + band)
#     - **floor_price**: giá sàn = RefPrice * (1 - band)
#     - **current_price**: Latest closing price
#     - **price_change**: Change from previous day's close
#     - **price_change_percent**: Percentage change
    
#     Fluctuation bands: HOSE 7%, HNX 10%, UPCOM 15%
#     """
#     request_id = str(uuid.uuid4())
#     service = get_ssi_service()
#     result = service.get_stock_price(symbol)
#     return create_response(result, request_id)


# @router.get("/index", response_model=MarketDataResponse)
# async def get_index_overview():
#     """
#     Get index overview for major indices.

#     This endpoint returns full index rows, including fields like:
#     Advances, Declines, NoChanges, TotalVol, TotalVal, etc.
#     """
#     request_id = str(uuid.uuid4())
#     service = get_ssi_service()
#     now = datetime.now()
#     # Match 1D behavior: before 09:15 use previous day, otherwise use current day.
#     if (now.hour, now.minute) < (9, 15):
#         target_day = now - timedelta(days=1)
#     else:
#         target_day = now
#     target_date_str = target_day.strftime("%d/%m/%Y")

#     cached_at = _index_overview_cache.get("cached_at")
#     if (
#         cached_at
#         and _index_overview_cache.get("date") == target_date_str
#         and (now - cached_at).total_seconds() < _index_overview_cache_ttl_seconds
#     ):
#         cached_rows = _index_overview_cache.get("rows", [])
#         return create_response(
#             {
#                 "success": True,
#                 "data": cached_rows,
#             },
#             request_id,
#         )

#     # Fixed set requested by product: VNINDEX, VN30, HNINDEX.
#     # Some SSI identifiers differ, so we try aliases per logical index.
#     target_indices = {
#         "VNINDEX": ["VNINDEX"],
#         "VN30": ["VN30"],
#         "HNINDEX": ["HNINDEX", "HNXINDEX"],
#     }

#     async def _fetch_index_with_fallback(logical_name: str, candidates: list[str]) -> Optional[dict]:
#         # SSI DailyIndex allows pageSize in {10, 20, 50, 100, 1000}
#         # and enforces roughly 1 request per second.
#         for candidate in candidates:
#             local_request_id = str(uuid.uuid4())
#             result = await asyncio.to_thread(
#                 service.get_daily_index,
#                 local_request_id,
#                 candidate,
#                 target_date_str,
#                 target_date_str,
#                 1,
#                 10,
#                 "",
#                 "",
#             )

#             # Respect SSI quota limit to avoid "maximum admitted 1 per 1s".
#             await asyncio.sleep(1.05)

#             if not result.get("success"):
#                 continue

#             payload = result.get("data", [])
#             rows = payload if isinstance(payload, list) else (payload.get("data", []) if isinstance(payload, dict) else [])
#             if not rows:
#                 continue

#             row = dict(rows[0])
#             row["IndexId"] = logical_name
#             return row

#         return None

#     merged_rows = []
#     for name, aliases in target_indices.items():
#         row = await _fetch_index_with_fallback(name, aliases)
#         if row:
#             merged_rows.append(row)

#     _index_overview_cache["cached_at"] = now
#     _index_overview_cache["date"] = target_date_str
#     _index_overview_cache["rows"] = merged_rows

#     return create_response(
#         {
#             "success": True,
#             "data": merged_rows,
#         },
#         request_id,
#     )


# @router.get("/stock-price-v2/{symbol}", response_model=MarketDataResponse)
# async def get_latest_historical_chart_data(
#     symbol: str,
#     interval: str = Query("15m", description="Interval: 15m, 1h, or 1d")
# ):
#     """
#     📈 Get exactly the latest 1000 records for a specific interval
    
#     This endpoint automatically syncs missing intra-day info and returns the latest available points:
#     - **interval**: 15m, 1h, 1d (defaults to 15m)
#     - Returns latest **1000** records (fixed)
    
#     **Example:** `/api/stock-price-v2/VNM?interval=1h`
#     """
#     request_id = str(uuid.uuid4())
#     service = get_ssi_service()
#     result = service.get_latest_historical_chart_data(
#         symbol=symbol.upper(),
#         interval=interval.lower(),
#         limit=1000
#     )
#     result = _coerce_ohlcv_payload_numbers(result)
#     return create_response(result, request_id)
