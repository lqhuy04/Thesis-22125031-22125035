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
            time_str: Time string like "6 ngày trước", "Yesterday 23:10", "22/1 07:02"
            
        Returns:
            Parsed datetime or None
        """
        try:
            from datetime import datetime, timedelta
            
            time_str = time_str.strip()
            now = datetime.now()
            
            # Handle relative dates "X ngày/giờ/tuần trước"
            pattern = r'(\d+)\s*(phút|giờ|ngày|tuần|tháng|năm)\s*trước'
            match = re.search(pattern, time_str.lower())
            if match:
                value = int(match.group(1))
                unit = match.group(2)
                
                if unit == 'phút':
                    return now - timedelta(minutes=value)
                elif unit == 'giờ':
                    return now - timedelta(hours=value)
                elif unit == 'ngày':
                    return now - timedelta(days=value)
                elif unit == 'tuần':
                    return now - timedelta(weeks=value)
                elif unit == 'tháng':
                    return now - timedelta(days=value * 30)
                elif unit == 'năm':
                    return now - timedelta(days=value * 365)
            
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
            # Prepare data - only fields that exist in database
            data = {
                "title": news.title,
                "link": news.link,
                "stock_symbol": news.stock_symbol,
                "description": news.description,
                "time": news.time.isoformat() if news.time else None,
                "image_url": news.image_url,
                "content": news.content,
                "source": news.source,
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
            
            # Order by updated_at descending (newest first)
            query = query.order("updated_at", desc=True)
            
            # Apply pagination
            offset = (page - 1) * page_size
            query = query.range(offset, offset + page_size - 1)
            
            # Execute query
            result = query.execute()
            
            # Calculate pagination
            total = result.count if result.count else 0
            total_pages = (total + page_size - 1) // page_size
            
            # Convert to NewsResponse objects
            news_list = []
            if result.data:
                for item in result.data:
                    news_list.append(NewsResponse(**item))
            
            return {
                "items": news_list,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
            
        except Exception as e:
            print(f"Error getting news: {e}")
            import traceback
            traceback.print_exc()
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
                .order("updated_at", desc=True)\
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
