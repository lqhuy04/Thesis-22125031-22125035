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
    result =  MarketService.search_stock(symbol)
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
    📈 Get exactly the latest 300 records for a specific interval
    
    This endpoint automatically syncs missing intra-day info and returns the latest available points:
    - **interval**: 15m, 1h, 1d (defaults to 15m)
    - Returns latest **300** records (fixed)
    
    **Example:** `/api/stock-price/VNM?interval=1h`
    """
    request_id = str(uuid.uuid4())
    result = MarketService.get_stock_price_by_interval(symbol, interval=interval)
    return {
        "data": result[-300:] if result and len(result) > 300 else result,
        "errorCode": 0 if result else 500001,
        "errorDesc": "" if result else "No data found for the specified symbol and interval",
        "requestId": request_id,
        "result": bool(result)
    }
    
@router.post("/price/{symbol}", response_model=Any)
async def update_price_data_for_symbol_with_time_interval(symbol: str):
    """
    🔄 Manually trigger price data update for a stock symbol
    
    This endpoint forces a sync of missing intra-day price data for the specified symbol.
    Use this if you want to ensure the latest data is available before fetching.
    
    **Example:** `/api/price/VNM`
    """
    request_id = str(uuid.uuid4())
    result = MarketService.update_price_data_for_symbol(symbol)
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
        "data": [ vnindex_result, hnxindex_result, vn30_result, vn100_result ],
        "errorCode": 0 if vnindex_result and hnxindex_result and vn30_result and vn100_result else 500001,
        "errorDesc": "" if vnindex_result and hnxindex_result and vn30_result and vn100_result else "No data found for the specified index",
        "requestId": request_id,
        "result": bool(vnindex_result and hnxindex_result and vn30_result and vn100_result)
    }

@router.get("/market-index/{index_id}", response_model=Any)
async def get_market_index_by_id(index_id: str):
    request_id = str(uuid.uuid4())
    result = MarketService.get_market_index(index_id=index_id)
    return {
        "data": result,
        "errorCode": 0 if result else 500001,
        "errorDesc": "" if result else "No data found for the specified index",
        "requestId": request_id,
        "result": bool(result)
    }