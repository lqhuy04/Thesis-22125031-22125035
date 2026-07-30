"""
News Database Service
Handles database operations for financial news
"""
import requests
from supabase import create_client, Client
from app.config import settings
from app.models.article_schema import ArticleListItemResponse, ArticlesResponse
from app.utils.market_index import get_index_symbols
from typing import Optional, List, Union
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import re
from openai import OpenAI


class NewsExtraction(BaseModel):
    stock_symbols: List[str] = Field(
        description="List of Vietnamese stock tickers mentioned. Example: VNM, VIC, ACB"
    )

    sentiment: str = Field(
        description="positive | neutral | negative"
    )

    summary: str = Field(
        description="Short Vietnamese summary of the article (1-3 sentences)"
    )


supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
ARTICLE_LIST_FIELDS = "id,title,time,thumbnail,source"


class ArticlesService:
    """Service for news database operations"""

    @staticmethod
    def get_articles(
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[ArticleListItemResponse]:
        try:
            offset = max(0, offset)
            query = (
                supabase.table("Article")
                .select(ARTICLE_LIST_FIELDS)
                .order("time", desc=True, nullsfirst=False)
                .order("id", desc=True)
            )
            if limit is not None:
                normalized_limit = max(1, limit)
                query = query.range(offset, offset + normalized_limit - 1)
            result = query.execute()
            return [
                ArticleListItemResponse(**item)
                for item in (result.data or [])
            ]

        except Exception as e:
            print(f"Error getting news: {e}")
            import traceback
            traceback.print_exc()
            return []

    @staticmethod
    def get_article_by_id(article_id: str) -> Optional[ArticlesResponse]:
        try:
            result = (
                supabase.table("Article")
                .select("*")
                .eq("id", article_id)
                .limit(1)
                .execute()
            )
            if not result.data:
                return None
            return ArticlesResponse(**result.data[0])

        except Exception as e:
            print(f"Error getting article detail for id={article_id}: {e}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def get_articles_by_stock_symbol(
        stock_symbol: str,
        limit: Optional[int] = None,
        offset: int = 0,
        summary_only: bool = False,
    ) -> Union[List[ArticlesResponse], List[ArticleListItemResponse]]:
        try:
            offset = max(0, offset)
            stock = supabase.table("Stock").select("id").eq("stock_symbol", stock_symbol).execute()
            stock_id = stock.data[0]["id"] if stock.data else None
            if not stock_id:
                return []
            
            result = (
                supabase.table("Article_Stock")
                .select(
                    f"Article({ARTICLE_LIST_FIELDS})"
                    if summary_only
                    else "Article(*)"
                )
                .eq("stock_id", stock_id)
                .execute()
            )

            if not result.data:
                return []

            # Bước 3: Lấy danh sách article_id từ kết quả trên
            article_ids = []
            article_map = {}
            for item in result.data:
                article = item.get("Article")
                if not article:
                    continue
                article_id = str(article.get("id") or "")
                if article_id:
                    article_ids.append(article_id)
                    article_map[article_id] = article

            if not article_ids:
                return []

            # Bước 4: Đếm số stock được tag cho mỗi article_id
            # Chỉ giữ lại article nào chỉ có đúng 1 stock tag
            count_result = (
                supabase.table("Article_Stock")
                .select("article_id")
                .in_("article_id", article_ids)
                .execute()
            )

            from collections import Counter
            tag_counts = Counter(
                str(row["article_id"]) for row in count_result.data
            )
            exclusive_ids = {aid for aid, count in tag_counts.items() if count == 1}

            # Bước 5: Build response chỉ từ exclusive articles
            articles = []
            article_model = (
                ArticleListItemResponse
                if summary_only
                else ArticlesResponse
            )
            for article_id, article in article_map.items():
                if article_id not in exclusive_ids:
                    continue
                try:
                    articles.append(article_model(**article))
                except Exception:
                    continue

            articles.sort(
                key=lambda item: (
                    item.time.timestamp() if item.time else float("-inf"),
                    item.id,
                ),
                reverse=True,
            )
            if limit is not None:
                return articles[offset:offset + max(1, limit)]
            return articles[offset:]

        except Exception as e:
            print(f"Error getting news: {e}")
            import traceback
            traceback.print_exc()
            return []

    @staticmethod
    def get_macro_articles(
        limit: int = 50,
        offset: int = 0,
    ) -> List[ArticleListItemResponse]:
        try:
            limit = max(1, limit)
            offset = max(0, offset)

            result = (
                supabase.table("Article")
                .select(ARTICLE_LIST_FIELDS)
                .eq("article_type", "macro")
                .order("time", desc=True, nullsfirst=False)
                .order("id", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )

            if not result.data:
                return []

            macro_items = []
            for article in result.data:
                try:
                    macro_items.append(ArticleListItemResponse(**article))
                except Exception:
                    continue

            return macro_items

        except Exception as e:
            print(f"Error getting macro news: {e}")
            import traceback
            traceback.print_exc()
            return []

    @staticmethod
    def get_articles_by_category_id(
        category_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ArticleListItemResponse]:
        """
        Get news for a specific category by ID.
        Category(id) -> Article_Category(category_id, article_id) -> Article(id)
        """
        try:
            limit = max(1, limit)
            offset = max(0, offset)

            # Step 1: Get all article_ids linked to this category
            article_category_result = (
                supabase.table("Article_Category")
                .select("article_id")
                .eq("category_id", category_id)
                .execute()
            )
            if not article_category_result.data:
                return []

            article_ids = list({
                str(row["article_id"])
                for row in article_category_result.data
                if row.get("article_id")
            })
            if not article_ids:
                return []

            # Step 2: Fetch articles, sorted by time desc
            articles_result = (
                supabase.table("Article")
                .select(ARTICLE_LIST_FIELDS)
                .in_("id", article_ids)
                .order("time", desc=True, nullsfirst=False)
                .order("id", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            if not articles_result.data:
                return []

            articles: List[ArticleListItemResponse] = []
            for item in articles_result.data:
                try:
                    articles.append(ArticleListItemResponse(**item))
                except Exception:
                    continue

            return articles

        except Exception as e:
            print(f"Error getting news by category_id={category_id}: {e}")
            import traceback
            traceback.print_exc()
            return []
        
    @staticmethod
    def get_business_articles(
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[ArticleListItemResponse]:
        """
        Return the latest stock-type articles linked to at least one VN100 stock.
        Articles may be linked to multiple stocks.
        """
        try:
            requested_offset = max(0, offset)
            normalized_limit = max(1, limit) if limit is not None else None
            target_count = (
                requested_offset + normalized_limit
                if normalized_limit is not None
                else None
            )

            vn100_symbols = set(get_index_symbols("VN100"))
            if not vn100_symbols:
                return []

            stock_result = (
                supabase.table("Stock")
                .select("id")
                .in_("stock_symbol", sorted(vn100_symbols))
                .execute()
            )
            vn100_stock_ids = list(dict.fromkeys(
                str(row.get("id"))
                for row in (stock_result.data or [])
                if row.get("id")
            ))
            if not vn100_stock_ids:
                return []
            vn100_stock_id_set = set(vn100_stock_ids)

            page_size = (
                max(100, min(500, target_count * 4))
                if target_count is not None
                else 500
            )
            scan_offset = 0
            articles: List[ArticleListItemResponse] = []

            while True:
                article_result = (
                    supabase.table("Article")
                    .select(ARTICLE_LIST_FIELDS)
                    .eq("article_type", "stock")
                    .order("time", desc=True, nullsfirst=False)
                    .order("id", desc=True)
                    .range(scan_offset, scan_offset + page_size - 1)
                    .execute()
                )
                article_rows = article_result.data or []
                if not article_rows:
                    break

                article_ids = [
                    str(row.get("id"))
                    for row in article_rows
                    if row.get("id")
                ]
                linked_article_ids = set()

                for start in range(0, len(article_ids), 100):
                    link_result = (
                        supabase.table("Article_Stock")
                        .select("article_id, stock_id")
                        .in_("article_id", article_ids[start:start + 100])
                        .execute()
                    )
                    linked_article_ids.update(
                        str(row.get("article_id"))
                        for row in (link_result.data or [])
                        if row.get("article_id")
                        and str(row.get("stock_id")) in vn100_stock_id_set
                    )

                for payload in article_rows:
                    if str(payload.get("id")) not in linked_article_ids:
                        continue
                    try:
                        articles.append(ArticleListItemResponse(**payload))
                    except Exception:
                        continue

                    if (
                        target_count is not None
                        and len(articles) >= target_count
                    ):
                        return articles[requested_offset:target_count]

                if len(article_rows) < page_size:
                    break
                scan_offset += page_size

            if normalized_limit is not None:
                return articles[
                    requested_offset:requested_offset + normalized_limit
                ]
            return articles[requested_offset:]

        except Exception as e:
            print(f"Error getting business articles: {e}")
            import traceback
            traceback.print_exc()
            return []

    @staticmethod
    def get_today_highlight(
        stock_limit: int = 10,
        articles_per_stock: int = 2,
    ) -> List[dict]:
        """
        Traverse latest articles for VN100 stocks, collect the latest unique
        stocks, and return each stock with its latest related news.
        """
        try:
            from collections import defaultdict

            stock_limit = max(1, stock_limit)
            articles_per_stock = max(1, articles_per_stock)

            vn100_symbols = set(get_index_symbols("VN100"))
            if not vn100_symbols:
                return []

            vn100_stock_result = (
                supabase.table("Stock")
                .select("id, stock_symbol")
                .in_("stock_symbol", sorted(vn100_symbols))
                .execute()
            )
            vn100_stock_symbol_map = {
                str(item.get("id")): str(item.get("stock_symbol") or "").upper().strip()
                for item in (vn100_stock_result.data or [])
                if item.get("id")
                and str(item.get("stock_symbol") or "").upper().strip() in vn100_symbols
            }
            if not vn100_stock_symbol_map:
                return []

            def fetch_article_stock_links(article_ids: List[str], batch_size: int = 1000) -> List[dict]:
                """Fetch all Article_Stock links for article_ids, avoiding default row cap."""
                all_rows: List[dict] = []
                start = 0
                while True:
                    batch_result = (
                        supabase.table("Article_Stock")
                        .select("id, article_id, stock_id")
                        .in_("article_id", article_ids)
                        .order("id", desc=False)
                        .range(start, start + batch_size - 1)
                        .execute()
                    )
                    rows = batch_result.data or []
                    if not rows:
                        break

                    all_rows.extend(rows)
                    if len(rows) < batch_size:
                        break

                    start += batch_size

                return all_rows

            page_size = 500
            cursor_time = None
            cursor_id = None

            stock_to_articles = defaultdict(list)
            stock_latest_time = {}

            while True:
                qualified_stock_count = sum(
                    1 for items in stock_to_articles.values() if len(items) >= articles_per_stock
                )
                if qualified_stock_count >= stock_limit:
                    break

                query = (
                    supabase.table("Article")
                    .select("*")
                    .order("time", desc=True)
                    .order("id", desc=True)
                    .limit(page_size)
                )

                if cursor_time and cursor_id:
                    query = query.or_(
                        f"time.lt.{cursor_time},and(time.eq.{cursor_time},id.lt.{cursor_id})"
                    )

                latest_articles_result = query.execute()

                article_rows = latest_articles_result.data or []
                if not article_rows:
                    break

                article_ids = [
                    str(item.get("id"))
                    for item in article_rows
                    if item.get("id")
                ]
                if not article_ids:
                    if len(article_rows) < page_size:
                        break
                    last_row = article_rows[-1]
                    cursor_time = last_row.get("time")
                    cursor_id = last_row.get("id")
                    continue

                links_data = fetch_article_stock_links(article_ids=article_ids)
                if not links_data:
                    if len(article_rows) < page_size:
                        break
                    last_row = article_rows[-1]
                    cursor_time = last_row.get("time")
                    cursor_id = last_row.get("id")
                    continue

                article_to_stock_ids = defaultdict(list)
                for row in links_data:
                    article_id = str(row.get("article_id") or "")
                    stock_id = str(row.get("stock_id") or "")
                    if not article_id or not stock_id:
                        continue
                    if stock_id not in vn100_stock_symbol_map:
                        continue
                    if stock_id not in article_to_stock_ids[article_id]:
                        article_to_stock_ids[article_id].append(stock_id)

                for article in article_rows:
                    article_id = str(article.get("id") or "")
                    stock_ids = article_to_stock_ids.get(article_id, [])
                    for stock_id in stock_ids:
                        if stock_id not in stock_latest_time:
                            stock_latest_time[stock_id] = article.get("time")

                        if len(stock_to_articles[stock_id]) < articles_per_stock:
                            stock_to_articles[stock_id].append(article)

                if len(article_rows) < page_size:
                    break

                last_row = article_rows[-1]
                cursor_time = last_row.get("time")
                cursor_id = last_row.get("id")

            strict_stock_ids = [
                stock_id
                for stock_id, items in stock_to_articles.items()
                if len(items) >= articles_per_stock
            ]

            fallback_stock_ids = [
                stock_id
                for stock_id, items in stock_to_articles.items()
                if len(items) > 0 and len(items) < articles_per_stock
            ]

            if not strict_stock_ids and not fallback_stock_ids:
                return []

            strict_stock_ids = sorted(
                strict_stock_ids,
                key=lambda sid: stock_latest_time.get(sid) or datetime.min,
                reverse=True,
            )

            fallback_stock_ids = sorted(
                fallback_stock_ids,
                key=lambda sid: stock_latest_time.get(sid) or datetime.min,
                reverse=True,
            )

            selected_stock_ids = (strict_stock_ids + fallback_stock_ids)[:stock_limit]

            profile_result = (
                supabase.table("BI_Profile")
                .select("stock_id, logo, symbol, company_name, exchange")
                .in_("stock_id", selected_stock_ids)
                .execute()
            )
            profile_map = {
                str(item.get("stock_id")): item
                for item in (profile_result.data or [])
                if item.get("stock_id")
            }

            price_result = (
                supabase.table("Current_Stock_Price")
                .select(
                    "stock_id, price_change, per_price_change, ceiling_price, "
                    "floor_price, ref_price, current_price, total_match_vol, total_match_val"
                )
                .in_("stock_id", selected_stock_ids)
                .execute()
            )
            price_map = {
                str(item.get("stock_id")): item
                for item in (price_result.data or [])
                if item.get("stock_id")
            }

            def to_float(value) -> float:
                try:
                    if value is None or value == "":
                        return 0.0
                    return float(value)
                except Exception:
                    return 0.0

            def to_str(value) -> str:
                if value is None:
                    return ""
                if hasattr(value, "isoformat"):
                    return value.isoformat()
                return str(value)

            def to_news_item(article: dict, stock_symbol: str) -> dict:
                return {
                    "id": str(article.get("id") or ""),
                    "title": str(article.get("title") or ""),
                    "link": str(article.get("link") or ""),
                    "stock_symbol": stock_symbol,
                    "description": str(article.get("description") or ""),
                    "time": to_str(article.get("time")),
                    "thumbnail": str(article.get("thumbnail") or ""),
                    "published_at": to_str(article.get("published_at") or article.get("time")),
                    "content": str(article.get("content") or ""),
                    "source": str(article.get("source") or ""),
                    "sentiment": str(article.get("sentiment") or ""),
                }

            highlights = []
            for stock_id in selected_stock_ids:
                stock_symbol = vn100_stock_symbol_map.get(stock_id, "")
                if not stock_symbol:
                    continue

                stock_articles = stock_to_articles.get(stock_id, [])

                profile = profile_map.get(stock_id, {})
                price = price_map.get(stock_id, {})

                if not stock_articles:
                    continue

                highlights.append(
                    {
                        "stock_id": stock_id,
                        "symbol": stock_symbol,
                        "logo": str(profile.get("logo") or ""),
                        "company_name": str(profile.get("company_name") or ""),
                        "exchange": str(profile.get("exchange") or ""),
                        "PriceChange": to_float(price.get("price_change")),
                        "PerPriceChange": to_float(price.get("per_price_change")),
                        "CeilingPrice": to_float(price.get("ceiling_price")),
                        "FloorPrice": to_float(price.get("floor_price")),
                        "RefPrice": to_float(price.get("ref_price")),
                        "CurrentPrice": to_float(price.get("current_price")),
                        "TotalMatchVol": to_float(price.get("total_match_vol")),
                        "TotalMatchVal": to_float(price.get("total_match_val")),
                        "news": [
                            to_news_item(article=item, stock_symbol=stock_symbol)
                            for item in stock_articles[:articles_per_stock]
                        ],
                    }
                )

            return highlights

        except Exception as e:
            print(f"Error getting today highlights: {e}")
            import traceback
            traceback.print_exc()
            return []
