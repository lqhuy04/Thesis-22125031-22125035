import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.services.fundamental_analysis_service import FundamentalAnalysisService


class FundamentalAnalysisServiceTests(unittest.TestCase):
    def test_get_indicators_keeps_latest_annual_row_contract(self):
        latest_row = [{"year": 2025, "roe": 0.25}]

        with (
            patch.object(
                FundamentalAnalysisService,
                "_resolve_stock_id",
                return_value="stock-id",
            ),
            patch.object(
                FundamentalAnalysisService,
                "_get_latest_annual_rows",
                return_value=latest_row,
            ) as latest_rows,
        ):
            result = FundamentalAnalysisService.get_indicators("vnm")

        self.assertEqual(result, latest_row)
        latest_rows.assert_called_once_with("FA_Indicator", "stock-id")

    def test_indicator_history_returns_all_rows_in_year_order(self):
        rows = [
            {"year": 2021, "roe": 0.2},
            {"year": 2022, "roe": 0.21},
            {"year": 2023, "roe": 0.22},
            {"year": 2024, "roe": 0.23},
            {"year": 2025, "roe": 0.24},
        ]
        query = MagicMock()
        query.select.return_value = query
        query.eq.return_value = query
        query.order.return_value = query
        query.execute.return_value = SimpleNamespace(data=rows)
        mocked_supabase = MagicMock()
        mocked_supabase.table.return_value = query

        with (
            patch.object(
                FundamentalAnalysisService,
                "_resolve_stock_id",
                return_value="stock-id",
            ),
            patch(
                "app.services.fundamental_analysis_service.supabase",
                mocked_supabase,
            ),
        ):
            result = FundamentalAnalysisService.get_indicator_history("vnm")

        self.assertEqual(result, rows)
        mocked_supabase.table.assert_called_once_with("FA_Indicator")
        query.eq.assert_called_once_with("stock_id", "stock-id")
        query.order.assert_called_once_with("year", desc=False)
        query.limit.assert_not_called()

    def test_income_statements_return_full_history_without_changing_latest_helper(self):
        rows = [
            {"year": 2021, "net_revenue": 1, "net_profit_after_tax": 1},
            {"year": 2022, "net_revenue": 2, "net_profit_after_tax": 2},
            {"year": 2023, "net_revenue": 3, "net_profit_after_tax": 3},
            {"year": 2024, "net_revenue": 4, "net_profit_after_tax": 4},
            {"year": 2025, "net_revenue": 5, "net_profit_after_tax": 5},
        ]
        query = MagicMock()
        query.select.return_value = query
        query.eq.return_value = query
        query.order.return_value = query
        query.execute.return_value = SimpleNamespace(data=rows)
        mocked_supabase = MagicMock()
        mocked_supabase.table.return_value = query

        with (
            patch.object(
                FundamentalAnalysisService,
                "_resolve_stock_id",
                return_value="stock-id",
            ),
            patch.object(
                FundamentalAnalysisService,
                "_get_latest_annual_rows",
            ) as latest_rows,
            patch(
                "app.services.fundamental_analysis_service.supabase",
                mocked_supabase,
            ),
        ):
            result = FundamentalAnalysisService.get_income_statements("vnm")

        self.assertEqual(result, rows)
        mocked_supabase.table.assert_called_once_with("FA_IncomeStatement")
        query.eq.assert_called_once_with("stock_id", "stock-id")
        query.order.assert_called_once_with("year", desc=False)
        query.limit.assert_not_called()
        latest_rows.assert_not_called()


if __name__ == "__main__":
    unittest.main()
