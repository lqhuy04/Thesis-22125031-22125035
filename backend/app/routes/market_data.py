"""
Market Data Routes
FastAPI routes for SSI FC Data API integration
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
import uuid
import asyncio
from datetime import datetime, timedelta

from app.services.ssi_service import get_ssi_service, SSIMarketDataService
from app.services.news_db_service import NewsDBService
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


@router.get("/status", response_model=SSIApiStatus)
async def check_api_status():
    """
    Check SSI API connection status
    
    Returns the current status of the SSI API configuration and connectivity.
    """
    consumer_configured = bool(settings.SSI_CONSUMER_ID and settings.SSI_CONSUMER_SECRET)
    
    if not consumer_configured:
        return SSIApiStatus(
            connected=False,
            message="SSI API credentials not configured. Please set SSI_CONSUMER_ID and SSI_CONSUMER_SECRET in your environment.",
            consumer_id_configured=False
        )
    
    try:
        service = get_ssi_service()
        result = service.get_access_token()
        
        if result.get("success"):
            return SSIApiStatus(
                connected=True,
                message="SSI API connection successful",
                consumer_id_configured=True
            )
        else:
            return SSIApiStatus(
                connected=False,
                message=f"SSI API connection failed: {result.get('error', 'Unknown error')}",
                consumer_id_configured=True
            )
    except Exception as e:
        return SSIApiStatus(
            connected=False,
            message=f"SSI API connection error: {str(e)}",
            consumer_id_configured=True
        )


@router.get("/top-stocks", response_model=MarketDataResponse)
async def get_top_stocks(
    symbols: Optional[str] = Query(None, description="Comma-separated stock symbols (e.g., VNM,FPT,VCB). Default: VNM,FPT,VCB,VIC,VHM")
):
    """
    🏠 Get top/featured stocks for home page display
    
    Returns 5 stocks with their current prices and price changes.
    Perfect for displaying featured stocks on the home page.
    
    - **symbols**: Optional comma-separated list of stock symbols
    - Default stocks: VNM, FPT, VCB, VIC, VHM
    
    Example: `/market-data/top-stocks` or `/market-data/top-stocks?symbols=SSI,VNM,FPT,TCB,MBB`
    """
    request_id = str(uuid.uuid4())
    service = get_ssi_service()
    
    # Parse comma-separated symbols if provided
    symbol_list = None
    if symbols:
        symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    
    result = service.get_top_stocks(symbol_list)
    return create_response(result, request_id)


@router.get("/search/{query}", response_model=MarketDataResponse)
async def search_securities(
    query: str,
    market: Optional[str] = Query(None, description="Filter by market (HOSE, HNX, UPCOM)"),
    page_index: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)")
):
    """
    🚀 Search for securities by symbol (case-insensitive)
    
    Filters out đị quỹ, chứng quyền - only returns actual stocks.
    
    - **query**: Stock symbol to search for (e.g., VNM, fpt)
    - **market**: Filter by specific market - HOSE, HNX, or UPCOM (optional)
    - **page_index**: Page number for pagination (default: 1)
    - **page_size**: Number of items per page (default: 20, max: 100)
    """
    request_id = str(uuid.uuid4())
    service = get_ssi_service()
    result = service.search_securities(
        query=query,
        market=market or "",
        page_index=page_index,
        page_size=page_size
    )
    return create_response(result, request_id)


@router.get("/price/{symbol}", response_model=MarketDataResponse)
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
    service = get_ssi_service()
    result = service.get_stock_price(symbol)
    return create_response(result, request_id)


@router.get("/securities", response_model=MarketDataResponse)
async def get_securities_list(
    market: MarketEnum = Query(..., description="Market code (HOSE, HNX, UPCOM)"),
    page_index: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=1000, description="Items per page")
):
    """
    Get list of securities from a specific market
    
    - **market**: Market code (HOSE, HNX, UPCOM)
    - **page_index**: Page number for pagination (default: 1)
    - **page_size**: Number of items per page (default: 100, max: 1000)
    """
    request_id = str(uuid.uuid4())
    service = get_ssi_service()
    result = service.get_securities_list(market.value, page_index, page_size)
    return create_response(result, request_id)


@router.get("/securities/{symbol}", response_model=MarketDataResponse)
async def get_securities_details(
    symbol: str,
    market: MarketEnum = Query(..., description="Market code (HOSE, HNX, UPCOM)"),
    page_index: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=1000, description="Items per page")
):
    """
    Get details of a specific security
    
    - **symbol**: Stock symbol (e.g., ACB, VNM, FPT)
    - **market**: Market code (HOSE, HNX, UPCOM)
    - **page_index**: Page number for pagination (default: 1)
    - **page_size**: Number of items per page (default: 100, max: 1000)
    """
    request_id = str(uuid.uuid4())
    service = get_ssi_service()
    result = service.get_securities_details(market.value, symbol.upper(), page_index, page_size)
    return create_response(result, request_id)


@router.get("/ohlc/daily/{symbol}", response_model=MarketDataResponse)
async def get_daily_ohlc(
    symbol: str,
    from_date: str = Query(..., description="Start date (DD/MM/YYYY)"),
    to_date: str = Query(..., description="End date (DD/MM/YYYY)"),
    page_index: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=1000, description="Items per page"),
    ascending: bool = Query(True, description="Sort ascending")
):
    """
    Get daily OHLC (Open, High, Low, Close) data for a stock
    
    - **symbol**: Stock symbol (e.g., VNM, FPT, ACB)
    - **from_date**: Start date in format DD/MM/YYYY
    - **to_date**: End date in format DD/MM/YYYY
    - **page_index**: Page number for pagination (default: 1)
    - **page_size**: Number of items per page (default: 100, max: 1000)
    - **ascending**: Sort order (default: True)
    """
    request_id = str(uuid.uuid4())
    service = get_ssi_service()
    result = service.get_daily_ohlc(
        symbol.upper(), from_date, to_date, page_index, page_size, ascending
    )
    return create_response(result, request_id)


@router.get("/ohlc/intraday/{symbol}", response_model=MarketDataResponse)
async def get_intraday_ohlc(
    symbol: str,
    from_date: str = Query(..., description="Start date (DD/MM/YYYY)"),
    to_date: str = Query(..., description="End date (DD/MM/YYYY)"),
    resolution: ResolutionEnum = Query(ResolutionEnum.ONE_MIN, description="Time resolution in minutes"),
    page_index: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=1000, description="Items per page"),
    ascending: bool = Query(True, description="Sort ascending")
):
    """
    Get intraday OHLC data for a stock
    
    - **symbol**: Stock symbol (e.g., VNM, FPT, ACB)
    - **from_date**: Start date in format DD/MM/YYYY
    - **to_date**: End date in format DD/MM/YYYY
    - **resolution**: Time resolution (1, 5, 15, 30, or 60 minutes)
    - **page_index**: Page number for pagination (default: 1)
    - **page_size**: Number of items per page (default: 100, max: 1000)
    - **ascending**: Sort order (default: True)
    """
    request_id = str(uuid.uuid4())
    service = get_ssi_service()
    result = service.get_intraday_ohlc(
        symbol.upper(), from_date, to_date, page_index, page_size, ascending, resolution.value
    )
    return create_response(result, request_id)


@router.get("/index", response_model=MarketDataResponse)
async def get_index_overview():
    """
    Get index overview for major indices.

    This endpoint returns full index rows, including fields like:
    Advances, Declines, NoChanges, TotalVol, TotalVal, etc.
    """
    request_id = str(uuid.uuid4())
    service = get_ssi_service()
    today_str = datetime.now().strftime("%d/%m/%Y")

    cached_at = _index_overview_cache.get("cached_at")
    if (
        cached_at
        and _index_overview_cache.get("date") == today_str
        and (datetime.now() - cached_at).total_seconds() < _index_overview_cache_ttl_seconds
    ):
        cached_rows = _index_overview_cache.get("rows", [])
        return create_response(
            {
                "success": True,
                "data": {
                    "data": cached_rows,
                    "totalRecord": len(cached_rows),
                    "date": today_str,
                },
            },
            request_id,
        )

    # Fixed set requested by product: VNINDEX, VN30, HNINDEX.
    # Some SSI identifiers differ, so we try aliases per logical index.
    target_indices = {
        "VNINDEX": ["VNINDEX"],
        "VN30": ["VN30"],
        "HNINDEX": ["HNINDEX", "HNXINDEX"],
    }

    async def _fetch_index_with_fallback(logical_name: str, candidates: list[str]) -> Optional[dict]:
        # SSI DailyIndex allows pageSize in {10, 20, 50, 100, 1000}
        # and enforces roughly 1 request per second.
        for days_back in range(0, 1):
            target_date = (datetime.now() - timedelta(days=days_back)).strftime("%d/%m/%Y")

            for candidate in candidates:
                local_request_id = str(uuid.uuid4())
                result = await asyncio.to_thread(
                    service.get_daily_index,
                    local_request_id,
                    candidate,
                    target_date,
                    target_date,
                    1,
                    10,
                    "",
                    "",
                )

                # Respect SSI quota limit to avoid "maximum admitted 1 per 1s".
                await asyncio.sleep(1.05)

                if not result.get("success"):
                    continue

                payload = result.get("data", [])
                rows = payload if isinstance(payload, list) else (payload.get("data", []) if isinstance(payload, dict) else [])
                if not rows:
                    continue

                row = dict(rows[0])
                row["IndexId"] = logical_name
                return row

        return None

    merged_rows = []
    for name, aliases in target_indices.items():
        row = await _fetch_index_with_fallback(name, aliases)
        if row:
            merged_rows.append(row)

    _index_overview_cache["cached_at"] = datetime.now()
    _index_overview_cache["date"] = today_str
    _index_overview_cache["rows"] = merged_rows

    return create_response(
        {
            "success": True,
            "data": {
                "data": merged_rows,
                "totalRecord": len(merged_rows),
                "date": today_str,
            },
        },
        request_id,
    )


@router.get("/stock-price/daily/{symbol}", response_model=MarketDataResponse)
async def get_daily_stock_price(
    symbol: str,
    from_date: str = Query(..., description="Start date (DD/MM/YYYY)"),
    to_date: str = Query(..., description="End date (DD/MM/YYYY)"),
    market: str = Query("hose", description="Market code (hose, hnx, upcom)"),
    page_index: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=1000, description="Items per page")
):
    """
    Get daily stock price data
    
    - **symbol**: Stock symbol (e.g., VNM, FPT, ACB)
    - **from_date**: Start date in format DD/MM/YYYY
    - **to_date**: End date in format DD/MM/YYYY
    - **market**: Market code (hose, hnx, upcom)
    - **page_index**: Page number for pagination (default: 1)
    - **page_size**: Number of items per page (default: 100, max: 1000)
    """
    request_id = str(uuid.uuid4())
    service = get_ssi_service()
    result = service.get_daily_stock_price(
        symbol.upper(), from_date, to_date, page_index, page_size, market.upper()
    )
    return create_response(result, request_id)


@router.get("/stock-price/{symbol}", response_model=MarketDataResponse)
async def get_stock_price_by_timeframe(
    symbol: str,
    timeframe: TimeFrameEnum = Query(..., description="Time frame (1D, 1W, 1M, 1Y, 5Y)"),
    market: str = Query("hose", description="Market code (hose, hnx, upcom)")
):
    """
    📊 Get stock price data optimized for chart display
    
    **Interval per timeframe:**
    - **1D** (1 day): 15-minute intervals
    - **1W** (1 week): 2-hour intervals
    - **1M** (1 month): 12-hour intervals
    - **1Y** (1 year): 1-week intervals
    - **5Y** (5 years): 1-month intervals
    
    **Example:** `/api/stock-price/VNM?timeframe=1M`
    """
    request_id = str(uuid.uuid4())
    service = get_ssi_service()
    result = service.get_stock_prices_by_timeframe(
        symbol=symbol.upper(),
        timeframe=timeframe.value,
        market=market.lower()
    )
    return create_response(result, request_id)


@router.get("/today-highlights", response_model=MarketDataResponse)
async def get_today_highlights(
    symbols: Optional[str] = Query(None, description="Comma-separated major symbols (e.g., VNM,FPT,VCB,SSI)"),
    stock_limit: int = Query(10, ge=1, le=30, description="Number of major stocks to return"),
    news_limit: int = Query(2, ge=1, le=10, description="Latest news count per symbol")
):
    """
    📌 Tiêu điểm hôm nay

    Returns:
    - Major stocks snapshot (default 10)
    - Latest news for each symbol (default 2)
    """
    request_id = str(uuid.uuid4())
    service = get_ssi_service()
    today_str = datetime.now().strftime("%d/%m/%Y")

    default_major_symbols = [
        "VNM", "FPT", "VCB", "VIC", "VHM",
        "SSI", "MBB", "HPG", "TCB", "ACB",
    ]

    symbol_list = default_major_symbols
    if symbols:
        symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]

    symbol_list = symbol_list[:stock_limit]

    cache_key = (tuple(symbol_list), news_limit, today_str)
    cached_item = _today_highlights_cache.get(cache_key)
    if cached_item:
        cached_at = cached_item.get("cached_at")
        if cached_at and (datetime.now() - cached_at).total_seconds() < _today_highlights_cache_ttl_seconds:
            cached_data = cached_item.get("data", {})
            cached_stocks = cached_data.get("major_stocks", [])
            cache_is_complete = bool(cached_stocks) and all(
                stock.get("current_price") is not None for stock in cached_stocks
            )
            if cache_is_complete:
                return create_response({"success": True, "data": cached_data}, request_id)

    major_result = service.get_top_stocks(symbol_list)

    if not major_result.get("success"):
        return create_response(major_result, request_id)

    major_stocks = major_result.get("data", [])
    symbols_for_news = [item.get("symbol", "") for item in major_stocks if item.get("symbol")]
    batched_news = await NewsDBService.get_latest_news_for_symbols(symbols_for_news, limit=news_limit)

    enriched_major_stocks = []
    for item in major_stocks:
        symbol = item.get("symbol", "")
        latest_news = batched_news.get(symbol, [])
        item_with_news = dict(item)
        item_with_news["latest_news"] = [news.model_dump() for news in latest_news]
        enriched_major_stocks.append(item_with_news)

    payload_data = {
        "major_stocks": enriched_major_stocks,
    }

    # Cache only complete payloads to avoid serving stale partial results.
    is_complete = bool(enriched_major_stocks) and all(
        item.get("current_price") is not None for item in enriched_major_stocks
    )
    if is_complete:
        _today_highlights_cache[cache_key] = {
            "cached_at": datetime.now(),
            "data": payload_data,
        }

    return create_response(
        {
            "success": True,
            "data": payload_data,
        },
        request_id,
    )

@router.get("/historical-chart/{symbol}", response_model=MarketDataResponse)
async def get_latest_historical_chart_data(
    symbol: str,
    interval: str = Query("15m", description="Interval: 15m, 1h, or 1d")
):
    """
    📈 Get exactly the latest 1000 records for a specific interval
    
    This endpoint automatically syncs missing intra-day info and returns the latest available points:
    - **interval**: 15m, 1h, 1d (defaults to 15m)
    - Returns latest **1000** records (fixed)
    
    **Example:** `/api/historical-chart/VNM?interval=1h`
    """
    request_id = str(uuid.uuid4())
    service = get_ssi_service()
    result = service.get_latest_historical_chart_data(
        symbol=symbol.upper(),
        interval=interval.lower(),
        limit=1000
    )
    return create_response(result, request_id)
