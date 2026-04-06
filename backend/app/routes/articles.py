"""
News Routes
API endpoints for financial news
"""
from fastapi import APIRouter, Query
from app.models.article_schema import ArticlesListResponse
from app.services.articles_service import ArticlesService
from typing import Optional
from uuid import uuid4

router = APIRouter(prefix="/api/articles", tags=["Articles"])

@router.get("", response_model=ArticlesListResponse)
async def get_all_articles(
    limit: Optional[int] = Query(None, ge=1, le=500, description="Optional maximum number of latest articles")
):
    """
    Lấy tất cả tin tức tài chính, sắp xếp theo thời gian mới nhất.

    - **limit**: Giới hạn số bài viết trả về (optional)
    """

    print("limit:", limit)
    articles = ArticlesService.get_articles(limit=limit)

    return ArticlesListResponse(
        data=articles,
        errorCode=0,
        errorDesc="",
        requestId=str(uuid4()),
        result=True
    )

@router.get("/macro", response_model=ArticlesListResponse)
async def get_macro_articles(
    min_symbols: int = Query(5, ge=5, description="Minimum impacted symbols count"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of articles")
):
    """
    Lấy tin tức "Kinh tế vĩ mô" có tác động lên nhiều mã cổ phiếu.

    - **min_symbols**: Số lượng mã bị ảnh hưởng tối thiểu (mặc định: 3)
    - **limit**: Số lượng bài viết tối đa trả về
    """
    articles = ArticlesService.get_macro_articles(min_symbols=min_symbols, limit=limit)
    return ArticlesListResponse(
        data=articles,
        errorCode=0,
        errorDesc="",
        requestId=str(uuid4()),
        result=True
    )

@router.get("/stock/{stock_symbol}", response_model=ArticlesListResponse)
async def get_articles_by_stock_symbol(
    stock_symbol: str,
    limit: Optional[int] = Query(None, ge=1, le=500, description="Optional maximum number of latest articles"),
):
    """
    Lấy tất cả tin tức tài chính liên quan đến một mã chứng khoán cụ thể.
    
    - **stock_symbol**
    """
    # Gọi service để lấy danh sách articles
    articles = ArticlesService.get_articles_by_stock_symbol(
        stock_symbol=stock_symbol.upper(),
        limit=limit,
    )
    
    # Giả định NewsListData nhận vào một list các items
    # Và ArticlesListResponse bao bọc NewsListData
    return ArticlesListResponse(
        data=articles,
        errorCode=0,
        errorDesc="",
        requestId=str(uuid4()),
        result=True
    )


@router.get("/category/{category_id}", response_model=ArticlesListResponse)
async def get_news_single_category(
    category_id: str,
    limit: int = Query(100, ge=1, le=500, description="Maximum number of articles")
):
    """Get news list for one category by category ID or category name."""
    articles = ArticlesService.get_articles_by_category_id(category_id=category_id, limit=limit)
    return ArticlesListResponse(
        data=articles,
        errorCode=0,
        errorDesc="",
        requestId=str(uuid4()),
        result=True,
    )









