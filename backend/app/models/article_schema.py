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


class RelatedStockResponse(BaseModel):
    """Stock ticker linked to an article and its latest percentage change."""
    symbol: str = Field(..., description="Related stock symbol")
    per_price_change: Optional[float] = Field(
        None,
        description="Latest stock price percentage change",
    )


class ArticlesResponse(ArticlesBase):
    """Schema for Articles response"""
    id: str = Field(..., description="Unique Articles identifier")
    related_stocks: List[RelatedStockResponse] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


class ArticleListItemResponse(BaseModel):
    """Minimal article payload used by news list items."""
    id: str = Field(..., description="Unique article identifier")
    title: str = Field(..., description="Article title")
    time: Optional[datetime] = Field(None, description="Publication time")
    thumbnail: Optional[str] = Field(None, description="Article image URL")
    source: Optional[str] = Field(None, description="Article source")
    related_stocks: List[RelatedStockResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class ArticlesListResponse(BaseModel):
    """Standardized API response for Articles list"""
    data: list[ArticleListItemResponse]
    errorCode: int = Field(default=0, description="Error code (0 = success)")
    errorDesc: str = Field(default="", description="Error description")
    requestId: str = Field(default="", description="Unique request ID")
    result: bool = Field(default=True, description="Success flag")


class ArticleDetailResponse(BaseModel):
    """Standardized API response for one complete article."""
    data: Optional[ArticlesResponse] = None
    errorCode: int = Field(default=0, description="Error code (0 = success)")
    errorDesc: str = Field(default="", description="Error description")
    requestId: str = Field(default="", description="Unique request ID")
    result: bool = Field(default=True, description="Success flag")


class TodayHighlightNewsItem(BaseModel):
    """Minimal news payload used by the today-highlight card."""
    id: str = Field(..., description="Unique news identifier")
    title: str = Field("", description="News title")
    sentiment: Optional[str] = Field(None, description="News sentiment")


class TodayHighlightStockItem(BaseModel):
    """One stock item in today-highlight response"""
    stock_id: str = Field(..., description="Unique stock identifier")
    symbol: str = Field("", description="Stock symbol")
    logo: str = Field("", description="Stock logo URL")
    company_name: str = Field("", description="Company name")
    PriceChange: float = Field(0.0, description="Price change")
    PerPriceChange: float = Field(0.0, description="Percent price change")
    CurrentPrice: float = Field(0.0, description="Current price")
    news: List[TodayHighlightNewsItem] = Field(default_factory=list, description="Latest related news")


class TodayHighlightResponse(BaseModel):
    """Standardized API response for today-highlight list"""
    data: List[TodayHighlightStockItem]
    errorCode: int = Field(default=0, description="Error code (0 = success)")
    errorDesc: str = Field(default="", description="Error description")
    requestId: str = Field(default="", description="Unique request ID")
    result: bool = Field(default=True, description="Success flag")
