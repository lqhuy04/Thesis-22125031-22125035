"""
Articles data models and schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class ArticlesBase(BaseModel):
    """Base Articles schema - matches database structure"""
    title: str = Field(..., description="Articles article title")
    link: str = Field(..., description="URL to the full article")
    description: Optional[str] = Field(None, description="Articles article summary/description")
    time: Optional[datetime] = Field(None, description="Publication time")
    thumbnail: Optional[str] = Field(None, description="URL to article image")
    content: Optional[str] = Field(None, description="Article content text")
    source: Optional[str] = Field(None, description="Articles source website")
    sentiment: Optional[str] = Field(None, description="Sentiment label: positive, neutral, negative")
    summary: Optional[str] = Field(None, description="AI-generated short summary")


class ArticlesCreate(ArticlesBase):
    """Schema for creating Articles"""
    pass


class ArticlesResponse(ArticlesBase):
    """Schema for Articles response"""
    id: str = Field(..., description="Unique Articles identifier")
    
    class Config:
        from_attributes = True

class ArticlesListResponse(BaseModel):
    """Standardized API response for Articles list"""
    data: list[ArticlesResponse]
    errorCode: int = Field(default=0, description="Error code (0 = success)")
    errorDesc: str = Field(default="", description="Error description")
    requestId: str = Field(default="", description="Unique request ID")
    result: bool = Field(default=True, description="Success flag")


class TodayHighlightNewsItem(BaseModel):
    """One news item in today-highlight response"""
    id: str = Field(..., description="Unique news identifier")
    title: str = Field("", description="News title")
    link: str = Field("", description="News link")
    stock_symbol: str = Field("", description="Related stock symbol")
    description: str = Field("", description="News description")
    time: str = Field("", description="News date string")
    thumbnail: str = Field("", description="News image URL")
    published_at: str = Field("", description="Published timestamp string")
    content: str = Field("", description="News content")
    source: str = Field("", description="News source")
    sentiment: str = Field("", description="News sentiment")


class TodayHighlightStockItem(BaseModel):
    """One stock item in today-highlight response"""
    stock_id: str = Field(..., description="Unique stock identifier")
    symbol: str = Field("", description="Stock symbol")
    company_name: str = Field("", description="Company name")
    exchange: str = Field("", description="Exchange code")
    PriceChange: float = Field(0.0, description="Price change")
    PerPriceChange: float = Field(0.0, description="Percent price change")
    CeilingPrice: float = Field(0.0, description="Ceiling price")
    FloorPrice: float = Field(0.0, description="Floor price")
    RefPrice: float = Field(0.0, description="Reference price")
    CurrentPrice: float = Field(0.0, description="Current price")
    TotalMatchVol: float = Field(0.0, description="Total matched volume")
    TotalMatchVal: float = Field(0.0, description="Total matched value")
    news: List[TodayHighlightNewsItem] = Field(default_factory=list, description="Latest exclusive news")


class TodayHighlightResponse(BaseModel):
    """Standardized API response for today-highlight list"""
    data: List[TodayHighlightStockItem]
    errorCode: int = Field(default=0, description="Error code (0 = success)")
    errorDesc: str = Field(default="", description="Error description")
    requestId: str = Field(default="", description="Unique request ID")
    result: bool = Field(default=True, description="Success flag")