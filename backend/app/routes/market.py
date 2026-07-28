"""
Market Data Routes
FastAPI routes for SSI FC Data API integration
"""
from fastapi import APIRouter, Query, Depends
import uuid
from supabase_auth import Any
from app.services.market_service import MarketService
from app.models.market_data_schemas import SectorStockMovementResponse, InvestingIdeaResponse
from app.middleware.auth_middleware import get_current_user


router = APIRouter(prefix="/api", tags=["Market Data"], dependencies=[Depends(get_current_user)])

@router.get("/all-symbol", response_model=Any)
def get_all_symbols():
    request_id = str(uuid.uuid4())
    result = MarketService.get_all_symbols()
    return {
        "data": result,
        "errorCode": 0,
        "errorDesc": "",
        "requestId": request_id,
        "result": True
    }

@router.get("/all-stocks", response_model=Any)
def get_all_stocks(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (default 20)"),
):
    """
    📋 Get paginated list of VN100 stocks with movement data

    Each item has the same fields as the industry-movement endpoint
    (stock_id, symbol, company_name, logo, exchange, PriceChange, PerPriceChange,
    CeilingPrice, FloorPrice, RefPrice, CurrentPrice, TotalMatchVol, TotalMatchVal),
    sorted by stock symbol.

    **Example:** `/api/all-stocks?page=1&page_size=20`
    """
    request_id = str(uuid.uuid4())
    payload = MarketService.get_all_stocks_movement(page=page, page_size=page_size)

    has_data = len(payload.get("items", [])) > 0
    return {
        "data": payload.get("items", []),
        "page": payload.get("page", page),
        "pageSize": payload.get("page_size", page_size),
        "total": payload.get("total", 0),
        "totalPages": payload.get("total_pages", 0),
        "errorCode": 0 if has_data else 500001,
        "errorDesc": "" if has_data else "No stock data found",
        "requestId": request_id,
        "result": has_data,
    }

@router.get("/search/{symbol}", response_model=Any)
def search_stock_by_symbol(
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
def get_latest_historical_chart_data(
    symbol: str,
    interval: str = Query("15m", description="Interval: 15m, 1h, or 1d")
):
    """
    📈 Get exactly the latest 300 records for a specific interval

    The stock symbol is resolved through Stock.stock_symbol, then price rows
    are queried from Stock_Price_1m or Stock_Price_1d by Stock.id.

    - **interval**: 15m, 1h, 1d (defaults to 15m)
    - Returns latest **300** records (fixed)
    
    **Example:** `/api/price/VNM?interval=1h`
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


@router.get("/market-index-price/{index_id}", response_model=Any)
def get_market_index_historical_values(
    index_id: str,
    interval: str = Query(
        "15m",
        description="Interval: 1m, 5m, 15m, 30m, 1h, 1d, 1w, or 1M",
    ),
):
    """
    Get the latest 300 historical values for a market index.

    Intraday intervals are derived from MarketIndex_Value_1m. Daily, weekly,
    and monthly intervals are derived from MarketIndex_Value_1d.

    **Example:** `/api/market-index-price/VN100?interval=1d`
    """
    request_id = str(uuid.uuid4())
    result = MarketService.get_market_index_value_by_interval(
        index_id,
        interval=interval,
    )
    return {
        "data": result,
        "errorCode": 0 if result else 500001,
        "errorDesc": (
            ""
            if result
            else "No historical data found for the specified market index and interval"
        ),
        "requestId": request_id,
        "result": bool(result),
    }
    
@router.get("/current-price/{symbol}", response_model=Any)
def get_stock_price(symbol: str):
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


@router.get("/related-stocks/{symbol}", response_model=Any)
def get_related_stocks(symbol: str):
    """
    🔗 Get up to 6 VN100 stocks related to the given VN100 symbol

    "Related" = sharing at least one category (industry) with the input symbol,
    while both the input and returned stocks belong to VN100. Results are picked
    randomly. Each item has: symbol, current_price, per_price_change.

    **Example:** `/api/related-stocks/VNM`
    """
    request_id = str(uuid.uuid4())
    result = MarketService.get_related_stocks(symbol)
    has_data = len(result) > 0
    return {
        "data": result,
        "errorCode": 0 if has_data else 500001,
        "errorDesc": "" if has_data else "No related stocks found for the specified symbol",
        "requestId": request_id,
        "result": has_data,
    }

@router.get("/industry-movement", response_model=SectorStockMovementResponse)
def get_industry_movement(
    industry_id: str = Query(
        ...,
        description="Industry (category) id; results are restricted to VN100 stocks",
    ),
    limit: int | None = Query(None, ge=1, description="Max number of stocks to return"),
):
    request_id = str(uuid.uuid4())
    payload = MarketService.get_industry_stocks_movement(
        industry_id=industry_id,
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
def get_market_indices():
    request_id = str(uuid.uuid4())
    vn100_result = MarketService.get_market_index(index_id="VN100")
    vn30_result = MarketService.get_market_index(index_id="VN30")

    return {
        "data": [vn100_result,  vn30_result ],
        "errorCode": 0 if vn30_result and vn100_result else 500001,
        "errorDesc": "" if vn30_result and vn100_result else "No data found for the specified index",
        "requestId": request_id,
        "result": bool(vn30_result and vn100_result)
    }

@router.get("/market-index/{index_id}/random-stocks", response_model=Any)
def get_random_market_index_stocks(
    index_id: str,
    limit: int = Query(6, ge=1, le=20, description="Number of random stocks"),
):
    """
    Get a random stock sample belonging to the specified market index.

    **Example:** `/api/market-index/VN100/random-stocks?limit=6`
    """
    request_id = str(uuid.uuid4())
    result = MarketService.get_random_market_index_stocks(
        index_id=index_id,
        limit=limit,
    )
    return {
        "data": result,
        "errorCode": 0 if result else 500001,
        "errorDesc": (
            ""
            if result
            else "No stocks found for the specified market index"
        ),
        "requestId": request_id,
        "result": bool(result),
    }

@router.get("/market-index/{index_id}", response_model=Any)
def get_market_index_by_id(index_id: str):
    request_id = str(uuid.uuid4())
    result = MarketService.get_market_index(index_id=index_id)
    return {
        "data": result,
        "errorCode": 0 if result else 500001,
        "errorDesc": "" if result else "No data found for the specified index",
        "requestId": request_id,
        "result": bool(result)
    }


@router.get("/investing-idea", response_model=InvestingIdeaResponse)
def get_investing_idea(
    msgType: str = Query(
        ...,
        description=(
            "Category to fetch. One of: top_gainers, top_decliners, top_volume, "
            "cheap_under_50k, top_searched, top_watchlist"
        ),
    ),
    interval: str = Query(
        "today",
        description=(
            "Time window for trend ranking (top_gainers / top_decliners / top_volume): "
            "today, 1w, 1mo, 3mo, 6mo. Defaults to 'today'. Ignored for other categories."
        ),
    ),
    limit: int = Query(100, ge=1, le=100, description="Number of stocks in the list"),
):
    request_id = str(uuid.uuid4())
    data = MarketService.get_investing_idea_by_type(
        msg_type=msgType, limit=limit, interval=interval
    )

    has_data = len(data) > 0
    return {
        "data": data,
        "errorCode": 0 if has_data else 500001,
        "errorDesc": "" if has_data else "No investing idea data found",
        "requestId": request_id,
        "result": has_data,
    }
