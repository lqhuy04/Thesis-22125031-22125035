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
    
    async def get_news(stock_symbol: str) -> List[Dict]:
        """
        Lấy tất cả bài báo liên quan đến một mã chứng khoán cụ thể.
        
        Args:
            stock_symbol: Mã chứng khoán (ví dụ: 'AAPL')
            
        Returns:
            Danh sách các bài báo (Article) liên quan
        """
        try:
            # Sử dụng dấu '!' để thực hiện inner join thông qua bảng trung gian Article_Stock
            # Chúng ta lọc ở bảng 'Stock' dựa trên 'stock_symbol' 
            # và lấy dữ liệu từ bảng 'Article'
            result = supabase.table("Article_Stock") \
                .select("""
                    Article(*),
                    Stock!inner(stock_symbol)
                """) \
                .eq("Stock.stock_symbol", stock_symbol.upper()) \
                .execute()

            # Dữ liệu trả về từ Supabase khi join thường nằm trong list lồng nhau
            # Chúng ta cần bóc tách để lấy danh sách Article phẳng
            articles = []
            if result.data:
                # result.data sẽ có dạng: [{"Article": {...}}, {"Article": {...}}]
                articles = [NewsResponse(**item["Article"]) for item in result.data if item.get("Article")]

            return articles

        except Exception as e:
            print(f"Error getting news for {stock_symbol}: {e}")
            return []