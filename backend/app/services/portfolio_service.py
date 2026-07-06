"""
Portfolio Service
Handles transaction-oriented operations for the Portfolio table.
Each row is a transaction (buy) with `stock_id`, `user_id`, `amount`, `buy_price`, and `time`.
GET groups transactions by `stock_id` and returns market/profile enrichment plus sorted history.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.utils.supabase_client import supabase

from app.config import settings


class PortfolioService:
    """Service for portfolio transaction operations."""

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
            "buy_price": PortfolioService._to_float(row.get("buy_price")),
            "time": row.get("time"),
        }

    @staticmethod
    def list_portfolios_by_user_id(user_id: str) -> List[Dict]:
        try:
            # fetch user transactions ordered by time (oldest first)
            result = (
                supabase.table(PortfolioService.TABLE_NAME)
                .select("id, stock_id, user_id, amount, buy_price, time")
                .eq("user_id", user_id)
                .order("time")
                .execute()
            )

            rows: List[Dict] = result.data or []

            # group by stock_id
            groups: Dict[str, Dict] = {}
            for r in rows:
                sid = r.get("stock_id")
                if not sid:
                    continue
                if sid not in groups:
                    groups[sid] = {"stock_id": sid, "user_id": user_id, "history": [], "id": r.get("id")}
                groups[sid]["history"].append({
                    "id": r.get("id"),
                    "amount": PortfolioService._to_float(r.get("amount")),
                    "buy_price": PortfolioService._to_float(r.get("buy_price")),
                    "time": r.get("time"),
                })

            stock_ids = list(groups.keys())

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
            symbols = [profiles_by_stock[sid].get("symbol") for sid in stock_ids if profiles_by_stock.get(sid) and profiles_by_stock[sid].get("symbol")]
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

            # build grouped response
            response: List[Dict] = []
            for sid, group in groups.items():
                profile = profiles_by_stock.get(sid, {})
                symbol = (profile.get("symbol") or "")
                price_row = prices_by_symbol.get(str(symbol).upper(), {})

                # map price fields with safe defaults
                current_price = PortfolioService._to_float(price_row.get("current_price"))
                price_change = PortfolioService._to_float(price_row.get("price_change") or price_row.get("PriceChange"))
                per_price_change = PortfolioService._to_float(price_row.get("per_price_change") or price_row.get("PerPriceChange"))
                ceiling_price = PortfolioService._to_float(price_row.get("ceiling_price"))
                floor_price = PortfolioService._to_float(price_row.get("floor_price"))
                ref_price = PortfolioService._to_float(price_row.get("ref_price") or price_row.get("RefPrice"))
                total_match_vol = PortfolioService._to_float(price_row.get("total_match_vol") or price_row.get("TotalMatchVol"))
                total_match_val = PortfolioService._to_float(price_row.get("total_match_val") or price_row.get("TotalMatchVal"))

                response.append({
                    "id": group.get("id"),
                    "stock_id": sid,
                    "symbol": symbol,
                    "company_name": profile.get("company_name"),
                    "logo": profile.get("logo"),
                    "exchange": profile.get("exchange"),
                    "PriceChange": price_change,
                    "PerPriceChange": per_price_change,
                    "CeilingPrice": ceiling_price,
                    "FloorPrice": floor_price,
                    "RefPrice": ref_price,
                    "CurrentPrice": current_price,
                    "TotalMatchVol": total_match_vol,
                    "TotalMatchVal": total_match_val,
                    "history": group.get("history", []),
                })

            return response
        except Exception as e:
            print(f"Error listing portfolios by user_id: {e}")
            raise ValueError(f"Failed to list portfolios by user_id: {str(e)}")

    @staticmethod
    def create_portfolio(symbol: str, user_id: str, amount: float, buy_price: float, time: Optional[datetime] = None) -> Dict:
        try:
            # resolve symbol -> stock_id
            sym = symbol.strip().upper()

            stock_id = None
            # 1) try BI_Profile.symbol -> stock_id (preferred)
            try:
                prof_res = (
                    supabase.table("BI_Profile")
                    .select("stock_id")
                    .eq("symbol", sym)
                    .limit(1)
                    .execute()
                )
                if prof_res.data and prof_res.data[0].get("stock_id"):
                    stock_id = prof_res.data[0].get("stock_id")
            except Exception:
                # ignore and fallback
                pass

            # 2) fallback to Stock.stock_symbol -> id
            if not stock_id:
                try:
                    stock_res = (
                        supabase.table("Stock")
                        .select("id")
                        .eq("stock_symbol", sym)
                        .limit(1)
                        .execute()
                    )
                    if stock_res.data:
                        stock_id = stock_res.data[0].get("id")
                except Exception:
                    pass

            if not stock_id:
                raise ValueError(f"Stock symbol not found: {symbol}")

            payload = {
                "stock_id": stock_id,
                "user_id": user_id.strip(),
                "amount": amount,
                "buy_price": round(buy_price, 4),
                "time": (time.isoformat() if time else datetime.utcnow().isoformat()),
            }

            result = supabase.table(PortfolioService.TABLE_NAME).insert(payload).execute()
            if not result.data:
                return payload
            return PortfolioService._normalize_row(result.data[0])
        except Exception as e:
            print(f"Error creating portfolio transaction: {e}")
            raise ValueError(f"Failed to create portfolio transaction: {str(e)}")

    @staticmethod
    def update_portfolio(
        portfolio_id: str,
        amount: Optional[float] = None,
        buy_price: Optional[float] = None,
        time: Optional[datetime] = None,
    ) -> Optional[Dict]:
        try:
            payload: Dict[str, Any] = {}
            if amount is not None:
                payload["amount"] = amount
            if buy_price is not None:
                payload["buy_price"] = round(buy_price, 4)
            if time is not None:
                payload["time"] = time.isoformat()

            if not payload:
                raise ValueError("At least one field (amount, buy_price, time) must be provided")

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
            print(f"Error updating portfolio transaction: {e}")
            raise ValueError(f"Failed to update portfolio transaction: {str(e)}")

    @staticmethod
    def delete_portfolios(portfolio_ids: List[str]) -> bool:
        try:
            if not portfolio_ids:
                return False

            result = (
                supabase.table(PortfolioService.TABLE_NAME)
                .delete()
                .in_("id", portfolio_ids)
                .execute()
            )

            return bool(result.data)

        except Exception as e:
            print(f"Error deleting portfolios: {e}")
            raise ValueError(f"Failed to delete portfolios: {str(e)}")
