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
    
    async def get_news(stock_symbol: Optional[str] = None) -> List[NewsResponse]:
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