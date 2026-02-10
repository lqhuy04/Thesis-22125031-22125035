"""
News data models and schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class NewsBase(BaseModel):
    """Base news schema - matches database structure"""
    title: str = Field(..., description="News article title")
    link: str = Field(..., description="URL to the full article")
    stock_symbol: Optional[str] = Field(None, description="Associated stock ticker symbol")
    description: Optional[str] = Field(None, description="News article summary/description")
    time: Optional[datetime] = Field(None, description="Publication time")
    image_url: Optional[str] = Field(None, description="URL to article image")
    content: Optional[str] = Field(None, description="Article content text")
    source: Optional[str] = Field(None, description="News source website")


class NewsCreate(NewsBase):
    """Schema for creating news"""
    pass


class NewsResponse(NewsBase):
    """Schema for news response"""
    id: str = Field(..., description="Unique news identifier")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        from_attributes = True


class NewsListData(BaseModel):
    """Paginated news data"""
    items: list[NewsResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class NewsListResponse(BaseModel):
    """Standardized API response for news list"""
    data: NewsListData
    errorCode: int = Field(default=0, description="Error code (0 = success)")
    errorDesc: str = Field(default="", description="Error description")
    requestId: str = Field(default="", description="Unique request ID")
    result: bool = Field(default=True, description="Success flag")
