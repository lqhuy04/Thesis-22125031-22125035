"""
News Database Service
Handles database operations for financial news
"""
import requests
from supabase import create_client, Client
from app.config import settings
from app.models.article_schema import ArticlesResponse
from app.utils.market_index import get_index_symbols
from typing import Optional, List
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
class ArticlesService:
    """Service for news database operations"""

    @staticmethod
    def get_articles(limit: Optional[int] = None) -> List[ArticlesResponse]:
        try:
            query = supabase.table("Article").select("*").order("time", desc=True)
            if limit is not None:
                query = query.limit(max(1, limit))
            result = query.execute()
            return [ArticlesResponse(**item) for item in result.data] if result.data else []

        except Exception as e:
            print(f"Error getting news: {e}")
            import traceback
            traceback.print_exc()
            return []

    @staticmethod
    def get_articles_by_stock_symbol(stock_symbol: str, limit: Optional[int] = None) -> List[ArticlesResponse]:
        try:
            stock = supabase.table("Stock").select("id").eq("stock_symbol", stock_symbol).execute()
            stock_id = stock.data[0]["id"] if stock.data else None
            if not stock_id:
                return []
            
            result = (
                supabase.table("Article_Stock")
                .select("Article(*)")
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
            for article_id, article in article_map.items():
                if article_id not in exclusive_ids:
                    continue
                try:
                    articles.append(ArticlesResponse(**article))
                except Exception:
                    continue

            articles.sort(key=lambda item: item.time or datetime.min, reverse=True)
            if limit is not None:
                return articles[: max(1, limit)]
            return articles

        except Exception as e:
            print(f"Error getting news: {e}")
            import traceback
            traceback.print_exc()
            return []

    @staticmethod
    def get_macro_articles(limit: int = 50) -> List[ArticlesResponse]:
        try:
            limit = max(1, limit)

            result = (
                supabase.table("Article")
                .select("*")
                .eq("article_type", "macro")
                .order("time", desc=True)
                .limit(limit)
                .execute()
            )

            if not result.data:
                return []

            macro_items = []
            for article in result.data:
                try:
                    macro_items.append(ArticlesResponse(**article))
                except Exception:
                    continue

            return macro_items

        except Exception as e:
            print(f"Error getting macro news: {e}")
            import traceback
            traceback.print_exc()
            return []

    @staticmethod
    def get_articles_by_category_id(category_id: str, limit: int = 100) -> List[ArticlesResponse]:
        """
        Get news for a specific category by ID.
        Category(id) -> Article_Category(category_id, article_id) -> Article(id)
        """
        try:
            limit = max(1, limit)

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
                .select("*")
                .in_("id", article_ids)
                .order("time", desc=True)
                .limit(limit)
                .execute()
            )
            if not articles_result.data:
                return []

            articles: List[ArticlesResponse] = []
            for item in articles_result.data:
                try:
                    articles.append(ArticlesResponse(**item))
                except Exception:
                    continue

            return articles

        except Exception as e:
            print(f"Error getting news by category_id={category_id}: {e}")
            import traceback
            traceback.print_exc()
            return []
        
    @staticmethod
    def get_business_articles(limit: Optional[int] = None) -> List[ArticlesResponse]:
        """
        Return the latest stock-type articles linked to exactly one stock,
        where that single linked stock belongs to VN100.
        """
        try:
            from collections import Counter

            normalized_limit = max(1, limit) if limit is not None else None

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

            # First collect candidate articles that have at least one VN100 link.
            page_size = 1000
            offset = 0
            candidate_article_ids: List[str] = []
            while True:
                link_result = (
                    supabase.table("Article_Stock")
                    .select("id, article_id")
                    .in_("stock_id", vn100_stock_ids)
                    .order("id", desc=False)
                    .range(offset, offset + page_size - 1)
                    .execute()
                )
                link_rows = link_result.data or []
                if not link_rows:
                    break

                candidate_article_ids.extend(
                    str(row.get("article_id"))
                    for row in link_rows
                    if row.get("article_id")
                )
                if len(link_rows) < page_size:
                    break
                offset += page_size

            candidate_article_ids = list(dict.fromkeys(candidate_article_ids))
            if not candidate_article_ids:
                return []

            # Count every link of each candidate, including links to stocks
            # outside VN100. Only articles with exactly one total link qualify.
            link_counts: Counter = Counter()
            for start in range(0, len(candidate_article_ids), 100):
                article_id_chunk = candidate_article_ids[start:start + 100]
                chunk_offset = 0
                while True:
                    count_result = (
                        supabase.table("Article_Stock")
                        .select("id, article_id")
                        .in_("article_id", article_id_chunk)
                        .order("id", desc=False)
                        .range(chunk_offset, chunk_offset + page_size - 1)
                        .execute()
                    )
                    count_rows = count_result.data or []
                    if not count_rows:
                        break

                    link_counts.update(
                        str(row.get("article_id"))
                        for row in count_rows
                        if row.get("article_id")
                    )
                    if len(count_rows) < page_size:
                        break
                    chunk_offset += page_size

            article_ids = [
                article_id
                for article_id in candidate_article_ids
                if link_counts.get(article_id) == 1
            ]
            if not article_ids:
                return []

            articles: List[ArticlesResponse] = []
            for start in range(0, len(article_ids), 100):
                article_result = (
                    supabase.table("Article")
                    .select("*")
                    .in_("id", article_ids[start:start + 100])
                    .eq("article_type", "stock")
                    .order("time", desc=True)
                    .execute()
                )
                for payload in (article_result.data or []):
                    try:
                        articles.append(ArticlesResponse(**payload))
                    except Exception:
                        continue

            articles.sort(
                key=lambda item: item.time.timestamp() if item.time else float("-inf"),
                reverse=True,
            )
            if normalized_limit is not None:
                return articles[:normalized_limit]
            return articles

        except Exception as e:
            print(f"Error getting business articles: {e}")
            import traceback
            traceback.print_exc()
            return []

    @staticmethod
    def get_today_highlight(
        stock_limit: int = 10,
        articles_per_stock: int = 2,
        return_debug: bool = False,
    ) -> List[dict] | dict:
        """
        Traverse latest articles for VN100 stocks, keep only exclusive articles
        (1 symbol per article), collect latest unique stocks, and return each stock
        with latest exclusive news.
        """
        try:
            from collections import Counter, defaultdict

            stock_limit = max(1, stock_limit)
            articles_per_stock = max(1, articles_per_stock)

            debug_info = {
                "stock_limit": stock_limit,
                "articles_per_stock": articles_per_stock,
                "pages_scanned": 0,
                "articles_scanned": 0,
                "articles_with_id": 0,
                "article_stock_links_scanned": 0,
                "exclusive_article_candidates": 0,
                "unique_exclusive_stocks_seen": 0,
                "strict_stocks_count": 0,
                "fallback_stocks_count": 0,
                "selected_stocks_count": 0,
                "returned_stocks_count": 0,
                "vn100_universe_size": 0,
                "ended_reason": "",
            }

            def finalize(items: List[dict], ended_reason: Optional[str] = None) -> List[dict] | dict:
                if ended_reason:
                    debug_info["ended_reason"] = ended_reason
                debug_info["returned_stocks_count"] = len(items)
                if return_debug:
                    return {"data": items, "debug": debug_info}
                return items

            vn100_symbols = set(get_index_symbols("VN100"))
            if not vn100_symbols:
                return finalize([], "vn100_universe_empty")

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
            debug_info["vn100_universe_size"] = len(vn100_stock_symbol_map)
            if not vn100_stock_symbol_map:
                return finalize([], "vn100_stocks_missing")

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
                debug_info["pages_scanned"] += 1

                article_rows = latest_articles_result.data or []
                debug_info["articles_scanned"] += len(article_rows)
                if not article_rows:
                    debug_info["ended_reason"] = "no_more_articles"
                    break

                article_ids = [
                    str(item.get("id"))
                    for item in article_rows
                    if item.get("id")
                ]
                debug_info["articles_with_id"] += len(article_ids)
                if not article_ids:
                    if len(article_rows) < page_size:
                        debug_info["ended_reason"] = "last_page_without_article_ids"
                        break
                    last_row = article_rows[-1]
                    cursor_time = last_row.get("time")
                    cursor_id = last_row.get("id")
                    continue

                links_data = fetch_article_stock_links(article_ids=article_ids)
                debug_info["article_stock_links_scanned"] += len(links_data)
                if not links_data:
                    if len(article_rows) < page_size:
                        debug_info["ended_reason"] = "last_page_without_links"
                        break
                    last_row = article_rows[-1]
                    cursor_time = last_row.get("time")
                    cursor_id = last_row.get("id")
                    continue

                tag_counts = Counter(
                    str(row.get("article_id"))
                    for row in links_data
                    if row.get("article_id")
                )

                article_to_stock_id = {}
                for row in links_data:
                    article_id = str(row.get("article_id") or "")
                    stock_id = str(row.get("stock_id") or "")
                    if not article_id or not stock_id:
                        continue
                    if tag_counts.get(article_id) != 1:
                        continue
                    if stock_id not in vn100_stock_symbol_map:
                        continue
                    article_to_stock_id[article_id] = stock_id

                debug_info["exclusive_article_candidates"] += len(article_to_stock_id)

                for article in article_rows:
                    article_id = str(article.get("id") or "")
                    stock_id = article_to_stock_id.get(article_id)
                    if not stock_id:
                        continue

                    if stock_id not in stock_latest_time:
                        stock_latest_time[stock_id] = article.get("time")

                    if len(stock_to_articles[stock_id]) < articles_per_stock:
                        stock_to_articles[stock_id].append(article)

                if len(article_rows) < page_size:
                    debug_info["ended_reason"] = "reached_last_page"
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

            debug_info["unique_exclusive_stocks_seen"] = len(stock_to_articles)
            debug_info["strict_stocks_count"] = len(strict_stock_ids)
            debug_info["fallback_stocks_count"] = len(fallback_stock_ids)

            if not strict_stock_ids and not fallback_stock_ids:
                return finalize([], "no_eligible_stocks")

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
            debug_info["selected_stocks_count"] = len(selected_stock_ids)

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
                if len(stock_articles) < articles_per_stock:
                    # Fallback query to fetch up to 2 exclusive latest news for this stock.
                    fallback_articles = ArticlesService.get_articles_by_stock_symbol(
                        stock_symbol=stock_symbol,
                        limit=articles_per_stock,
                    )
                    if fallback_articles:
                        stock_articles = [article.dict() for article in fallback_articles]

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

            return finalize(highlights, debug_info.get("ended_reason") or "completed")

        except Exception as e:
            print(f"Error getting today highlights: {e}")
            import traceback
            traceback.print_exc()
            if return_debug:
                return {
                    "data": [],
                    "debug": {
                        "error": str(e),
                        "ended_reason": "exception",
                    },
                }
            return []
