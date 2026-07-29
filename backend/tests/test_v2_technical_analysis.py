import unittest
from datetime import date
from unittest.mock import patch

import pandas as pd

from agentic_ai_v2.analyze.agents.technical import (
    _fetch_current_price,
    _format_output,
)


class V2TechnicalAnalysisCurrentPriceTests(unittest.TestCase):
    @patch(
        "agentic_ai_v2.analyze.agents.technical."
        "MarketService.get_current_stock_price"
    )
    def test_fetch_current_price_keeps_real_vnd_value(
        self,
        get_current_stock_price,
    ):
        get_current_stock_price.return_value = {"CurrentPrice": 128_500}

        self.assertEqual(_fetch_current_price("FPT"), 128_500.0)
        get_current_stock_price.assert_called_once_with("FPT")

    def test_live_price_is_output_without_affecting_candle_indicator_scoring(self):
        frame = pd.DataFrame(
            [
                {
                    "trading_time": pd.Timestamp("2026-07-28T00:00:00Z"),
                    "close": 100.0,
                    "sma_20": 90.0,
                    "sma_50": 84.0,
                },
                {
                    "trading_time": pd.Timestamp("2026-07-29T00:00:00Z"),
                    "close": 80.0,
                    "sma_20": 90.0,
                    "sma_50": 85.0,
                },
            ]
        )

        output = _format_output(
            symbol="FPT",
            interval="1d",
            source_table="Stock_Price_1d",
            requested_from_date=date(2026, 7, 28),
            requested_to_date=date(2026, 7, 29),
            frame=frame,
            selected_indicators={"ma"},
            current_price=128.5,
        )

        self.assertEqual(
            output["current_price"],
            {
                "value": 128.5,
                "time": None,
                "source": "Current_Stock_Price",
            },
        )
        self.assertEqual(output["indicators"]["ma"]["score"], 0)
        self.assertIn(
            "MA chưa có tín hiệu tăng rõ ràng",
            output["indicators"]["ma"]["reason"],
        )

    def test_missing_live_price_falls_back_to_latest_candle_close(self):
        frame = pd.DataFrame(
            [
                {
                    "trading_time": pd.Timestamp("2026-07-28T00:00:00Z"),
                    "close": 127.0,
                },
                {
                    "trading_time": pd.Timestamp("2026-07-29T00:00:00Z"),
                    "close": 128.0,
                },
            ]
        )

        output = _format_output(
            symbol="FPT",
            interval="1d",
            source_table="Stock_Price_1d",
            requested_from_date=date(2026, 7, 28),
            requested_to_date=date(2026, 7, 29),
            frame=frame,
            selected_indicators=set(),
        )

        self.assertEqual(
            output["current_price"],
            {
                "value": 128.0,
                "time": "2026-07-29T00:00:00+00:00",
                "source": "Stock_Price_1d",
            },
        )


if __name__ == "__main__":
    unittest.main()
