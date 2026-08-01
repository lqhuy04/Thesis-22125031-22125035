import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app.backtest as backtest
from app.backtest.single_indicator_backtest import INDICATORS
from app.backtest.vn30_stats import build_symbol_stats, update_vn30_stats_file
from app.services.backtest_pipeline_service import _build_market_dataframe


class BacktestScopeTests(unittest.TestCase):
    def test_walk_forward_is_not_exported(self):
        self.assertFalse(hasattr(backtest, "walk_forward"))

    def test_single_indicator_backtest_keeps_all_five_indicators(self):
        self.assertEqual(
            set(INDICATORS),
            {"RSI", "MACD", "KDJ", "Bollinger Bands", "MA Crossover"},
        )

    def test_vn30_stats_excludes_legacy_walk_forward_data(self):
        symbol_stats = build_symbol_stats(
            symbol="FPT",
            full_metrics={},
            engine_metrics={},
            benchmarks={},
            regime={},
            confidence={},
            stats={},
            full_trades=[],
        )
        self.assertNotIn("walk_forward", symbol_stats)

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "vn30_stats.json"
            output_path.write_text(
                '{"symbols":{"ACB":{"walk_forward":{"summary":{}}}}}',
                encoding="utf-8",
            )

            update_vn30_stats_file("FPT", symbol_stats, str(output_path))

            content = output_path.read_text(encoding="utf-8")
            self.assertNotIn("walk_forward", content)

    @patch(
        "app.services.backtest_pipeline_service."
        "MarketService.get_market_index_value_by_interval"
    )
    def test_market_benchmark_uses_index_daily_values(self, get_market_values):
        get_market_values.return_value = [
            {"trading_time": "2023-12-29T14:45:00", "value": "1129.93"},
            {"trading_time": "2024-01-02T14:45:00", "value": "1131.72"},
            {"trading_time": "2024-01-03T14:45:00", "value": "1144.17"},
        ]

        frame = _build_market_dataframe(
            index_name="VNINDEX",
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        get_market_values.assert_called_once_with(
            index_name="VNINDEX",
            interval="1d",
            limit=10_000,
        )
        self.assertEqual(frame["close"].tolist(), [1131.72])
        self.assertEqual(
            frame["datetime"].dt.strftime("%Y-%m-%d").tolist(),
            ["2024-01-02"],
        )


if __name__ == "__main__":
    unittest.main()
