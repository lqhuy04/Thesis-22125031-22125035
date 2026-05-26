"""
Market Data Routes
FastAPI routes for SSI FC Data API integration
"""
from fastapi import APIRouter, Query
import uuid
from supabase_auth import Any
from app.services.market_service import MarketService
from app.services.ssi_service import get_ssi_service
from app.models.market_data_schemas import SectorStockMovementResponse, IndexImpactResponse, InvestingIdeaResponse


router = APIRouter(prefix="/api", tags=["Market Data"])

@router.get("/all-symbol", response_model=Any)
async def get_all_symbols():
    request_id = str(uuid.uuid4())
    result = MarketService.get_all_symbols()
    return {
        "data": result,
        "errorCode": 0,
        "errorDesc": "",
        "requestId": request_id,
        "result": True
    }

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
        "data": result,
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


@router.get("/industry-movement", response_model=SectorStockMovementResponse)
async def get_industry_movement(
    industry: str = Query(..., description="Industry name, e.g. Bất động sản"),
    limit: int | None = Query(None, ge=1, description="Max number of stocks to return"),
):
    request_id = str(uuid.uuid4())
    payload = MarketService.get_industry_stocks_movement(
        industry=industry,
        limit=limit,
    )

    has_data = len(payload.get("items", [])) > 0
    return {
        "data": payload.get("items", []),
        "errorCode": 0 if has_data else 500001,
        "errorDesc": "" if has_data else "No data found for the specified industry",
        "requestId": request_id,
        "result": has_data,
    }

@router.get("/market-index", response_model=Any)
async def get_market_indices():
    request_id = str(uuid.uuid4())
    vnindex_result = MarketService.get_market_index(index_id="VNINDEX")
    hnxindex_result = MarketService.get_market_index(index_id="HNXINDEX")
    hnxupcomindex_result = MarketService.get_market_index(index_id="HNXUpcomIndex")
    vn30_result = MarketService.get_market_index(index_id="VN30")
    vn100_result = MarketService.get_market_index(index_id="VN100")

    return {
        "data": [ vnindex_result, hnxindex_result,hnxupcomindex_result, vn30_result, vn100_result ],
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


@router.get("/top-impact/{index_id}", response_model=IndexImpactResponse)
async def get_top_index_impact_stocks(
    index_id: str,
    limit: int = Query(10, ge=1, le=100, description="Number of top impacted stocks"),
):
    request_id = str(uuid.uuid4())
    result = MarketService.get_top_index_impact_stocks(index_id=index_id, limit=limit)
    return {
        "data": result,
        "errorCode": 0 if result else 500001,
        "errorDesc": "" if result else "No impact data found for the specified index",
        "requestId": request_id,
        "result": bool(result),
    }


@router.get("/investing-idea", response_model=InvestingIdeaResponse)
async def get_investing_idea(
    limit: int = Query(100, ge=1, le=100, description="Number of stocks per list"),
):
    request_id = str(uuid.uuid4())
    payload = MarketService.get_investing_ideas(limit=limit)

    has_data = (
        bool(payload.get("trend", {}).get("top_gainers"))
        or bool(payload.get("trend", {}).get("top_decliners"))
        or bool(payload.get("trend", {}).get("top_volume"))
        or bool(payload.get("top_choice", {}).get("cheap_under_50k"))
        or bool(payload.get("community", {}).get("top_searched"))
        or bool(payload.get("community", {}).get("top_watchlist"))
    )

    return {
        "data": payload,
        "errorCode": 0 if has_data else 500001,
        "errorDesc": "" if has_data else "No investing idea data found",
        "requestId": request_id,
        "result": has_data,
    }

@router.get("/test", response_model=Any)
async def test():
    request_id = str(uuid.uuid4())
    ssi_service = get_ssi_service()
    result = ssi_service.get_securities_list(
        market="hose",
        page_size=1000,
    )
    return {
        "data": result,
        "errorCode": 0 if result else 500001,
        "errorDesc": "" if result else "No data found for the specified index",
        "requestId": request_id,
        "result": bool(result)
    }