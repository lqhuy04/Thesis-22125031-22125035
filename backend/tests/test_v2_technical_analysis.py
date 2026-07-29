import unittest
from datetime import date
from unittest.mock import patch

import pandas as pd

from agentic_ai_v2.analyze.agents.technical import (
    _fetch_current_price,
    _format_output,
    _score_kdj,
    technical_agent,
)


class V2TechnicalAnalysisKDJTests(unittest.TestCase):
    def test_overbought_kdj_scores_zero_even_with_bullish_cross(self):
        score, reason = _score_kdj(
            pd.Series(
                {
                    "kdj_k": 85.0,
                    "kdj_d": 82.0,
                    "kdj_j": 90.0,
                }
            ),
            pd.Series(
                {
                    "kdj_k": 79.0,
                    "kdj_d": 80.0,
                    "kdj_j": 84.0,
                }
            ),
        )

        self.assertEqual(score, 0)
        self.assertIn("quá mua", reason)

    def test_oversold_recovery_scores_one(self):
        score, reason = _score_kdj(
            pd.Series(
                {
                    "kdj_k": 18.0,
                    "kdj_d": 22.0,
                    "kdj_j": 15.0,
                }
            ),
            pd.Series(
                {
                    "kdj_k": 14.0,
                    "kdj_d": 23.0,
                    "kdj_j": 12.0,
                }
            ),
        )

        self.assertEqual(score, 1)
        self.assertIn("quá bán", reason)

    def test_bullish_cross_outside_overbought_zone_scores_one(self):
        score, reason = _score_kdj(
            pd.Series(
                {
                    "kdj_k": 55.0,
                    "kdj_d": 52.0,
                    "kdj_j": 60.0,
                }
            ),
            pd.Series(
                {
                    "kdj_k": 48.0,
                    "kdj_d": 50.0,
                    "kdj_j": 46.0,
                }
            ),
        )

        self.assertEqual(score, 1)
        self.assertIn("cắt lên", reason)


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

    @patch(
        "agentic_ai_v2.analyze.agents.technical._fetch_current_price"
    )
    @patch(
        "agentic_ai_v2.analyze.agents.technical."
        "TechnicalIndicatorsService.calculate_all_indicators"
    )
    @patch(
        "agentic_ai_v2.analyze.agents.technical."
        "MarketService.get_stock_price_by_interval"
    )
    def test_backtest_plan_never_reads_live_current_price(
        self,
        get_prices,
        calculate_indicators,
        fetch_current_price,
    ):
        dates = pd.date_range("2023-01-01", periods=51, tz="UTC")
        get_prices.return_value = [
            {
                "trading_time": timestamp.isoformat(),
                "open": 100 + index,
                "high": 101 + index,
                "low": 99 + index,
                "close": 100 + index,
                "volume": 1_000 + index,
            }
            for index, timestamp in enumerate(dates)
        ]
        calculate_indicators.return_value = {
            "rsi_14": [50.0] * 51,
            "sma_20": [100.0] * 51,
            "sma_50": [90.0] * 51,
            "bb_upper": [160.0] * 51,
            "bb_middle": [120.0] * 51,
            "bb_lower": [80.0] * 51,
            "macd": [1.0] * 51,
            "macd_signal": [0.5] * 51,
            "macd_histogram": [0.5] * 51,
            "kdj_k": [50.0] * 51,
            "kdj_d": [45.0] * 51,
            "kdj_j": [55.0] * 51,
        }

        result = technical_agent(
            {
                "mode": "manual",
                "symbol": "FPT",
                "data_selection": {
                    "technical": {
                        "ma": True,
                        "boll": False,
                        "rsi": False,
                        "macd": False,
                        "kdj": False,
                    }
                },
                "plan": {
                    "technical": {
                        "interval": "1d",
                        "from_date": "2023-01-01",
                        "to_date": "2023-02-20",
                        "use_current_price": False,
                    }
                },
            }
        )["agent_results"]["technical_agent"]

        fetch_current_price.assert_not_called()
        self.assertEqual(
            result["current_price"],
            {
                "value": 150.0,
                "time": "2023-02-20T00:00:00+00:00",
                "source": "Stock_Price_1d",
            },
        )


if __name__ == "__main__":
    unittest.main()
