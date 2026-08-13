"""
News Database Service
Handles database operations for financial news
"""
import requests
from supabase import create_client, Client
from app.config import settings
from app.models.article_schema import ArticleListItemResponse, ArticlesResponse
from app.utils.market_index import get_index_stocks
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
        limit: int = 50,
        offset: int = 0,
    ) -> List[ArticleListItemResponse]:
        """
        Return stock-type articles ordered from newest to oldest.
        """
        try:
            normalized_limit = max(1, limit)
            normalized_offset = max(0, offset)

            article_result = (
                supabase.table("Article")
                .select(ARTICLE_LIST_FIELDS)
                .eq("article_type", "stock")
                .order("time", desc=True, nullsfirst=False)
                .order("id", desc=True)
                .range(
                    normalized_offset,
                    normalized_offset + normalized_limit - 1,
                )
                .execute()
            )

            return ArticlesService._to_list_items(article_result.data or [])

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
        Return random VN100 stocks with up to N latest related articles each.
        """
        try:
            from collections import defaultdict
            import random

            stock_limit = max(1, stock_limit)
            articles_per_stock = max(1, articles_per_stock)

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

            selected_stock_ids = random.sample(
                list(vn100_stock_symbol_map),
                k=min(stock_limit, len(vn100_stock_symbol_map)),
            )

            articles_result = supabase.rpc(
                "get_latest_articles_for_stocks",
                {
                    "p_stock_ids": selected_stock_ids,
                    "p_articles_per_stock": articles_per_stock,
                },
            ).execute()

            stock_to_articles = defaultdict(list)
            for article in articles_result.data or []:
                stock_id = str(article.get("stock_id") or "")
                if stock_id in vn100_stock_symbol_map:
                    stock_to_articles[stock_id].append(article)

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
