"""
Market Data Routes
FastAPI routes for SSI FC Data API integration
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
import uuid

from app.services.ssi_service import get_ssi_service, SSIMarketDataService
from app.models.market_data_schemas import (
    SecuritiesListRequest,
    SecuritiesDetailsRequest,
    IndexComponentsRequest,
    IndexListRequest,
    DailyOHLCRequest,
    IntradayOHLCRequest,
    DailyIndexRequest,
    DailyStockPriceRequest,
    MarketDataResponse,
    SSIApiStatus,
    MarketEnum,
    ExchangeEnum,
    ResolutionEnum,
    SecurityItem,
    SecuritySearchResponse
)
from app.config import settings

router = APIRouter(prefix="/market-data", tags=["Market Data"])


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


@router.get("/search", response_model=MarketDataResponse)
async def search_securities(
    query: str = Query("", description="Search by symbol only"),
    market: Optional[str] = Query(None, description="Filter by market (HOSE, HNX, UPCOM)"),
    page_index: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)")
):
    """
    🚀 Search for securities with prices (optimized with parallel fetching)
    
    Returns securities matching the search query with current price information:
    - **symbol**: Stock symbol
    - **name**: Company name
    - **market**: Market (HOSE, HNX, UPCOM)
    - **current_price**: Latest closing price
    - **price_change**: Change from previous day's close
    - **price_change_percent**: Percentage change from previous day
    
    **Performance**: Uses parallel API calls to fetch prices (~1-2s for 20 results)
    
    - **query**: Search term (symbol only) - matches against stock symbols containing this text
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
    💰 Get current price for a single stock
    
    Returns:
    - **symbol**: Stock symbol
    - **current_price**: Latest closing price
    - **price_change**: Change from previous day's close
    - **price_change_percent**: Percentage change from previous day
    
    Formula: `(Current Price - Previous Close) / Previous Close × 100`
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


@router.get("/index/components/{index_code}", response_model=MarketDataResponse)
async def get_index_components(
    index_code: str,
    page_index: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=1000, description="Items per page")
):
    """
    Get components of a specific index
    
    - **index_code**: Index code (e.g., VN30, VN100, HNX30)
    - **page_index**: Page number for pagination (default: 1)
    - **page_size**: Number of items per page (default: 100, max: 1000)
    """
    request_id = str(uuid.uuid4())
    service = get_ssi_service()
    result = service.get_index_components(index_code.lower(), page_index, page_size)
    return create_response(result, request_id)


@router.get("/index/list", response_model=MarketDataResponse)
async def get_index_list(
    exchange: ExchangeEnum = Query(..., description="Exchange code (hose, hnx)"),
    page_index: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=1000, description="Items per page")
):
    """
    Get list of indices for an exchange
    
    - **exchange**: Exchange code (hose, hnx)
    - **page_index**: Page number for pagination (default: 1)
    - **page_size**: Number of items per page (default: 100, max: 1000)
    """
    request_id = str(uuid.uuid4())
    service = get_ssi_service()
    result = service.get_index_list(exchange.value, page_index, page_size)
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
        symbol.lower(), from_date, to_date, page_index, page_size, ascending
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
        symbol.lower(), from_date, to_date, page_index, page_size, ascending, resolution.value
    )
    return create_response(result, request_id)


@router.get("/index/daily/{index_id}", response_model=MarketDataResponse)
async def get_daily_index(
    index_id: str,
    from_date: str = Query(..., description="Start date (DD/MM/YYYY)"),
    to_date: str = Query(..., description="End date (DD/MM/YYYY)"),
    page_index: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=1000, description="Items per page"),
    order_by: Optional[str] = Query("", description="Field to order by"),
    order: Optional[str] = Query("", description="Sort order (asc/desc)")
):
    """
    Get daily index data
    
    - **index_id**: Index ID (e.g., VN100, VN30, HNX30)
    - **from_date**: Start date in format DD/MM/YYYY
    - **to_date**: End date in format DD/MM/YYYY
    - **page_index**: Page number for pagination (default: 1)
    - **page_size**: Number of items per page (default: 100, max: 1000)
    - **order_by**: Field to order by (optional)
    - **order**: Sort order - asc or desc (optional)
    """
    request_id = str(uuid.uuid4())
    service = get_ssi_service()
    result = service.get_daily_index(
        request_id, index_id, from_date, to_date, page_index, page_size, order_by or "", order or ""
    )
    return create_response(result, request_id)


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
        symbol.lower(), from_date, to_date, page_index, page_size, market.lower()
    )
    return create_response(result, request_id)
