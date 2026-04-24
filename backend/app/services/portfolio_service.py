"""
Portfolio Service
Handles database operations for portfolios and holdings.
"""
from typing import Any, Dict, List, Optional
from supabase import create_client, Client
from app.config import settings

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


class PortfolioService:
    """Service for portfolio and holdings database operations."""

    @staticmethod
    async def list_portfolios(user_id: Optional[str] = None) -> List[Dict]:
        try:
            query = supabase.table("Portfolios").select("id, user_id, name, description")
            if user_id:
                query = query.eq("user_id", user_id)
            result = query.order("name").execute()
            return result.data or []
        except Exception as e:
            print(f"Error listing portfolios: {e}")
            raise ValueError(f"Failed to list portfolios: {str(e)}")

    @staticmethod
    async def get_portfolio_by_user_id(user_id: str) -> Optional[Dict]:
        try:
            result = (
                supabase.table("Portfolios")
                .select("id, user_id, name, description")
                .eq("user_id", user_id)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error fetching portfolio by user_id: {e}")
            raise ValueError(f"Failed to fetch portfolio by user_id: {str(e)}")

    @staticmethod
    async def get_portfolio_by_id(portfolio_id: str) -> Optional[Dict]:
        try:
            result = (
                supabase.table("Portfolios")
                .select("id, user_id, name, description")
                .eq("id", portfolio_id)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error fetching portfolio: {e}")
            raise ValueError(f"Failed to fetch portfolio: {str(e)}")

    @staticmethod
    async def create_portfolio(user_id: str, name: str, description: Optional[str] = None) -> Dict:
        try:
            existing = await PortfolioService.get_portfolio_by_user_id(user_id)
            if existing:
                raise ValueError("User already has a portfolio")

            payload = {
                "user_id": user_id,
                "name": name,
                "description": description,
            }
            result = (
                supabase.table("Portfolios")
                .insert(payload)
                .execute()
            )
            return result.data[0] if result.data else payload
        except Exception as e:
            print(f"Error creating portfolio: {e}")
            raise ValueError(f"Failed to create portfolio: {str(e)}")

    @staticmethod
    async def update_portfolio(
        portfolio_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[Dict]:
        try:
            payload = {}
            if name is not None:
                payload["name"] = name
            if description is not None:
                payload["description"] = description

            if not payload:
                raise ValueError("At least one field (name or description) must be provided")

            result = (
                supabase.table("Portfolios")
                .update(payload)
                .eq("id", portfolio_id)
                .execute()
            )

            return result.data[0] if result.data else None
        except ValueError:
            raise
        except Exception as e:
            print(f"Error updating portfolio: {e}")
            raise ValueError(f"Failed to update portfolio: {str(e)}")

    @staticmethod
    async def delete_portfolio(portfolio_id: str) -> bool:
        try:
            result = (
                supabase.table("Portfolios")
                .delete()
                .eq("id", portfolio_id)
                .execute()
            )
            return bool(result.data)
        except Exception as e:
            print(f"Error deleting portfolio: {e}")
            raise ValueError(f"Failed to delete portfolio: {str(e)}")

    @staticmethod
    def _to_float(value: Any) -> float:
        try:
            if value is None or value == "":
                return 0.0
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _enrich_holdings_with_market_data(holdings: List[Dict]) -> List[Dict]:
        if not holdings:
            return []

        symbols = list({str(h.get("ticker", "")).upper() for h in holdings if h.get("ticker")})

        prices_by_symbol: Dict[str, float] = {}
        if symbols:
            try:
                price_result = (
                    supabase.table("Current_Stock_Price")
                    .select("symbol, current_price")
                    .in_("symbol", symbols)
                    .execute()
                )
                for row in (price_result.data or []):
                    symbol = str(row.get("symbol", "")).upper()
                    prices_by_symbol[symbol] = PortfolioService._to_float(row.get("current_price"))
            except Exception as e:
                print(f"Error fetching current prices for holdings: {e}")

        names_by_symbol: Dict[str, str] = {}
        if symbols:
            try:
                profile_result = (
                    supabase.table("BI_Profile")
                    .select("symbol, company_name")
                    .in_("symbol", symbols)
                    .execute()
                )
                for row in (profile_result.data or []):
                    symbol = str(row.get("symbol", "")).upper()
                    if row.get("company_name"):
                        names_by_symbol[symbol] = row.get("company_name")
            except Exception as e:
                print(f"Error fetching company names for holdings: {e}")

        enriched: List[Dict] = []
        for row in holdings:
            symbol = str(row.get("ticker", "")).upper()
            shares = PortfolioService._to_float(row.get("shares"))
            avg_buy_price = PortfolioService._to_float(row.get("avg_buy_price"))
            current_price = prices_by_symbol.get(symbol)

            cost_value = round(shares * avg_buy_price, 4)
            market_value = round(shares * current_price, 4) if current_price is not None else 0.0
            profit_loss = round(market_value - cost_value, 4) if current_price is not None else 0.0
            profit_loss_percent = round((profit_loss / cost_value) * 100, 4) if cost_value > 0 else 0.0

            enriched.append({
                "id": row.get("id"),
                "portfolio_id": row.get("portfolio_id"),
                "ticker": symbol,
                "company_name": row.get("company_name") or names_by_symbol.get(symbol),
                "shares": shares,
                "avg_buy_price": avg_buy_price,
                "current_price": current_price,
                "cost_value": cost_value,
                "market_value": market_value,
                "profit_loss": profit_loss,
                "profit_loss_percent": profit_loss_percent,
            })

        return enriched

    @staticmethod
    async def list_holdings(portfolio_id: str) -> List[Dict]:
        try:
            result = (
                supabase.table("Holdings")
                .select("id, portfolio_id, ticker, company_name, shares, avg_buy_price")
                .eq("portfolio_id", portfolio_id)
                .order("ticker")
                .execute()
            )
            return PortfolioService._enrich_holdings_with_market_data(result.data or [])
        except Exception as e:
            print(f"Error listing holdings: {e}")
            raise ValueError(f"Failed to list holdings: {str(e)}")

    @staticmethod
    async def get_holding_by_id(portfolio_id: str, holding_id: str) -> Optional[Dict]:
        try:
            result = (
                supabase.table("Holdings")
                .select("id, portfolio_id, ticker, company_name, shares, avg_buy_price")
                .eq("portfolio_id", portfolio_id)
                .eq("id", holding_id)
                .limit(1)
                .execute()
            )
            data = result.data or []
            if not data:
                return None
            return PortfolioService._enrich_holdings_with_market_data(data)[0]
        except Exception as e:
            print(f"Error fetching holding: {e}")
            raise ValueError(f"Failed to fetch holding: {str(e)}")

    @staticmethod
    async def add_holding(
        portfolio_id: str,
        ticker: str,
        shares: float,
        buy_price: float,
        company_name: Optional[str] = None,
    ) -> Dict:
        try:
            symbol = ticker.upper().strip()

            existing = (
                supabase.table("Holdings")
                .select("id, shares, avg_buy_price")
                .eq("portfolio_id", portfolio_id)
                .eq("ticker", symbol)
                .limit(1)
                .execute()
            )

            if existing.data:
                old = existing.data[0]
                old_shares = PortfolioService._to_float(old.get("shares"))
                old_avg = PortfolioService._to_float(old.get("avg_buy_price"))
                new_total_shares = old_shares + shares
                new_avg = ((old_shares * old_avg) + (shares * buy_price)) / new_total_shares

                updated = (
                    supabase.table("Holdings")
                    .update({
                        "shares": new_total_shares,
                        "avg_buy_price": round(new_avg, 4),
                        "company_name": company_name,
                    })
                    .eq("id", old.get("id"))
                    .execute()
                )
                row = updated.data[0] if updated.data else {
                    "id": old.get("id"),
                    "portfolio_id": portfolio_id,
                    "ticker": symbol,
                    "company_name": company_name,
                    "shares": new_total_shares,
                    "avg_buy_price": round(new_avg, 4),
                }
            else:
                inserted = (
                    supabase.table("Holdings")
                    .insert({
                        "portfolio_id": portfolio_id,
                        "ticker": symbol,
                        "company_name": company_name,
                        "shares": shares,
                        "avg_buy_price": round(buy_price, 4),
                    })
                    .execute()
                )
                row = inserted.data[0] if inserted.data else {
                    "portfolio_id": portfolio_id,
                    "ticker": symbol,
                    "company_name": company_name,
                    "shares": shares,
                    "avg_buy_price": round(buy_price, 4),
                }

            return PortfolioService._enrich_holdings_with_market_data([row])[0]
        except Exception as e:
            print(f"Error adding holding: {e}")
            raise ValueError(f"Failed to add holding: {str(e)}")

    @staticmethod
    async def update_holding(
        portfolio_id: str,
        holding_id: str,
        shares: Optional[float] = None,
        avg_buy_price: Optional[float] = None,
        company_name: Optional[str] = None,
    ) -> Optional[Dict]:
        try:
            payload: Dict[str, Any] = {}
            if shares is not None:
                payload["shares"] = shares
            if avg_buy_price is not None:
                payload["avg_buy_price"] = round(avg_buy_price, 4)
            if company_name is not None:
                payload["company_name"] = company_name

            if not payload:
                raise ValueError("At least one field (shares, avg_buy_price, company_name) must be provided")

            result = (
                supabase.table("Holdings")
                .update(payload)
                .eq("portfolio_id", portfolio_id)
                .eq("id", holding_id)
                .execute()
            )

            if not result.data:
                return None

            return PortfolioService._enrich_holdings_with_market_data([result.data[0]])[0]
        except ValueError:
            raise
        except Exception as e:
            print(f"Error updating holding: {e}")
            raise ValueError(f"Failed to update holding: {str(e)}")

    @staticmethod
    async def delete_holding(portfolio_id: str, holding_id: str) -> bool:
        try:
            result = (
                supabase.table("Holdings")
                .delete()
                .eq("portfolio_id", portfolio_id)
                .eq("id", holding_id)
                .execute()
            )
            return bool(result.data)
        except Exception as e:
            print(f"Error deleting holding: {e}")
            raise ValueError(f"Failed to delete holding: {str(e)}")

    @staticmethod
    async def get_holdings_summary(portfolio_id: str) -> Dict:
        holdings = await PortfolioService.list_holdings(portfolio_id)
        total_cost = round(sum(PortfolioService._to_float(h.get("cost_value")) for h in holdings), 4)
        total_market_value = round(sum(PortfolioService._to_float(h.get("market_value")) for h in holdings), 4)
        total_profit_loss = round(total_market_value - total_cost, 4)
        total_profit_loss_percent = round((total_profit_loss / total_cost) * 100, 4) if total_cost > 0 else 0.0

        return {
            "portfolio_id": portfolio_id,
            "holding_count": len(holdings),
            "total_cost": total_cost,
            "total_market_value": total_market_value,
            "total_profit_loss": total_profit_loss,
            "total_profit_loss_percent": total_profit_loss_percent,
        }
