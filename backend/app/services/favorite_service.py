"""
Favorite Service
Handles operations for the Favorite table.
Each row represents a favorited stock with `stock_id`, and `user_id`.
GET groups favorites for user and returns enriched profile data.
"""
from typing import Any, Dict, List

from app.utils.supabase_client import supabase

from app.config import settings


class FavoriteService:
    """Service for favorite operations."""

    TABLE_NAME = "Favorite"

    @staticmethod
    def _resolve_stock_id_by_symbol(symbol: str) -> str:
        sym = symbol.strip().upper()

        try:
            prof_res = (
                supabase.table("BI_Profile")
                .select("stock_id, symbol")
                .eq("symbol", sym)
                .limit(1)
                .execute()
            )
            if not prof_res.data or not prof_res.data[0].get("stock_id"):
                raise ValueError(f"Stock symbol not found: {symbol}")
            return prof_res.data[0].get("stock_id")
        except ValueError:
            raise
        except Exception:
            raise ValueError(f"Stock symbol not found: {symbol}")

    @staticmethod
    def _normalize_row(row: Dict) -> Dict:
        return {
            "id": row.get("id"),
            "stock_id": row.get("stock_id"),
            "user_id": row.get("user_id"),
        }
    
    @staticmethod
    def _to_float(value) -> float:
        try:
            return float(value) if value is not None else 0.0
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def list_favorites_by_user_id(user_id: str) -> List[Dict]:
        try:
            # fetch user favorites
            result = (
                supabase.table(FavoriteService.TABLE_NAME)
                .select("id, stock_id, user_id")
                .eq("user_id", user_id)
                .order("id")
                .execute()
            )

            rows: List[Dict] = result.data or []

            if not rows:
                return []

            stock_ids = [r.get("stock_id") for r in rows if r.get("stock_id")]

            # fetch profile info (symbol, company_name, exchange)
            profiles_by_stock: Dict[str, Dict] = {}
            if stock_ids:
                try:
                    profile_result = (
                        supabase.table("BI_Profile")
                        .select("stock_id, symbol, company_name, exchange, logo")
                        .in_("stock_id", stock_ids)
                        .execute()
                    )
                    for p in (profile_result.data or []):
                        profiles_by_stock[str(p.get("stock_id"))] = p
                except Exception:
                    pass

            # fetch current prices by symbol
            symbols = [
                profiles_by_stock[sid].get("symbol")
                for sid in stock_ids
                if profiles_by_stock.get(sid) and profiles_by_stock[sid].get("symbol")
            ]
            prices_by_symbol: Dict[str, Dict] = {}
            if symbols:
                try:
                    price_result = (
                        supabase.table("Current_Stock_Price")
                        .select("*")
                        .in_("symbol", symbols)
                        .execute()
                    )
                    for p in (price_result.data or []):
                        prices_by_symbol[str(p.get("symbol")).upper()] = p
                except Exception:
                    pass

            # build response
            response: List[Dict] = []
            for row in rows:
                sid = row.get("stock_id")
                profile = profiles_by_stock.get(sid, {})
                symbol = profile.get("symbol") or ""
                price_row = prices_by_symbol.get(str(symbol).upper(), {})

                # map price fields with safe defaults
                current_price     = FavoriteService._to_float(price_row.get("current_price"))
                price_change      = FavoriteService._to_float(price_row.get("price_change")     or price_row.get("PriceChange"))
                per_price_change  = FavoriteService._to_float(price_row.get("per_price_change") or price_row.get("PerPriceChange"))
                ceiling_price     = FavoriteService._to_float(price_row.get("ceiling_price"))
                floor_price       = FavoriteService._to_float(price_row.get("floor_price"))
                ref_price         = FavoriteService._to_float(price_row.get("ref_price")        or price_row.get("RefPrice"))
                total_match_vol   = FavoriteService._to_float(price_row.get("total_match_vol")  or price_row.get("TotalMatchVol"))
                total_match_val   = FavoriteService._to_float(price_row.get("total_match_val")  or price_row.get("TotalMatchVal"))

                response.append({
                    "id":           row.get("id"),
                    "stock_id":     sid,
                    "symbol":       symbol,
                    "company_name": profile.get("company_name", ""),
                    "exchange":     profile.get("exchange", ""),
                    "logo":         profile.get("logo", ""),
                    "PriceChange":    price_change,
                    "PerPriceChange": per_price_change,
                    "CeilingPrice":   ceiling_price,
                    "FloorPrice":     floor_price,
                    "RefPrice":       ref_price,
                    "CurrentPrice":   current_price,
                    "TotalMatchVol":  total_match_vol,
                    "TotalMatchVal":  total_match_val,
                })

            return response
        except Exception as e:
            print(f"Error listing favorites by user_id: {e}")
            raise ValueError(f"Failed to list favorites by user_id: {str(e)}")

    @staticmethod
    def add_favorite(symbol: str, user_id: str) -> Dict:
        try:
            # resolve symbol -> stock_id from BI_Profile
            stock_id = FavoriteService._resolve_stock_id_by_symbol(symbol)

            # check if favorite already exists
            try:
                existing = (
                    supabase.table(FavoriteService.TABLE_NAME)
                    .select("id")
                    .eq("stock_id", stock_id)
                    .eq("user_id", user_id.strip())
                    .limit(1)
                    .execute()
                )
                if existing.data:
                    raise ValueError(f"Stock {symbol} is already favorited")
            except ValueError:
                raise
            except Exception:
                pass

            payload = {
                "stock_id": stock_id,
                "user_id": user_id.strip(),
            }

            result = supabase.table(FavoriteService.TABLE_NAME).insert(payload).execute()
            if not result.data:
                return payload
            return FavoriteService._normalize_row(result.data[0])
        except Exception as e:
            print(f"Error adding favorite: {e}")
            raise ValueError(f"Failed to add favorite: {str(e)}")

    @staticmethod
    def remove_favorite_by_symbol(symbol: str, user_id: str) -> bool:
        try:
            stock_id = FavoriteService._resolve_stock_id_by_symbol(symbol)
            result = (
                supabase.table(FavoriteService.TABLE_NAME)
                .delete()
                .eq("stock_id", stock_id)
                .eq("user_id", user_id.strip())
                .execute()
            )

            return bool(result.data)
        except Exception as e:
            print(f"Error removing favorite by symbol: {e}")
            raise ValueError(f"Failed to remove favorite by symbol: {str(e)}")


    @staticmethod
    def check_is_favorited(symbol: str, user_id: str) -> Dict:
        """
        Efficiently check if a stock is favorited by a user.
        Uses limit(1) to avoid fetching unnecessary data.
        """
        try:
            # resolve symbol -> stock_id from BI_Profile
            sym = symbol.strip().upper()

            try:
                prof_res = (
                    supabase.table("BI_Profile")
                    .select("stock_id, symbol")
                    .eq("symbol", sym)
                    .limit(1)
                    .execute()
                )
                if not prof_res.data or not prof_res.data[0].get("stock_id"):
                    raise ValueError(f"Stock symbol not found: {symbol}")
                stock_id = prof_res.data[0].get("stock_id")
                resolved_symbol = prof_res.data[0].get("symbol", sym)
            except ValueError:
                raise
            except Exception as e:
                raise ValueError(f"Stock symbol not found: {symbol}")

            # Check if favorite exists (efficient: limit(1))
            result = (
                supabase.table(FavoriteService.TABLE_NAME)
                .select("id", count="exact")
                .eq("stock_id", stock_id)
                .eq("user_id", user_id.strip())
                .limit(1)
                .execute()
            )

            is_favorited = bool(result.data and len(result.data) > 0)

            return {
                "is_favorited": is_favorited,
                "symbol": resolved_symbol,
            }
        except Exception as e:
            print(f"Error checking if stock is favorited: {e}")
            raise ValueError(f"Failed to check if stock is favorited: {str(e)}")
