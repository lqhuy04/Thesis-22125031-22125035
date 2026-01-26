"""
News Database Service
Handles database operations for financial news
"""
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
    def parse_time_to_datetime(time_str: str) -> Optional[datetime]:
        """
        Parse Vietnamese time string to datetime
        
        Args:
            time_str: Time string like "Yesterday 23:10", "Hôm qua 23:10", "22/1 07:02"
            
        Returns:
            Parsed datetime or None
        """
        try:
            from datetime import datetime, timedelta
            
            time_str = time_str.strip()
            now = datetime.now()
            
            # Handle "Yesterday" or "Hôm qua"
            if "Yesterday" in time_str or "Hôm qua" in time_str:
                time_part = time_str.split()[-1]  # Get "23:10"
                hour, minute = map(int, time_part.split(':'))
                yesterday = now - timedelta(days=1)
                return yesterday.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # Handle "DD/M HH:MM" format (e.g., "22/1 07:02")
            if '/' in time_str and ' ' in time_str:
                date_part, time_part = time_str.split(' ')
                day, month = map(int, date_part.split('/'))
                hour, minute = map(int, time_part.split(':'))
                year = now.year
                # If month is in the future, it's from last year
                if month > now.month:
                    year -= 1
                return datetime(year, month, day, hour, minute)
            
            return None
        except Exception as e:
            print(f"Error parsing time '{time_str}': {e}")
            return None
    
    @staticmethod
    async def create_news(news: NewsCreate) -> Optional[NewsResponse]:
        """
        Create a new news entry (with duplicate prevention via UNIQUE constraint on link)
        
        Args:
            news: News data to insert
            
        Returns:
            Created news response or None if duplicate
        """
        try:
            # Parse published_at if not provided
            published_at = news.published_at
            if not published_at and news.time:
                published_at = NewsDBService.parse_time_to_datetime(news.time)
            
            # Prepare data
            data = {
                "title": news.title,
                "link": news.link,
                "stock_symbol": news.stock_symbol,
                "description": news.description,
                "time": news.time,
                "image_url": news.image_url,
                "published_at": published_at.isoformat() if published_at else None,
                "content": news.content,  # Already a dict/JSONB structure
                "author": news.author,
                "article_images": news.article_images if news.article_images else [],
                "tags": news.tags if news.tags else [],
                "source": news.source if news.source else "StockBiz",
                "is_content_extracted": news.is_content_extracted if news.is_content_extracted is not None else False
            }
            
            # Insert (will fail silently if duplicate link)
            result = supabase.table("financial_news").insert(data).execute()
            
            if result.data and len(result.data) > 0:
                return NewsResponse(**result.data[0])
            return None
            
        except Exception as e:
            # Duplicate key will raise exception - this is expected
            if "duplicate key" in str(e).lower() or "unique constraint" in str(e).lower():
                return None
            print(f"Error creating news: {e}")
            return None
    
    @staticmethod
    async def bulk_create_news(news_list: List[NewsCreate]) -> Dict[str, int]:
        """
        Bulk insert news items (skips duplicates)
        
        Args:
            news_list: List of news to insert
            
        Returns:
            Dictionary with created and skipped counts
        """
        created = 0
        skipped = 0
        
        for news in news_list:
            result = await NewsDBService.create_news(news)
            if result:
                created += 1
            else:
                skipped += 1
        
        return {"created": created, "skipped": skipped}
    
    @staticmethod
    async def get_news(
        page: int = 1,
        page_size: int = 20,
        stock_symbol: Optional[str] = None,
        search: Optional[str] = None
    ) -> Dict:
        """
        Get news with pagination and filters
        
        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            stock_symbol: Filter by stock symbol
            search: Search in title and description
            
        Returns:
            Dictionary with news data and pagination info
        """
        try:
            # Build query
            query = supabase.table("financial_news").select("*", count="exact")
            
            # Apply filters
            if stock_symbol:
                query = query.eq("stock_symbol", stock_symbol.upper())
            
            if search:
                # Search in title or description
                query = query.or_(f"title.ilike.%{search}%,description.ilike.%{search}%")
            
            # Order by created_at descending (newest first)
            query = query.order("created_at", desc=True)
            
            # Apply pagination
            offset = (page - 1) * page_size
            query = query.range(offset, offset + page_size - 1)
            
            # Execute query
            result = query.execute()
            
            # Calculate pagination
            total = result.count if result.count else 0
            total_pages = (total + page_size - 1) // page_size
            
            news_list = [NewsResponse(**item) for item in result.data] if result.data else []
            
            return {
                "items": news_list,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
            
        except Exception as e:
            print(f"Error getting news: {e}")
            return {
                "items": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0
            }
    
    @staticmethod
    async def get_latest_news_link() -> Optional[str]:
        """
        Get the link of the most recently crawled news
        
        Returns:
            Latest news link or None
        """
        try:
            result = supabase.table("financial_news")\
                .select("link")\
                .order("created_at", desc=True)\
                .limit(1)\
                .execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]["link"]
            return None
            
        except Exception as e:
            print(f"Error getting latest news link: {e}")
            return None
    
    @staticmethod
    async def get_news_by_id(news_id: str) -> Optional[NewsResponse]:
        """
        Get a single news item by ID
        
        Args:
            news_id: News UUID
            
        Returns:
            News response or None
        """
        try:
            result = supabase.table("financial_news")\
                .select("*")\
                .eq("id", news_id)\
                .single()\
                .execute()
            
            if result.data:
                return NewsResponse(**result.data)
            return None
            
        except Exception as e:
            print(f"Error getting news by ID: {e}")
            return None
