"""
News Database Service
Handles database operations for financial news
"""
import asyncio
from supabase import create_client, Client
from app.config import get_settings
from app.models.article_schema import ArticlesResponse
from typing import Optional, List
from datetime import datetime
settings = get_settings()
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
    def get_macro_articles(min_symbols: int = 5, limit: int = 50) -> List[ArticlesResponse]:
        try:
            min_symbols = max(1, min_symbols)
            limit = max(1, limit)

            result = supabase.rpc(
                "get_macro_articles",
                {"min_symbols": min_symbols, "lim": limit}
            ).execute()

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
        Category(id) -> Category_Stock(stock_id) -> Article_Stock(article_id) -> Article
        """
        try:
            limit = max(1, limit)


            # Step 1: Get all stock_ids linked to this category
            category_stock_result = (
                supabase.table("Category_Stock")
                .select("stock_id")
                .eq("category_id", category_id)
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
        try:
            result = (
                supabase.table("Article")
                .select("*")
                .execute()
            )

            if not result.data:
                return []
            
            # Bước 3: Lấy danh sách article_id từ kết quả trên
            article_ids = []
            article_map = {}
            for item in result.data:
                article_id = str(item.get("id") or "")
                if article_id:
                    article_ids.append(article_id)
                    article_map[article_id] = item

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
