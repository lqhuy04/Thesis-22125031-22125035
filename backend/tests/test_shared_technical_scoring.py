import unittest
from datetime import date, timedelta

import pandas as pd

from agentic_ai_v2.analyze.agents.technical import _format_output
from agentic_ai_v2.analyze.technical_scoring import (
    SCORE_COLUMN_BY_INDICATOR,
    TECHNICAL_INDICATORS,
    score_indicators,
)
from app.backtest.engine import ScoringEngine


class SharedTechnicalScoringTests(unittest.TestCase):
    @staticmethod
    def _build_frame() -> pd.DataFrame:
        start = date(2026, 1, 1)
        rows = [
            {
                "trading_time": pd.Timestamp(
                    start + timedelta(days=position),
                    tz="UTC",
                ),
                "close": 100.0,
                "rsi_14": 45.0,
                "sma_20": 99.0,
                "sma_50": 100.0,
                "bb_upper": 110.0,
                "bb_middle": 100.0,
                "bb_lower": 90.0,
                "macd": -0.2,
                "macd_signal": -0.1,
                "macd_histogram": -0.1,
                "kdj_k": 40.0,
                "kdj_d": 45.0,
                "kdj_j": 35.0,
            }
            for position in range(51)
        ]
        rows[-2].update(
            {
                "close": 99.0,
                "rsi_14": 49.0,
                "sma_20": 99.0,
                "sma_50": 100.0,
                "macd": -0.2,
                "macd_signal": -0.1,
                "macd_histogram": -0.1,
                "kdj_k": 40.0,
                "kdj_d": 45.0,
                "kdj_j": 35.0,
            }
        )
        rows[-1].update(
            {
                "close": 101.0,
                "rsi_14": 51.0,
                "sma_20": 101.0,
                "sma_50": 100.0,
                "macd": 0.1,
                "macd_signal": 0.0,
                "macd_histogram": 0.1,
                "kdj_k": 50.0,
                "kdj_d": 45.0,
                "kdj_j": 55.0,
            }
        )
        return pd.DataFrame(rows)

    def test_analyze_and_backtest_adapters_use_shared_scores(self):
        frame = self._build_frame()
        expected = score_indicators(frame.iloc[-1], frame.iloc[-2])

        analyze_output = _format_output(
            symbol="FPT",
            interval="1d",
            source_table="Stock_Price_1d",
            requested_from_date=frame.iloc[-2]["trading_time"].date(),
            requested_to_date=frame.iloc[-1]["trading_time"].date(),
            frame=frame,
            selected_indicators=set(TECHNICAL_INDICATORS),
        )
        scored_frame = ScoringEngine().score_dataframe(frame)

        self.assertEqual(analyze_output["indicators"], expected)
        for name, column in SCORE_COLUMN_BY_INDICATOR.items():
            self.assertEqual(
                scored_frame.iloc[-1][column],
                expected[name]["score"],
            )
        self.assertEqual(scored_frame.iloc[-1]["total_score"], 5.0)
        self.assertTrue(scored_frame.iloc[:50]["total_score"].isna().all())


if __name__ == "__main__":
    unittest.main()
