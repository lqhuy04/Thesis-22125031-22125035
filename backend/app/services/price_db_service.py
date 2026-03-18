"""
Price Database Service
Handles database operations for historical stock prices (15m, 1h, 1d intervals)
"""
from supabase import create_client, Client
from app.config import settings
from typing import Optional, List, Dict, Any
from datetime import datetime

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

class PriceDBService:
    """Service for stock price database operations with different intervals"""
    
    @staticmethod
    def get_latest_trading_time(symbol: str, interval: str = "15m") -> Optional[datetime]:
        """
        Get the most recent trading time in the database for a given symbol and interval.
        """
        try:
            result = supabase.table(f"stock_prices_{interval}") \
                .select("trading_time") \
                .eq("symbol", symbol.upper()) \
                .order("trading_time", desc=True) \
                .limit(1) \
                .execute()
            
            if result.data and len(result.data) > 0:
                time_str = result.data[0]["trading_time"]
                # time_str could be ISO 8601 with or without suffix
                try:
                    # Remove Z and parse as naive datetime for easy comparison
                    clean_str = time_str.split('+')[0].replace('Z', '')
                    return datetime.fromisoformat(clean_str)
                except ValueError:
                    return datetime.strptime(time_str[:19], "%Y-%m-%dT%H:%M:%S")
            return None
        except Exception as e:
            print(f"Error fetching latest trading time for {symbol} ({interval}): {e}")
            return None

    @staticmethod
    def get_oldest_trading_time(symbol: str, interval: str = "15m") -> Optional[datetime]:
        """
        Get the oldest trading time in the database for a given symbol and interval.
        """
        try:
            result = supabase.table(f"stock_prices_{interval}") \
                .select("trading_time") \
                .eq("symbol", symbol.upper()) \
                .order("trading_time", desc=False) \
                .limit(1) \
                .execute()

            if result.data and len(result.data) > 0:
                time_str = result.data[0]["trading_time"]
                try:
                    clean_str = time_str.split('+')[0].replace('Z', '')
                    return datetime.fromisoformat(clean_str)
                except ValueError:
                    return datetime.strptime(time_str[:19], "%Y-%m-%dT%H:%M:%S")
            return None
        except Exception as e:
            print(f"Error fetching oldest trading time for {symbol} ({interval}): {e}")
            return None

    @staticmethod
    def insert_prices(prices: List[Dict[str, Any]], interval: str = "15m") -> bool:
        """
        Insert multiple price records into the database.
        prices should be a list of dictionaries with keys:
        symbol, trading_time, open, high, low, close, volume
        """
        if not prices:
            return True
            
        try:
            # Batch insert
            result = supabase.table(f"stock_prices_{interval}").upsert(prices).execute()
            return True
        except Exception as e:
            print(f"Error inserting prices for {interval}: {e}")
            return False

    @staticmethod
    def get_latest_prices(symbol: str, limit: int = 1000, interval: str = "15m") -> List[Dict[str, Any]]:
        """
        Retrieve the most recent N prices from the database for a specific symbol and interval.
        Ordered by trading_time ASC.
        """
        try:
            query = supabase.table(f"stock_prices_{interval}") \
                .select("symbol, trading_time, open, high, low, close, volume") \
                .eq("symbol", symbol.upper()) \
                .order("trading_time", desc=True) \
                .limit(limit)
            
            result = query.execute()
            data = result.data if result.data else []
            return list(reversed(data))
        except Exception as e:
            print(f"Error fetching latest prices for {symbol} ({interval}): {e}")
            return []

    @staticmethod
    def get_prices(
        symbol: str, 
        start_time: Optional[datetime] = None, 
        end_time: Optional[datetime] = None,
        interval: str = "15m"
    ) -> List[Dict[str, Any]]:
        """
        Retrieve historical prices from the database for a specific symbol.
        Ordered by trading_time ASC.
        """
        try:
            query = supabase.table(f"stock_prices_{interval}") \
                .select("symbol, trading_time, open, high, low, close, volume") \
                .eq("symbol", symbol.upper())
            
            if start_time:
                query = query.gte("trading_time", start_time.isoformat())
            if end_time:
                query = query.lte("trading_time", end_time.isoformat())
                
            query = query.order("trading_time", desc=False)
            
            result = query.execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Error fetching prices for {symbol} ({interval}): {e}")
            return []

    @staticmethod
    def prune_to_latest(symbol: str, limit: int = 1000, interval: str = "15m") -> bool:
        """
        Keep only the latest N records for a symbol and interval.
        """
        if limit <= 0:
            return True

        symbol_upper = symbol.upper()
        try:
            latest_rows = supabase.table(f"stock_prices_{interval}") \
                .select("trading_time") \
                .eq("symbol", symbol_upper) \
                .order("trading_time", desc=True) \
                .limit(limit) \
                .execute()

            if not latest_rows.data or len(latest_rows.data) < limit:
                return True

            cutoff = latest_rows.data[-1]["trading_time"]
            supabase.table(f"stock_prices_{interval}") \
                .delete() \
                .eq("symbol", symbol_upper) \
                .lt("trading_time", cutoff) \
                .execute()
            return True
        except Exception as e:
            print(f"Error pruning prices for {symbol_upper} ({interval}): {e}")
            return False
