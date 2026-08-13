import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.services.fundamental_analysis_service import FundamentalAnalysisService


class FundamentalAnalysisServiceTests(unittest.TestCase):
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
