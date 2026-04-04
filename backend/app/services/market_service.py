"""
Price Database Service
Handles database operations for historical stock prices (15m, 1h, 1d intervals)
"""
import asyncio
import uuid
from supabase import create_client, Client
from app.config import settings
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
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
            result = supabase.table(f"Stock_Price_{interval}") \
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
    def _normalize_time(time_str: str) -> str:
        try:
            h, m, _ = time_str.split(":")
            return f"{h}:{m}:00"
        except Exception:
            return "00:00:00"
    
    @staticmethod
    def _time_to_minutes(t: str) -> int:
        h, m, _ = t.split(":")
        return int(h) * 60 + int(m)

    @staticmethod
    def _minutes_to_time(m: int) -> str:
        h = m // 60
        mm = m % 60
        return f"{h:02d}:{mm:02d}:00"

    @staticmethod
    def _build_allowed_times(interval: str) -> set:
        # Base timeline
        start = 9 * 60 + 15   # 09:15
        end = 14 * 60 + 30    # 14:30
        last = 14 * 60 + 45   # 14:45

        allowed = set()

        if interval == "1m":
            return None  # không cần filter

        if interval.endswith("m"):
            step = int(interval.replace("m", ""))

            # special case 30m
            if step == 30:
                start = 9 * 60 + 30  # 09:30

            cur = start
            while cur <= end:
                allowed.add(cur)
                cur += step

            # luôn include 14:45 nếu có trong yêu cầu
            if step in [5, 15]:
                allowed.add(last)

        elif interval == "1h":
            cur = 10 * 60  # 10:00
            while cur <= 14 * 60:
                allowed.add(cur)
                cur += 60

        return allowed
    
    

    @staticmethod
    def _get_clean_intraday_ohlc(
        symbol: str,
        from_date: str,
        from_time: str,
        interval: str,
        to_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:

        today = date.today().strftime("%d/%m/%Y")
        ssi_service = get_ssi_service()
        result = ssi_service.get_intraday_ohlc(
            symbol=symbol,
            from_date=from_date,
            to_date=to_date or today,
            page_size=9999
        )

        if not (result["success"] and result["data"]["data"]):
            return []

        data = result["data"]["data"]

        # normalize time
        for record in data:
            if "Time" in record and record["Time"]:
                record["Time"] = MarketService._normalize_time(record["Time"])
        

        # build from_datetime
        from_dt = None
        if from_date and from_time:
            from_dt = datetime.strptime(
                f"{from_date} {from_time}",
                "%d/%m/%Y %H:%M:%S"
            )
    
        allowed = MarketService._build_allowed_times(interval)

        filtered = []
        for record in data:
            t = record.get("Time")
            d = record.get("TradingDate")

            if not t or not d:
                continue

            # parse record datetime
            try:
                record_dt = datetime.strptime(
                    f"{d} {t}",
                    "%d/%m/%Y %H:%M:%S"
                )
            except Exception:
                continue

            # filter theo from_datetime (strict >)
            if from_dt and record_dt <= from_dt:
                continue

            # filter theo interval (nếu không phải 1m)
            if allowed is not None:
                minutes = MarketService._time_to_minutes(t)
                if minutes not in allowed:
                    continue

            filtered.append(record)

        return filtered
    
    def _ssi_item_to_db_record(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert SSI candle format into DB row format."""
        from datetime import datetime

        trading_date = item.get("TradingDate")
        if not trading_date:
            return None

        trading_time = item.get("Time")
        try:
            dt_obj = datetime.strptime(f"{trading_date} {trading_time}", "%d/%m/%Y %H:%M:%S")
        except ValueError:
            return None

        return {
            "symbol": item.get("Symbol").upper(),
            "trading_time": dt_obj.isoformat(),
            "open": float(item.get("Open")  or 0),
            "high": float(item.get("High")  or 0),
            "low": float(item.get("Low")  or 0),
            "close": float(item.get("Close")  or 0),
            "volume": float(item.get("Volume")  or 0),
        }
        
    @staticmethod
    def _insert_prices(prices: List[Dict[str, Any]], interval: str = "15m") -> bool:
        """
        Insert multiple price records into the database.
        prices should be a list of dictionaries with keys:
        symbol, trading_time, open, high, low, close, volume
        """
        if not prices:
            return True
            
        try:
            # Batch insert
            result = supabase.table(f"Stock_Price_{interval}").upsert(prices).execute()
            return True
        except Exception as e:
            print(f"Error inserting prices for {interval}: {e}")
            return False
        
        
    @staticmethod
    def update_price_data_for_symbol_with_time_interval(
        symbol: str, 
        limit: int = 1050, 
        interval: str = "15m"
    ) -> bool:
        try:
            latest_time = MarketService._get_latest_trading_time(symbol, interval)

            # =========================
            # CASE 1: chưa có data
            # =========================
            if latest_time is None:
                all_data: list = []
                cursor_to = date.today()

                while len(all_data) < limit:
                    cursor_from = cursor_to - timedelta(days=30)

                    batch = MarketService._get_clean_intraday_ohlc(
                        symbol=symbol,
                        from_date=cursor_from.strftime("%d/%m/%Y"),
                        to_date=cursor_to.strftime("%d/%m/%Y"),
                        from_time="00:00:00",
                        interval=interval
                    )

                    if not batch:
                        break

                    # prepend (giữ thứ tự thời gian)
                    all_data = batch + all_data

                    print(f"Fetched batch of {len(batch)} records for {symbol} ({interval}) from {cursor_from.strftime("%d/%m/%Y")} to {cursor_to.strftime("%d/%m/%Y")}, total so far: {len(all_data)}")
                    # lùi tiếp
                    cursor_to = cursor_from - timedelta(days=1)  # tránh trùng ngày
                    
                # lấy đúng limit bản ghi mới nhất
                result_data = all_data[-limit:] if len(all_data) > limit else all_data
                
                
                upload_data = []
                for result in result_data:
                    record = MarketService._ssi_item_to_db_record(result)
                    if record:
                        upload_data.append(record)

                if  upload_data:
                    MarketService._insert_prices(upload_data, interval=interval)
                    
                return True

            # =========================
            # CASE 2: đã có data
            # =========================
            formatted_date = latest_time.strftime("%d/%m/%Y")
            formatted_time = latest_time.strftime("%H:%M:%S")

            result_data = MarketService._get_clean_intraday_ohlc(
                symbol=symbol,
                from_date=formatted_date,
                to_date=date.today().strftime("%d/%m/%Y"),
                from_time=formatted_time,
                interval=interval
            )
            
            upload_data = []
            for result in result_data:
                record = MarketService._ssi_item_to_db_record(result)
                if record:
                    upload_data.append(record)

            if  upload_data:
                MarketService._insert_prices(upload_data, interval=interval)

            return True

        except Exception as e:
            print(f"Error fetching current stock price for {symbol}: {e}")
            return False
        
    @staticmethod
    def get_stock_price_by_interval(symbol: str, interval: str = "15m") -> List[Dict[str, Any]]:
        """
        Retrieve all prices from the database for a specific symbol and interval.
        Ordered by trading_time ASC using pagination.
        """
        try:
            all_data = []
            page_size = 1000
            start = 0

            while True:
                response = supabase.table(f"Stock_Price_{interval}") \
                    .select("symbol, trading_time, open, high, low, close, volume") \
                    .eq("symbol", symbol.upper()) \
                    .order("trading_time", desc=False) \
                    .range(start, start + page_size - 1) \
                    .execute()

                data = response.data or []

                if not data:
                    break

                all_data.extend(data)

                # Nếu số record trả về < page_size → đã hết data
                if len(data) < page_size:
                    break

                start += page_size

            return all_data

        except Exception as e:
            print(f"Error fetching prices for {symbol} ({interval}): {e}")
            return []
        
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
        
