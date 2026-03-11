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
            supabase.table("company_profiles")
            .select("*")
            .eq("symbol", symbol.upper())
            .single()
            .execute()
        )
        return result.data or None

    @staticmethod
    def get_leaders(symbol: str) -> list[dict]:
        result = (
            supabase.table("company_leaders")
            .select("*")
            .eq("symbol", symbol.upper())
            .execute()
        )
        return result.data or []

    @staticmethod
    def get_subsidiaries(symbol: str) -> list[dict]:
        result = (
            supabase.table("company_subsidiaries")
            .select("*")
            .eq("symbol", symbol.upper())
            .execute()
        )
        return result.data or []
