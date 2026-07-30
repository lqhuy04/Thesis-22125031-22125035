"""
Search history service.
Stores the last 6 unique searched stocks per user.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List

from supabase import Client, create_client

from app.config import settings


supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


class SearchHistoryService:
    TABLE_NAME = "Search_History"
    MAX_RECORDS = 6

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
    def _fetch_price_map(stock_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        if not stock_ids:
            return {}

        try:
            result = (
                supabase.table("Current_Stock_Price")
                .select("stock_id, current_price, per_price_change")
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
    def _build_response(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not rows:
            return []

        stock_ids = list(dict.fromkeys(
            str(row.get("stock_id") or "")
            for row in rows
            if row.get("stock_id")
        ))
        profile_map = SearchHistoryService._fetch_profile_map(stock_ids)
        price_map = SearchHistoryService._fetch_price_map(stock_ids)

        response: List[Dict[str, Any]] = []
        for row in rows:
            stock_id = str(row.get("stock_id") or "")
            profile = profile_map.get(stock_id, {})
            symbol = str(profile.get("symbol") or "").upper()
            if not symbol:
                continue

            price = price_map.get(stock_id, {})

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
                .select("stock_id, searched_at")
                .eq("user_id", user_id)
                .order("searched_at", desc=True)
                .order("stock_id")
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
            searched_at = datetime.now(timezone.utc).isoformat()

            (
                supabase.table(SearchHistoryService.TABLE_NAME)
                .upsert(
                    {
                        "user_id": user_id,
                        "stock_id": stock_id,
                        "searched_at": searched_at,
                    },
                    on_conflict="user_id,stock_id",
                )
                .execute()
            )

            ordered_rows = (
                supabase.table(SearchHistoryService.TABLE_NAME)
                .select("stock_id, searched_at")
                .eq("user_id", user_id)
                .order("searched_at", desc=True)
                .order("stock_id")
                .execute()
            ).data or []

            stale_stock_ids = [
                row.get("stock_id")
                for row in ordered_rows[SearchHistoryService.MAX_RECORDS:]
                if row.get("stock_id")
            ]
            if stale_stock_ids:
                (
                    supabase.table(SearchHistoryService.TABLE_NAME)
                    .delete()
                    .eq("user_id", user_id)
                    .in_("stock_id", stale_stock_ids)
                    .execute()
                )

            return SearchHistoryService.list_search_history_by_user_id(user_id)
        except ValueError:
            raise
        except Exception as e:
            print(f"Error adding search history: {e}")
            raise ValueError(f"Failed to add search history: {str(e)}")
