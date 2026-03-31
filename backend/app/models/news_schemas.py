"""
News data models and schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class NewsBase(BaseModel):
    """Base news schema - matches database structure"""
    title: str = Field(..., description="News article title")
    link: str = Field(..., description="URL to the full article")
    description: Optional[str] = Field(None, description="News article summary/description")
    time: Optional[datetime] = Field(None, description="Publication time")
    image_url: Optional[str] = Field(None, description="URL to article image")
    content: Optional[str] = Field(None, description="Article content text")
    source: Optional[str] = Field(None, description="News source website")
    sentiment: Optional[str] = Field(None, description="Sentiment label: positive, neutral, negative")
    summary: Optional[str] = Field(None, description="AI-generated short summary")


class NewsCreate(NewsBase):
    """Schema for creating news"""
    pass


class NewsResponse(NewsBase):
    """Schema for news response"""
    id: str = Field(..., description="Unique news identifier")
    
    class Config:
        from_attributes = True

class NewsListResponse(BaseModel):
    """Standardized API response for news list"""
    data: list[NewsResponse]
    errorCode: int = Field(default=0, description="Error code (0 = success)")
    errorDesc: str = Field(default="", description="Error description")
    requestId: str = Field(default="", description="Unique request ID")
    result: bool = Field(default=True, description="Success flag")
    
class CategoryNewsItem(BaseModel):
    """A single category with its latest news articles."""
    category_id: str
    category_name: str
    news: List[NewsResponse]

class NewsCategoriesResponse(BaseModel):
    """Standardized API response for grouped news by categories."""
    data: List[CategoryNewsItem]  # Changed from Dict[str, list[NewsResponse]]
    errorCode: int = Field(default=0, description="Error code (0 = success)")
    errorDesc: str = Field(default="", description="Error description")
    requestId: str = Field(default="", description="Unique request ID")
    result: bool = Field(default=True, description="Success flag")