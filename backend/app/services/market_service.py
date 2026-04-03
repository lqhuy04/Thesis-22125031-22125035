"""
Price Database Service
Handles database operations for historical stock prices (15m, 1h, 1d intervals)
"""
import uuid
from supabase import create_client, Client
from app.config import settings
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.services.ssi_service import get_ssi_service
from datetime import date, datetime


supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

class MarketService:
    """Service for stock price database operations with different intervals"""
    
    def __init__(self):
        pass
    
    @staticmethod
    def _get_latest_trading_time(symbol: str, interval: str = "15m") -> Optional[datetime]:
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
    def search_stock_by_symbol(symbol: str) -> Dict[str, Any]:
        try:
            query = supabase.table("BI_Profile") \
                .select("stock_id, symbol, company_name, exchange") \
                .eq("symbol", symbol.upper())
            
            result = query.execute()
            data = result.data if result.data else []

            if len(data) == 0:
                return {}

            stock = data[0]  # ✅ Get the first matching record
            
            return {
                "stock_id": stock['stock_id'],
                "symbol": stock['symbol'],
                "company_name": stock['company_name'],
            }
        except Exception as e:
            print(f"Error search stock: {e}")
            return {}
            
    @staticmethod
    def get_stock_price_by_interval(symbol: str, limit: int = 1000, interval: str = "15m") -> List[Dict[str, Any]]:
        """
        Retrieve the most recent N prices from the database for a specific symbol and interval.
        Ordered by trading_time ASC.
        """
        try:
            query = supabase.table(f"stock_prices_{interval}") \
                .select("symbol, trading_time, open, high, low, close, volume") \
                .eq("symbol", symbol.upper()) \
                .order("trading_time", desc=False) \
                .limit(limit)
            
            result = query.execute()
            data = result.data if result.data else []
            return data
        except Exception as e:
            print(f"Error fetching latest prices for {symbol} ({interval}): {e}")
            return []
        
    @staticmethod
    def update_price_data_for_symbol_with_time_interval(symbol: str, limit: int = 1050, interval: str = "15m") -> bool:
        try:
            ssi_service = get_ssi_service()
            latest_time = MarketService._get_latest_trading_time(symbol, interval)
            
            print(f"Latest trading time for {symbol} ({interval}): {latest_time}")
            
            today = date.today().strftime("%d/%m/%Y")
            result = ssi_service.get_intraday_ohlc(symbol=symbol, from_date="04/03/2026", to_date="03/04/2026", page_size=9999)
            print(result)
            
            return True
            
        except Exception as e:
            print(f"Error fetching current stock price for {symbol}: {e}")
            return False
        
    @staticmethod
    def get_current_stock_price(symbol: str) -> Dict[str, Any]:
        try:
            query = supabase.table("BI_Profile") \
                .select("stock_id, symbol, company_name, exchange") \
                .eq("symbol", symbol.upper())
            
            result = query.execute()
            data = result.data if result.data else []

            if len(data) == 0:
                return {}

            stock = data[0]  # ✅ Get the first matching record

            ssi_service = get_ssi_service()
            today = date.today().strftime("%d/%m/%Y")
            result = ssi_service.get_daily_stock_price(
                symbol=stock['symbol'],  # ✅ Index into the dict, not the list
                from_date=today,
                to_date=today,
                market=stock['exchange'].lower()
            )
            
            filtered=[]
            if result["success"] and result["data"]["data"]:
                filtered = [
                    record for record in result["data"]["data"]
                    if record.get("Symbol", "").upper() == symbol.upper()
                ]
                
            if len(filtered) == 0:
                return {}
                
            price = filtered[0]
            
            return {
                "stock_id": stock['stock_id'],
                "symbol": stock['symbol'],
                "company_name": stock['company_name'],
                "exchange": stock['exchange'],
                "PriceChange": price['PriceChange'],
                "PerPriceChange": price['PerPriceChange'],
                "CeilingPrice": price['CeilingPrice'],
                "FloorPrice": price['FloorPrice'],
                "RefPrice": price['RefPrice'],
                "CurrentPrice": price['ClosePrice']
            }
        except Exception as e:
            print(f"Error fetching current stock price for {symbol}: {e}")
            return {}
        
    @staticmethod
    def get_market_index(index_id: str) -> List[Dict[str, Any]]:
        try:
            ssi_service = get_ssi_service()
            today = date.today().strftime("%d/%m/%Y")
            
            result = ssi_service.get_daily_index(
                request_id=str(uuid.uuid4()),
                from_date=today,
                to_date=today,
                index_id=index_id
            )
            
            return result['data'][0] if result["success"] and result["data"] else {}
        except Exception as e:
            print(f"Error fetching market index: {e}")
            return {}
        

        
    
    
    

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
