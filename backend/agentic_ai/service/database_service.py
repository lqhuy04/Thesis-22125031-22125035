import os
from dotenv import load_dotenv
import pandas as pd
from supabase import Client, create_client
import talib
import numpy as np
from typing import Dict, Any
import math

load_dotenv()

def _get_supabase_client() -> Client:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in environment.")
    return create_client(supabase_url, supabase_key)

def get_articles(symbol: str, from_date: str, to_date: str):
    """
    Lấy danh sách bài báo liên quan đến một mã chứng khoán + thị trường trong khoảng thời gian nhất định.
    """
    try: 
        supabase = _get_supabase_client();
    
        stock = supabase.table("Stock").select("id").eq("stock_symbol", symbol).execute()
        
        stock_id = stock.data[0]["id"] if stock.data else None
        if not stock_id:
            return []
        
        result = (
            supabase.table("Article_Stock")
            .select("Article(*)")
            .eq("stock_id", stock_id)
            .execute()
        )
        
        if not result.data:
            return []
        
        formatted_result = []
        for item in result.data:
            article = item.get("Article")
            if not article:
                continue

            article_time = article.get("time")
            if not article_time:
                continue

            # Filter theo khoảng ngày
            if from_date <= article_time <= to_date:
                formatted_result.append({
                    "time": article_time,
                    "title": article.get("title"),
                    "summary": article.get("summary"),
                })
        
        # Sort theo thời gian cũ -> mới
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
        

def get_technical_analysis(symbol: str, interval: str, from_date: str, to_date: str, indicators: list[str]):
    """
    Lấy chỉ số phân tích kỹ thuật cho một mã chứng khoán.
    """
    try:
        supabase = _get_supabase_client()

        # ==============================
        # CASE 1: Không có indicators
        # ==============================
        if not indicators:
            from_iso = f"{from_date}T00:00:00+00:00"
            to_iso = f"{to_date}T23:59:59+00:00"

            response = supabase.table(f"Stock_Price_{interval}") \
                .select("trading_time, open, high, low, close, volume") \
                .eq("symbol", symbol.upper()) \
                .gte("trading_time", from_iso) \
                .lte("trading_time", to_iso) \
                .order("trading_time", desc=False) \
                .execute()

            if not response.data:
                return {
                    "priceData": [],
                    "indicatorsData": [],
                }

            return {
                "priceData": response.data,
                "indicatorsData": [],
            }

        # ==============================
        # CASE 2: Có indicators
        # ==============================
        # Lấy toàn bộ data để tính indicator
        response = supabase.table(f"Stock_Price_{interval}") \
            .select("trading_time, open, high, low, close, volume") \
            .eq("symbol", symbol.upper()) \
            .order("trading_time", desc=False) \
            .execute()

        if not response.data:
            return {
                "priceData": [],
                "indicatorsData": [],
            }

        df = pd.DataFrame(response.data)

        # Convert datetime
        df["trading_time"] = pd.to_datetime(df["trading_time"], utc=True)
        df = df.sort_values("trading_time").reset_index(drop=True)

        # Tính indicators
        indicators_result = calculate_all_indicators(df, indicators)

        # ==============================
        # Lọc theo khoảng thời gian
        # ==============================
        from_dt = pd.to_datetime(from_date).tz_localize("UTC")
        to_dt = pd.to_datetime(to_date).tz_localize("UTC") + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

        mask = (df["trading_time"] >= from_dt) & (df["trading_time"] <= to_dt)

        filtered_df = df[mask].reset_index(drop=True)
        filtered_indices = df[mask].index

        # ==============================
        # Filter indicators theo index
        # ==============================
        filtered_indicators = {}
        for key, values in indicators_result.items():
            filtered_indicators[key] = [
                values[i] for i in filtered_indices if i < len(values)
            ]

        # ==============================
        # Build indicatorsData
        # ==============================
        records = []
        for i, row in filtered_df.iterrows():
            t_dt = row["trading_time"]

            record = {
                "TradingDate": t_dt.strftime("%d/%m/%Y"),
                "Time": t_dt.strftime("%H:%M:%S"),
            }

            for key, values in filtered_indicators.items():
                record[key] = values[i] if i < len(values) else None

            records.append(record)

        # ==============================
        # priceData sau khi filter
        # ==============================
        filtered_price_data = []

        for _, row in filtered_df.iterrows():
            t_dt = row["trading_time"]

            record = {
                "TradingDate": t_dt.strftime("%d/%m/%Y"),
                "Time": t_dt.strftime("%H:%M:%S"),
                "open": row["open"],
                "high": row["high"],
                "low": row["low"],
                "close": row["close"],
                "volume": row["volume"],
            }

            filtered_price_data.append(record)

        # Nếu không có indicator nào
        if not indicators_result:
            return {
                "priceData": filtered_price_data,
                "indicatorsData": [],
            }

        return {
            "priceData": filtered_price_data,
            "indicatorsData": records,
        }

    except Exception as e:
        print(f"[Database Service] get_technical_analysis error: {e}")
        return {
            "priceData": [],
            "indicatorsData": [],
        }