import tempfile
import unittest
from pathlib import Path

import app.backtest as backtest
from app.backtest.single_indicator_backtest import INDICATORS
from app.backtest.vn30_stats import build_symbol_stats, update_vn30_stats_file


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


if __name__ == "__main__":
    unittest.main()
