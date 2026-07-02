"""
Financial Database Service
Handles database operations for financial metrics
"""
from supabase import create_client, Client
from app.config import settings
from typing import Optional, List, Dict

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


# Mã ngành ICB cấp Industry theo chữ số đầu của mã ICB chi tiết (như bảng `category`
# lưu: 0001, 1000, ..., 9000). Dầu khí là '0001' (không phải '0000').
_ICB_INDUSTRY_CODE = {
    "0": "0001", "1": "1000", "2": "2000", "3": "3000", "4": "4000",
    "5": "5000", "6": "6000", "7": "7000", "8": "8000", "9": "9000",
}


def icb_to_industry_code(icb_code) -> Optional[str]:
    """Ánh xạ mã ICB chi tiết (vd '8355') → mã ngành ICB cấp Industry ('8000').
    Trả về None nếu mã rỗng/không hợp lệ."""
    return _ICB_INDUSTRY_CODE.get(str(icb_code or "").strip()[:1])

class FundamentalAnalysisService:
    """Service for financial metrics database operations"""

    @staticmethod
    def get_summary(symbol: str) -> Optional[Dict]:
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

            # FA_Summary may be an empty list for newly-listed stocks with no
            # summary row yet — avoid IndexError on [0].
            fa_summary = result.data.get("FA_Summary") or []
            return fa_summary[0] if fa_summary else None

        except Exception as e:
            print(f"Error fetching fundamental summary: {e}")
            raise ValueError(f"Failed to fetch fundamental summary: {str(e)}")

    @staticmethod
    def get_balance_sheets(symbol: str) -> List[Dict]:
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
    def get_cash_flows(symbol: str) -> List[Dict]:
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
    def get_indicators(symbol: str ) -> List[Dict]:
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
    def get_income_statements(symbol: str ) -> List[Dict]:
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

    @staticmethod
    def get_industry_aggregate(icb_code: str) -> List[Dict]:
        """
        Đọc chỉ tiêu TRUNG VỊ ngành đã precompute (bảng FA_Industry_Aggregate) cho
        ngành ICB cấp Industry tương ứng `icb_code`. Mỗi bản ghi là 1 năm (year,
        peer_count và các chỉ số trung vị) → dùng để so sánh mã CP với mặt bằng
        ngành và tính CAGR ngành trong phân tích cơ bản.

        Trả về [] nếu không xác định được ngành, chưa precompute, hoặc lỗi truy vấn
        (so sánh ngành là phần bổ trợ, KHÔNG được làm hỏng pipeline phân tích).
        """
        industry_code = icb_to_industry_code(icb_code)
        if not industry_code:
            return []
        try:
            res = (
                supabase.table("FA_Industry_Aggregate")
                .select("*")
                .eq("category_id", industry_code)
                .execute()
            )
            return res.data or []
        except Exception as e:
            print(f"Error fetching industry aggregate for ICB {icb_code} ({industry_code}): {e}")
            return []

