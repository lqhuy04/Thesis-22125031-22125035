"""
News Routes
API endpoints for financial news
"""
from fastapi import APIRouter, Query, Depends
from app.models.article_schema import ArticlesListResponse, TodayHighlightResponse
from app.services.articles_service import ArticlesService
from app.middleware.auth_middleware import get_current_user
from typing import Optional
from uuid import uuid4

router = APIRouter(prefix="/api/articles", tags=["Articles"], dependencies=[Depends(get_current_user)])

@router.get("", response_model=ArticlesListResponse)
def get_all_articles(
    limit: Optional[int] = Query(None, ge=1, le=500, description="Optional maximum number of latest articles")
):
    """
    Lấy tất cả tin tức tài chính, sắp xếp theo thời gian mới nhất.

    - **limit**: Giới hạn số bài viết trả về (optional)
    """

    articles = ArticlesService.get_articles(limit=limit)

    return ArticlesListResponse(
        data=articles,
        errorCode=0,
        errorDesc="",
        requestId=str(uuid4()),
        result=True
    )

@router.get("/macro", response_model=ArticlesListResponse)
def get_macro_articles(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of articles")
):
    """
    Lấy tin tức "Kinh tế vĩ mô" (article_type = "macro").

    - **limit**: Số lượng bài viết tối đa trả về
    """
    articles = ArticlesService.get_macro_articles(limit=limit)
    return ArticlesListResponse(
        data=articles,
        errorCode=0,
        errorDesc="",
        requestId=str(uuid4()),
        result=True
    )

@router.get("/business", response_model=ArticlesListResponse)
def get_business_articles(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of articles")
):
    """
    Lấy tin tức mới nhất có ``article_type = "stock"`` và liên kết với
    đúng một mã cổ phiếu; mã duy nhất đó phải thuộc VN100.

    - **limit**: Số lượng bài viết tối đa trả về
    """
    articles = ArticlesService.get_business_articles(limit=limit)
    return ArticlesListResponse(
        data=articles,
        errorCode=0,
        errorDesc="",
        requestId=str(uuid4()),
        result=True
    )


@router.get("/today-highlight", response_model=TodayHighlightResponse)
def get_today_highlight_articles():
    """
    Lấy 10 mã cổ phiếu VN100 có tin mới nhất.
    Mỗi mã trả về tối đa 2 bài mới nhất chỉ gắn với đúng 1 mã cổ phiếu.
    """
    highlights = ArticlesService.get_today_highlight(stock_limit=10, articles_per_stock=2)

    return TodayHighlightResponse(
        data=highlights,
        errorCode=0,
        errorDesc="",
        requestId=str(uuid4()),
        result=True,
    )


@router.get("/stock/{stock_symbol}", response_model=ArticlesListResponse)
def get_articles_by_stock_symbol(
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
def get_news_single_category(
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