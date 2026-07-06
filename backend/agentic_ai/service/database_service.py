import os
from dotenv import load_dotenv
import pandas as pd
from supabase import Client
from app.utils.supabase_client import supabase
import talib
import numpy as np
from typing import Dict, Any, List
import math
from datetime import time as dtime


load_dotenv()

def _get_supabase_client() -> Client:
    """Return the shared Supabase client (reuses one pooled connection pool)."""
    return supabase

def get_articles(symbol: str, from_date: str, to_date: str):
    """
    Lấy bài báo liên quan đến một mã chứng khoán trong khoảng thời gian.
    Chỉ giữ lại bài báo được tag DUY NHẤT cho mã đó (exclusive articles).
    """
    try:
        supabase = _get_supabase_client()

        # Bước 1: Lấy stock_id
        stock = supabase.table("Stock").select("id").eq("stock_symbol", symbol).execute()
        stock_id = stock.data[0]["id"] if stock.data else None
        if not stock_id:
            return []

        # Bước 2: Lấy tất cả article liên quan đến stock này
        result = (
            supabase.table("Article_Stock")
            .select("Article(*)")
            .eq("stock_id", stock_id)
            .execute()
        )
        if not result.data:
            return []

        # Bước 3: Build article_map và lọc theo khoảng ngày
        article_ids = []
        article_map = {}
        for item in result.data:
            article = item.get("Article")
            if not article:
                continue

            article_time = article.get("time")
            if not article_time:
                continue

            # Filter theo khoảng ngày sớm — tránh xử lý article ngoài range
            if not (from_date <= article_time <= to_date):
                continue

            article_id = str(article.get("id") or "")
            if article_id:
                article_ids.append(article_id)
                article_map[article_id] = article

        if not article_ids:
            return []

        # Bước 4: Đếm số stock được tag cho mỗi article
        # Chỉ giữ article nào chỉ được tag cho đúng 1 mã (exclusive)
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
        formatted_result = []
        for article_id, article in article_map.items():
            if article_id not in exclusive_ids:
                continue
            formatted_result.append({
                "time":    article.get("time"),
                "title":   article.get("title"),
                "summary": article.get("summary"),
            })

        # Sort cũ → mới
        formatted_result.sort(key=lambda x: x["time"])
        return formatted_result

    except Exception as e:
        print(f"[Database Service] get_articles error: {e}")
        return []
    
def get_fundamental_analysis(symbol: str, indicators: list[str]):
    """
    Lấy chỉ số phân tích cơ bản cho một mã chứng khoán.
    """
    try:
        supabase = _get_supabase_client();
    
        stock = supabase.table("Stock").select("id").eq("stock_symbol", symbol).execute()
        
        stock_id = stock.data[0]["id"] if stock.data else None
        if not stock_id:
            return {
                "summary": "",
                "indicators": {},
            }
        
        summary_result = (
            supabase.table("FA_Summary")
            .select("summary")
            .eq("stock_id", stock_id)
            .execute()
        )
        
        if not summary_result.data:
            return {
                "summary": "",
                "indicators": {},
            }
        
        if not indicators:
            return {"summary": summary_result.data[0]["summary"], "indicators": {}}
        
        indicators_result = (
            supabase.table("FA_Indicator")
            .select(",".join(indicators))
            .eq("stock_id", stock_id)
            .execute()
        )
        
        if  not indicators_result.data:
            return {
                "summary": "",
                "indicators": {},
            }
        
        return  {
            "summary": summary_result.data[0]["summary"],
            "indicators": indicators_result.data[0],
        }
            
    except Exception as e:
        print(f"[Database Service] get_fundamental_analysis error: {e}")
        return {
            "summary": "",
            "indicators": {},
        }
        
def _sanitize_indicators(indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Replace NaN/inf with None for JSON compliance"""
        sanitized = {}
        for key, values in indicators.items():
            if isinstance(values, list):
                sanitized[key] = [
                    None if (v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))))
                    else round(v, 4)
                    for v in values
                ]
            else:
                sanitized[key] = values
        return sanitized
        
def calculate_all_indicators(df: pd.DataFrame, required_indicators: list[str]) -> Dict[str, Any]:
    if df.empty or len(df) < 50:
        raise ValueError("Insufficient data for indicator calculation")

    open_prices = np.array(df['open'].values, dtype=np.float64)
    high_prices = np.array(df['high'].values, dtype=np.float64)
    low_prices = np.array(df['low'].values, dtype=np.float64)
    close_prices = np.array(df['close'].values, dtype=np.float64)
    volume = np.array(df['volume'].values, dtype=np.float64)

    indicators = {}

    try:
        # SMA
        if "sma_20" in required_indicators:
            indicators['sma_20'] = talib.SMA(close_prices, 20).tolist()

        if "sma_50" in required_indicators:
            indicators['sma_50'] = talib.SMA(close_prices, 50).tolist()

        # RSI
        if "rsi_14" in required_indicators:
            indicators['rsi_14'] = talib.RSI(close_prices, 14).tolist()

        # MACD
        if any(k in required_indicators for k in ["macd", "macd_signal", "macd_histogram"]):
            macd, macd_signal, macd_hist = talib.MACD(close_prices, 12, 26, 9)

            if "macd" in required_indicators:
                indicators['macd'] = macd.tolist()
            if "macd_signal" in required_indicators:
                indicators['macd_signal'] = macd_signal.tolist()
            if "macd_histogram" in required_indicators:
                indicators['macd_histogram'] = macd_hist.tolist()

        # Bollinger Bands
        if any(k in required_indicators for k in ["bb_upper", "bb_middle", "bb_lower"]):
            bb_upper, bb_middle, bb_lower = talib.BBANDS(close_prices, 20, 2, 2)

            if "bb_upper" in required_indicators:
                indicators['bb_upper'] = bb_upper.tolist()
            if "bb_middle" in required_indicators:
                indicators['bb_middle'] = bb_middle.tolist()
            if "bb_lower" in required_indicators:
                indicators['bb_lower'] = bb_lower.tolist()

        # KDJ
        if any(k in required_indicators for k in ["kdj_k", "kdj_d", "kdj_j"]):
            slowk, slowd = talib.STOCH(
                high_prices, low_prices, close_prices,
                fastk_period=9,
                slowk_period=3,
                slowk_matype=1,
                slowd_period=3,
                slowd_matype=1
            )

            if "kdj_k" in required_indicators:
                indicators['kdj_k'] = slowk.tolist()
            if "kdj_d" in required_indicators:
                indicators['kdj_d'] = slowd.tolist()
            if "kdj_j" in required_indicators:
                indicators['kdj_j'] = (3 * slowk - 2 * slowd).tolist()

        return _sanitize_indicators(indicators)

    except Exception as e:
        raise ValueError(f"Error calculating indicators: {str(e)}")
    
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


def _fetch_raw(table: str, symbol: str) -> pd.DataFrame:
    """
    Paginate qua Supabase để lấy TOÀN BỘ records (1000 rows/request).
    Trả về DataFrame index bởi trading_time ASC.
    """
    PAGE_SIZE = 1000
    all_rows: List[Dict] = []
    offset = 0
    supabase = _get_supabase_client()

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


def _resample_ohlcv(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    """Aggregate DataFrame OHLCV theo pandas resample rule."""
    return df.resample(rule, label="left", closed="left").agg(
        open=("open",     "first"),
        high=("high",     "max"),
        low=("low",       "min"),
        close=("close",   "last"),
        volume=("volume", "sum"),
    ).dropna(subset=["open"])   # bỏ nến rỗng (không có giao dịch)

def get_technical_analysis(symbol: str, interval: str, from_date: str, to_date: str, indicators: list[str]):
    """
    Lấy chỉ số phân tích kỹ thuật cho một mã chứng khoán.

    Cách lấy giá theo đúng pattern của get_stock_price_by_interval:
    - Intraday (1m, 5m, 15m, 30m, 1h) → fetch toàn bộ Stock_Price_1m rồi resample
    - Daily    (1d, 1w, 1M)            → fetch toàn bộ Stock_Price_1d rồi resample
    - Sau đó filter theo from_date / to_date
    - Tính indicators trên toàn bộ data trước khi filter (đảm bảo đủ lookback period)
    """
    try:
        # ──────────────────────────────────────────────────────
        # Bước 1: Fetch raw + resample theo interval
        # ──────────────────────────────────────────────────────
        if interval in _INTRADAY_INTERVALS:
            _, rule, cutoff = _INTRADAY_INTERVALS[interval]
            df = _fetch_raw("Stock_Price_1m", symbol.upper())

            if df.empty:
                return {"priceData": [], "indicatorsData": []}

            if interval == "1m":
                pass  # không resample
            else:
                if cutoff is not None:
                    df = df[df.index.time <= cutoff]
                df = _resample_ohlcv(df, rule)

        elif interval in _DAILY_INTERVALS:
            _, rule, _ = _DAILY_INTERVALS[interval]
            df = _fetch_raw("Stock_Price_1d", symbol.upper())

            if df.empty:
                return {"priceData": [], "indicatorsData": []}

            if interval != "1d":
                df = _resample_ohlcv(df, rule)

        else:
            valid = list(_INTRADAY_INTERVALS) + list(_DAILY_INTERVALS)
            raise ValueError(f"Unsupported interval: '{interval}'. Valid: {valid}")

        # Reset index để trading_time thành column
        df = df.reset_index()
        df["trading_time"] = pd.to_datetime(df["trading_time"], utc=True)
        df = df.sort_values("trading_time").reset_index(drop=True)

        # ──────────────────────────────────────────────────────
        # Bước 2: Tính indicators trên TOÀN BỘ data (trước filter)
        # Quan trọng: đảm bảo đủ lookback period (VD: RSI cần 14 nến trước)
        # ──────────────────────────────────────────────────────
        indicators_result = {}
        if indicators:
            indicators_result = calculate_all_indicators(df, indicators)

        # ──────────────────────────────────────────────────────
        # Bước 3: Filter theo from_date / to_date
        # ──────────────────────────────────────────────────────
        from_dt = pd.to_datetime(from_date).tz_localize("UTC")
        to_dt = (
            pd.to_datetime(to_date).tz_localize("UTC")
            + pd.Timedelta(days=1)
            - pd.Timedelta(seconds=1)
        )

        mask = (df["trading_time"] >= from_dt) & (df["trading_time"] <= to_dt)
        filtered_df = df[mask].reset_index(drop=True)
        original_indices = df[mask].index.tolist()

        if filtered_df.empty:
            return {"priceData": [], "indicatorsData": []}

        # ──────────────────────────────────────────────────────
        # Bước 4: Filter indicators theo index gốc
        # ──────────────────────────────────────────────────────
        filtered_indicators = {}
        for key, values in indicators_result.items():
            filtered_indicators[key] = [
                values[i] for i in original_indices if i < len(values)
            ]

        # ──────────────────────────────────────────────────────
        # Bước 5: Build priceData + indicatorsData
        # ──────────────────────────────────────────────────────
        price_data = []
        indicators_data = []

        for local_i, (_, row) in enumerate(filtered_df.iterrows()):
            t_dt = row["trading_time"]
            date_str = t_dt.strftime("%d/%m/%Y")
            time_str = t_dt.strftime("%H:%M:%S")

            price_data.append({
                "TradingDate": date_str,
                "Time": time_str,
                "open": row["open"],
                "high": row["high"],
                "low": row["low"],
                "close": row["close"],
                "volume": row["volume"],
            })

            if filtered_indicators:
                record = {"TradingDate": date_str, "Time": time_str}
                for key, values in filtered_indicators.items():
                    record[key] = values[local_i] if local_i < len(values) else None
                indicators_data.append(record)

        return {
            "priceData": price_data,
            "indicatorsData": indicators_data,
        }

    except Exception as e:
        print(f"[Database Service] get_technical_analysis error: {e}")
        return {
            "priceData": [],
            "indicatorsData": [],
        }