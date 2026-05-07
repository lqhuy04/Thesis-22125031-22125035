"""
Favorite Service
Handles operations for the Favorite table.
Each row represents a favorited stock with `stock_id`, and `user_id`.
GET groups favorites for user and returns enriched profile data.
"""
from typing import Any, Dict, List

from supabase import Client, create_client

from app.config import settings

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


class FavoriteService:
    """Service for favorite operations."""

    TABLE_NAME = "Favorite"

    @staticmethod
    def _normalize_row(row: Dict) -> Dict:
        return {
            "id": row.get("id"),
            "stock_id": row.get("stock_id"),
            "user_id": row.get("user_id"),
        }

    @staticmethod
    async def list_favorites_by_user_id(user_id: str) -> List[Dict]:
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
                        .select("stock_id, symbol, company_name, exchange")
                        .in_("stock_id", stock_ids)
                        .execute()
                    )
                    for p in (profile_result.data or []):
                        profiles_by_stock[str(p.get("stock_id"))] = p
                except Exception:
                    pass

            # build response
            response: List[Dict] = []
            for row in rows:
                sid = row.get("stock_id")
                profile = profiles_by_stock.get(sid, {})

                response.append({
                    "id": row.get("id"),
                    "stock_id": sid,
                    "user_id": user_id,
                    "symbol": profile.get("symbol", ""),
                    "company_name": profile.get("company_name", ""),
                    "exchange": profile.get("exchange", ""),
                })

            return response
        except Exception as e:
            print(f"Error listing favorites by user_id: {e}")
            raise ValueError(f"Failed to list favorites by user_id: {str(e)}")

    @staticmethod
    async def add_favorite(symbol: str, user_id: str) -> Dict:
        try:
            # resolve symbol -> stock_id from BI_Profile
            sym = symbol.strip().upper()

            try:
                prof_res = (
                    supabase.table("BI_Profile")
                    .select("stock_id")
                    .eq("symbol", sym)
                    .limit(1)
                    .execute()
                )
                if not prof_res.data or not prof_res.data[0].get("stock_id"):
                    raise ValueError(f"Stock symbol not found: {symbol}")
                stock_id = prof_res.data[0].get("stock_id")
            except ValueError:
                raise
            except Exception as e:
                raise ValueError(f"Stock symbol not found: {symbol}")

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
    async def delete_favorites(favorite_ids: List[str]) -> bool:
        try:
            if not favorite_ids:
                return False

            result = (
                supabase.table(FavoriteService.TABLE_NAME)
                .delete()
                .in_("id", favorite_ids)
                .execute()
            )

            return bool(result.data)
        except Exception as e:
            print(f"Error deleting favorites: {e}")
            raise ValueError(f"Failed to delete favorites: {str(e)}")

    @staticmethod
    async def remove_favorite_by_stock_id(stock_id: str, user_id: str) -> bool:
        try:
            result = (
                supabase.table(FavoriteService.TABLE_NAME)
                .delete()
                .eq("stock_id", stock_id)
                .eq("user_id", user_id)
                .execute()
            )

            return bool(result.data)
        except Exception as e:
            print(f"Error removing favorite by stock_id: {e}")
            raise ValueError(f"Failed to remove favorite by stock_id: {str(e)}")

    @staticmethod
    async def check_is_favorited(symbol: str, user_id: str) -> Dict:
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
