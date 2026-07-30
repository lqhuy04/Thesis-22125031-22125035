"""
News Database Service
Handles database operations for financial news
"""
import requests
from supabase import create_client, Client
from app.config import settings
from app.models.article_schema import ArticleListItemResponse, ArticlesResponse
from app.utils.market_index import get_index_stocks, get_index_symbols
from typing import Optional, List, Union
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
ARTICLE_LIST_FIELDS = "id,title,time,thumbnail,source,article_type"


class ArticlesService:
    """Service for news database operations"""

    @staticmethod
    def _attach_related_stocks(article_rows: List[dict]) -> List[dict]:
        """
        Attach related stocks to stock-type articles using batched queries.
        Non-stock articles always receive an empty list.
        """
        payloads = [
            {
                **row,
                "related_stocks": [],
            }
            for row in article_rows
        ]
        stock_article_ids = [
            str(row.get("id"))
            for row in payloads
            if row.get("id") and row.get("article_type") == "stock"
        ]
        if not stock_article_ids:
            return payloads

        links: List[dict] = []
        for batch_start in range(0, len(stock_article_ids), 100):
            article_id_batch = stock_article_ids[batch_start:batch_start + 100]
            range_start = 0

            while True:
                link_result = (
                    supabase.table("Article_Stock")
                    .select("article_id,stock_id")
                    .in_("article_id", article_id_batch)
                    .range(range_start, range_start + 999)
                    .execute()
                )
                link_rows = link_result.data or []
                links.extend(link_rows)

                if len(link_rows) < 1000:
                    break
                range_start += 1000

        stock_ids = list(dict.fromkeys(
            str(row.get("stock_id"))
            for row in links
            if row.get("stock_id")
        ))
        if not stock_ids:
            return payloads

        stocks: List[dict] = []
        prices: List[dict] = []
        for batch_start in range(0, len(stock_ids), 200):
            stock_id_batch = stock_ids[batch_start:batch_start + 200]
            stock_result = (
                supabase.table("Stock")
                .select("id,stock_symbol")
                .in_("id", stock_id_batch)
                .execute()
            )
            price_result = (
                supabase.table("Current_Stock_Price")
                .select("stock_id,per_price_change")
                .in_("stock_id", stock_id_batch)
                .execute()
            )
            stocks.extend(stock_result.data or [])
            prices.extend(price_result.data or [])

        symbol_by_stock_id = {
            str(row.get("id")): str(row.get("stock_symbol") or "").upper()
            for row in stocks
            if row.get("id") and row.get("stock_symbol")
        }

        def to_optional_float(value) -> Optional[float]:
            if value is None or value == "":
                return None
            try:
                return float(value)
            except (TypeError, ValueError):
                return None

        price_change_by_stock_id = {
            str(row.get("stock_id")): to_optional_float(
                row.get("per_price_change")
            )
            for row in prices
            if row.get("stock_id")
        }

        stocks_by_article: dict[str, dict[str, dict]] = {}
        for link in links:
            article_id = str(link.get("article_id") or "")
            stock_id = str(link.get("stock_id") or "")
            symbol = symbol_by_stock_id.get(stock_id, "")
            if not article_id or not symbol:
                continue

            stocks_by_article.setdefault(article_id, {})[symbol] = {
                "symbol": symbol,
                "per_price_change": price_change_by_stock_id.get(stock_id),
            }

        for payload in payloads:
            article_id = str(payload.get("id") or "")
            related_by_symbol = stocks_by_article.get(article_id, {})
            payload["related_stocks"] = sorted(
                related_by_symbol.values(),
                key=lambda item: item["symbol"],
            )

        return payloads

    @staticmethod
    def _to_list_items(article_rows: List[dict]) -> List[ArticleListItemResponse]:
        items: List[ArticleListItemResponse] = []
        for payload in ArticlesService._attach_related_stocks(article_rows):
            try:
                items.append(ArticleListItemResponse(**payload))
            except Exception:
                continue
        return items

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
            return ArticlesService._to_list_items(result.data or [])

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
            payload = ArticlesService._attach_related_stocks(
                [result.data[0]]
            )[0]
            return ArticlesResponse(**payload)

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

            article_map = {}
            for item in result.data:
                article = item.get("Article")
                if not article:
                    continue
                article_id = str(article.get("id") or "")
                if article_id:
                    article_map[article_id] = article

            if not article_map:
                return []

            article_model = (
                ArticleListItemResponse
                if summary_only
                else ArticlesResponse
            )
            validated_articles = []
            for article in article_map.values():
                try:
                    validated_articles.append(
                        (article_model(**article), article)
                    )
                except Exception:
                    continue

            validated_articles.sort(
                key=lambda entry: (
                    entry[0].time.timestamp()
                    if entry[0].time
                    else float("-inf"),
                    entry[0].id,
                ),
                reverse=True,
            )

            if limit is not None:
                selected = validated_articles[
                    offset:offset + max(1, limit)
                ]
            else:
                selected = validated_articles[offset:]

            enriched_payloads = ArticlesService._attach_related_stocks(
                [payload for _, payload in selected]
            )
            return [
                article_model(**payload)
                for payload in enriched_payloads
            ]

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

            return ArticlesService._to_list_items(result.data)

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

            return ArticlesService._to_list_items(articles_result.data)

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
            articles: List[dict] = []

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
                        ArticleListItemResponse(**payload)
                        articles.append(payload)
                    except Exception:
                        continue

                    if (
                        target_count is not None
                        and len(articles) >= target_count
                    ):
                        return ArticlesService._to_list_items(
                            articles[requested_offset:target_count]
                        )

                if len(article_rows) < page_size:
                    break
                scan_offset += page_size

            if normalized_limit is not None:
                selected_articles = articles[
                    requested_offset:requested_offset + normalized_limit
                ]
            else:
                selected_articles = articles[requested_offset:]

            return ArticlesService._to_list_items(selected_articles)

        except Exception as e:
            print(f"Error getting business articles: {e}")
            import traceback
            traceback.print_exc()
            return []

    @staticmethod
    def get_today_highlight(
        stock_limit: int = 10,
        articles_per_stock: int = 2,
        max_scan_pages: int = 5,
    ) -> List[dict]:
        """
        Return the VN100 stocks with the latest related news.

        A stock only needs one article to qualify. Up to ``articles_per_stock``
        articles are collected while scanning a bounded number of pages.
        """
        try:
            from collections import defaultdict

            stock_limit = max(1, stock_limit)
            articles_per_stock = max(1, articles_per_stock)
            max_scan_pages = max(1, max_scan_pages)

            vn100_stock_symbol_map = {
                str(item.get("id")): str(
                    item.get("stock_symbol") or ""
                ).upper().strip()
                for item in get_index_stocks("VN100")
                if item.get("id")
                and str(item.get("stock_symbol") or "").strip()
            }
            if not vn100_stock_symbol_map:
                return []

            def fetch_article_stock_links(
                article_ids: List[str],
                article_id_batch_size: int = 100,
                row_batch_size: int = 1000,
            ) -> List[dict]:
                """Fetch links in small ID batches and avoid PostgREST's row cap."""
                all_rows: List[dict] = []
                for batch_start in range(
                    0,
                    len(article_ids),
                    article_id_batch_size,
                ):
                    article_id_batch = article_ids[
                        batch_start:batch_start + article_id_batch_size
                    ]
                    row_start = 0

                    while True:
                        batch_result = (
                            supabase.table("Article_Stock")
                            .select("article_id, stock_id")
                            .in_("article_id", article_id_batch)
                            .order("article_id", desc=False)
                            .order("stock_id", desc=False)
                            .range(
                                row_start,
                                row_start + row_batch_size - 1,
                            )
                            .execute()
                        )
                        rows = batch_result.data or []
                        all_rows.extend(rows)

                        if len(rows) < row_batch_size:
                            break
                        row_start += row_batch_size

                return all_rows

            page_size = 200
            cursor_time = None
            cursor_id = None

            stock_to_articles = defaultdict(list)
            selected_stock_ids: List[str] = []
            selected_stock_id_set = set()

            for _ in range(max_scan_pages):
                query = (
                    supabase.table("Article")
                    .select("id,title,time,sentiment")
                    .eq("article_type", "stock")
                    .not_.is_("time", "null")
                    .order("time", desc=True, nullsfirst=False)
                    .order("id", desc=True)
                    .limit(page_size)
                )

                if cursor_time is not None and cursor_id is not None:
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
                    break

                article_to_stock_ids = defaultdict(list)
                for row in fetch_article_stock_links(article_ids):
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
                    stock_ids = sorted(
                        article_to_stock_ids.get(article_id, []),
                        key=lambda stock_id: vn100_stock_symbol_map.get(
                            stock_id,
                            "",
                        ),
                    )

                    for stock_id in stock_ids:
                        if stock_id not in selected_stock_id_set:
                            if len(selected_stock_ids) >= stock_limit:
                                continue
                            selected_stock_ids.append(stock_id)
                            selected_stock_id_set.add(stock_id)

                        if len(stock_to_articles[stock_id]) < articles_per_stock:
                            stock_to_articles[stock_id].append(article)

                if len(selected_stock_ids) >= stock_limit:
                    break

                if len(article_rows) < page_size:
                    break

                last_row = article_rows[-1]
                cursor_time = last_row.get("time")
                cursor_id = last_row.get("id")
                if cursor_time is None or cursor_id is None:
                    break

            if not selected_stock_ids:
                return []

            profile_result = (
                supabase.table("BI_Profile")
                .select("stock_id, logo, company_name")
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
                .select("stock_id,price_change,per_price_change,current_price")
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

            def to_news_item(article: dict) -> dict:
                return {
                    "id": str(article.get("id") or ""),
                    "title": str(article.get("title") or ""),
                    "sentiment": (
                        str(article.get("sentiment"))
                        if article.get("sentiment") is not None
                        else None
                    ),
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
                        "PriceChange": to_float(price.get("price_change")),
                        "PerPriceChange": to_float(price.get("per_price_change")),
                        "CurrentPrice": to_float(price.get("current_price")),
                        "news": [
                            to_news_item(article=item)
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
