"""
News data models and schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime


class ContentBlock(BaseModel):
    """Individual content block (text, image, etc.)"""
    type: Literal["text", "image"] = Field(..., description="Block type")
    content: Optional[str] = Field(None, description="Text content for text blocks")
    url: Optional[str] = Field(None, description="Image URL for image blocks")
    caption: Optional[str] = Field(None, description="Image caption")
    alt: Optional[str] = Field(None, description="Image alt text")


class StructuredContent(BaseModel):
    """Structured content with blocks"""
    blocks: List[ContentBlock] = Field(default=[], description="Array of content blocks")


class NewsBase(BaseModel):
    """Base news schema"""
    title: str = Field(..., description="News article title")
    link: str = Field(..., description="URL to the full article")
    stock_symbol: Optional[str] = Field(None, description="Associated stock ticker symbol")
    description: Optional[str] = Field(None, description="News article summary/description")
    time: Optional[str] = Field(None, description="Publication time as string")
    image_url: Optional[str] = Field(None, description="URL to article image")
    published_at: Optional[datetime] = Field(None, description="Parsed publication timestamp")
    content: Optional[Dict[str, Any]] = Field(None, description="Structured article content with blocks")
    author: Optional[str] = Field(None, description="Article author name")
    article_images: Optional[List[str]] = Field(default=[], description="Array of image URLs in article")
    tags: Optional[List[str]] = Field(default=[], description="Article tags/categories")
    source: Optional[str] = Field(default="StockBiz", description="News source website")
    is_content_extracted: Optional[bool] = Field(default=False, description="Content extraction status")


class NewsCreate(NewsBase):
    """Schema for creating news"""
    pass


class NewsResponse(NewsBase):
    """Schema for news response"""
    id: str = Field(..., description="Unique news identifier")
    created_at: datetime = Field(..., description="When the news was added to database")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
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
