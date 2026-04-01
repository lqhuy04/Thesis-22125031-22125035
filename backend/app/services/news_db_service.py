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
import unicodedata

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
    def _normalize_text(value: str) -> str:
        """Normalize text for case-insensitive and accent-insensitive matching."""
        base = str(value or "").strip().lower()
        if not base:
            return ""
        normalized = unicodedata.normalize("NFD", base)
        no_accents = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
        return no_accents

    @staticmethod
    def _resolve_category_ids(
        category_input: str,
        allow_token_substring: bool = False,
    ) -> List[str]:
        """Resolve category IDs from either category id or category name.

        - Strict mode: exact id/name and full-phrase substring (accent-insensitive).
        - Loose mode: additionally allows token-based substring matching.
        """
        raw_value = str(category_input or "").strip()
        if not raw_value:
            return []

        categories_result = (
            supabase.table("Category")
            .select("id, category_name")
            .execute()
        )
        if not categories_result.data:
            return []

        wanted_raw = raw_value.lower()
        wanted_norm = NewsDBService._normalize_text(raw_value)
        wanted_keywords = [
            NewsDBService._normalize_text(keyword)
            for keyword in NewsDBService._build_category_keywords(raw_value)
            if NewsDBService._normalize_text(keyword)
        ]
        matched_ids: List[str] = []

        for row in categories_result.data:
            cat_id = str(row.get("id") or "").strip()
            cat_name = str(row.get("category_name") or "").strip()
            if not cat_id:
                continue

            if cat_id.lower() == wanted_raw:
                matched_ids.append(cat_id)
                continue

            if cat_name.lower() == wanted_raw:
                matched_ids.append(cat_id)
                continue

            cat_name_norm = NewsDBService._normalize_text(cat_name)
            if cat_name_norm == wanted_norm:
                matched_ids.append(cat_id)
                continue

            # Strict phrase-level matching to avoid noisy matches like "hang" -> "cang hang khong".
            if wanted_norm and wanted_norm in cat_name_norm:
                matched_ids.append(cat_id)
                continue

            if allow_token_substring and any(keyword in cat_name_norm for keyword in wanted_keywords):
                matched_ids.append(cat_id)

        # Deduplicate while preserving order.
        return list(dict.fromkeys(matched_ids))

    @staticmethod
    def _get_news_sync(stock_symbol: Optional[str] = None, limit: Optional[int] = None) -> List[NewsResponse]:
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

                articles = []
                seen_ids = set()
                for item in result.data:
                    article = item.get("Article")
                    if not article:
                        continue
                    article_id = str(article.get("id") or "")
                    if article_id and article_id in seen_ids:
                        continue
                    if article_id:
                        seen_ids.add(article_id)
                    try:
                        articles.append(NewsResponse(**article))
                    except Exception:
                        continue

                articles.sort(key=lambda item: item.time or datetime.min, reverse=True)
                if limit is not None:
                    return articles[: max(1, limit)]
                return articles

            else:
                query = supabase.table("Article").select("*").order("time", desc=True)
                if limit is not None:
                    query = query.limit(max(1, limit))
                result = query.execute()
                return [NewsResponse(**item) for item in result.data] if result.data else []

        except Exception as e:
            print(f"Error getting news: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def get_news(stock_symbol: Optional[str] = None, limit: Optional[int] = None) -> List[NewsResponse]:
        """Async wrapper for fetching news using thread pool to avoid blocking event loop."""
        return await asyncio.to_thread(NewsDBService._get_news_sync, stock_symbol, limit)

    @staticmethod
    def _get_news_by_categories_sync(categories: List[str], limit: int = 100) -> List[NewsResponse]:
        """Get news by category names, sorted by latest publication time."""
        try:
            limit = max(1, limit)
            requested_categories = [str(c or "").strip() for c in categories if str(c or "").strip()]
            if not requested_categories:
                return []

            requested_keywords: List[str] = []
            for category in requested_categories:
                for keyword in NewsDBService._build_category_keywords(category):
                    keyword_norm = NewsDBService._normalize_text(keyword)
                    if keyword_norm:
                        requested_keywords.append(keyword_norm)
            requested_keywords = list(dict.fromkeys(requested_keywords))

            stock_ids_set = set()

            # Priority 1: match by BI_Profile.industry_name substring (map by stock industry).
            stock_profile_result = (
                supabase.table("Stock")
                .select("id, BI_Profile(industry_name)")
                .execute()
            )

            for stock_row in (stock_profile_result.data or []):
                stock_id = str(stock_row.get("id") or "").strip()
                if not stock_id:
                    continue

                profiles = stock_row.get("BI_Profile") or []
                if not isinstance(profiles, list):
                    continue

                matched = False
                for profile in profiles:
                    industry_name = str((profile or {}).get("industry_name") or "").strip()
                    if not industry_name:
                        continue
                    industry_norm = NewsDBService._normalize_text(industry_name)
                    if any(keyword in industry_norm for keyword in requested_keywords):
                        matched = True
                        break

                if matched:
                    stock_ids_set.add(stock_id)

            # Priority 2 (fallback/extension): resolve categories and include mapped stocks.
            matched_category_ids = set()
            for category in requested_categories:
                resolved_ids = NewsDBService._resolve_category_ids(
                    category,
                    allow_token_substring=True,
                )
                for resolved_id in resolved_ids:
                    matched_category_ids.add(resolved_id)

            if matched_category_ids:
                category_stock_result = (
                    supabase.table("Category_Stock")
                    .select("stock_id")
                    .in_("category_id", list(matched_category_ids))
                    .execute()
                )
                for row in (category_stock_result.data or []):
                    stock_id = str(row.get("stock_id") or "").strip()
                    if stock_id:
                        stock_ids_set.add(stock_id)

            stock_ids = list(stock_ids_set)
            if not stock_ids:
                return []

            links_result = (
                supabase.table("Article_Stock")
                .select("article_id")
                .in_("stock_id", stock_ids)
                .execute()
            )
            if not links_result.data:
                return []

            article_ids = list({
                str(row.get("article_id") or "").strip()
                for row in links_result.data
                if row.get("article_id")
            })
            if not article_ids:
                return []

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

            articles: List[NewsResponse] = []
            for item in articles_result.data:
                try:
                    articles.append(NewsResponse(**item))
                except Exception:
                    continue

            return articles
        except Exception as e:
            print(f"Error getting news by categories: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def get_news_by_categories(categories: List[str], limit: int = 100) -> List[NewsResponse]:
        """Async wrapper to fetch news by category names."""
        return await asyncio.to_thread(
            NewsDBService._get_news_by_categories_sync,
            categories,
            limit,
        )

    @staticmethod
    def _get_news_grouped_by_category_names_sync(
        categories: List[str],
        limit_per_category: int = 3,
    ) -> List[Dict]:
        """Get latest news grouped by input keywords.

        Pipeline per keyword:
        1) Find categories whose names contain the keyword (accent-insensitive substring).
        2) Map to stocks via Category_Stock.
        3) Fetch latest related news via Article_Stock -> Article.
        """
        try:
            limit_per_category = max(1, limit_per_category)
            requested_keywords = [str(c or "").strip() for c in categories if str(c or "").strip()]
            if not requested_keywords:
                return []

            categories_result = (
                supabase.table("Category")
                .select("id, category_name")
                .execute()
            )
            category_rows = categories_result.data or []
            if not category_rows:
                return []

            result: List[Dict] = []
            for keyword in requested_keywords:
                keyword_norm = NewsDBService._normalize_text(keyword)
                keyword_tokens = [
                    token
                    for token in re.split(r"\s+", keyword_norm)
                    if len(token) >= 2
                ]

                matched_category_ids: List[str] = []
                for row in category_rows:
                    category_id = str(row.get("id") or "").strip()
                    category_name = str(row.get("category_name") or "").strip()
                    if not category_id or not category_name:
                        continue

                    category_name_norm = NewsDBService._normalize_text(category_name)
                    phrase_match = bool(keyword_norm and keyword_norm in category_name_norm)
                    token_match = bool(keyword_tokens and all(token in category_name_norm for token in keyword_tokens))
                    if phrase_match or token_match:
                        matched_category_ids.append(category_id)

                matched_category_ids = list(dict.fromkeys(matched_category_ids))
                if not matched_category_ids:
                    result.append(
                        {
                            "category_id": keyword,
                            "category_name": keyword,
                            "news": [],
                        }
                    )
                    continue

                category_stock_result = (
                    supabase.table("Category_Stock")
                    .select("stock_id")
                    .in_("category_id", matched_category_ids)
                    .execute()
                )
                stock_ids = list({
                    str(row.get("stock_id") or "").strip()
                    for row in (category_stock_result.data or [])
                    if row.get("stock_id")
                })

                if not stock_ids:
                    result.append(
                        {
                            "category_id": keyword,
                            "category_name": keyword,
                            "news": [],
                        }
                    )
                    continue

                links_result = (
                    supabase.table("Article_Stock")
                    .select("article_id")
                    .in_("stock_id", stock_ids)
                    .execute()
                )
                article_ids = list({
                    str(row.get("article_id") or "").strip()
                    for row in (links_result.data or [])
                    if row.get("article_id")
                })

                if not article_ids:
                    result.append(
                        {
                            "category_id": keyword,
                            "category_name": keyword,
                            "news": [],
                        }
                    )
                    continue

                articles_result = (
                    supabase.table("Article")
                    .select("*")
                    .in_("id", article_ids)
                    .order("time", desc=True)
                    .limit(limit_per_category)
                    .execute()
                )

                news_items: List[NewsResponse] = []
                for item in (articles_result.data or []):
                    try:
                        news_items.append(NewsResponse(**item))
                    except Exception:
                        continue

                result.append(
                    {
                        "category_id": keyword,
                        "category_name": keyword,
                        "news": news_items,
                    }
                )

            return result
        except Exception as e:
            print(f"Error getting grouped news by category names: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def get_news_grouped_by_category_names(
        categories: List[str],
        limit_per_category: int = 3,
    ) -> List[Dict]:
        """Async wrapper to fetch grouped news for explicit category names."""
        return await asyncio.to_thread(
            NewsDBService._get_news_grouped_by_category_names_sync,
            categories,
            limit_per_category,
        )

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
    def _get_news_by_category_id_sync(category_id: str, limit: int = 100) -> List[NewsResponse]:
        """
        Get news for a specific category by ID.
        Category(id) -> Category_Stock(stock_id) -> Article_Stock(article_id) -> Article
        """
        try:
            limit = max(1, limit)

            resolved_ids = NewsDBService._resolve_category_ids(
                category_id,
                allow_token_substring=False,
            )
            if not resolved_ids:
                return []

            # Step 1: Get all stock_ids linked to this category
            category_stock_result = (
                supabase.table("Category_Stock")
                .select("stock_id")
                .in_("category_id", resolved_ids)
                .execute()
            )
            if not category_stock_result.data:
                return []

            stock_ids = list({
                str(row["stock_id"])
                for row in category_stock_result.data
                if row.get("stock_id")
            })
            if not stock_ids:
                return []

            # Step 2: Get all article_ids linked to these stocks
            links_result = (
                supabase.table("Article_Stock")
                .select("article_id")
                .in_("stock_id", stock_ids)
                .execute()
            )
            if not links_result.data:
                return []

            article_ids = list({
                str(row["article_id"])
                for row in links_result.data
                if row.get("article_id")
            })
            if not article_ids:
                return []

            # Step 3: Fetch articles, sorted by time desc
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

            articles: List[NewsResponse] = []
            for item in articles_result.data:
                try:
                    articles.append(NewsResponse(**item))
                except Exception:
                    continue

            return articles

        except Exception as e:
            print(f"Error getting news by category_id={category_id}: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def get_news_by_category_id(category_id: str, limit: int = 100) -> List[NewsResponse]:
        """Async wrapper to fetch news by category ID."""
        return await asyncio.to_thread(
            NewsDBService._get_news_by_category_id_sync,
            category_id,
            limit,
        )

    @staticmethod
    def _get_news_grouped_by_top_categories_sync(
        top_n: int = 3,
        limit_per_category: int = 3
    ) -> List[Dict]:
        """Get top N categories by stock count, with latest news for each."""
        try:
            # Step 1: Get all Category_Stock links to count stocks per category
            category_stock_result = (
                supabase.table("Category_Stock")
                .select("category_id, stock_id")
                .execute()
            )
            if not category_stock_result.data:
                return []

            # Count stocks per category
            category_stock_count: Dict[str, set] = {}
            for row in category_stock_result.data:
                cat_id = str(row.get("category_id") or "")
                stock_id = str(row.get("stock_id") or "")
                if cat_id and stock_id:
                    category_stock_count.setdefault(cat_id, set()).add(stock_id)

            # Pick top N categories by stock count
            top_category_ids = sorted(
                category_stock_count.keys(),
                key=lambda cid: len(category_stock_count[cid]),
                reverse=True
            )[:top_n]

            if not top_category_ids:
                return []

            # Step 2: Fetch category names
            categories_result = (
                supabase.table("Category")
                .select("id, category_name")
                .in_("id", top_category_ids)
                .execute()
            )
            category_map = {
                str(row["id"]): row["category_name"]
                for row in (categories_result.data or [])
                if row.get("id") and row.get("category_name")
            }

            # Step 3: For each top category, get stock_ids -> article_ids -> latest articles
            result = []
            for cat_id in top_category_ids:
                cat_name = category_map.get(cat_id, "")
                stock_ids = list(category_stock_count[cat_id])

                # Get article_ids linked to these stocks
                links_result = (
                    supabase.table("Article_Stock")
                    .select("article_id")
                    .in_("stock_id", stock_ids)
                    .execute()
                )
                if not links_result.data:
                    result.append({
                        "category_id": cat_id,
                        "category_name": cat_name,
                        "news": []
                    })
                    continue

                article_ids = list({
                    str(row["article_id"])
                    for row in links_result.data
                    if row.get("article_id")
                })

                # Fetch latest N articles
                articles_result = (
                    supabase.table("Article")
                    .select("*")
                    .in_("id", article_ids)
                    .order("time", desc=True)
                    .limit(limit_per_category)
                    .execute()
                )

                news_items = []
                for item in (articles_result.data or []):
                    try:
                        news_items.append(NewsResponse(**item))
                    except Exception:
                        continue

                result.append({
                    "category_id": cat_id,
                    "category_name": cat_name,
                    "news": news_items
                })

            return result

        except Exception as e:
            print(f"Error getting news by top categories: {e}")
            import traceback
            traceback.print_exc()
            return []


    async def get_news_grouped_by_top_categories(
        top_n: int = 3,
        limit_per_category: int = 3
    ) -> List[Dict]:
        """Async wrapper."""
        return await asyncio.to_thread(
            NewsDBService._get_news_grouped_by_top_categories_sync,
            top_n,
            limit_per_category,
        )