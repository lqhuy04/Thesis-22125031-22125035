"""
Market Data Routes
FastAPI routes for SSI FC Data API integration
"""
from fastapi import APIRouter, Query
import uuid
import asyncio
from supabase_auth import Any
from app.services.market_service import MarketService

router = APIRouter(prefix="/api", tags=["Market Data"])

@router.get("/search/{symbol}", response_model=Any)
async def search_stock_by_symbol(
    symbol: str,
):
    request_id = str(uuid.uuid4())
    result =  MarketService.search_stock_by_symbol(symbol)
    return {
        "data": result,
        "errorCode": 0 if result else 500001,
        "errorDesc": "" if result else "Stock not found or error occurred",
        "requestId": request_id,
        "result": bool(result)
    }

@router.get("/price/{symbol}", response_model=Any)
async def get_latest_historical_chart_data(
    symbol: str,
    interval: str = Query("15m", description="Interval: 15m, 1h, or 1d")
):
    """
    📈 Get exactly the latest 1000 records for a specific interval
    
    This endpoint automatically syncs missing intra-day info and returns the latest available points:
    - **interval**: 15m, 1h, 1d (defaults to 15m)
    - Returns latest **1000** records (fixed)
    
    **Example:** `/api/stock-price/VNM?interval=1h`
    """
    request_id = str(uuid.uuid4())
    result = MarketService.get_stock_price_by_interval(symbol, limit=1000, interval=interval)
    return {
        "data": result,
        "errorCode": 0 if result else 500001,
        "errorDesc": "" if result else "No data found for the specified symbol and interval",
        "requestId": request_id,
        "result": bool(result)
    }
    
@router.post("/price/{symbol}", response_model=Any)
async def update_price_data_for_symbol_with_time_interval(symbol: str, interval: str = Query("15m", description="Interval: 15m, 1h, or 1d")):
    """
    🔄 Manually trigger price data update for a stock symbol
    
    This endpoint forces a sync of missing intra-day price data for the specified symbol.
    Use this if you want to ensure the latest data is available before fetching.
    
    **Example:** `/api/price/VNM`
    """
    request_id = str(uuid.uuid4())
    result = MarketService.update_price_data_for_symbol_with_time_interval(symbol, interval=interval)
    
    return {
        "data": result,
        "errorCode": 0 if result else 500001,
        "errorDesc": "" if result else "Failed to update price data for the specified symbol",
        "requestId": request_id,
        "result": result
    }


@router.get("/current-price/{symbol}", response_model=Any)
async def get_stock_price(symbol: str):
    """
    💰 Get ceiling/floor/reference price for a stock
    
    Calculates prices based on Vietnamese stock market rules:
    - **reference_price**: Previous day's closing price (giá tham chiếu)
    - **ceiling_price**: giá trần = RefPrice * (1 + band)
    - **floor_price**: giá sàn = RefPrice * (1 - band)
    - **current_price**: Latest closing price
    - **price_change**: Change from previous day's close
    - **price_change_percent**: Percentage change
    
    Fluctuation bands: HOSE 7%, HNX 10%, UPCOM 15%
    """
    request_id = str(uuid.uuid4())
    result = MarketService.get_current_stock_price(symbol)
    return {
        "data": result,
        "errorCode": 0 if result else 500001,
        "errorDesc": "" if result else "Stock not found or error occurred",
        "requestId": request_id,
        "result": bool(result)
    }

@router.get("/market-index", response_model=Any)
async def get_market_indices():
    request_id = str(uuid.uuid4())
    vnindex_result = MarketService.get_market_index(index_id="VNINDEX")
    await asyncio.sleep(1.05)
    hnxindex_result = MarketService.get_market_index(index_id="HNXINDEX")
    await asyncio.sleep(1.05)
    vn30_result = MarketService.get_market_index(index_id="VN30")
    await asyncio.sleep(1.05)
    vn100_result = MarketService.get_market_index(index_id="VN100")

    return {
        "data": {
            "VNINDEX": vnindex_result,
            "HNXINDEX": hnxindex_result,
            "VN30": vn30_result,
            "VN100": vn100_result
        },
        "errorCode": 0 if vnindex_result and hnxindex_result and vn30_result and vn100_result else 500001,
        "errorDesc": "" if vnindex_result and hnxindex_result and vn30_result and vn100_result else "No data found for the specified index",
        "requestId": request_id,
        "result": bool(vnindex_result and hnxindex_result and vn30_result and vn100_result)
    }

# @router.get("/index", response_model=Any)
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


