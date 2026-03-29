"""
Company Profile Database Service
Handles queries for company_profiles, company_leaders, company_subsidiaries.
"""
from supabase import create_client, Client
from app.config import get_settings
from typing import Optional

settings = get_settings()
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


class CompanyService:

    @staticmethod
    def get_profile(symbol: str) -> Optional[dict]:
        result = (
            supabase.table("Stock")
            .select("id, BI_Profile(*)")   # embedded resource qua FK
            .eq("stock_symbol", symbol.upper())
            .single()
            .execute()
        )
        
        if not result.data:
            return None

        return result.data.get("BI_Profile")[0] or None

    @staticmethod
    def get_leaders(symbol: str) -> list[dict]:
        result = (
            supabase.table("Stock")
            .select("id, BI_Leader(*)")
            .eq("stock_symbol", symbol.upper())
            .single()
            .execute()
        )
        
        if not result.data:
            return []
        
        return result.data.get("BI_Leader") or []

    @staticmethod
    def get_subsidiaries(symbol: str) -> list[dict]:
        result = (
            supabase.table("Stock")
            .select("id, BI_Subsidiary(*)")
            .eq("stock_symbol", symbol.upper())
            .single()
            .execute()
        )
        if not result.data:
            return []
        
        return result.data.get("BI_Subsidiary") or []
