"""
News Routes
API endpoints for financial news
"""
from fastapi import APIRouter, Query
from app.models.news_schemas import NewsListResponse, NewsListData
from app.services.news_db_service import NewsDBService
from typing import Optional
from uuid import uuid4

router = APIRouter(prefix="/news", tags=["News"])


@router.get("", response_model=NewsListResponse)
async def get_news(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    stock_symbol: Optional[str] = Query(None, description="Filter by stock symbol"),
    search: Optional[str] = Query(None, description="Search in title and description")
):
    """
    Get financial news with pagination and filters
    
    - **page**: Page number (starts from 1)
    - **page_size**: Number of items per page (max 100)
    - **stock_symbol**: Filter news by stock ticker (e.g., VNM, SSI)
    - **search**: Search keyword in title and description
    """
    result = await NewsDBService.get_news(
        page=page,
        page_size=page_size,
        stock_symbol=stock_symbol,
        search=search
    )
    
    return NewsListResponse(
        data=NewsListData(**result),
        errorCode=0,
        errorDesc="",
        requestId=str(uuid4()),
        result=True
    )
