"""
Financial Database Service
Handles database operations for financial metrics
"""
from supabase import create_client, Client
from app.config import settings
from typing import Optional, List, Dict
from datetime import datetime

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

class FinancialDBService:
    """Service for financial metrics database operations"""
    
    @staticmethod
    async def get_financial_metrics_by_symbol(
        symbol: str,
        year: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Get financial metrics for a specific symbol
        
        Args:
            symbol: Stock symbol (e.g., 'VNM')
            year: Specific year to filter (optional)
            limit: Maximum number of records to return (optional)
        
        Returns:
            List of financial metrics records
        """
        try:
            # Build query
            query = supabase.table("financial_metrics").select("*").eq("symbol", symbol.upper())
            
            # Add year filter if provided
            if year:
                query = query.eq("year", year)
            
            # Order by year descending (most recent first)
            query = query.order("year", desc=True)
            
            # Apply limit if provided
            if limit:
                query = query.limit(limit)
            
            # Execute query
            result = query.execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error fetching financial metrics: {e}")
            raise ValueError(f"Failed to fetch financial metrics: {str(e)}")
    
    @staticmethod
    async def get_latest_financial_metrics(symbol: str) -> Optional[Dict]:
        """
        Get the most recent financial metrics for a symbol
        
        Args:
            symbol: Stock symbol
        
        Returns:
            Latest financial metrics record or None
        """
        try:
            result = await FinancialDBService.get_financial_metrics_by_symbol(
                symbol=symbol,
                limit=1
            )
            return result[0] if result else None
            
        except Exception as e:
            print(f"Error fetching latest financial metrics: {e}")
            return None
    
    @staticmethod
    async def get_available_years(symbol: str) -> List[str]:
        """
        Get list of available years for a symbol
        
        Args:
            symbol: Stock symbol
        
        Returns:
            List of years as strings
        """
        try:
            result = supabase.table("financial_metrics")\
                .select("year")\
                .eq("symbol", symbol.upper())\
                .order("year", desc=True)\
                .execute()
            
            if result.data:
                return [record["year"] for record in result.data]
            return []
            
        except Exception as e:
            print(f"Error fetching available years: {e}")
            return []
    
    @staticmethod
    async def insert_financial_metrics(metrics_data: List[Dict]) -> bool:
        """
        Insert financial metrics records into database
        
        Args:
            metrics_data: List of financial metrics dictionaries
        
        Returns:
            True if successful, False otherwise
        """
        try:
            result = supabase.table("financial_metrics").insert(metrics_data).execute()
            return bool(result.data)
            
        except Exception as e:
            print(f"Error inserting financial metrics: {e}")
            raise ValueError(f"Failed to insert financial metrics: {str(e)}")
    
    @staticmethod
    async def upsert_financial_metrics(metrics_data: List[Dict]) -> bool:
        """
        Upsert (insert or update) financial metrics records
        Updates existing records based on symbol + year combination
        
        Args:
            metrics_data: List of financial metrics dictionaries
        
        Returns:
            True if successful, False otherwise
        """
        try:
            result = supabase.table("financial_metrics")\
                .upsert(metrics_data, on_conflict="symbol,year")\
                .execute()
            return bool(result.data)
            
        except Exception as e:
            print(f"Error upserting financial metrics: {e}")
            raise ValueError(f"Failed to upsert financial metrics: {str(e)}")

    @staticmethod
    async def get_balance_sheets(symbol: str, year: Optional[int] = None) -> List[Dict]:
        """
        Get balance sheets for a specific symbol
        """
        try:
            query = supabase.table("financial_balance_sheets").select("*").eq("symbol", symbol.upper())
            if year:
                query = query.eq("year", year)
            query = query.order("year", desc=True)
            result = query.execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Error fetching balance sheets: {e}")
            raise ValueError(f"Failed to fetch balance sheets: {str(e)}")

    @staticmethod
    async def get_cash_flows(symbol: str, year: Optional[int] = None) -> List[Dict]:
        """
        Get cash flows for a specific symbol
        """
        try:
            query = supabase.table("financial_cash_flows").select("*").eq("symbol", symbol.upper())
            if year:
                query = query.eq("year", year)
            query = query.order("year", desc=True)
            result = query.execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Error fetching cash flows: {e}")
            raise ValueError(f"Failed to fetch cash flows: {str(e)}")

    @staticmethod
    async def get_financial_indicators(symbol: str, year: Optional[int] = None) -> List[Dict]:
        """
        Get financial indicators for a specific symbol
        """
        try:
            query = supabase.table("financial_indicators").select("*").eq("symbol", symbol.upper())
            if year:
                query = query.eq("year", year)
            query = query.order("year", desc=True)
            result = query.execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Error fetching financial indicators: {e}")
            raise ValueError(f"Failed to fetch financial indicators: {str(e)}")

    @staticmethod
    async def get_income_statements(symbol: str, year: Optional[int] = None) -> List[Dict]:
        """
        Get income statements for a specific symbol
        """
        try:
            query = supabase.table("financial_income_statements").select("*").eq("symbol", symbol.upper())
            if year:
                query = query.eq("year", year)
            query = query.order("year", desc=True)
            result = query.execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Error fetching income statements: {e}")
            raise ValueError(f"Failed to fetch income statements: {str(e)}")

