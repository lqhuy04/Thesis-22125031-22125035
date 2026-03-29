"""
News Routes
API endpoints for financial news
"""
from fastapi import APIRouter, Query
from app.models.news_schemas import NewsListResponse
from app.services.news_db_service import NewsDBService
from typing import Optional
from uuid import uuid4

router = APIRouter(prefix="/api/news", tags=["News"])


@router.get("/{stock_symbol}", response_model=NewsListResponse)
async def get_news(
    stock_symbol: str,
):
    """
    Lấy tất cả tin tức tài chính liên quan đến một mã chứng khoán cụ thể.
    
    - **stock_symbol**: Mã chứng khoán (VD: VNM, SSI, AAPL)
    """
    # Gọi service để lấy danh sách articles
    articles = await NewsDBService.get_news(
        stock_symbol=stock_symbol.upper()
    )
    
    # Giả định NewsListData nhận vào một list các items
    # Và NewsListResponse bao bọc NewsListData
    return NewsListResponse(
        data=articles,
        errorCode=0,
        errorDesc="",
        requestId=str(uuid4()),
        result=True
    )
