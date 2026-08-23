"""
Financial Database Service
Handles database operations for financial metrics
"""
from supabase import create_client, Client
from app.config import settings
from typing import Optional, List, Dict

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


# Mã ngành ICB cấp 2 theo 2 chữ số đầu của mã ICB chi tiết (khớp bảng `Category`:
# 0500, 1300, 1700, 2300, 2700, 3300, 3500, 3700, 4500, 5300, 5500, 5700, 6500,
# 7500, 8300, 8500, 8600, 8700, 8900, 9500). Đã xác minh bằng dữ liệu thực tế
# trong BI_Profile: mọi icb_code hợp lệ đều khớp đúng 1 category theo 2 số đầu.
_ICB_CATEGORY_CODE = {
    "05": "0500", "13": "1300", "17": "1700", "23": "2300", "27": "2700",
    "33": "3300", "35": "3500", "37": "3700", "45": "4500", "53": "5300",
    "55": "5500", "57": "5700", "65": "6500", "75": "7500", "83": "8300",
    "85": "8500", "86": "8600", "87": "8700", "89": "8900", "95": "9500",
}


def icb_to_industry_code(icb_code) -> Optional[str]:
    """Ánh xạ mã ICB chi tiết (vd '8355') → mã ngành ICB cấp 2 ('8300').
    Trả về None nếu mã rỗng/không hợp lệ."""
    return _ICB_CATEGORY_CODE.get(str(icb_code or "").strip()[:2])


class FundamentalAnalysisService:
    """Service for financial metrics database operations"""

    @staticmethod
    def _resolve_stock_id(symbol: str) -> Optional[str]:
        """Resolve a stock symbol through Stock before querying FA tables."""
        stock_result = (
            supabase.table("Stock")
            .select("id")
            .eq("stock_symbol", symbol.strip().upper())
            .limit(1)
            .execute()
        )

        if not stock_result.data:
            return None

        return stock_result.data[0].get("id")

    @staticmethod
    def _get_latest_annual_rows(table_name: str, stock_id: str) -> List[Dict]:
        """Return the row for the latest available financial year."""
        result = (
            supabase.table(table_name)
            .select("*")
            .eq("stock_id", stock_id)
            .order("year", desc=True)
            .limit(1)
            .execute()
        )
        return result.data or []

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
            stock_id = FundamentalAnalysisService._resolve_stock_id(symbol)
            if not stock_id:
                return None

            result = (
                supabase.table("FA_Summary")
                .select("*")
                .eq("stock_id", stock_id)
                .limit(1)
                .execute()
            )
            rows = result.data or []
            return rows[0] if rows else None

        except Exception as e:
            print(f"Error fetching fundamental summary: {e}")
            raise ValueError(f"Failed to fetch fundamental summary: {str(e)}")

    @staticmethod
    def get_cash_flows(symbol: str) -> List[Dict]:
        """
        Get cash flow data for the latest available year of a symbol.
        """
        try:
            stock_id = FundamentalAnalysisService._resolve_stock_id(symbol)
            if not stock_id:
                return []

            return FundamentalAnalysisService._get_latest_annual_rows(
                "FA_CashFlow", stock_id
            )
        except Exception as e:
            print(f"Error fetching cash flows: {e}")
            raise ValueError(f"Failed to fetch cash flows: {str(e)}")

    @staticmethod
    def get_indicators(symbol: str) -> List[Dict]:
        """
        Get financial indicators for the latest available year of a symbol.
        """
        try:
            stock_id = FundamentalAnalysisService._resolve_stock_id(symbol)
            if not stock_id:
                return []

            return FundamentalAnalysisService._get_latest_annual_rows(
                "FA_Indicator", stock_id
            )
        except Exception as e:
            print(f"Error fetching financial indicators: {e}")
            raise ValueError(f"Failed to fetch financial indicators: {str(e)}")

    @staticmethod
    def get_indicator_history(symbol: str) -> List[Dict]:
        """Get the full annual financial-indicator history for a symbol.

        This is intentionally separate from ``get_indicators`` so existing API
        consumers keep receiving only the latest annual row. Historical rows
        are used by the analysis pipeline for multi-year metrics such as CAGR.
        """
        try:
            stock_id = FundamentalAnalysisService._resolve_stock_id(symbol)
            if not stock_id:
                return []

            result = (
                supabase.table("FA_Indicator")
                .select("*")
                .eq("stock_id", stock_id)
                .order("year", desc=False)
                .execute()
            )
            return result.data or []
        except Exception as e:
            print(f"Error fetching financial indicator history: {e}")
            raise ValueError(
                f"Failed to fetch financial indicator history: {str(e)}"
            )

    @staticmethod
    def get_income_statements(symbol: str) -> List[Dict]:
        """
        Get the full annual income-statement history for a symbol.

        This query is intentionally separate from ``_get_latest_annual_rows``:
        cash flow and financial indicators still return only their latest year.
        """
        try:
            stock_id = FundamentalAnalysisService._resolve_stock_id(symbol)
            if not stock_id:
                return []

            result = (
                supabase.table("FA_IncomeStatement")
                .select("*")
                .eq("stock_id", stock_id)
                .order("year", desc=False)
                .execute()
            )
            return result.data or []
        except Exception as e:
            print(f"Error fetching income statements: {e}")
            raise ValueError(f"Failed to fetch income statements: {str(e)}")

    @staticmethod
    def get_industry_aggregate(icb_code: str) -> List[Dict]:
        """
        Đọc chỉ tiêu TRUNG VỊ ngành đã precompute (bảng FA_Industry_Aggregate) cho
        ngành ICB cấp 2 tương ứng `icb_code`. Mỗi bản ghi là 1 năm (year,
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
