"""
Financial Database Service
Handles database operations for financial metrics
"""
from supabase import create_client, Client
from app.config import settings
from typing import Optional, List, Dict

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

class FundamentalAnalysisService:
    """Service for financial metrics database operations"""

    @staticmethod
    async def get_summary(symbol: str) -> Optional[Dict]:
        """
        Get AI-generated fundamental summary for a specific symbol.

        Args:
            symbol: Stock symbol (e.g., 'VNM')

        Returns:
            Summary record with symbol and summary fields, or None if not found
        """
        try:
            result = supabase.table("Stock") \
                .select("id, FA_Summary(*)") \
                .eq("stock_symbol", symbol.upper()) \
                .single() \
                .execute()

            if not result.data:
                return None
        
            return result.data.get("FA_Summary")[0] or None

        except Exception as e:
            print(f"Error fetching fundamental summary: {e}")
            raise ValueError(f"Failed to fetch fundamental summary: {str(e)}")

    @staticmethod
    async def get_balance_sheets(symbol: str) -> List[Dict]:
        """
        Get balance sheets for a specific symbol
        """
        try:
            result = supabase.table("Stock").select("id, FA_BalanceSheet(*)").eq("stock_symbol", symbol.upper()).single().execute()
            
            if not result.data:
                return []
            
            return result.data.get("FA_BalanceSheet") or []
            
        except Exception as e:
            print(f"Error fetching balance sheets: {e}")
            raise ValueError(f"Failed to fetch balance sheets: {str(e)}")

    @staticmethod
    async def get_cash_flows(symbol: str) -> List[Dict]:
        """
        Get cash flows for a specific symbol
        """
        try:
            result = supabase.table("Stock").select("id, FA_CashFlow(*)").eq("stock_symbol", symbol.upper()).single().execute()
            
            if not result.data:
                return []
            
            return result.data.get("FA_CashFlow") or []
        except Exception as e:
            print(f"Error fetching cash flows: {e}")
            raise ValueError(f"Failed to fetch cash flows: {str(e)}")

    @staticmethod
    async def get_indicators(symbol: str ) -> List[Dict]:
        """
        Get financial indicators for a specific symbol
        """
        try:
            result = supabase.table("Stock").select("id, FA_Indicator(*)").eq("stock_symbol", symbol.upper()).single().execute()
            
            if not result.data:
                return []
            
            return result.data.get("FA_Indicator") or []
        except Exception as e:
            print(f"Error fetching financial indicators: {e}")
            raise ValueError(f"Failed to fetch financial indicators: {str(e)}")

    @staticmethod
    async def get_income_statements(symbol: str ) -> List[Dict]:
        """
        Get income statements for a specific symbol
        """
        try:
            result = supabase.table("Stock").select("id, FA_IncomeStatement(*)").eq("stock_symbol", symbol.upper()).single().execute()
            
            if not result.data:
                return []
            
            return result.data.get("FA_IncomeStatement") or []
        except Exception as e:
            print(f"Error fetching income statements: {e}")
            raise ValueError(f"Failed to fetch income statements: {str(e)}")

