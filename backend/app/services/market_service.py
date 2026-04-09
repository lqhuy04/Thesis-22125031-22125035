"""
Price Database Service
Handles database operations for historical stock prices (15m, 1h, 1d intervals)
"""
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
    
    def get_last_trading_day(now):
        if now.hour < 9 or (now.hour == 9 and now.minute < 15):
            now = now - timedelta(days=1)

        # Nếu rơi vào cuối tuần thì lùi tiếp
        while now.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
            now -= timedelta(days=1)

        return now
    
    @staticmethod
    def _parse_interval_minutes(interval: str) -> int:
        """'1m'->1, '5m'->5, '15m'->15, '30m'->30, '1h'->60"""
        if interval.endswith("h"):
            return int(interval.replace("h", "")) * 60
        return int(interval.replace("m", ""))
    
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
    def _get_clean_intraday_ohlc(
        symbol: str,
        from_date: str,
        from_time: str,
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

            filtered.append(record)

        return filtered
    
    @staticmethod
    def _resample_to_interval(
        candles_1m: List[Dict[str, Any]],
        interval: str
    ) -> List[Dict[str, Any]]:
        """
        Aggregate 1m candles into target interval candles.
        OPEN=first, HIGH=max, LOW=min, CLOSE=last, VOL=sum
        """
        if not candles_1m:
            return []

        interval_minutes = MarketService._parse_interval_minutes(interval)
        if interval_minutes == 1:
            return candles_1m

        def get_bucket(dt: datetime) -> Optional[datetime]:
            if interval_minutes == 30:
                morning_start = 9 * 60 + 30
            elif interval_minutes == 60:
                morning_start = 10 * 60
            else:
                morning_start = 9 * 60 + 15
            
            SESSION_ANCHORS = [
                (morning_start, 11 * 60 + 30),
                (13 * 60,       14 * 60 + 45),
            ]
            
            total_minutes = dt.hour * 60 + dt.minute
            for session_start, session_end in SESSION_ANCHORS:
                if session_start <= total_minutes <= session_end:
                    offset = (total_minutes - session_start) // interval_minutes
                    bucket_minutes = session_start + offset * interval_minutes
                    return dt.replace(
                        hour=bucket_minutes // 60,
                        minute=bucket_minutes % 60,
                        second=0,
                        microsecond=0
                    )
            return None

        # Group candles by (symbol, date, bucket)
        buckets: Dict[tuple, List[Dict]] = {}
        for c in candles_1m:
            try:
                dt = datetime.fromisoformat(c["trading_time"])
            except Exception:
                continue

            bucket_dt = get_bucket(dt)
            if bucket_dt is None:
                continue

            key = (c["symbol"], bucket_dt)
            buckets.setdefault(key, []).append(c)

        # Aggregate
        result = []
        for (symbol, bucket_dt), group in sorted(buckets.items(), key=lambda x: x[0][1]):
            result.append({
                "symbol": symbol,
                "trading_time": bucket_dt.isoformat(),
                "open":   group[0]["open"],
                "high":   max(c["high"]   for c in group),
                "low":    min(c["low"]    for c in group),
                "close":  group[-1]["close"],
                "volume": sum(c["volume"] for c in group),
            })

        return result
    
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
    def _trim_to_limit(symbol: str, interval: str, limit: int = 1050) -> None:
        """Xóa các record cũ nhất, chỉ giữ lại `limit` record mới nhất."""
        try:
            # Lấy trading_time của record thứ `limit` từ mới nhất
            cutoff_result = supabase.table(f"Stock_Price_{interval}") \
                .select("trading_time") \
                .eq("symbol", symbol.upper()) \
                .order("trading_time", desc=True) \
                .limit(1) \
                .offset(limit) \
                .execute()

            if not cutoff_result.data:
                return  # Tổng số record <= limit, không cần xóa

            cutoff_time = cutoff_result.data[0]["trading_time"]

            # Xóa tất cả record có trading_time <= cutoff_time
            supabase.table(f"Stock_Price_{interval}") \
                .delete() \
                .eq("symbol", symbol.upper()) \
                .lte("trading_time", cutoff_time) \
                .execute()

            print(f"[{symbol}|{interval}] Trimmed records older than {cutoff_time}")

        except Exception as e:
            print(f"[{symbol}|{interval}] Error trimming records: {e}")
        
    
        
    @staticmethod
    def update_price_data_for_symbol_with_time_interval(
        symbol: str,
        limit: int = 350,
        interval: str = "15m"
    ) -> bool:
        try:
            interval_minutes = MarketService._parse_interval_minutes(interval)
            latest_time = MarketService._get_latest_trading_time(symbol, interval)

            # =========================
            # CASE 1: chưa có data → fetch đủ 1050 nến interval
            # =========================
            if latest_time is None:
                all_1m: List[Dict] = []
                cursor_to = MarketService.get_last_trading_day(datetime.now())
                resampled = []

                while len(resampled) < limit:
                    cursor_from = cursor_to - timedelta(days=30)

                    batch = MarketService._get_clean_intraday_ohlc(
                        symbol=symbol,
                        from_date=cursor_from.strftime("%d/%m/%Y"),
                        to_date=cursor_to.strftime("%d/%m/%Y"),
                        from_time="00:00:00",
                    )

                    if not batch:
                        # Không còn data nữa → dừng, insert những gì có
                        print(f"[{symbol}|{interval}] No more data available, stopping at {len(resampled)} candles")
                        break

                    # Prepend batch mới vào
                    all_1m = batch + all_1m

                    # Convert & resample toàn bộ để đếm chính xác
                    candles_1m = [
                        r for r in (MarketService._ssi_item_to_db_record(x) for x in all_1m)
                        if r
                    ]
                    resampled = MarketService._resample_to_interval(candles_1m, interval)

                    print(
                        f"[{symbol}|{interval}] 1m={len(all_1m)} → resampled={len(resampled)}/{limit}"
                        f" | window {cursor_from:%d/%m/%Y}→{cursor_to:%d/%m/%Y}"
                    )

                    cursor_to = cursor_from - timedelta(days=1)

                # Lấy đúng limit bản ghi mới nhất
                upload_data = resampled[-limit:] if len(resampled) > limit else resampled

            # =========================
            # CASE 2: đã có data → chỉ fetch delta, recalc bucket đang mở
            # =========================
            else:
                # Lùi về đầu bucket hiện tại để recalculate bucket đang mở
                bucket_start_minute = (latest_time.hour * 60 + latest_time.minute) // interval_minutes * interval_minutes
                bucket_start = latest_time.replace(
                    hour=bucket_start_minute // 60,
                    minute=bucket_start_minute % 60,
                    second=0,
                    microsecond=0
                )
                # Lấy 1 phút trước bucket_start để filter > bucket_start - 1m
                from_dt = bucket_start - timedelta(minutes=1)

                raw_1m = MarketService._get_clean_intraday_ohlc(
                    symbol=symbol,
                    from_date=from_dt.strftime("%d/%m/%Y"),
                    to_date=date.today().strftime("%d/%m/%Y"),
                    from_time=from_dt.strftime("%H:%M:%S"),
                )

                candles_1m = [
                    r for r in (MarketService._ssi_item_to_db_record(x) for x in raw_1m)
                    if r
                ]

                upload_data = MarketService._resample_to_interval(candles_1m, interval)

            if upload_data:
                MarketService._insert_prices(upload_data, interval=interval)
                print(f"[{symbol}|{interval}] Inserted {len(upload_data)} candles")

            MarketService._trim_to_limit(symbol, interval, limit)

            return True

        except Exception as e:
            print(f"Error updating {symbol} ({interval}): {e}")
            return False
    
    @staticmethod
    def get_stock_price_by_interval(symbol: str, interval: str = "15m") -> List[Dict[str, Any]]:
        """
        Retrieve all prices from the database for a specific symbol and interval.
        Ordered by trading_time ASC using pagination.
        """
        try:
            response = supabase.table(f"Stock_Price_{interval}") \
                    .select("symbol, trading_time, open, high, low, close, volume") \
                    .eq("symbol", symbol.upper()) \
                    .order("trading_time", desc=False) \
                    .execute()
                    
            result = response.data if response.data else []
            return result

        except Exception as e:
            print(f"Error fetching prices for {symbol} ({interval}): {e}")
            return []
        
    @staticmethod
    def search_stock(keyword: str) -> List[Dict[str, Any]]:
        try:
            keyword = keyword.strip()

            if not keyword:
                return []

            query = supabase.table("BI_Profile") \
                .select("stock_id, symbol, company_name, exchange") \
                .or_(
                    f"symbol.ilike.%{keyword}%,company_name.ilike.%{keyword}%"
                )

            result = query.execute()
            data = result.data if result.data else []

            return [
                {
                    "stock_id": stock["stock_id"],
                    "symbol": stock["symbol"],
                    "company_name": stock["company_name"],
                    "exchange": stock["exchange"],
                }
                for stock in data
                if len(stock["symbol"]) <= 3   # ✅ filter tại đây
            ]

        except Exception as e:
            print(f"Error search stock: {e}")
            return []
        
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
            today = MarketService.get_last_trading_day(datetime.now()).strftime("%d/%m/%Y")
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
                "PriceChange": float(price['PriceChange']),
                "PerPriceChange": float(price['PerPriceChange']),
                "CeilingPrice": float(price['CeilingPrice']),
                "FloorPrice": float(price['FloorPrice']),
                "RefPrice": float(price['RefPrice']),
                "CurrentPrice": float(price['ClosePrice'])
            }
        except Exception as e:
            print(f"Error fetching current stock price for {symbol}: {e}")
            return {}
        
    @staticmethod
    def get_market_index(index_id: str) -> List[Dict[str, Any]]:
        try:
            ssi_service = get_ssi_service()
            today = MarketService.get_last_trading_day(datetime.now()).strftime("%d/%m/%Y")
            
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
        
