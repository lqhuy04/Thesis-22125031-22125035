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
    image_url: Optional[str] = Field(None, description="URL to article image")
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