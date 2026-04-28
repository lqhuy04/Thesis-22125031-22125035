"""
Portfolio Service
Handles database operations for the flat portfolio table.
"""
from typing import Any, Dict, Optional

from supabase import Client, create_client

from app.config import settings

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


class PortfolioService:
    """Service for portfolio table operations."""

    TABLE_NAME = "Portfolio"

    @staticmethod
    def _to_float(value: Any) -> float:
        try:
            if value is None or value == "":
                return 0.0
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _normalize_row(row: Dict) -> Dict:
        return {
            "id": row.get("id"),
            "stock_id": row.get("stock_id"),
            "user_id": row.get("user_id"),
            "amount": PortfolioService._to_float(row.get("amount")),
            "avg_price": PortfolioService._to_float(row.get("avg_price")),
        }

    @staticmethod
    async def list_portfolios_by_user_id(user_id: str) -> list[Dict]:
        try:
            result = (
                supabase.table(PortfolioService.TABLE_NAME)
                .select("id, stock_id, user_id, amount, avg_price")
                .eq("user_id", user_id)
                .order("id")
                .execute()
            )
            return [PortfolioService._normalize_row(row) for row in (result.data or [])]
        except Exception as e:
            print(f"Error listing portfolios by user_id: {e}")
            raise ValueError(f"Failed to list portfolios by user_id: {str(e)}")

    @staticmethod
    async def create_portfolio(stock_id: str, user_id: str, amount: float, avg_price: float) -> Dict:
        try:
            stock_key = stock_id.strip()
            user_key = user_id.strip()
            payload = {
                "stock_id": stock_key,
                "user_id": user_key,
                "amount": amount,
                "avg_price": round(avg_price, 4),
            }

            existing = (
                supabase.table(PortfolioService.TABLE_NAME)
                .select("id, stock_id, user_id, amount, avg_price")
                .eq("user_id", user_key)
                .eq("stock_id", stock_key)
                .limit(1)
                .execute()
            )

            if existing.data:
                result = (
                    supabase.table(PortfolioService.TABLE_NAME)
                    .update({
                        "amount": amount,
                        "avg_price": round(avg_price, 4),
                    })
                    .eq("id", existing.data[0].get("id"))
                    .execute()
                )
                if not result.data:
                    return PortfolioService._normalize_row(existing.data[0])
                return PortfolioService._normalize_row(result.data[0])

            result = supabase.table(PortfolioService.TABLE_NAME).insert(payload).execute()
            if not result.data:
                return payload
            return PortfolioService._normalize_row(result.data[0])
        except Exception as e:
            print(f"Error creating portfolio: {e}")
            raise ValueError(f"Failed to create portfolio: {str(e)}")

    @staticmethod
    async def update_portfolio(
        portfolio_id: str,
        amount: Optional[float] = None,
        avg_price: Optional[float] = None,
    ) -> Optional[Dict]:
        try:
            payload: Dict[str, Any] = {}
            if amount is not None:
                payload["amount"] = amount
            if avg_price is not None:
                payload["avg_price"] = round(avg_price, 4)

            if not payload:
                raise ValueError("At least one field (amount, avg_price) must be provided")

            result = (
                supabase.table(PortfolioService.TABLE_NAME)
                .update(payload)
                .eq("id", portfolio_id)
                .execute()
            )

            if not result.data:
                return None

            return PortfolioService._normalize_row(result.data[0])
        except ValueError:
            raise
        except Exception as e:
            print(f"Error updating portfolio: {e}")
            raise ValueError(f"Failed to update portfolio: {str(e)}")

    @staticmethod
    async def delete_portfolio(portfolio_id: str) -> bool:
        try:
            result = (
                supabase.table(PortfolioService.TABLE_NAME)
                .delete()
                .eq("id", portfolio_id)
                .execute()
            )
            return bool(result.data)
        except Exception as e:
            print(f"Error deleting portfolio: {e}")
            raise ValueError(f"Failed to delete portfolio: {str(e)}")
