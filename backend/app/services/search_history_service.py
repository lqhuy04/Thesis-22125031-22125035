"""
Search history service.
Stores the last 6 unique searched stocks per user.
"""
from typing import Any, Dict, List
import secrets
import time
import uuid

from supabase import Client, create_client

from app.config import settings


supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


class SearchHistoryService:
    TABLE_NAME = "Search_History"
    MAX_RECORDS = 6

    @staticmethod
    def _generate_uuid7() -> str:
        timestamp_ms = int(time.time_ns() // 1_000_000)
        random_a = secrets.randbits(12)
        random_b = secrets.randbits(62)

        value = (
            (timestamp_ms & ((1 << 48) - 1)) << 80
            | 0x7 << 76
            | (random_a & ((1 << 12) - 1)) << 64
            | 0x2 << 62
            | (random_b & ((1 << 62) - 1))
        )
        return str(uuid.UUID(int=value))

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        return (symbol or "").strip().upper()

    @staticmethod
    def _to_float(value: Any) -> float:
        try:
            if value is None or value == "":
                return 0.0
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _fetch_profile_map(stock_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        if not stock_ids:
            return {}

        try:
            result = (
                supabase.table("BI_Profile")
                .select("stock_id, symbol, company_name")
                .in_("stock_id", stock_ids)
                .execute()
            )
            return {
                str(item.get("stock_id") or ""): item
                for item in (result.data or [])
                if item.get("stock_id")
            }
        except Exception:
            return {}

    @staticmethod
    def _fetch_price_map(symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        if not symbols:
            return {}

        try:
            result = (
                supabase.table("Current_Stock_Price")
                .select("symbol, current_price, per_price_change")
                .in_("symbol", symbols)
                .execute()
            )
            return {
                str(item.get("symbol") or "").upper(): item
                for item in (result.data or [])
                if item.get("symbol")
            }
        except Exception:
            return {}

    @staticmethod
    def _build_response(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not rows:
            return []

        stock_ids = [str(row.get("stock_id") or "") for row in rows if row.get("stock_id")]
        profile_map = SearchHistoryService._fetch_profile_map(stock_ids)

        symbols = [
            str(profile_map.get(stock_id, {}).get("symbol") or "").upper()
            for stock_id in stock_ids
            if profile_map.get(stock_id, {}).get("symbol")
        ]
        price_map = SearchHistoryService._fetch_price_map(symbols)

        response: List[Dict[str, Any]] = []
        for row in rows:
            stock_id = str(row.get("stock_id") or "")
            profile = profile_map.get(stock_id, {})
            symbol = str(profile.get("symbol") or "").upper()
            if not symbol:
                continue

            price = price_map.get(symbol, {})

            response.append(
                {
                    "symbol": symbol,
                    "current_price": SearchHistoryService._to_float(price.get("current_price")),
                    "per_price_change": SearchHistoryService._to_float(price.get("per_price_change")),
                }
            )

        return response

    @staticmethod
    def _resolve_stock_id(symbol: str) -> str:
        result = (
            supabase.table("BI_Profile")
            .select("stock_id, symbol")
            .eq("symbol", symbol)
            .limit(1)
            .execute()
        )

        if not result.data:
            raise ValueError(f"Stock symbol not found: {symbol}")

        stock_id = str(result.data[0].get("stock_id") or "").strip()
        if not stock_id:
            raise ValueError(f"Stock symbol not found: {symbol}")

        return stock_id

    @staticmethod
    def list_search_history_by_user_id(user_id: str) -> List[Dict[str, Any]]:
        try:
            result = (
                supabase.table(SearchHistoryService.TABLE_NAME)
                .select("stock_id, id")
                .eq("user_id", user_id)
                .order("id", desc=True)
                .execute()
            )
            rows = result.data or []
            return SearchHistoryService._build_response(rows)
        except Exception as e:
            print(f"Error listing search history by user_id: {e}")
            raise ValueError(f"Failed to list search history by user_id: {str(e)}")

    @staticmethod
    def add_search_history(symbol: str, user_id: str) -> List[Dict[str, Any]]:
        try:
            sym = SearchHistoryService._normalize_symbol(symbol)
            if not sym:
                raise ValueError("Symbol is required")

            stock_id = SearchHistoryService._resolve_stock_id(sym)

            existing = (
                supabase.table(SearchHistoryService.TABLE_NAME)
                .select("stock_id")
                .eq("user_id", user_id)
                .eq("stock_id", stock_id)
                .limit(1)
                .execute()
            )
            if existing.data:
                return SearchHistoryService.list_search_history_by_user_id(user_id)

            ordered_rows = (
                supabase.table(SearchHistoryService.TABLE_NAME)
                .select("id, stock_id")
                .eq("user_id", user_id)
                .order("id", desc=False)
                .execute()
            ).data or []

            if len(ordered_rows) >= SearchHistoryService.MAX_RECORDS:
                oldest_row = ordered_rows[0]
                oldest_id = oldest_row.get("id")
                if oldest_id:
                    supabase.table(SearchHistoryService.TABLE_NAME) \
                        .delete() \
                        .eq("user_id", user_id) \
                        .eq("id", oldest_id) \
                        .execute()

            supabase.table(SearchHistoryService.TABLE_NAME).insert(
                {
                    "id": SearchHistoryService._generate_uuid7(),
                    "user_id": user_id,
                    "stock_id": stock_id,
                }
            ).execute()

            return SearchHistoryService.list_search_history_by_user_id(user_id)
        except ValueError:
            raise
        except Exception as e:
            print(f"Error adding search history: {e}")
            raise ValueError(f"Failed to add search history: {str(e)}")

    @staticmethod
    def remove_search_history_by_symbol(symbol: str, user_id: str) -> List[Dict[str, Any]]:
        try:
            sym = SearchHistoryService._normalize_symbol(symbol)
            if not sym:
                raise ValueError("Symbol is required")

            stock_id = SearchHistoryService._resolve_stock_id(sym)

            supabase.table(SearchHistoryService.TABLE_NAME) \
                .delete() \
                .eq("user_id", user_id) \
                .eq("stock_id", stock_id) \
                .execute()

            return SearchHistoryService.list_search_history_by_user_id(user_id)
        except ValueError:
            raise
        except Exception as e:
            print(f"Error removing search history by symbol: {e}")
            raise ValueError(f"Failed to remove search history by symbol: {str(e)}")

    @staticmethod
    def clear_search_history(user_id: str) -> List[Dict[str, Any]]:
        try:
            supabase.table(SearchHistoryService.TABLE_NAME) \
                .delete() \
                .eq("user_id", user_id) \
                .execute()
            return []
        except Exception as e:
            print(f"Error clearing search history: {e}")
            raise ValueError(f"Failed to clear search history: {str(e)}")