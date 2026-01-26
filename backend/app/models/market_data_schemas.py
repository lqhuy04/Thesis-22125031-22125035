"""
Pydantic schemas for SSI Market Data API requests and responses
"""
from pydantic import BaseModel, Field
from typing import Optional, Any, List
from enum import Enum


class MarketEnum(str, Enum):
    """Vietnamese stock market exchanges"""
    HOSE = "HOSE"  # Ho Chi Minh Stock Exchange
    HNX = "HNX"    # Hanoi Stock Exchange
    UPCOM = "UPCOM" # Unlisted Public Company Market


class ExchangeEnum(str, Enum):
    """Exchange codes for index lists"""
    HOSE = "hose"
    HNX = "hnx"


class ResolutionEnum(int, Enum):
    """Intraday resolution options in minutes"""
    ONE_MIN = 1
    FIVE_MIN = 5
    FIFTEEN_MIN = 15
    THIRTY_MIN = 30
    ONE_HOUR = 60


class TimeFrameEnum(str, Enum):
    """Time frame options for stock price charts"""
    ONE_DAY = "1D"      # 1 day - 5 minute intervals
    ONE_WEEK = "1W"     # 1 week - 1 hour intervals
    SEVEN_DAYS = "7D"   # 7 days - 1 hour intervals
    ONE_MONTH = "1M"    # 1 month - 1 day intervals
    ONE_YEAR = "1Y"     # 1 year - 1 day intervals
    FIVE_YEARS = "5Y"   # 5 years - 1 week intervals


# Request Models
class SecuritiesListRequest(BaseModel):
    """Request for getting securities list"""
    market: MarketEnum = Field(..., description="Market code (HOSE, HNX, UPCOM)")
    page_index: int = Field(1, ge=1, description="Page number for pagination")
    page_size: int = Field(100, ge=1, le=1000, description="Number of items per page")


class SecuritiesDetailsRequest(BaseModel):
    """Request for getting securities details"""
    market: MarketEnum = Field(..., description="Market code (HOSE, HNX, UPCOM)")
    symbol: str = Field(..., min_length=1, max_length=10, description="Stock symbol (e.g., ACB, VNM)")
    page_index: int = Field(1, ge=1, description="Page number for pagination")
    page_size: int = Field(100, ge=1, le=1000, description="Number of items per page")


class IndexComponentsRequest(BaseModel):
    """Request for getting index components"""
    index_code: str = Field(..., min_length=1, max_length=20, description="Index code (e.g., VN30, VN100)")
    page_index: int = Field(1, ge=1, description="Page number for pagination")
    page_size: int = Field(100, ge=1, le=1000, description="Number of items per page")


class IndexListRequest(BaseModel):
    """Request for getting index list"""
    exchange: ExchangeEnum = Field(..., description="Exchange code (hose, hnx)")
    page_index: int = Field(1, ge=1, description="Page number for pagination")
    page_size: int = Field(100, ge=1, le=1000, description="Number of items per page")


class DailyOHLCRequest(BaseModel):
    """Request for getting daily OHLC data"""
    symbol: str = Field(..., min_length=1, max_length=10, description="Stock symbol (e.g., VNM, FPT)")
    from_date: str = Field(..., description="Start date in format DD/MM/YYYY")
    to_date: str = Field(..., description="End date in format DD/MM/YYYY")
    page_index: int = Field(1, ge=1, description="Page number for pagination")
    page_size: int = Field(100, ge=1, le=1000, description="Number of items per page")
    ascending: bool = Field(True, description="Sort order (True for ascending)")


class IntradayOHLCRequest(BaseModel):
    """Request for getting intraday OHLC data"""
    symbol: str = Field(..., min_length=1, max_length=10, description="Stock symbol (e.g., VNM, FPT)")
    from_date: str = Field(..., description="Start date in format DD/MM/YYYY")
    to_date: str = Field(..., description="End date in format DD/MM/YYYY")
    page_index: int = Field(1, ge=1, description="Page number for pagination")
    page_size: int = Field(100, ge=1, le=1000, description="Number of items per page")
    ascending: bool = Field(True, description="Sort order (True for ascending)")
    resolution: ResolutionEnum = Field(ResolutionEnum.ONE_MIN, description="Time resolution in minutes")


class DailyIndexRequest(BaseModel):
    """Request for getting daily index data"""
    index_id: str = Field(..., min_length=1, max_length=20, description="Index ID (e.g., VN100, VN30)")
    from_date: str = Field(..., description="Start date in format DD/MM/YYYY")
    to_date: str = Field(..., description="End date in format DD/MM/YYYY")
    page_index: int = Field(1, ge=1, description="Page number for pagination")
    page_size: int = Field(100, ge=1, le=1000, description="Number of items per page")
    order_by: Optional[str] = Field("", description="Field to order by")
    order: Optional[str] = Field("", description="Sort order (asc or desc)")


class DailyStockPriceRequest(BaseModel):
    """Request for getting daily stock price data"""
    symbol: str = Field(..., min_length=1, max_length=10, description="Stock symbol (e.g., VNM, FPT)")
    from_date: str = Field(..., description="Start date in format DD/MM/YYYY")
    to_date: str = Field(..., description="End date in format DD/MM/YYYY")
    page_index: int = Field(1, ge=1, description="Page number for pagination")
    page_size: int = Field(100, ge=1, le=1000, description="Number of items per page")
    market: str = Field("hose", description="Market code (hose, hnx, upcom)")


class StockPriceByTimeFrameRequest(BaseModel):
    """Request for getting stock prices by time frame"""
    symbol: str = Field(..., min_length=1, max_length=10, description="Stock symbol (e.g., VNM, FPT)")
    timeframe: TimeFrameEnum = Field(..., description="Time frame (1D, 1W, 7D, 1M, 1Y, 5Y)")
    market: str = Field("hose", description="Market code (hose, hnx, upcom)")


# Response Models
class MarketDataResponse(BaseModel):
    """Standard response for market data endpoints"""
    data: Any = Field(default={}, description="Response data from SSI API")
    errorCode: int = Field(0, description="Error code (0 for success)")
    errorDesc: str = Field("", description="Error description")
    requestId: str = Field(..., description="Unique request identifier")
    result: bool = Field(..., description="Whether the request was successful")


class SSIApiStatus(BaseModel):
    """Response model for SSI API status check"""
    connected: bool = Field(..., description="Whether the API connection is working")
    message: str = Field(..., description="Status message")
    consumer_id_configured: bool = Field(..., description="Whether consumer ID is configured")


# Security Search Models
class SecurityItem(BaseModel):
    """Individual security item with price info"""
    symbol: str = Field(..., description="Stock symbol (e.g., VNM, FPT)")
    name: str = Field("", description="Company name")
    market: str = Field("", description="Market exchange (HOSE, HNX, UPCOM)")
    current_price: Optional[float] = Field(None, description="Current/latest closing price")
    price_change: Optional[float] = Field(None, description="Price change from previous day close")
    price_change_percent: Optional[float] = Field(None, description="Price change percentage")


class SecuritySearchResponse(BaseModel):
    """Response for security search endpoint"""
    data: List[SecurityItem] = Field(default=[], description="List of matching securities")
    total: int = Field(0, description="Total number of results")
    errorCode: int = Field(0, description="Error code (0 for success)")
    errorDesc: str = Field("", description="Error description")
    requestId: str = Field(..., description="Unique request identifier")
    result: bool = Field(..., description="Whether the request was successful")
