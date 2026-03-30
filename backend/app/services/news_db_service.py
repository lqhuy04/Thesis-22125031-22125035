"""
News Database Service
Handles database operations for financial news
"""
import asyncio
from supabase import create_client, Client
from app.config import get_settings
from app.models.news_schemas import NewsCreate, NewsResponse
from typing import Optional, List, Dict
from datetime import datetime
import re

settings = get_settings()
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


class NewsDBService:
    """Service for news database operations"""

    @staticmethod
    def _build_category_keywords(category: str) -> List[str]:
        """Build keyword list from a category phrase for fuzzy word matching."""
        normalized = str(category or "").strip().lower()
        if not normalized:
            return []
        tokens = [token for token in re.split(r"\s+", normalized) if token]
        # Keep phrase and meaningful tokens (avoid 1-char noise).
        keywords = [normalized]
        keywords.extend([token for token in tokens if len(token) >= 2])
        return list(dict.fromkeys(keywords))

    @staticmethod
    def _get_news_sync(stock_symbol: Optional[str] = None) -> List[NewsResponse]:
        try:
            if stock_symbol:
                # Bước 1: Lấy stock_id từ bảng Stock theo symbol
                stock_result = (
                    supabase.table("Stock")
                    .select("id")
                    .eq("stock_symbol", stock_symbol.upper())
                    .execute()
                )

                if not stock_result.data:
                    return []

                stock_id = stock_result.data[0]["id"]

                # Bước 2: FK join Article_Stock → Article, filter theo stock_id
                result = (
                    supabase.table("Article_Stock")
                    .select("Article(*)")
                    .eq("stock_id", stock_id)
                    .execute()
                )

                if not result.data:
                    return []

                return [
                    NewsResponse(**item["Article"])
                    for item in result.data
                    if item.get("Article")
                ]

            else:
                result = supabase.table("Article").select("*").execute()
                return [NewsResponse(**item) for item in result.data] if result.data else []

        except Exception as e:
            print(f"Error getting news: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def get_news(stock_symbol: Optional[str] = None) -> List[NewsResponse]:
        """Async wrapper for fetching news using thread pool to avoid blocking event loop."""
        return await asyncio.to_thread(NewsDBService._get_news_sync, stock_symbol)

    async def get_latest_news(stock_symbol: str, limit: int = 2) -> List[NewsResponse]:
        """Get latest N news items for a stock symbol."""
        try:
            articles = await NewsDBService.get_news(stock_symbol=stock_symbol.upper())
            if not articles:
                return []

            # Sort by publication time descending, fallback to minimum for missing timestamps.
            articles_sorted = sorted(
                articles,
                key=lambda item: item.time or datetime.min,
                reverse=True,
            )
            return articles_sorted[: max(0, limit)]
        except Exception as e:
            print(f"Error getting latest news for {stock_symbol}: {e}")
            return []

    @staticmethod
    def _get_latest_news_for_symbols_sync(symbols: List[str], limit: int = 2) -> Dict[str, List[NewsResponse]]:
        """Batch fetch latest news per symbol to avoid N+1 database queries."""
        try:
            symbols_upper = [s.strip().upper() for s in symbols if s and s.strip()]
            result_map: Dict[str, List[NewsResponse]] = {s: [] for s in symbols_upper}
            if not symbols_upper:
                return result_map

            # Resolve symbol -> stock_id
            stocks_result = (
                supabase.table("Stock")
                .select("id, stock_symbol")
                .in_("stock_symbol", symbols_upper)
                .execute()
            )
            if not stocks_result.data:
                return result_map

            symbol_to_stock_id: Dict[str, str] = {}
            stock_id_to_symbol: Dict[str, str] = {}
            for row in stocks_result.data:
                symbol = str(row.get("stock_symbol") or "").upper().strip()
                stock_id = str(row.get("id") or "").strip()
                if symbol and stock_id:
                    symbol_to_stock_id[symbol] = stock_id
                    stock_id_to_symbol[stock_id] = symbol

            stock_ids = list(stock_id_to_symbol.keys())
            if not stock_ids:
                return result_map

            links_result = (
                supabase.table("Article_Stock")
                .select("stock_id, Article(*)")
                .in_("stock_id", stock_ids)
                .execute()
            )
            if not links_result.data:
                return result_map

            grouped: Dict[str, List[NewsResponse]] = {s: [] for s in symbols_upper}
            for row in links_result.data:
                stock_id = str(row.get("stock_id") or "").strip()
                symbol = stock_id_to_symbol.get(stock_id)
                article = row.get("Article")
                if not symbol or not article:
                    continue
                try:
                    grouped[symbol].append(NewsResponse(**article))
                except Exception:
                    continue

            for symbol in symbols_upper:
                items = grouped.get(symbol, [])
                items.sort(key=lambda item: item.time or datetime.min, reverse=True)
                result_map[symbol] = items[: max(0, limit)]

            return result_map
        except Exception as e:
            print(f"Error getting latest news for symbols: {e}")
            return {s.strip().upper(): [] for s in symbols if s and s.strip()}

    async def get_latest_news_for_symbols(symbols: List[str], limit: int = 2) -> Dict[str, List[NewsResponse]]:
        """Async wrapper for batch latest news retrieval by symbol list."""
        return await asyncio.to_thread(NewsDBService._get_latest_news_for_symbols_sync, symbols, limit)

    @staticmethod
    def _get_macro_news_sync(min_symbols: int = 3, limit: int = 50) -> List[NewsResponse]:
        """Get news items linked to at least `min_symbols` distinct stock symbols."""
        try:
            min_symbols = max(1, min_symbols)
            limit = max(1, limit)

            link_rows = (
                supabase.table("Article_Stock")
                .select("article_id, stock_id, Stock(stock_symbol)")
                .execute()
            )

            if not link_rows.data:
                return []

            article_to_stock_ids: Dict[str, set] = {}
            for row in link_rows.data:
                article_id = row.get("article_id")
                stock_id = row.get("stock_id")

                if not article_id or not stock_id:
                    continue

                if article_id not in article_to_stock_ids:
                    article_to_stock_ids[article_id] = set()

                article_to_stock_ids[article_id].add(str(stock_id))

            matched_article_ids = [
                article_id
                for article_id, stock_ids in article_to_stock_ids.items()
                if len(stock_ids) >= min_symbols
            ]

            if not matched_article_ids:
                return []

            article_rows = (
                supabase.table("Article")
                .select("*")
                .in_("id", matched_article_ids)
                .execute()
            )

            if not article_rows.data:
                return []

            macro_items: List[NewsResponse] = []
            for article in article_rows.data:
                article_id = str(article.get("id", ""))
                impacted_count = len(article_to_stock_ids.get(article_id, set()))

                if impacted_count < min_symbols:
                    continue

                try:
                    macro_items.append(NewsResponse(**article))
                except Exception:
                    continue

            macro_items.sort(key=lambda item: item.time or datetime.min, reverse=True)
            return macro_items[:limit]
        except Exception as e:
            print(f"Error getting macro news: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def get_macro_news(min_symbols: int = 3, limit: int = 50) -> List[NewsResponse]:
        """Async wrapper for macro-impact news query."""
        return await asyncio.to_thread(NewsDBService._get_macro_news_sync, min_symbols, limit)

    @staticmethod
    def _get_news_by_categories_sync(categories: List[str], limit: int = 100) -> List[NewsResponse]:
        """
        Get news linked to symbols whose BI_Profile.industry_name matches provided categories.

        Matching is case-insensitive substring against industry_name.
        """
        try:
            normalized_categories = [c.strip().lower() for c in categories if c and c.strip()]
            if not normalized_categories:
                return []

            category_keywords = {
                category: NewsDBService._build_category_keywords(category)
                for category in normalized_categories
            }

            limit = max(1, limit)

            # Load stock + profile once, then filter in Python to avoid brittle embedded filters.
            stocks_result = (
                supabase.table("Stock")
                .select("id, BI_Profile(industry_name)")
                .execute()
            )

            if not stocks_result.data:
                return []

            matched_stock_ids: set[str] = set()
            for row in stocks_result.data:
                stock_id = row.get("id")
                profiles = row.get("BI_Profile") or []
                industry_name = ""
                if profiles and isinstance(profiles, list):
                    industry_name = str((profiles[0] or {}).get("industry_name") or "")
                industry_name_lower = industry_name.lower()

                if not stock_id or not industry_name_lower:
                    continue

                is_match = False
                for category in normalized_categories:
                    keywords = category_keywords.get(category, [])
                    if any(keyword in industry_name_lower for keyword in keywords):
                        is_match = True
                        break

                if is_match:
                    matched_stock_ids.add(str(stock_id))

            if not matched_stock_ids:
                return []

            links_result = (
                supabase.table("Article_Stock")
                .select("article_id, stock_id")
                .in_("stock_id", list(matched_stock_ids))
                .execute()
            )

            if not links_result.data:
                return []

            matched_article_ids = list({str(row.get("article_id")) for row in links_result.data if row.get("article_id")})
            if not matched_article_ids:
                return []

            article_rows = (
                supabase.table("Article")
                .select("*")
                .in_("id", matched_article_ids)
                .execute()
            )

            if not article_rows.data:
                return []

            articles: List[NewsResponse] = []
            for item in article_rows.data:
                try:
                    articles.append(NewsResponse(**item))
                except Exception:
                    continue

            articles.sort(key=lambda item: item.time or datetime.min, reverse=True)
            return articles[:limit]

        except Exception as e:
            print(f"Error getting news by categories: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def get_news_by_categories(categories: List[str], limit: int = 100) -> List[NewsResponse]:
        """Async wrapper to fetch news by industry categories of symbols."""
        return await asyncio.to_thread(NewsDBService._get_news_by_categories_sync, categories, limit)

    async def get_news_by_category(category: str, limit: int = 100) -> List[NewsResponse]:
        """Get news list for a single category phrase."""
        return await NewsDBService.get_news_by_categories([category], limit=limit)

    @staticmethod
    def _get_news_grouped_by_categories_sync(categories: List[str], limit_per_category: int = 100) -> Dict[str, List[NewsResponse]]:
        """Get grouped news mapping: category -> list of related news."""
        try:
            original_categories = [c.strip() for c in categories if c and c.strip()]
            grouped: Dict[str, List[NewsResponse]] = {category: [] for category in original_categories}
            if not original_categories:
                return grouped

            limit_per_category = max(1, limit_per_category)

            category_to_keywords = {
                category: NewsDBService._build_category_keywords(category)
                for category in original_categories
            }

            stocks_result = (
                supabase.table("Stock")
                .select("id, BI_Profile(industry_name)")
                .execute()
            )
            if not stocks_result.data:
                return grouped

            category_to_stock_ids: Dict[str, set] = {category: set() for category in original_categories}
            all_stock_ids: set[str] = set()

            for row in stocks_result.data:
                stock_id = row.get("id")
                profiles = row.get("BI_Profile") or []
                industry_name = ""
                if profiles and isinstance(profiles, list):
                    industry_name = str((profiles[0] or {}).get("industry_name") or "")
                industry_name_lower = industry_name.lower()

                if not stock_id or not industry_name_lower:
                    continue

                stock_id_str = str(stock_id)
                for category in original_categories:
                    keywords = category_to_keywords.get(category, [])
                    if any(keyword in industry_name_lower for keyword in keywords):
                        category_to_stock_ids[category].add(stock_id_str)
                        all_stock_ids.add(stock_id_str)

            if not all_stock_ids:
                return grouped

            links_result = (
                supabase.table("Article_Stock")
                .select("article_id, stock_id")
                .in_("stock_id", list(all_stock_ids))
                .execute()
            )
            if not links_result.data:
                return grouped

            category_to_article_ids: Dict[str, set] = {category: set() for category in original_categories}
            all_article_ids: set[str] = set()

            for row in links_result.data:
                article_id = row.get("article_id")
                stock_id = row.get("stock_id")
                if not article_id or not stock_id:
                    continue
                article_id_str = str(article_id)
                stock_id_str = str(stock_id)

                for category in original_categories:
                    if stock_id_str in category_to_stock_ids[category]:
                        category_to_article_ids[category].add(article_id_str)
                        all_article_ids.add(article_id_str)

            if not all_article_ids:
                return grouped

            article_rows = (
                supabase.table("Article")
                .select("*")
                .in_("id", list(all_article_ids))
                .execute()
            )
            if not article_rows.data:
                return grouped

            article_map: Dict[str, NewsResponse] = {}
            for item in article_rows.data:
                try:
                    news_item = NewsResponse(**item)
                    article_map[str(news_item.id)] = news_item
                except Exception:
                    continue

            for category in original_categories:
                articles = [
                    article_map[article_id]
                    for article_id in category_to_article_ids[category]
                    if article_id in article_map
                ]
                articles.sort(key=lambda item: item.time or datetime.min, reverse=True)
                grouped[category] = articles[:limit_per_category]

            return grouped
        except Exception as e:
            print(f"Error getting grouped news by categories: {e}")
            import traceback
            traceback.print_exc()
            return {c.strip(): [] for c in categories if c and c.strip()}

    async def get_news_grouped_by_categories(categories: List[str], limit_per_category: int = 100) -> Dict[str, List[NewsResponse]]:
        """Async wrapper for grouped category news."""
        return await asyncio.to_thread(
            NewsDBService._get_news_grouped_by_categories_sync,
            categories,
            limit_per_category,
        )