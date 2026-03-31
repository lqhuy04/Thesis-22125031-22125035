"""
News Routes
API endpoints for financial news
"""
from fastapi import APIRouter, Query
from app.models.news_schemas import NewsListResponse, CategoryNewsItem, NewsCategoriesResponse
from app.services.news_db_service import NewsDBService
from typing import Optional
from uuid import uuid4

router = APIRouter(prefix="/api/news", tags=["News"])


@router.get("/by-category", response_model=NewsListResponse)
async def get_news_by_category(
    categories: str = Query(..., description="Comma-separated categories (e.g., Ngân hàng,Bất Động sản,Hàng tiêu dùng)"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of articles")
):
    """
    Lấy tin tức theo nhóm ngành của mã cổ phiếu.

    Frontend truyền vào danh sách category, backend lọc symbol theo BI_Profile.industry_name
    rồi trả về các bài báo liên quan.
    """
    category_list = [item.strip() for item in categories.split(",") if item.strip()]
    articles = await NewsDBService.get_news_by_categories(categories=category_list, limit=limit)

    return NewsListResponse(
        data=articles,
        errorCode=0,
        errorDesc="",
        requestId=str(uuid4()),
        result=True,
    )


# Router
@router.get("/categories", response_model=NewsCategoriesResponse)
async def get_news_categories(
    top_n: int = Query(3, ge=1, le=20, description="Number of top categories to return"),
    limit_per_category: int = Query(3, ge=1, le=50, description="Maximum articles per category")
):
    """
    Get top categories by stock count, each with their latest news.

    Example response:
    data: [
      {"category_id": "1", "category_name": "Bất động sản", "news": [...]},
      {"category_id": "2", "category_name": "Ngân hàng",    "news": [...]},
      {"category_id": "3", "category_name": "Xăng dầu",     "news": [...]}
    ]
    """
    grouped = await NewsDBService.get_news_grouped_by_top_categories(
        top_n=top_n,
        limit_per_category=limit_per_category,
    )

    return NewsCategoriesResponse(
        data=[CategoryNewsItem(**item) for item in grouped],
        errorCode=0,
        errorDesc="",
        requestId=str(uuid4()),
        result=True,
    )


@router.get("/category/{category_id}", response_model=NewsListResponse)
async def get_news_single_category(
    category_id: str,
    limit: int = Query(100, ge=1, le=500, description="Maximum number of articles")
):
    """Get news list for one category by ID."""
    articles = await NewsDBService.get_news_by_category_id(category_id=category_id, limit=limit)
    return NewsListResponse(
        data=articles,
        errorCode=0,
        errorDesc="",
        requestId=str(uuid4()),
        result=True,
    )


@router.get("/macro-economic", response_model=NewsListResponse)
async def get_macro_economic_news(
    min_symbols: int = Query(3, ge=3, description="Minimum impacted symbols count"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of articles")
):
    """
    Lấy tin tức "Kinh tế vĩ mô" có tác động lên nhiều mã cổ phiếu.

    - **min_symbols**: Số lượng mã bị ảnh hưởng tối thiểu (mặc định: 3)
    - **limit**: Số lượng bài viết tối đa trả về
    """
    articles = await NewsDBService.get_macro_news(min_symbols=min_symbols, limit=limit)
    return NewsListResponse(
        data=articles,
        errorCode=0,
        errorDesc="",
        requestId=str(uuid4()),
        result=True
    )


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
