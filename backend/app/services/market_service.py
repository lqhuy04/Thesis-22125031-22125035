"""
Price Database Service
Handles database operations for historical stock prices (15m, 1h, 1d intervals)
"""
from supabase import create_client, Client
from app.config import settings
from collections import Counter
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from app.utils.market_index import get_index_symbols
import random
import pandas as pd


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
            symbol = (symbol or "").strip().upper()
            if not symbol:
                return []

            if interval in MarketService._INTRADAY_INTERVALS:
                return MarketService._aggregate_from_1m(symbol, interval)
            elif interval in MarketService._DAILY_INTERVALS:
                return MarketService._aggregate_from_1d(symbol, interval)
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
    def _resolve_stock_id(symbol: str) -> Optional[str]:
        """Resolve Stock.stock_symbol to the UUID used by stock-price tables."""
        normalized_symbol = (symbol or "").strip().upper()
        if not normalized_symbol:
            return None

        response = (
            supabase.table("Stock")
            .select("id")
            .eq("stock_symbol", normalized_symbol)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        if not rows or not rows[0].get("id"):
            return None

        return str(rows[0]["id"])

    @staticmethod
    def _fetch_raw(table: str, symbol: str) -> pd.DataFrame:
        """
        Resolve symbol -> Stock.id, sau đó paginate dữ liệu theo stock_id.

        Stock_Price_1m và Stock_Price_1d không lưu symbol trực tiếp; cả hai
        tham chiếu Stock(id) bằng cột stock_id.
        Trả về DataFrame index bởi trading_time ASC.
        """
        PAGE_SIZE = 1000
        all_rows: List[Dict] = []
        offset = 0
        stock_id = MarketService._resolve_stock_id(symbol)
        if not stock_id:
            return pd.DataFrame()

        while True:
            response = supabase.table(table) \
                .select("stock_id, trading_time, open, high, low, close, volume") \
                .eq("stock_id", stock_id) \
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

    # ──────────────────────────────────────────────────────────────────────────
    # Historical MarketIndex values
    # ──────────────────────────────────────────────────────────────────────────

    _MARKET_INDEX_INTRADAY_INTERVALS = {
        "1m": "1min",
        "5m": "5min",
        "15m": "15min",
        "30m": "30min",
        "1h": "1h",
    }

    _MARKET_INDEX_DAILY_INTERVALS = {
        "1d": "1D",
        "1w": "1W",
        "1M": "1ME",
    }

    @staticmethod
    def _resolve_market_index_id(index_name: str) -> Optional[str]:
        """Resolve MarketIndex.name to the UUID used by index-value tables."""
        normalized_name = (index_name or "").strip().upper()
        if not normalized_name:
            return None

        response = (
            supabase.table("MarketIndex")
            .select("id")
            .eq("name", normalized_name)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        if not rows or not rows[0].get("id"):
            return None

        return str(rows[0]["id"])

    @staticmethod
    def _fetch_market_index_raw(
        table: str,
        market_index_id: str,
    ) -> pd.DataFrame:
        """Paginate all historical values for one MarketIndex UUID."""
        page_size = 1000
        offset = 0
        all_rows: List[Dict[str, Any]] = []

        while True:
            response = (
                supabase.table(table)
                .select("market_index_id, trading_time, value")
                .eq("market_index_id", market_index_id)
                .order("trading_time", desc=False)
                .range(offset, offset + page_size - 1)
                .execute()
            )
            rows = response.data or []
            all_rows.extend(rows)

            if len(rows) < page_size:
                break
            offset += page_size

        if not all_rows:
            return pd.DataFrame()

        df = pd.DataFrame(all_rows)
        df["trading_time"] = pd.to_datetime(df["trading_time"], errors="coerce")
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna(subset=["trading_time", "value"])
        return df.set_index("trading_time").sort_index()

    @staticmethod
    def _market_index_df_to_records(
        df: pd.DataFrame,
        index_name: str,
    ) -> List[Dict[str, Any]]:
        """Convert a MarketIndex DataFrame to the public API record format."""
        if df.empty:
            return []

        output = df.reset_index()
        output["trading_time"] = output["trading_time"].dt.strftime(
            "%Y-%m-%dT%H:%M:%S"
        )
        output["index_id"] = index_name
        return output[["index_id", "trading_time", "value"]].to_dict(
            orient="records"
        )

    @staticmethod
    def get_market_index_value_by_interval(
        index_name: str,
        interval: str = "15m",
        limit: int = 300,
    ) -> List[Dict[str, Any]]:
        """
        Return the latest historical index values for a requested interval.

        Intraday intervals use MarketIndex_Value_1m; daily, weekly and monthly
        intervals use MarketIndex_Value_1d. Resampled buckets retain their last
        available index value.
        """
        try:
            normalized_name = (index_name or "").strip().upper()
            if not normalized_name:
                return []

            if interval in MarketService._MARKET_INDEX_INTRADAY_INTERVALS:
                table = "MarketIndex_Value_1m"
                rule = MarketService._MARKET_INDEX_INTRADAY_INTERVALS[interval]
                raw_interval = interval == "1m"
            elif interval in MarketService._MARKET_INDEX_DAILY_INTERVALS:
                table = "MarketIndex_Value_1d"
                rule = MarketService._MARKET_INDEX_DAILY_INTERVALS[interval]
                raw_interval = interval == "1d"
            else:
                valid = list(
                    MarketService._MARKET_INDEX_INTRADAY_INTERVALS
                ) + list(MarketService._MARKET_INDEX_DAILY_INTERVALS)
                raise ValueError(
                    f"Unsupported interval: '{interval}'. Valid: {valid}"
                )

            market_index_id = MarketService._resolve_market_index_id(
                normalized_name
            )
            if not market_index_id:
                return []

            df = MarketService._fetch_market_index_raw(table, market_index_id)
            if df.empty:
                return []

            if raw_interval:
                result_df = df[["value"]]
            else:
                result_df = (
                    df.resample(rule, label="left", closed="left")
                    .agg(value=("value", "last"))
                    .dropna(subset=["value"])
                )

            result_df = result_df.tail(limit)
            return MarketService._market_index_df_to_records(
                result_df,
                normalized_name,
            )
        except Exception as e:
            print(
                f"Error fetching historical MarketIndex values for "
                f"{index_name} ({interval}): {e}"
            )
            return []
    
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

            # Resolve the VN100 universe through
            # MarketIndex -> Stock_MarketIndex -> Stock.
            vn100_symbols = set(get_index_symbols("VN100"))
            if not vn100_symbols:
                return []

            # Search only BI_Profile rows whose symbols belong to VN100.
            result = supabase.table("BI_Profile") \
                .select("stock_id, symbol, company_name, exchange, logo") \
                .in_("symbol", sorted(vn100_symbols)) \
                .or_(f"symbol.ilike.%{keyword}%,company_name.ilike.%{keyword}%") \
                .limit(50) \
                .execute()

            data = result.data or []

            filtered = [
                stock
                for stock in data
                if str(stock.get("symbol") or "").upper() in vn100_symbols
            ]
            if not filtered:
                return []

            # Query 2: batch lấy giá theo khóa stock_id của schema mới.
            stock_ids = [
                str(stock.get("stock_id"))
                for stock in filtered
                if stock.get("stock_id")
            ]
            price_result = supabase.table("Current_Stock_Price") \
                .select("stock_id, current_price, price_change, per_price_change") \
                .in_("stock_id", stock_ids) \
                .execute()

            price_map = {
                str(row["stock_id"]): row
                for row in (price_result.data or [])
                if row.get("stock_id")
            }

            for stock in filtered:
                stock_id = str(stock.get("stock_id") or "")
                stock.update(price_map.get(stock_id, {}))

            return sorted(filtered, key=lambda x: MarketService.get_priority(x, keyword))

        except Exception as e:
            print(f"Error search stock: {e}")
            return []
        
    @staticmethod
    def get_current_stock_price(symbol: str) -> Dict[str, Any]:
        try:
            normalized_symbol = (symbol or "").strip().upper()
            if not normalized_symbol:
                return {}

            query = supabase.table("BI_Profile") \
                .select("stock_id, symbol, company_name, exchange, logo") \
                .eq("symbol", normalized_symbol) \
                .limit(1)
            
            result = query.execute()
            data = result.data if result.data else []

            if len(data) == 0:
                return {}

            stock = data[0]  # ✅ Get the first matching record
            stock_id = stock.get("stock_id")
            if not stock_id:
                return {}

            query2 = supabase.table("Current_Stock_Price") \
                .select("*") \
                .eq("stock_id", stock_id) \
                .limit(1)
            
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
    def _build_stock_price_summaries(
        stock_ids: List[Any],
    ) -> List[Dict[str, Any]]:
        """Map Stock ids to the compact response used by related-stock cards."""
        normalized_ids = list(dict.fromkeys(
            str(stock_id)
            for stock_id in stock_ids
            if stock_id is not None
        ))
        if not normalized_ids:
            return []

        stock_result = (
            supabase.table("Stock")
            .select("id, stock_symbol")
            .in_("id", normalized_ids)
            .execute()
        )
        stocks = stock_result.data or []
        if not stocks:
            return []

        price_result = (
            supabase.table("Current_Stock_Price")
            .select("stock_id, current_price, per_price_change")
            .in_("stock_id", normalized_ids)
            .execute()
        )
        price_by_stock_id = {
            str(price.get("stock_id")): price
            for price in (price_result.data or [])
            if price.get("stock_id")
        }

        return [
            {
                "symbol": str(stock.get("stock_symbol") or "").upper(),
                "current_price": MarketService._to_float(
                    price_by_stock_id.get(str(stock.get("id")), {}).get(
                        "current_price"
                    )
                ),
                "per_price_change": MarketService._to_float(
                    price_by_stock_id.get(str(stock.get("id")), {}).get(
                        "per_price_change"
                    )
                ),
            }
            for stock in stocks
            if stock.get("id") and stock.get("stock_symbol")
        ]

    @staticmethod
    def get_related_stocks(symbol: str, limit: int = 6) -> List[Dict[str, Any]]:
        """
        Get up to `limit` VN100 stocks that share at least one category
        (industry) with the input VN100 symbol, picked randomly.

        Flow:
          1. Resolve the VN100 stock universe.
          2. VN100 Stock: stock_symbol -> id
          3. Category_Stock: id -> category_id(s)
          4. Category_Stock: category_id(s) -> VN100 sibling stock_ids
          5. Current_Stock_Price: stock_id -> current_price, per_price_change

        Returns: [{symbol, current_price, per_price_change}, ...]
        """
        try:
            symbol = symbol.strip().upper() if symbol else ""
            if not symbol:
                return []

            # 1. Resolve the VN100 universe before applying the category rule.
            vn100_symbols = set(get_index_symbols("VN100"))
            if not vn100_symbols:
                return []

            vn100_stock_result = (
                supabase.table("Stock")
                .select("id, stock_symbol")
                .in_("stock_symbol", sorted(vn100_symbols))
                .execute()
            )
            vn100_stock_id_by_symbol = {
                str(row.get("stock_symbol") or "").upper().strip(): str(row.get("id"))
                for row in (vn100_stock_result.data or [])
                if row.get("id")
                and str(row.get("stock_symbol") or "").upper().strip() in vn100_symbols
            }
            if not vn100_stock_id_by_symbol:
                return []

            # The input and every related candidate must belong to VN100.
            stock_id = vn100_stock_id_by_symbol.get(symbol)
            if not stock_id:
                return []
            vn100_stock_ids = set(vn100_stock_id_by_symbol.values())

            # 2. Categories that the input VN100 stock belongs to.
            cat_result = (
                supabase.table("Category_Stock")
                .select("category_id")
                .eq("stock_id", stock_id)
                .execute()
            )
            category_ids = [
                row.get("category_id")
                for row in (cat_result.data or [])
                if row.get("category_id") is not None
            ]
            if not category_ids:
                return []

            # 3. Keep only VN100 siblings sharing those categories.
            sibling_result = (
                supabase.table("Category_Stock")
                .select("stock_id")
                .in_("category_id", category_ids)
                .execute()
            )
            sibling_ids = {
                str(row.get("stock_id"))
                for row in (sibling_result.data or [])
                if row.get("stock_id") is not None
                and str(row.get("stock_id")) in vn100_stock_ids
            }
            sibling_ids.discard(stock_id)
            if not sibling_ids:
                return []

            # Random max `limit` siblings.
            sibling_ids = list(sibling_ids)
            random.shuffle(sibling_ids)
            sibling_ids = sibling_ids[:max(1, limit)]

            return MarketService._build_stock_price_summaries(sibling_ids)
        except Exception as e:
            print(f"Error fetching related stocks for {symbol}: {e}")
            return []

    @staticmethod
    def get_random_market_index_stocks(
        index_id: str,
        limit: int = 6,
    ) -> List[Dict[str, Any]]:
        """Return a random stock sample belonging to one MarketIndex."""
        try:
            normalized_index = (index_id or "").strip().upper()
            if not normalized_index:
                return []

            market_index_result = (
                supabase.table("MarketIndex")
                .select("id")
                .eq("name", normalized_index)
                .limit(1)
                .execute()
            )
            market_index_rows = market_index_result.data or []
            if not market_index_rows or not market_index_rows[0].get("id"):
                return []

            membership_result = (
                supabase.table("Stock_MarketIndex")
                .select("stock_id")
                .eq("market_index_id", market_index_rows[0]["id"])
                .execute()
            )
            stock_ids = list(dict.fromkeys(
                str(row.get("stock_id"))
                for row in (membership_result.data or [])
                if row.get("stock_id")
            ))
            if not stock_ids:
                return []

            stocks = MarketService._build_stock_price_summaries(stock_ids)
            random.shuffle(stocks)
            return stocks[:max(1, min(limit, 20))]
        except Exception as e:
            print(f"Error fetching random stocks for index {index_id}: {e}")
            return []

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
        industry_id: str,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get VN100 stock movement list for one industry.
        Resolves the VN100 universe first, intersects it with
        Category_Stock.stock_id, then enriches the remaining stocks with
        Current_Stock_Price using the same stock_id.
        Returns all stocks by default, or first `limit` stocks if provided.
        """
        try:
            industry_id = str(industry_id).strip() if industry_id is not None else ""
            if not industry_id:
                return {"items": []}

            # 1. Resolve the VN100 universe before applying the industry rule.
            vn100_symbols = set(get_index_symbols("VN100"))
            if not vn100_symbols:
                return {"items": []}

            vn100_profile_result = (
                supabase.table("BI_Profile")
                .select("stock_id, symbol, company_name, exchange, logo")
                .in_("symbol", sorted(vn100_symbols))
                .execute()
            )
            vn100_profiles = [
                profile
                for profile in (vn100_profile_result.data or [])
                if profile.get("stock_id")
                and str(profile.get("symbol") or "").upper().strip() in vn100_symbols
            ]
            profile_by_stock_id: Dict[str, Dict[str, Any]] = {
                str(profile["stock_id"]): profile
                for profile in vn100_profiles
            }
            if not profile_by_stock_id:
                return {"items": []}

            # 2. Apply the industry rule only within the VN100 universe.
            category_result = (
                supabase.table("Category_Stock")
                .select("stock_id")
                .eq("category_id", industry_id)
                .execute()
            )
            category_rows = category_result.data if category_result.data else []
            stock_ids = list(dict.fromkeys(
                str(row.get("stock_id"))
                for row in category_rows
                if row.get("stock_id")
                and str(row.get("stock_id")) in profile_by_stock_id
            ))
            if not stock_ids:
                return {"items": []}

            # 3. Fetch prices only for VN100 stocks belonging to this industry.
            prices = MarketService._fetch_rows_by_stock_ids(
                "Current_Stock_Price",
                "stock_id, price_change, per_price_change, ceiling_price, floor_price, "
                "ref_price, current_price, total_match_vol, total_match_val",
                stock_ids,
            )

            items: List[Dict[str, Any]] = []
            for price in prices:
                stock_id = str(price.get("stock_id") or "")
                profile = profile_by_stock_id.get(stock_id)
                if not profile:
                    continue
                symbol = str(profile.get("symbol") or "").upper()

                items.append({
                    "stock_id": stock_id,
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
            print(f"Error fetching industry stocks movement for {industry_id}: {e}")
            return {"items": []}
        
    @staticmethod
    def get_all_stocks_movement(
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        Get paginated movement list for VN100 stocks.
        Each item has the same fields as get_industry_stocks_movement.
        Data source is BI_Profile joined with Current_Stock_Price.
        """
        try:
            page = max(page, 1)
            page_size = max(page_size, 1)

            vn100_symbols = set(get_index_symbols("VN100"))
            if not vn100_symbols:
                return {
                    "items": [],
                    "page": page,
                    "page_size": page_size,
                    "total": 0,
                    "total_pages": 0,
                }

            profile_result = (
                supabase.table("BI_Profile")
                .select("stock_id, symbol, company_name, exchange, logo")
                .in_("symbol", sorted(vn100_symbols))
                .execute()
            )
            profiles = [
                profile
                for profile in (profile_result.data or [])
                if profile.get("stock_id")
                and str(profile.get("symbol") or "").upper().strip() in vn100_symbols
            ]

            if not profiles:
                return {
                    "items": [],
                    "page": page,
                    "page_size": page_size,
                    "total": 0,
                    "total_pages": 0,
                }

            profile_by_stock_id: Dict[str, Dict[str, Any]] = {
                str(profile["stock_id"]): profile
                for profile in profiles
            }

            prices = MarketService._fetch_rows_by_stock_ids(
                "Current_Stock_Price",
                "stock_id, price_change, per_price_change, ceiling_price, floor_price, "
                "ref_price, current_price, total_match_vol, total_match_val",
                list(profile_by_stock_id.keys()),
            )

            items: List[Dict[str, Any]] = []
            for price in prices:
                stock_id = str(price.get("stock_id") or "")
                profile = profile_by_stock_id.get(stock_id)
                if not profile:
                    continue
                symbol = str(profile.get("symbol") or "").upper().strip()

                items.append({
                    "stock_id": stock_id,
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

            items.sort(key=lambda x: x.get("symbol", ""))

            total = len(items)
            total_pages = (total + page_size - 1) // page_size
            start = (page - 1) * page_size
            end = start + page_size

            return {
                "items": items[start:end],
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages,
            }
        except Exception as e:
            print(f"Error fetching all stocks movement: {e}")
            return {
                "items": [],
                "page": page,
                "page_size": page_size,
                "total": 0,
                "total_pages": 0,
            }

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
    def _fetch_rows_by_stock_ids(
        table: str,
        select_fields: str,
        stock_ids: List[str],
    ) -> List[Dict[str, Any]]:
        """Paginate rows whose stock_id belongs to the supplied universe."""
        normalized_ids = list(dict.fromkeys(
            str(stock_id).strip()
            for stock_id in stock_ids
            if stock_id is not None and str(stock_id).strip()
        ))
        if not normalized_ids:
            return []

        page_size = 1000
        rows: List[Dict[str, Any]] = []
        for id_chunk in MarketService._chunked(normalized_ids, chunk_size=100):
            offset = 0
            while True:
                response = (
                    supabase.table(table)
                    .select(select_fields)
                    .in_("stock_id", id_chunk)
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

    # Valid investing-idea categories (msgType values).
    _INVESTING_IDEA_TYPES = {
        "top_gainers",
        "top_decliners",
        "top_volume",
        "cheap_under_50k",
        "top_searched",
        "top_watchlist",
    }

    # Trend categories that support a period-based `interval`.
    _INVESTING_IDEA_TREND_TYPES = {"top_gainers", "top_decliners", "top_volume"}

    # interval -> số ngày lịch lùi về để lấy nến mốc so sánh.
    _INVESTING_IDEA_PERIOD_DAYS = {
        "1w": 7,
        "1mo": 30,
        "3mo": 90,
        "6mo": 180,
    }

    @staticmethod
    def _fetch_daily_rows_in_range(
        start_iso: str,
        end_iso: Optional[str] = None,
        select_fields: str = "stock_id, trading_time, close, volume",
        stock_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Paginate Stock_Price_1d lấy các row có trading_time trong [start_iso, end_iso].
        end_iso None nghĩa là không giới hạn cận trên.
        trading_time lưu dạng ISO ("YYYY-MM-DDTHH:MM:SS") nên so sánh chuỗi = so sánh thời gian.
        """
        page_size = 1000
        offset = 0
        rows: List[Dict[str, Any]] = []

        while True:
            query = (
                supabase.table("Stock_Price_1d")
                .select(select_fields)
                .gte("trading_time", start_iso)
            )
            if end_iso:
                query = query.lte("trading_time", end_iso)
            if stock_ids:
                query = query.in_("stock_id", stock_ids)

            response = (
                query.order("trading_time", desc=False)
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
    def _build_period_trend_rows(
        profile_by_stock_id: Dict[str, Dict[str, Any]],
        price_by_stock_id: Dict[str, Dict[str, Any]],
        period_days: int,
    ) -> List[Dict[str, Any]]:
        """
        Tính % thay đổi giá và % thay đổi khối lượng theo kỳ cho mỗi mã,
        bằng cách chỉ fetch HAI lát mỏng từ Stock_Price_1d:
          1. Cửa sổ "recent": vài ngày gần nhất  → nến mới nhất mỗi mã.
          2. Cửa sổ "past": quanh (latest - period_days) → nến gần nhất tại/trước mốc.

        Trả về list row (định dạng public_row) với:
          - per_price_change = % thay đổi close theo kỳ
          - _vol_change      = % thay đổi volume theo kỳ (None nếu vol mốc <= 0)
        """
        stock_ids = list(profile_by_stock_id.keys())
        if not stock_ids:
            return []

        # ── Mốc thời gian mới nhất trong universe VN100 (1 query rẻ) ───────
        latest_resp = (
            supabase.table("Stock_Price_1d")
            .select("trading_time")
            .in_("stock_id", stock_ids)
            .order("trading_time", desc=True)
            .limit(1)
            .execute()
        )
        if not latest_resp.data:
            return []
        try:
            global_latest = datetime.fromisoformat(latest_resp.data[0]["trading_time"])
        except Exception:
            return []

        latest_date = global_latest.date()
        target_date = latest_date - timedelta(days=period_days)

        def pick_latest(rows: List[Dict[str, Any]], cap_date=None) -> Dict[str, Dict[str, Any]]:
            """Per stock_id giữ nến có trading_time lớn nhất (<= cap_date nếu có)."""
            picked: Dict[str, Dict[str, Any]] = {}
            for r in rows:
                stock_id = str(r.get("stock_id") or "").strip()
                if stock_id not in profile_by_stock_id:
                    continue
                try:
                    dt = datetime.fromisoformat(r["trading_time"])
                except Exception:
                    continue
                if cap_date is not None and dt.date() > cap_date:
                    continue
                prev = picked.get(stock_id)
                if prev is None or dt > prev["_dt"]:
                    picked[stock_id] = {
                        "_dt": dt,
                        "close": MarketService._to_float(r.get("close")),
                        "volume": MarketService._to_float(r.get("volume")),
                    }
            return picked

        # ── Lát 1: nến mới nhất (4 ngày lịch gần nhất là đủ) ──────────────
        recent_rows = MarketService._fetch_daily_rows_in_range(
            start_iso=(latest_date - timedelta(days=4)).isoformat(),
            stock_ids=stock_ids,
        )
        latest_by_stock_id = pick_latest(recent_rows)

        # ── Lát 2: nến tại/trước target (đệm 12 ngày cho cuối tuần/lễ) ────
        past_rows = MarketService._fetch_daily_rows_in_range(
            start_iso=(target_date - timedelta(days=12)).isoformat(),
            end_iso=target_date.isoformat() + "T23:59:59",
            stock_ids=stock_ids,
        )
        past_by_stock_id = pick_latest(past_rows, cap_date=target_date)

        rows: List[Dict[str, Any]] = []
        for stock_id, latest in latest_by_stock_id.items():
            past = past_by_stock_id.get(stock_id)
            if not past:
                continue

            close_now, close_past = latest["close"], past["close"]
            if close_past <= 0:
                continue  # không tính được % giá

            price_change_pct = (close_now - close_past) / close_past * 100.0

            vol_now, vol_past = latest["volume"], past["volume"]
            vol_change_pct = (
                (vol_now - vol_past) / vol_past * 100.0 if vol_past > 0 else None
            )

            profile = profile_by_stock_id[stock_id]
            symbol = str(profile.get("symbol") or "").upper().strip()
            price = price_by_stock_id.get(stock_id, {})
            rows.append({
                "logo": profile.get("logo") or "",
                "symbol": symbol,
                "company_name": profile.get("company_name") or "",
                "current_price": MarketService._to_float(price.get("current_price")),
                "price_change": round(close_now - close_past, 2),
                "per_price_change": round(price_change_pct, 2),
                "_vol_change": round(vol_change_pct, 2) if vol_change_pct is not None else None,
            })

        return rows

    # Investing-idea list is paginated: fixed page size, capped at 100 items total.
    _INVESTING_IDEA_MAX_TOTAL = 100

    @staticmethod
    def get_investing_idea_by_type(
        msg_type: str,
        limit: int = 20,
        interval: str = "today",
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Build a single investing-idea category page and return it as a flat list.

        Supported msg_type values:
        - top_gainers / top_decliners / top_volume  (trend)
        - cheap_under_50k                            (top choice)
        - top_searched / top_watchlist               (community)

        `interval` (chỉ áp dụng cho 3 loại trend):
        - "today" (mặc định): xếp hạng theo dữ liệu Current_Stock_Price như cũ.
        - "1w" / "1mo" / "3mo" / "6mo": xếp hạng theo % thay đổi của close
          (gainers/decliners) hoặc volume (top_volume) giữa nến mới nhất và nến
          cách 1 tuần / 1 / 3 / 6 tháng trong bảng Stock_Price_1d.

        `offset` / `limit` paginate the ranked list — page size is `limit`
        (default 20), and the ranked list is capped at `_INVESTING_IDEA_MAX_TOTAL`
        (100) items regardless of how far `offset` is pushed.

        The stock universe is restricted to current VN100 constituents before
        any category-specific ranking rule is applied.
        """
        try:
            if msg_type not in MarketService._INVESTING_IDEA_TYPES:
                return []

            limit = max(1, min(limit, MarketService._INVESTING_IDEA_MAX_TOTAL))
            offset = max(0, offset)
            if offset >= MarketService._INVESTING_IDEA_MAX_TOTAL:
                return []
            page_end = min(offset + limit, MarketService._INVESTING_IDEA_MAX_TOTAL)
            interval = (interval or "today").strip().lower()

            vn100_symbols = set(get_index_symbols("VN100"))
            if not vn100_symbols:
                return []

            profile_response = (
                supabase.table("BI_Profile")
                .select("stock_id, symbol, company_name, logo, exchange")
                .in_("symbol", sorted(vn100_symbols))
                .execute()
            )
            profiles = profile_response.data or []

            profile_by_symbol: Dict[str, Dict[str, Any]] = {}
            profile_by_stock_id: Dict[str, Dict[str, Any]] = {}
            for profile in profiles:
                symbol = str(profile.get("symbol") or "").upper().strip()
                stock_id = str(profile.get("stock_id") or "").strip()
                if not symbol or symbol not in vn100_symbols:
                    continue
                profile_by_symbol[symbol] = profile
                if stock_id:
                    profile_by_stock_id[stock_id] = profile

            if not profile_by_stock_id:
                return []

            prices = MarketService._fetch_rows_by_stock_ids(
                "Current_Stock_Price",
                "stock_id, current_price, price_change, per_price_change, total_match_vol",
                list(profile_by_stock_id.keys()),
            )
            price_by_stock_id: Dict[str, Dict[str, Any]] = {}
            price_by_symbol: Dict[str, Dict[str, Any]] = {}
            for price in prices:
                stock_id = str(price.get("stock_id") or "").strip()
                profile = profile_by_stock_id.get(stock_id)
                if not stock_id or not profile:
                    continue

                symbol = str(profile.get("symbol") or "").upper().strip()
                if not symbol:
                    continue

                price_by_stock_id[stock_id] = price
                price_by_symbol[symbol] = price

            def public_row(profile: Dict[str, Any], price: Dict[str, Any]) -> Dict[str, Any]:
                return {
                    "logo": profile.get("logo") or "",
                    "symbol": str(profile.get("symbol") or "").upper().strip(),
                    "company_name": profile.get("company_name") or "",
                    "current_price": MarketService._to_float(price.get("current_price")),
                    "price_change": MarketService._to_float(price.get("price_change")),
                    "per_price_change": MarketService._to_float(price.get("per_price_change")),
                }

            # ── Community categories: rank by interaction count ──────────────
            if msg_type in ("top_searched", "top_watchlist"):
                table = "Search_History" if msg_type == "top_searched" else "Favorite"
                rows = MarketService._fetch_rows_by_stock_ids(
                    table,
                    "stock_id",
                    list(profile_by_stock_id.keys()),
                )

                counts = Counter(
                    str(row.get("stock_id") or "").strip()
                    for row in rows
                    if row.get("stock_id")
                    and str(row.get("stock_id") or "").strip() in profile_by_stock_id
                )

                ranked_items: List[Dict[str, Any]] = []
                for stock_id, _count in sorted(
                    counts.items(),
                    key=lambda item: (
                        -item[1],
                        str(profile_by_stock_id.get(item[0], {}).get("symbol") or ""),
                    ),
                )[offset:page_end]:
                    profile = profile_by_stock_id.get(stock_id)
                    if not profile:
                        continue
                    symbol = str(profile.get("symbol") or "").upper().strip()
                    if not symbol:
                        continue
                    price = price_by_symbol.get(symbol, {})
                    ranked_items.append(public_row(profile, price))

                return ranked_items

            # ── Period-based trend (1w / 1mo / 3mo / 6mo) ────────────────────
            if (
                interval in MarketService._INVESTING_IDEA_PERIOD_DAYS
                and msg_type in MarketService._INVESTING_IDEA_TREND_TYPES
            ):
                period_rows = MarketService._build_period_trend_rows(
                    profile_by_stock_id,
                    price_by_stock_id,
                    MarketService._INVESTING_IDEA_PERIOD_DAYS[interval],
                )

                if msg_type == "top_gainers":
                    selected = sorted(
                        period_rows, key=lambda x: x["per_price_change"], reverse=True
                    )[offset:page_end]
                elif msg_type == "top_decliners":
                    selected = sorted(
                        period_rows, key=lambda x: x["per_price_change"]
                    )[offset:page_end]
                else:  # top_volume
                    selected = sorted(
                        [r for r in period_rows if r["_vol_change"] is not None],
                        key=lambda x: x["_vol_change"],
                        reverse=True,
                    )[offset:page_end]

                return [
                    {k: v for k, v in row.items() if not k.startswith("_")}
                    for row in selected
                ]

            # ── Trend / top-choice categories: rank by price metrics ─────────
            items: List[Dict[str, Any]] = []
            for symbol, price in price_by_symbol.items():
                if not symbol or len(symbol) > 3:
                    continue
                if symbol not in profile_by_symbol:
                    continue

                profile = profile_by_symbol[symbol]
                row = public_row(profile, price)
                row["_total_match_vol"] = MarketService._to_float(price.get("total_match_vol"))
                items.append(row)

            if msg_type == "top_gainers":
                selected = sorted(items, key=lambda x: x["per_price_change"], reverse=True)[offset:page_end]
            elif msg_type == "top_decliners":
                selected = sorted(items, key=lambda x: x["per_price_change"])[offset:page_end]
            elif msg_type == "top_volume":
                selected = sorted(items, key=lambda x: x["_total_match_vol"], reverse=True)[offset:page_end]
            else:  # cheap_under_50k
                selected = sorted(
                    [item for item in items if 0 < item["current_price"] < 50],
                    key=lambda x: (-x["current_price"], -x["_total_match_vol"], x["symbol"]),
                )[offset:page_end]

            # Drop internal-only fields (prefixed with "_") from the response.
            return [
                {k: v for k, v in row.items() if not k.startswith("_")}
                for row in selected
            ]
        except Exception as e:
            print(f"Error fetching investing idea ({msg_type}): {e}")
            return []
