"""
Price Database Service
Handles database operations for historical stock prices (15m, 1h, 1d intervals)
"""
from supabase import create_client, Client
from app.config import settings
from collections import Counter
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from app.services.ssi_service import get_ssi_service
from datetime import date, datetime
import time
import pandas as pd
from datetime import time as dtime
from typing import List, Dict, Any


supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

class MarketService:
    """Service for stock price database operations with different intervals"""
    
    def __init__(self):
        pass

    @staticmethod
    def get_all_symbols() -> List[str]:
        """Return all stock symbols from DB in ascending order."""
        try:
            page_size = 1000
            offset = 0
            symbols: List[str] = []

            while True:
                result = supabase.table("Stock") \
                    .select("stock_symbol") \
                    .order("stock_symbol", desc=False) \
                    .range(offset, offset + page_size - 1) \
                    .execute()

                data = result.data if result.data else []
                if not data:
                    break

                symbols.extend(
                    row["stock_symbol"]
                    for row in data
                    if row.get("stock_symbol")
                )

                if len(data) < page_size:
                    break

                offset += page_size

            return symbols
        except Exception as e:
            print(f"Error fetching all symbols: {e}")
            return []
    
    def get_last_trading_day(now):
        if now.hour < 9 or (now.hour == 9 and now.minute < 15):
            now = now - timedelta(days=1)

        # Nếu rơi vào cuối tuần thì lùi tiếp
        while now.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
            now -= timedelta(days=1)

        return now
    
    @staticmethod
    def _parse_interval_minutes(interval: str) -> int:
        """'1m'->1, '5m'->5, '15m'->15, '30m'->30, '1h'->60, '1d'->1440, '1w'->10080, '1M'->43200"""
        if interval.endswith("h"):
            return int(interval.replace("h", "")) * 60
        if interval == "1d":
            return 1440
        if interval == "1w":
            return 10080
        if interval == "1M":
            return 43200
        return int(interval.replace("m", ""))
    
    @staticmethod
    def _is_daily_based_interval(interval: str) -> bool:
        return interval in ("1d", "1w", "1M")
        
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
    def _get_clean_daily_ohlc(
        symbol: str,
        from_date: str,
        from_trading_time: Optional[datetime] = None,
        to_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Gọi get_daily_ohlc, trả về list record raw (chưa convert sang DB format).
        Lọc strict > from_trading_time nếu có.
        """
        today = date.today().strftime("%d/%m/%Y")
        ssi_service = get_ssi_service()
        result = ssi_service.get_daily_ohlc(
            symbol=symbol,
            from_date=from_date,
            to_date=to_date or today,
            page_size=9999
        )

        if not (result["success"] and result["data"]["data"]):
            return []

        data = result["data"]["data"]

        if from_trading_time is None:
            return data

        filtered = []
        for record in data:
            d = record.get("TradingDate")
            if not d:
                continue
            try:
                # Daily candle mặc định 14:45:00
                record_dt = datetime.strptime(f"{d} 14:45:00", "%d/%m/%Y %H:%M:%S")
            except Exception:
                continue
            if record_dt <= from_trading_time:
                continue
            filtered.append(record)

        return filtered
    
    @staticmethod
    def _resample_to_interval(
        candles: List[Dict[str, Any]],
        interval: str
    ) -> List[Dict[str, Any]]:
        """
        Aggregate candles into target interval.
        - Intraday (1m→5m/15m/30m/1h): dùng session bucket như cũ
        - Daily-based (1d→1w, 1d→1M): aggregate theo tuần/tháng
        - 1d: trả thẳng, không cần resample
        OPEN=first, HIGH=max, LOW=min, CLOSE=last, VOL=sum
        """
        if not candles:
            return []

        # ── 1d: không cần resample, trả thẳng ──────────────────────────────────
        if interval == "1d":
            return candles

        # ── 1w / 1M: aggregate daily candles theo tuần / tháng ─────────────────
        if interval in ("1w", "1M"):
            def get_daily_bucket(dt: datetime) -> datetime:
                if interval == "1w":
                    # Bucket = thứ Hai đầu tuần
                    return (dt - timedelta(days=dt.weekday())).replace(
                        hour=14, minute=45, second=0, microsecond=0
                    )
                else:  # "1M"
                    # Bucket = ngày đầu tháng
                    return dt.replace(
                        day=1, hour=14, minute=45, second=0, microsecond=0
                    )

            buckets: Dict[tuple, List[Dict]] = {}
            for c in candles:
                try:
                    dt = datetime.fromisoformat(c["trading_time"])
                except Exception:
                    continue
                bucket_dt = get_daily_bucket(dt)
                key = (c["symbol"], bucket_dt)
                buckets.setdefault(key, []).append(c)

            result = []
            for (symbol, bucket_dt), group in sorted(buckets.items(), key=lambda x: x[0][1]):
                result.append({
                    "symbol":       symbol,
                    "trading_time": bucket_dt.isoformat(),
                    "open":         group[0]["open"],
                    "high":         max(c["high"]   for c in group),
                    "low":          min(c["low"]    for c in group),
                    "close":        group[-1]["close"],
                    "volume":       sum(c["volume"] for c in group),
                })
            return result

        # ── Intraday: logic bucket session như cũ ──────────────────────────────
        interval_minutes = MarketService._parse_interval_minutes(interval)
        if interval_minutes == 1:
            return candles

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

        buckets: Dict[tuple, List[Dict]] = {}
        for c in candles:
            try:
                dt = datetime.fromisoformat(c["trading_time"])
            except Exception:
                continue
            bucket_dt = get_bucket(dt)
            if bucket_dt is None:
                continue
            key = (c["symbol"], bucket_dt)
            buckets.setdefault(key, []).append(c)

        result = []
        for (symbol, bucket_dt), group in sorted(buckets.items(), key=lambda x: x[0][1]):
            result.append({
                "symbol":       symbol,
                "trading_time": bucket_dt.isoformat(),
                "open":         group[0]["open"],
                "high":         max(c["high"]   for c in group),
                "low":          min(c["low"]    for c in group),
                "close":        group[-1]["close"],
                "volume":       sum(c["volume"] for c in group),
            })
        return result
    
    def _ssi_item_to_db_record(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert SSI candle format into DB row format."""
        from datetime import datetime

        trading_date = item.get("TradingDate")
        if not trading_date:
            return None

        trading_time = item.get("Time")

        # Daily OHLC trả về Time = null → mặc định 14:45:00
        if not trading_time:
            trading_time = "14:45:00"

        try:
            dt_obj = datetime.strptime(f"{trading_date} {trading_time}", "%d/%m/%Y %H:%M:%S")
        except ValueError:
            return None

        return {
            "symbol": item.get("Symbol").upper(),
            "trading_time": dt_obj.isoformat(),
            "open":   float(item.get("Open")   or 0),
            "high":   float(item.get("High")   or 0),
            "low":    float(item.get("Low")    or 0),
            "close":  float(item.get("Close")  or 0),
            "volume": float(item.get("Volume") or 0),
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
    def update_price_data_for_symbol(
        symbol: str,
        limit: int = 350,
    ) -> bool:
        try:
            print(f"\n===== START UPDATE {symbol} =====")

            intraday_intervals = ["1m", "5m", "15m", "30m", "1h"]
            daily_intervals = ["1d", "1w", "1M"]

            def to_db_records(raw):
                return [r for r in (MarketService._ssi_item_to_db_record(x) for x in raw) if r]

            # ─────────────────────────────────────────────
            # 1. INTRADAY
            # ─────────────────────────────────────────────
            print(f"[{symbol}] 🔄 Processing INTRADAY...")
            latest_1m = MarketService._get_latest_trading_time(symbol, "1m")
            print(f"[{symbol}] Latest 1m time: {latest_1m}")

            if latest_1m is None:
                print(f"[{symbol}] ⚠️ No existing intraday data → FULL FETCH")

                all_1m = []
                cursor_to = MarketService.get_last_trading_day(datetime.now())
                resampled_map = {i: [] for i in intraday_intervals}

                while any(len(resampled_map[i]) < limit for i in intraday_intervals):
                    cursor_from = cursor_to - timedelta(days=30)

                    print(f"[{symbol}] Fetch 1m: {cursor_from:%d/%m/%Y} → {cursor_to:%d/%m/%Y}")

                    batch = MarketService._get_clean_intraday_ohlc(
                        symbol=symbol,
                        from_date=cursor_from.strftime("%d/%m/%Y"),
                        to_date=cursor_to.strftime("%d/%m/%Y"),
                        from_time="00:00:00",
                    )

                    if not batch:
                        print(f"[{symbol}] ❌ No more 1m data")
                        break

                    print(f"[{symbol}] Fetched {len(batch)} rows")

                    all_1m = batch + all_1m
                    candles_1m = to_db_records(all_1m)

                    print(f"[{symbol}] Total 1m candles: {len(candles_1m)}")

                    for interval in intraday_intervals:
                        resampled = MarketService._resample_to_interval(candles_1m, interval)
                        resampled_map[interval] = resampled

                        print(
                            f"[{symbol}] Resampled {interval}: {len(resampled)}/{limit}"
                        )

                    cursor_to = cursor_from - timedelta(days=1)
                    time.sleep(1.1)

                for interval in intraday_intervals:
                    data = resampled_map[interval][-limit:]
                    if data:
                        print(f"[{symbol}] ✅ Insert {interval}: {len(data)} candles")
                        MarketService._insert_prices(data, interval=interval)
                        MarketService._trim_to_limit(symbol, interval, limit)

            else:
                print(f"[{symbol}] ⚡ Incremental intraday update")

                raw_1m = MarketService._get_clean_intraday_ohlc(
                    symbol=symbol,
                    from_date=latest_1m.strftime("%d/%m/%Y"),
                    to_date=date.today().strftime("%d/%m/%Y"),
                    from_time=latest_1m.strftime("%H:%M:%S"),
                )

                print(f"[{symbol}] Fetched delta 1m: {len(raw_1m)} rows")

                candles_1m = to_db_records(raw_1m)

                for interval in intraday_intervals:
                    data = MarketService._resample_to_interval(candles_1m, interval)
                    if data:
                        print(f"[{symbol}] ✅ Insert {interval}: {len(data)} candles")
                        MarketService._insert_prices(data, interval=interval)
                        MarketService._trim_to_limit(symbol, interval, limit)

            # ─────────────────────────────────────────────
            # 2. DAILY
            # ─────────────────────────────────────────────
            print(f"[{symbol}] 🔄 Processing DAILY...")
            latest_1d = MarketService._get_latest_trading_time(symbol, "1d")
            print(f"[{symbol}] Latest 1d time: {latest_1d}")

            if latest_1d is None:
                print(f"[{symbol}] ⚠️ No existing daily data → FULL FETCH")

                all_daily = []
                cursor_to = MarketService.get_last_trading_day(datetime.now())
                resampled_map = {i: [] for i in daily_intervals}

                while any(len(resampled_map[i]) < limit for i in daily_intervals):
                    cursor_from = cursor_to - timedelta(days=30)

                    print(f"[{symbol}] Fetch daily: {cursor_from:%d/%m/%Y} → {cursor_to:%d/%m/%Y}")

                    batch = MarketService._get_clean_daily_ohlc(
                        symbol=symbol,
                        from_date=cursor_from.strftime("%d/%m/%Y"),
                        to_date=cursor_to.strftime("%d/%m/%Y"),
                    )

                    if not batch:
                        print(f"[{symbol}] ❌ No more daily data")
                        break

                    print(f"[{symbol}] Fetched {len(batch)} rows")

                    all_daily = batch + all_daily
                    candles_1d = to_db_records(all_daily)

                    print(f"[{symbol}] Total 1d candles: {len(candles_1d)}")

                    for interval in daily_intervals:
                        resampled = MarketService._resample_to_interval(candles_1d, interval)
                        resampled_map[interval] = resampled

                        print(
                            f"[{symbol}] Resampled {interval}: {len(resampled)}/{limit}"
                        )

                    cursor_to = cursor_from - timedelta(days=1)
                    time.sleep(1.1)

                for interval in daily_intervals:
                    data = resampled_map[interval][-limit:]
                    if data:
                        print(f"[{symbol}] ✅ Insert {interval}: {len(data)} candles")
                        MarketService._insert_prices(data, interval=interval)
                        MarketService._trim_to_limit(symbol, interval, limit)

            else:
                print(f"[{symbol}] ⚡ Incremental daily update")

                raw_daily = MarketService._get_clean_daily_ohlc(
                    symbol=symbol,
                    from_date=latest_1d.strftime("%d/%m/%Y"),
                    from_trading_time=latest_1d,
                )

                print(f"[{symbol}] Fetched delta daily: {len(raw_daily)} rows")

                candles_1d = to_db_records(raw_daily)

                for interval in daily_intervals:
                    data = MarketService._resample_to_interval(candles_1d, interval)
                    if data:
                        print(f"[{symbol}] ✅ Insert {interval}: {len(data)} candles")
                        MarketService._insert_prices(data, interval=interval)
                        MarketService._trim_to_limit(symbol, interval, limit)

            print(f"===== DONE {symbol} =====\n")
            return True

        except Exception as e:
            print(f"[{symbol}] ❌ ERROR: {e}")
            return False
    
    # ──────────────────────────────────────────────────────────────────────────────
    # Mapping interval → (source_table, resample_rule, cutoff_time)
    # cutoff_time: cắt dữ liệu intraday đến giờ này (None = lấy hết)
    # ──────────────────────────────────────────────────────────────────────────────
    _INTRADAY_INTERVALS = {
        "1m":  ("Stock_Price_1m",  "1min",  None),
        "5m":  ("Stock_Price_1m",  "5min",  None),
        "15m": ("Stock_Price_1m",  "15min", None),
        "30m": ("Stock_Price_1m",  "30min", None),   # lấy đến 14:30
        "1h":  ("Stock_Price_1m",  "1h",    None),   # lấy đến 14:00
    }

    _DAILY_INTERVALS = {
        "1d": ("Stock_Price_1d", "1D",  None),
        "1w": ("Stock_Price_1d", "1W",  None),
        "1M": ("Stock_Price_1d", "1ME", None),   # pandas: month-end
    }


    @staticmethod
    def get_stock_price_by_interval(symbol: str, interval: str = "15m") -> List[Dict[str, Any]]:
        """
        Lấy dữ liệu OHLCV theo interval bằng cách aggregate từ dữ liệu gốc.

        Nguồn dữ liệu:
          - Bảng Stock_Price_1m → interval: 1m, 5m, 15m, 30m, 1h
          - Bảng Stock_Price_1d → interval: 1d, 1w, 1M
        """
        try:
            symbol_up = symbol.upper()

            if interval in MarketService._INTRADAY_INTERVALS:
                return MarketService._aggregate_from_1m(symbol_up, interval)
            elif interval in MarketService._DAILY_INTERVALS:
                return MarketService._aggregate_from_1d(symbol_up, interval)
            else:
                valid = list(MarketService._INTRADAY_INTERVALS) + list(MarketService._DAILY_INTERVALS)
                raise ValueError(f"Unsupported interval: '{interval}'. Valid: {valid}")

        except Exception as e:
            print(f"Error fetching prices for {symbol} ({interval}): {e}")
            return []

    # ──────────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _fetch_raw(table: str, symbol: str) -> pd.DataFrame:
        """
        Paginate qua Supabase để lấy TOÀN BỘ records (1000 rows/request).
        Trả về DataFrame index bởi trading_time ASC.
        """
        PAGE_SIZE = 1000
        all_rows: List[Dict] = []
        offset = 0

        while True:
            response = supabase.table(table) \
                .select("symbol, trading_time, open, high, low, close, volume") \
                .eq("symbol", symbol) \
                .order("trading_time", desc=False) \
                .range(offset, offset + PAGE_SIZE - 1) \
                .execute()

            rows = response.data or []
            all_rows.extend(rows)

            # Ít hơn PAGE_SIZE → đã đến trang cuối
            if len(rows) < PAGE_SIZE:
                break

            offset += PAGE_SIZE

        if not all_rows:
            return pd.DataFrame()

        df = pd.DataFrame(all_rows)
        df["trading_time"] = pd.to_datetime(df["trading_time"])
        df = df.set_index("trading_time")

        for col in ("open", "high", "low", "close", "volume"):
            df[col] = pd.to_numeric(df[col], errors="coerce")

        return df

    @staticmethod
    def _resample_ohlcv(df: pd.DataFrame, rule: str) -> pd.DataFrame:
        """Aggregate DataFrame OHLCV theo pandas resample rule."""
        return df.resample(rule, label="left", closed="left").agg(
            open=("open",     "first"),
            high=("high",     "max"),
            low=("low",       "min"),
            close=("close",   "last"),
            volume=("volume", "sum"),
        ).dropna(subset=["open"])   # bỏ nến rỗng (không có giao dịch)

    @staticmethod
    def _df_to_records(df: pd.DataFrame, symbol: str) -> List[Dict[str, Any]]:
        """Chuyển DataFrame về List[Dict] theo format chuẩn."""
        df = df.reset_index()
        df["trading_time"] = df["trading_time"].dt.strftime("%Y-%m-%dT%H:%M:%S")
        df["symbol"] = symbol
        return df[["symbol", "trading_time", "open", "high", "low", "close", "volume"]] \
            .to_dict(orient="records")

    @staticmethod
    def _aggregate_from_1m(symbol: str, interval: str) -> List[Dict[str, Any]]:
        """
        Fetch toàn bộ bảng 1m (paginate hết), sau đó:
        - interval == "1m" → trả thẳng toàn bộ (không resample)
        - còn lại          → resample + áp cutoff time nếu có
        """
        _, rule, cutoff = MarketService._INTRADAY_INTERVALS[interval]

        # Luôn paginate hết toàn bộ 1m dù interval là gì
        df = MarketService._fetch_raw("Stock_Price_1m", symbol)
        if df.empty:
            return []

        # 1m: trả thẳng toàn bộ, không resample
        if interval == "1m":
            return MarketService._df_to_records(df, symbol)

        # 5m, 15m, 30m, 1h: áp cutoff rồi resample
        if cutoff is not None:
            df = df[df.index.time <= cutoff]

        agg = MarketService._resample_ohlcv(df, rule)
        return MarketService._df_to_records(agg, symbol)

    @staticmethod
    def _aggregate_from_1d(symbol: str, interval: str) -> List[Dict[str, Any]]:
        """
        Fetch toàn bộ bảng 1d (paginate), sau đó:
          - interval == "1d" → trả thẳng toàn bộ records
          - còn lại          → resample (1w, 1M)
        """
        _, rule, _ = MarketService._DAILY_INTERVALS[interval]

        df = MarketService._fetch_raw("Stock_Price_1d", symbol)
        if df.empty:
            return []

        # 1d: không cần resample, trả toàn bộ
        if interval == "1d":
            return MarketService._df_to_records(df, symbol)

        agg = MarketService._resample_ohlcv(df, rule)
        return MarketService._df_to_records(agg, symbol)
    
    @staticmethod
    def get_priority(stock, keyword: str):
        symbol = stock["symbol"].lower()
        name = stock["company_name"].lower()
        kw = keyword.lower()

        if symbol.startswith(kw):
            return 1
        if kw in symbol:
            return 2
        if name.startswith(kw):
            return 3
        if kw in name:
            return 4
        return 5
        
    @staticmethod
    def search_stock(keyword: str) -> List[Dict[str, Any]]:
        try:
            keyword = keyword.strip()
            if not keyword:
                return []

            # Query 1: tìm stocks
            result = supabase.table("BI_Profile") \
                .select("stock_id, symbol, company_name, exchange, logo") \
                .or_(f"symbol.ilike.%{keyword}%,company_name.ilike.%{keyword}%") \
                .limit(50) \
                .execute()

            data = result.data or []

            filtered = [s for s in data if len(s["symbol"]) <= 3]
            if not filtered:
                return []

            # Query 2: batch lấy giá — thay vì N queries
            symbols = [s["symbol"] for s in filtered]
            price_result = supabase.table("Current_Stock_Price") \
                .select("symbol, current_price, price_change, per_price_change") \
                .in_("symbol", symbols) \
                .execute()

            price_map = {
                row["symbol"]: row
                for row in (price_result.data or [])
            }

            for stock in filtered:
                stock.update(price_map.get(stock["symbol"], {}))

            return sorted(filtered, key=lambda x: MarketService.get_priority(x, keyword))

        except Exception as e:
            print(f"Error search stock: {e}")
            return []
        
    @staticmethod
    def get_current_stock_price(symbol: str) -> Dict[str, Any]:
        try:
            query = supabase.table("BI_Profile") \
                .select("stock_id, symbol, company_name, exchange, logo") \
                .eq("symbol", symbol.upper())
            
            result = query.execute()
            data = result.data if result.data else []

            if len(data) == 0:
                return {}

            stock = data[0]  # ✅ Get the first matching record

            ###

            query2 = supabase.table("Current_Stock_Price") \
                .select("*") \
                .eq("symbol", symbol.upper())
            
            result2 = query2.execute()
            data2 = result2.data if result2.data else []

            if len(data2) == 0:
                return {}
            
            price = data2[0]
            
            return {
                "stock_id": stock['stock_id'],
                "symbol": stock['symbol'],
                "company_name": stock['company_name'],
                "exchange": stock['exchange'],
                "logo": stock['logo'],
                "PriceChange": price['price_change'],
                "PerPriceChange": price['per_price_change'],
                "CeilingPrice": price['ceiling_price'],
                "FloorPrice": price['floor_price'], 
                "RefPrice": price['ref_price'],
                "CurrentPrice": price['current_price'],
                "TotalMatchVol": price['total_match_vol'],
                "TotalMatchVal": price['total_match_val'],
            }
        except Exception as e:
            print(f"Error fetching current stock price for {symbol}: {e}")
            return {}

    @staticmethod
    def _to_float(value: Any) -> float:
        try:
            if value is None or value == "":
                return 0.0
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def get_industry_stocks_movement(
        industry: str,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get stock movement list for one industry, sorted by TotalMatchVal DESC.
        Data source is Current_Stock_Price table.
        Returns all stocks by default, or first `limit` stocks if provided.
        """
        try:
            keyword = (industry or "").strip()
            if not keyword:
                return {"items": []}

            profile_result = (
                supabase.table("BI_Profile")
                .select("stock_id, symbol, company_name, exchange, industry_name, logo")
                .ilike("industry_name", f"%{keyword}%")
                .execute()
            )

            profiles = profile_result.data if profile_result.data else []
            profiles = [
                p for p in profiles
                if p.get("symbol") and len(str(p.get("symbol"))) <= 3
            ]

            if not profiles:
                return {"items": []}

            profile_by_symbol: Dict[str, Dict[str, Any]] = {
                str(p.get("symbol", "")).upper(): p for p in profiles
                if p.get("symbol")
            }
            symbols = list(profile_by_symbol.keys())

            price_result = (
                supabase.table("Current_Stock_Price")
                .select(
                    "symbol, price_change, per_price_change, ceiling_price, floor_price, "
                    "ref_price, current_price, total_match_vol, total_match_val"
                )
                .in_("symbol", symbols)
                .execute()
            )

            prices = price_result.data if price_result.data else []

            items: List[Dict[str, Any]] = []
            for price in prices:
                symbol = str(price.get("symbol", "")).upper()
                profile = profile_by_symbol.get(symbol)
                if not profile:
                    continue

                items.append({
                    "stock_id": profile.get("stock_id") or "",
                    "symbol": symbol,
                    "company_name": profile.get("company_name") or "",
                    "logo": profile.get("logo") or "",
                    "exchange": profile.get("exchange") or "",
                    "PriceChange": MarketService._to_float(price.get("price_change")),
                    "PerPriceChange": MarketService._to_float(price.get("per_price_change")),
                    "CeilingPrice": MarketService._to_float(price.get("ceiling_price")),
                    "FloorPrice": MarketService._to_float(price.get("floor_price")),
                    "RefPrice": MarketService._to_float(price.get("ref_price")),
                    "CurrentPrice": MarketService._to_float(price.get("current_price")),
                    "TotalMatchVol": MarketService._to_float(price.get("total_match_vol")),
                    "TotalMatchVal": MarketService._to_float(price.get("total_match_val")),
                })

            items.sort(key=lambda x: x.get("TotalMatchVal", 0.0), reverse=True)

            if limit is not None:
                limit = max(limit, 1)
                items = items[:limit]

            return {"items": items}
        except Exception as e:
            print(f"Error fetching industry stocks movement for {industry}: {e}")
            return {"items": []}
        
    @staticmethod
    def get_market_index(index_id: str) -> Dict[str, Any]:
        try:
            result = (
                supabase
                .table("Current_Market_Index")
                .select("*")
                .eq("index_id", index_id)
                .single()
                .execute()
            )

            if not result.data:
                return {}

            row = result.data

            return {
                "IndexId":        row["index_id"],
                "IndexValue":     float(row["index_value"] or 0),
                "TradingDate":    row["trading_date"],
                "Time":           row["trading_time"],
                "Change":         float(row["change"] or 0),
                "RatioChange":    float(row["ratio_change"] or 0),
                "TotalTrade":     float(row["total_trade"] or 0),
                "TotalMatchVol":  float(row["total_match_vol"] or 0),
                "TotalMatchVal":  float(row["total_match_val"] or 0),
                "TypeIndex":      row["type_index"],
                "IndexName":      row["index_name"],
                "Advances":       float(row["advances"] or 0),
                "NoChanges":      float(row["no_changes"] or 0),
                "Declines":       float(row["declines"] or 0),
                "Ceilings":       float(row["ceilings"] or 0),
                "Floors":         float(row["floors"] or 0),
                "TotalDealVol":   float(row["total_deal_vol"] or 0),
                "TotalDealVal":   float(row["total_deal_val"] or 0),
                "TotalVol":       float(row["total_vol"] or 0),
                "TotalVal":       float(row["total_val"] or 0),
                "TradingSession": row["trading_session"],
            }
        except Exception as e:
            print(f"Error fetching market index: {e}")
            return {}

    @staticmethod
    def _extract_symbol_from_component(component: Dict[str, Any]) -> str:
        for key in (
            "Symbol", "symbol", "StockSymbol", "stockSymbol", "StockCode", "stockCode",
            "Ticker", "ticker", "Isin", "isin"
        ):
            value = component.get(key)
            if value:
                return str(value).upper().strip()
        return ""

    @staticmethod
    def _extract_weight_from_component(component: Dict[str, Any]) -> float:
        for key in ("Weight", "weight", "Ratio", "ratio", "Percent", "percent"):
            if key in component:
                return MarketService._to_float(component.get(key))
        return 0.0

    @staticmethod
    def _extract_index_components_payload(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Normalize SSI IndexComponents payload into a flat list of component dicts.

        SSI sample format:
        {
          "data": [{
            "IndexCode": "VNINDEX",
            "IndexComponent": [{"StockSymbol": "AAA"}, ...]
          }]
        }
        """
        container = payload.get("data") if isinstance(payload, dict) else None
        if not container:
            return []

        # Case 1: already flat list of component rows.
        if isinstance(container, list) and container and isinstance(container[0], dict) and "StockSymbol" in container[0]:
            return container

        flattened: List[Dict[str, Any]] = []
        if isinstance(container, list):
            for row in container:
                if not isinstance(row, dict):
                    continue
                children = row.get("IndexComponent") or row.get("indexComponent") or []
                if not isinstance(children, list):
                    continue
                for child in children:
                    if isinstance(child, dict):
                        flattened.append(child)
        return flattened

    @staticmethod
    def _chunked(items: List[str], chunk_size: int = 100) -> List[List[str]]:
        if chunk_size <= 0:
            chunk_size = 100
        return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]

    @staticmethod
    def _get_value_by_candidate_keys(row: Dict[str, Any], candidate_keys: List[str]) -> float:
        for key in candidate_keys:
            if key in row and row.get(key) is not None:
                return MarketService._to_float(row.get(key))
        return 0.0

    @staticmethod
    def _fetch_all_rows(table: str, select_fields: str = "*") -> List[Dict[str, Any]]:
        page_size = 1000
        offset = 0
        rows: List[Dict[str, Any]] = []

        while True:
            response = (
                supabase.table(table)
                .select(select_fields)
                .range(offset, offset + page_size - 1)
                .execute()
            )

            batch = response.data if response.data else []
            if not batch:
                break

            rows.extend(batch)

            if len(batch) < page_size:
                break

            offset += page_size

        return rows

    @staticmethod
    def get_investing_ideas(limit: int = 100) -> Dict[str, Any]:
        """
        Build investing ideas payload for three tabs:
        - trend: top gainers, decliners, and top volume
        - choice: stocks priced under 50k
        - community: top searched and top watchlisted stocks
        
        Excludes UPCOM exchange; only includes HOSE and HNX.
        """
        try:
            limit = max(1, min(limit, 100))

            profiles = MarketService._fetch_all_rows(
                "BI_Profile",
                "stock_id, symbol, company_name, logo, exchange"
            )
            prices = MarketService._fetch_all_rows(
                "Current_Stock_Price",
                "symbol, current_price, price_change, per_price_change, total_match_vol"
            )

            profile_by_symbol: Dict[str, Dict[str, Any]] = {}
            profile_by_stock_id: Dict[str, Dict[str, Any]] = {}
            for profile in profiles:
                symbol = str(profile.get("symbol") or "").upper().strip()
                stock_id = str(profile.get("stock_id") or "").strip()
                if not symbol or len(symbol) > 3:
                    continue
                exchange = str(profile.get("exchange") or "").upper().strip()
                if exchange == "UPCOM":
                    continue
                profile_by_symbol[symbol] = profile
                if stock_id:
                    profile_by_stock_id[stock_id] = profile

            price_by_symbol: Dict[str, Dict[str, Any]] = {
                str(price.get("symbol") or "").upper().strip(): price
                for price in prices
                if str(price.get("symbol") or "").strip()
            }

            def build_public_row(profile: Dict[str, Any], price: Dict[str, Any]) -> Dict[str, Any]:
                return {
                    "logo": profile.get("logo") or "",
                    "symbol": str(profile.get("symbol") or "").upper().strip(),
                    "company_name": profile.get("company_name") or "",
                    "current_price": MarketService._to_float(price.get("current_price")),
                    "price_change": MarketService._to_float(price.get("price_change")),
                    "per_price_change": MarketService._to_float(price.get("per_price_change")),
                }

            items: List[Dict[str, Any]] = []
            for symbol, price in price_by_symbol.items():
                if not symbol or len(symbol) > 3:
                    continue

                if symbol not in profile_by_symbol:
                    continue

                profile = profile_by_symbol[symbol]
                item = build_public_row(profile, price)
                item["_total_match_vol"] = MarketService._to_float(price.get("total_match_vol"))
                items.append(item)

            def build_ranked_items(stock_id_counts: Counter) -> List[Dict[str, Any]]:
                ranked_items: List[Dict[str, Any]] = []
                for stock_id, _count in sorted(
                    stock_id_counts.items(),
                    key=lambda item: (-item[1], str(profile_by_stock_id.get(item[0], {}).get("symbol") or "")),
                )[:limit]:
                    profile = profile_by_stock_id.get(stock_id)
                    if not profile:
                        continue

                    symbol = str(profile.get("symbol") or "").upper().strip()
                    if not symbol:
                        continue

                    price = price_by_symbol.get(symbol, {})
                    ranked_items.append(build_public_row(profile, price))

                return ranked_items

            search_history_rows = MarketService._fetch_all_rows("Search_History", "stock_id")
            favorite_rows = MarketService._fetch_all_rows("Favorite", "stock_id")

            search_counts = Counter(
                str(row.get("stock_id") or "").strip()
                for row in search_history_rows
                if row.get("stock_id") and str(row.get("stock_id") or "").strip() in profile_by_stock_id
            )
            favorite_counts = Counter(
                str(row.get("stock_id") or "").strip()
                for row in favorite_rows
                if row.get("stock_id") and str(row.get("stock_id") or "").strip() in profile_by_stock_id
            )

            # Keep only fields requested by API contract.
            def public_row(row: Dict[str, Any]) -> Dict[str, Any]:
                return {
                    "logo": row["logo"],
                    "symbol": row["symbol"],
                    "company_name": row["company_name"],
                    "current_price": row["current_price"],
                    "price_change": row["price_change"],
                    "per_price_change": row["per_price_change"],
                }

            top_gainers = sorted(items, key=lambda x: x["per_price_change"], reverse=True)[:limit]
            top_decliners = sorted(items, key=lambda x: x["per_price_change"])[:limit]
            top_volume = sorted(items, key=lambda x: x["_total_match_vol"], reverse=True)[:limit]
            cheap_under_50k = sorted(
                [item for item in items if item["current_price"] > 0 and item["current_price"] < 50],
                key=lambda x: (-x["current_price"], -x["_total_match_vol"], x["symbol"]),
            )[:limit]
            top_searched = build_ranked_items(search_counts)
            top_watchlist = build_ranked_items(favorite_counts)

            return {
                "trend": {
                    "top_gainers": [public_row(x) for x in top_gainers],
                    "top_decliners": [public_row(x) for x in top_decliners],
                    "top_volume": [public_row(x) for x in top_volume],
                },
                "top_choice": {
                    "cheap_under_50k": [public_row(x) for x in cheap_under_50k],
                },
                "community": {
                    "top_searched": top_searched,
                    "top_watchlist": top_watchlist,
                },
            }
        except Exception as e:
            print(f"Error fetching investing ideas: {e}")
            return {
                "trend": {
                    "top_gainers": [],
                    "top_decliners": [],
                    "top_volume": [],
                },
                "top_choice": {
                    "cheap_under_50k": [],
                },
                "community": {
                    "top_searched": [],
                    "top_watchlist": [],
                },
            }

    @staticmethod
    def get_top_index_impact_stocks(index_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top stocks impacting an index.
        ImpactScore is approximated by component weight * percent price change.
        """
        try:
            limit = max(1, limit)
            ssi_service = get_ssi_service()
            components_result = ssi_service.get_index_components(
                index_code=index_id,
                page_index=1,
                page_size=1000,
            )

            if not components_result.get("success"):
                return []

            raw_components = MarketService._extract_index_components_payload(
                components_result.get("data", {})
            )
            if not raw_components:
                return []

            component_map: Dict[str, Dict[str, Any]] = {}
            for component in raw_components:
                symbol = MarketService._extract_symbol_from_component(component)
                if not symbol:
                    continue
                component_map[symbol] = component

            symbols = list(component_map.keys())
            if not symbols:
                return []

            profiles: List[Dict[str, Any]] = []
            prices: List[Dict[str, Any]] = []

            for symbol_chunk in MarketService._chunked(symbols, chunk_size=100):
                profile_result = (
                    supabase.table("BI_Profile")
                    .select("stock_id, symbol, company_name, exchange")
                    .in_("symbol", symbol_chunk)
                    .execute()
                )
                if profile_result.data:
                    profiles.extend(profile_result.data)

                price_result = (
                    supabase.table("Current_Stock_Price")
                    .select("symbol, price_change, per_price_change, current_price, total_match_val")
                    .in_("symbol", symbol_chunk)
                    .execute()
                )
                if price_result.data:
                    prices.extend(price_result.data)

            profile_by_symbol = {str(p.get("symbol", "")).upper(): p for p in profiles if p.get("symbol")}

            items: List[Dict[str, Any]] = []
            for price in prices:
                symbol = str(price.get("symbol", "")).upper()
                if not symbol:
                    continue

                component = component_map.get(symbol)
                if not component:
                    continue

                profile = profile_by_symbol.get(symbol, {})
                weight = MarketService._extract_weight_from_component(component)
                per_price_change = MarketService._to_float(price.get("per_price_change"))
                weight_ratio = weight / 100.0 if abs(weight) > 1 else weight
                if weight > 0:
                    impact_score = weight_ratio * per_price_change
                else:
                    # Fallback when SSI payload has no weight field.
                    impact_score = per_price_change * MarketService._to_float(price.get("total_match_val"))

                items.append({
                    "stock_id": profile.get("stock_id"),
                    "symbol": symbol,
                    "company_name": profile.get("company_name") or "",
                    "exchange": profile.get("exchange") or "",
                    "Weight": weight,
                    "PriceChange": MarketService._to_float(price.get("price_change")),
                    "PerPriceChange": per_price_change,
                    "CurrentPrice": MarketService._to_float(price.get("current_price")),
                    "TotalMatchVal": MarketService._to_float(price.get("total_match_val")),
                    "ImpactScore": impact_score,
                    "AffectedPoints": 0.0,
                })

            # Convert relative impact score into estimated index points.
            index_snapshot = MarketService.get_market_index(index_id=index_id)
            index_change_points = MarketService._to_float(index_snapshot.get("Change")) if index_snapshot else 0.0

            signed_total = sum(item.get("ImpactScore", 0.0) for item in items)
            abs_total = sum(abs(item.get("ImpactScore", 0.0)) for item in items)

            if abs(index_change_points) > 0 and items:
                if abs(signed_total) > 1e-9:
                    scale = index_change_points / signed_total
                    for item in items:
                        item["AffectedPoints"] = round(item.get("ImpactScore", 0.0) * scale, 4)
                elif abs(abs_total) > 1e-9:
                    sign = 1.0 if index_change_points >= 0 else -1.0
                    for item in items:
                        portion = abs(item.get("ImpactScore", 0.0)) / abs_total
                        direction = 1.0 if item.get("ImpactScore", 0.0) >= 0 else -1.0
                        item["AffectedPoints"] = round(portion * abs(index_change_points) * sign * direction, 4)

            items.sort(key=lambda x: abs(x.get("ImpactScore", 0.0)), reverse=True)
            return items[:limit]
        except Exception as e:
            print(f"Error fetching top index impact stocks for {index_id}: {e}")
            return []
        
